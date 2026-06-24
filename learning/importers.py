from dataclasses import dataclass, field

from django.db import transaction

from .models import CBT, Choice, Question


REQUIRED_COLUMNS = [
    "cbt_title",
    "cbt_description",
    "passing_score",
    "question_order",
    "question_text",
    "choice_a",
    "choice_b",
    "choice_c",
    "choice_d",
    "correct_choice",
    "explanation",
]


@dataclass
class CBTImportResult:
    created_cbts: int = 0
    updated_cbts: int = 0
    created_questions: int = 0
    created_choices: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


def normalize(value):
    return "" if value is None else str(value).strip()


def parse_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def import_cbt_from_excel(uploaded_file, mode):
    try:
        from openpyxl import load_workbook
    except ImportError:
        return CBTImportResult(errors=["Dependency openpyxl belum terpasang. Jalankan: pip install openpyxl"])

    try:
        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
    except Exception as exc:
        return CBTImportResult(errors=[f"File Excel tidak bisa dibaca: {exc}"])

    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return CBTImportResult(errors=["File Excel kosong."])

    headers = [normalize(value).lower() for value in rows[0]]
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        return CBTImportResult(errors=["Kolom wajib belum ada: " + ", ".join(missing)])

    index = {column: headers.index(column) for column in REQUIRED_COLUMNS}
    parsed_rows = []
    result = CBTImportResult()

    for excel_row_number, row in enumerate(rows[1:], start=2):
        if not row or not any(normalize(value) for value in row):
            continue

        def value(column):
            position = index[column]
            return row[position] if position < len(row) else ""

        cbt_title = normalize(value("cbt_title"))
        cbt_description = normalize(value("cbt_description"))
        passing_score = parse_int(value("passing_score"), 70)
        question_order = parse_int(value("question_order"), len(parsed_rows) + 1)
        question_text = normalize(value("question_text"))
        choices = [
            normalize(value("choice_a")),
            normalize(value("choice_b")),
            normalize(value("choice_c")),
            normalize(value("choice_d")),
        ]
        correct_choice = normalize(value("correct_choice")).upper()
        explanation = normalize(value("explanation"))

        row_errors = []
        if not cbt_title:
            row_errors.append("cbt_title wajib diisi")
        if passing_score is None or not 0 <= passing_score <= 100:
            row_errors.append("passing_score harus angka 0-100")
        if question_order is None or question_order < 1:
            row_errors.append("question_order harus angka minimal 1")
        if not question_text:
            row_errors.append("question_text wajib diisi")
        if len([choice for choice in choices if choice]) < 2:
            row_errors.append("minimal 2 pilihan jawaban wajib diisi")
        if correct_choice not in {"A", "B", "C", "D"}:
            row_errors.append("correct_choice harus A, B, C, atau D")
        elif not choices[ord(correct_choice) - ord("A")]:
            row_errors.append("pilihan yang ditandai benar tidak boleh kosong")

        if row_errors:
            result.errors.append(f"Baris {excel_row_number}: " + "; ".join(row_errors))
            continue

        parsed_rows.append({
            "cbt_title": cbt_title,
            "cbt_description": cbt_description,
            "passing_score": passing_score,
            "question_order": question_order,
            "question_text": question_text,
            "choices": choices,
            "correct_choice": correct_choice,
            "explanation": explanation,
        })

    if result.errors:
        return result
    if not parsed_rows:
        return CBTImportResult(errors=["Tidak ada baris soal yang bisa diimport."])

    touched_cbt_ids = set()
    with transaction.atomic():
        for item in parsed_rows:
            cbt, created = CBT.objects.get_or_create(
                title=item["cbt_title"],
                defaults={
                    "description": item["cbt_description"],
                    "passing_score": item["passing_score"],
                    "is_active": True,
                },
            )
            if created:
                result.created_cbts += 1
            else:
                result.updated_cbts += 1 if cbt.id not in touched_cbt_ids else 0
                cbt.description = item["cbt_description"]
                cbt.passing_score = item["passing_score"]
                cbt.is_active = True
                cbt.save(update_fields=["description", "passing_score", "is_active"])

            if mode == "replace" and cbt.id not in touched_cbt_ids:
                cbt.questions.all().delete()
            touched_cbt_ids.add(cbt.id)

            question = Question.objects.create(
                cbt=cbt,
                text=item["question_text"],
                explanation=item["explanation"],
                order=item["question_order"],
            )
            result.created_questions += 1

            correct_index = ord(item["correct_choice"]) - ord("A")
            for index, choice_text in enumerate(item["choices"]):
                if not choice_text:
                    continue
                Choice.objects.create(
                    question=question,
                    text=choice_text,
                    is_correct=index == correct_index,
                )
                result.created_choices += 1

    return result


def build_cbt_import_template_xlsx():
    from io import BytesIO
    from zipfile import ZIP_DEFLATED, ZipFile
    from xml.sax.saxutils import escape

    rows = [
        REQUIRED_COLUMNS,
        [
            "CBT Kosakata Korea",
            "Latihan kosakata dasar Bahasa Korea",
            "70",
            "1",
            "Apa arti sekolah?",
            "Sekolah",
            "Rumah",
            "Pasar",
            "Kantor",
            "A",
            "학교 berarti sekolah.",
        ],
        [
            "CBT Kosakata Korea",
            "Latihan kosakata dasar Bahasa Korea",
            "70",
            "2",
            "Apa arti air?",
            "Air",
            "Buku",
            "Makanan",
            "Teman",
            "A",
            "물 berarti air.",
        ],
    ]

    def col_name(index):
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    def cell_xml(row_number, col_number, value):
        reference = f"{col_name(col_number)}{row_number}"
        return f'<c r="{reference}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'

    sheet_rows = []
    for row_number, row in enumerate(rows, start=1):
        cells = "".join(cell_xml(row_number, col_number, value) for col_number, value in enumerate(row, start=1))
        sheet_rows.append(f'<row r="{row_number}">{cells}</row>')

    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <dimension ref="A1:K{len(rows)}"/>
  <sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>'''

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>''')
        archive.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''')
        archive.writestr("xl/workbook.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Template CBT" sheetId="1" r:id="rId1"/></sheets>
</workbook>''')
        archive.writestr("xl/_rels/workbook.xml.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>''')
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    output.seek(0)
    return output.getvalue()
