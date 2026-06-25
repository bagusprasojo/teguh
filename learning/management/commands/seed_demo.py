from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from learning.models import CBT, Choice, Question, UBT, UBTChoice, UBTPackage, UBTQuestion, UserAccess, UserPreference, Video, Voucher


class Command(BaseCommand):
    help = "Seed demo data for Koready MVP."

    def handle(self, *args, **options):
        admin = self.upsert_user(
            username="admin",
            email="admin@koready.local",
            password="admin12345",
            is_staff=True,
            is_superuser=True,
        )
        demo_user = self.upsert_user(
            username="user",
            email="user@koready.local",
            password="user12345",
            is_staff=False,
            is_superuser=False,
        )
        UserAccess.objects.get_or_create(user=admin)
        UserAccess.objects.get_or_create(user=demo_user)
        UserPreference.objects.get_or_create(user=admin)
        UserPreference.objects.get_or_create(user=demo_user, defaults={"theme_mode": "soft", "accent_color": "emerald", "text_size": "large"})

        self.seed_vouchers()
        self.seed_videos()
        self.seed_cbts()
        self.seed_ubt()

        self.stdout.write(self.style.SUCCESS("Seeder selesai."))
        self.stdout.write("Admin: admin / admin12345")
        self.stdout.write("User : user / user12345")

    def upsert_user(self, username, email, password, is_staff, is_superuser):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()
        action = "dibuat" if created else "diupdate"
        self.stdout.write(f"User {username} {action}.")
        return user

    def seed_vouchers(self):
        vouchers = [
            ("KOREADY7", 7),
            ("KOREADY14", 14),
            ("KOREADY30", 30),
            ("KOREADY60", 60),
            ("KOREADY90", 90),
        ]
        for code, days in vouchers:
            voucher, _ = Voucher.objects.update_or_create(
                code=code,
                defaults={"duration_days": days, "is_active": True},
            )
            self.stdout.write(f"Voucher {voucher.code} siap ({days} hari).")

    def seed_videos(self):
        videos = [
            {
                "title": "Hangul Dasar: Membaca Huruf Korea",
                "description": "Pengenalan huruf vokal dan konsonan Korea untuk pemula. Contoh: \ud55c\uae00, \uc548\ub155\ud558\uc138\uc694.",
                "youtube_url": "https://www.youtube.com/watch?v=s5aobqyEaMQ",
            },
            {
                "title": "Salam Sehari-hari dalam Bahasa Korea",
                "description": "Belajar sapaan umum seperti \uc548\ub155\ud558\uc138\uc694, \uac10\uc0ac\ud569\ub2c8\ub2e4, dan \uc548\ub155\ud788 \uac00\uc138\uc694.",
                "youtube_url": "https://www.youtube.com/watch?v=0ZhOeA0RD9o",
            },
            {
                "title": "Kosakata Korea untuk Aktivitas Harian",
                "description": "Materi kosakata dasar tentang sekolah, rumah, makan, belajar, dan bekerja.",
                "youtube_url": "https://www.youtube.com/watch?v=Gg-VZxBIZjo",
            },
            {
                "title": "Partikel Dasar: \uc740/\ub294 dan \uc774/\uac00",
                "description": "Penjelasan ringkas fungsi partikel topik dan subjek dalam kalimat Korea sederhana.",
                "youtube_url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
            },
            {
                "title": "Latihan Membaca Kalimat Korea Pendek",
                "description": "Praktik membaca kalimat pendek dengan Hangul, romanisasi, dan arti Bahasa Indonesia.",
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
        ]
        for item in videos:
            video, _ = Video.objects.update_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "youtube_url": item["youtube_url"],
                    "is_active": True,
                },
            )
            self.stdout.write(f"Video siap: id={video.pk}")

    def seed_cbts(self):
        cbts = [
            {
                "title": "CBT Hangul Dasar",
                "description": "Latihan mengenali huruf dan bunyi Hangul dasar.",
                "questions": [
                    ("Apa nama sistem tulisan Korea?", ["Hangul", "Kanji", "Hiragana", "Latin"], 0, "Bahasa Korea menggunakan Hangul."),
                    ("Bunyi huruf \u3131 adalah?", ["g/k", "n", "m", "s"], 0, "\u3131 dibaca g atau k tergantung posisi."),
                    ("Kata \ud55c\uae00 dibaca?", ["Hangul", "Hana", "Hanguk", "Hago"], 0, "\ud55c\uae00 berarti Hangul."),
                ],
            },
            {
                "title": "CBT Salam Korea",
                "description": "Latihan sapaan dan ungkapan sopan sehari-hari.",
                "questions": [
                    ("Arti \uc548\ub155\ud558\uc138\uc694 adalah?", ["Halo", "Terima kasih", "Maaf", "Selamat tinggal"], 0, "Ungkapan ini adalah salam sopan."),
                    ("Ungkapan terima kasih yang sopan adalah?", ["\uac10\uc0ac\ud569\ub2c8\ub2e4", "\ubb3c", "\ud559\uad50", "\uc0ac\ub791"], 0, "\uac10\uc0ac\ud569\ub2c8\ub2e4 berarti terima kasih."),
                    ("\uc548\ub155\ud788 \uac00\uc138\uc694 dipakai saat?", ["Orang lain pergi", "Memesan makanan", "Menghitung angka", "Memperkenalkan nama"], 0, "Dipakai kepada orang yang pergi."),
                ],
            },
            {
                "title": "CBT Kosakata Dasar",
                "description": "Latihan arti kosakata Korea dasar.",
                "questions": [
                    ("Arti \ud559\uad50 adalah?", ["Sekolah", "Rumah", "Pasar", "Kantor"], 0, "\ud559\uad50 berarti sekolah."),
                    ("Arti \ubb3c adalah?", ["Air", "Nasi", "Buku", "Nama"], 0, "\ubb3c berarti air."),
                    ("Arti \ucc45 adalah?", ["Buku", "Kopi", "Teman", "Meja"], 0, "\ucc45 berarti buku."),
                ],
            },
            {
                "title": "CBT Grammar Pemula",
                "description": "Latihan pola kalimat dan partikel dasar.",
                "questions": [
                    ("Partikel topik yang benar adalah?", ["\uc740/\ub294", "\uc744/\ub97c", "\uc5d0\uc11c", "\uc640/\uacfc"], 0, "\uc740/\ub294 menandai topik."),
                    ("Pola kalimat sopan dasar untuk 'adalah' memakai?", ["\uc785\ub2c8\ub2e4", "\ud558\uace0", "\uc5c6\ub2e4", "\uc624\ub2e4"], 0, "\uc785\ub2c8\ub2e4 adalah bentuk formal sopan."),
                    ("Dalam \uc800\ub294 \ud559\uc0dd\uc785\ub2c8\ub2e4, arti \uc800\ub294 adalah?", ["Saya", "Kamu", "Sekolah", "Guru"], 0, "\uc800 adalah saya, \ub294 adalah partikel topik."),
                ],
            },
            {
                "title": "CBT Reading Pendek",
                "description": "Latihan memahami kalimat Korea pendek.",
                "questions": [
                    ("Kalimat \uc800\ub294 \ud559\uc0dd\uc785\ub2c8\ub2e4 berarti?", ["Saya adalah pelajar", "Saya makan", "Ini buku", "Dia guru"], 0, "\ud559\uc0dd berarti pelajar."),
                    ("\uc774\uac83\uc740 \ucc45\uc785\ub2c8\ub2e4 berarti?", ["Ini adalah buku", "Itu adalah air", "Saya guru", "Halo"], 0, "\uc774\uac83 berarti ini, \ucc45 berarti buku."),
                    ("\uce5c\uad6c\uac00 \uc654\uc5b4\uc694 berarti?", ["Teman datang", "Teman pergi", "Saya belajar", "Buku ada"], 0, "\uce5c\uad6c berarti teman dan \uc654\uc5b4\uc694 berarti datang."),
                ],
            },
        ]
        for cbt_data in cbts:
            cbt, _ = CBT.objects.update_or_create(
                title=cbt_data["title"],
                defaults={
                    "description": cbt_data["description"],
                    "passing_score": 70,
                    "is_active": True,
                },
            )
            cbt.questions.all().delete()
            for order, (text, choices, correct_index, explanation) in enumerate(cbt_data["questions"], start=1):
                question = Question.objects.create(cbt=cbt, text=text, explanation=explanation, order=order)
                for index, choice_text in enumerate(choices):
                    Choice.objects.create(question=question, text=choice_text, is_correct=index == correct_index)
            self.stdout.write(f"CBT siap: id={cbt.pk}")


    def seed_ubt(self):
        packages = [
            ("UBT Basic", "Paket UBT latihan dasar Bahasa Korea.", 150000, 30),
            ("UBT Intensive", "Paket UBT intensif dengan masa akses lebih panjang.", 250000, 60),
        ]
        for name, description, price, days in packages:
            package, _ = UBTPackage.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "price": price,
                    "access_duration_days": days,
                    "is_active": True,
                },
            )
            self.stdout.write(f"Paket UBT siap: id={package.pk}")

        ubt, _ = UBT.objects.update_or_create(
            title="UBT Bahasa Korea Dasar",
            defaults={
                "description": "Latihan UBT dasar Bahasa Korea.",
                "passing_score": 70,
                "is_active": True,
            },
        )
        ubt.questions.all().delete()
        questions = [
            ("Apa arti kata sekolah?", ["Sekolah", "Rumah", "Pasar", "Kantor"], 0, "hakgyo berarti sekolah."),
            ("Apa arti kata air?", ["Air", "Buku", "Makanan", "Teman"], 0, "mul berarti air."),
            ("Sapaan sopan untuk halo adalah?", ["Annyeonghaseyo", "Kamsahamnida", "Mianhamnida", "Jaljayo"], 0, "Annyeonghaseyo adalah salam sopan."),
        ]
        for order, (text, choices, correct_index, explanation) in enumerate(questions, start=1):
            question = UBTQuestion.objects.create(ubt=ubt, text=text, explanation=explanation, order=order)
            for index, choice_text in enumerate(choices):
                UBTChoice.objects.create(question=question, text=choice_text, is_correct=index == correct_index)
        self.stdout.write(f"UBT siap: id={ubt.pk}")
