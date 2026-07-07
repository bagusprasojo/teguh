from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import BlogCategory, BlogPost, CBT, Choice, Question, UBT, UBTChoice, UBTPackage, UBTQuestion, UBTRegistration, UserPreference, UserProfile, Video, Voucher




class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username atau Email")

    def clean_username(self):
        identifier = self.cleaned_data["username"].strip()
        if "@" not in identifier:
            return identifier
        users = User.objects.filter(email__iexact=identifier)
        if users.count() == 1:
            return users.first().username
        if users.count() > 1:
            raise forms.ValidationError("Email ini dipakai oleh lebih dari satu akun. Silakan login menggunakan username.")
        return identifier

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Akun belum aktif. Silakan cek email untuk verifikasi akun.",
                code="inactive",
            )
        super().confirm_login_allowed(user)


class BlogCategoryForm(forms.ModelForm):
    class Meta:
        model = BlogCategory
        fields = ["name", "slug"]
        labels = {
            "name": "Nama kategori",
            "slug": "Slug",
        }
        help_texts = {
            "slug": "Kosongkan untuk dibuat otomatis dari nama kategori.",
        }


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ["title", "slug", "category", "excerpt", "content", "cover", "status", "published_at"]
        labels = {
            "title": "Judul",
            "slug": "Slug",
            "category": "Kategori",
            "excerpt": "Ringkasan",
            "content": "Konten",
            "cover": "Cover",
            "status": "Status",
            "published_at": "Tanggal publish",
        }
        help_texts = {
            "slug": "Kosongkan untuk dibuat otomatis dari judul artikel.",
            "published_at": "Kosongkan agar otomatis diisi saat status Published.",
            "excerpt": "Opsional. Jika dikosongkan, ringkasan otomatis diambil dari teks awal konten artikel.",
            "cover": "Opsional. Jika dikosongkan, sistem memakai gambar pertama dari konten artikel untuk tampilan list/landing page.",
        }
        widgets = {
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Username",
        }
        help_texts = {
            "username": "Gunakan huruf, angka, atau karakter @/./+/-/_.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Konfirmasi password"
        self.fields["password1"].help_text = "Minimal 8 karakter dan jangan memakai password yang terlalu umum."
        self.fields["password2"].help_text = "Masukkan password yang sama untuk konfirmasi."
    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar. Silakan login atau gunakan email lain.")
        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "username": "Username",
            "first_name": "Nama depan",
            "last_name": "Nama belakang",
            "email": "Email",
        }
        help_texts = {
            "username": "Username dipakai untuk login.",
        }

class UserPhotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["photo"]
        labels = {
            "photo": "Foto profil",
        }
        help_texts = {
            "photo": "Upload foto profil. Foto akan tampil berbentuk lingkaran di menu kanan atas.",
        }

class VoucherRedeemForm(forms.Form):
    code = forms.CharField(max_length=40, label="Kode voucher")


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ["title", "description", "youtube_url", "cover", "is_active"]
        labels = {
            "title": "Judul",
            "description": "Deskripsi",
            "youtube_url": "URL YouTube",
            "cover": "Cover",
            "is_active": "Aktif",
        }
        help_texts = {
            "cover": "Kosongkan cover jika ingin otomatis memakai thumbnail YouTube sebagai cover.",
        }


class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = ["code", "duration_days", "is_active"]


class CBTForm(forms.ModelForm):
    class Meta:
        model = CBT
        fields = ["title", "description", "passing_score", "is_active"]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "media_type", "media_file", "media_url", "explanation", "order", "is_active"]
        labels = {
            "text": "Teks soal",
            "media_type": "Tipe media",
            "media_file": "Upload media",
            "media_url": "URL media",
            "explanation": "Pembahasan",
            "order": "Urutan",
            "is_active": "Aktif",
        }
        help_texts = {
            "media_file": "Upload gambar/audio/video lokal. Kosongkan jika memakai URL.",
            "media_url": "Gunakan untuk YouTube atau media eksternal. Kosongkan jika upload file.",
        }

    def clean(self):
        cleaned = super().clean()
        media_type = cleaned.get("media_type")
        media_file = cleaned.get("media_file")
        media_url = cleaned.get("media_url")
        if media_type == Question.MEDIA_NONE:
            return cleaned
        if media_type == Question.MEDIA_YOUTUBE and not media_url:
            self.add_error("media_url", "URL YouTube wajib diisi jika tipe media YouTube.")
        if media_type in {Question.MEDIA_IMAGE, Question.MEDIA_AUDIO, Question.MEDIA_VIDEO} and not (media_file or media_url):
            self.add_error("media_file", "Upload media atau isi URL media untuk tipe ini.")
        return cleaned


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]



class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ["theme_mode", "accent_color", "text_size"]
        labels = {
            "theme_mode": "Mode warna",
            "accent_color": "Warna aksen",
            "text_size": "Ukuran teks",
        }


class CBTImportForm(forms.Form):
    MODE_REPLACE = "replace"
    MODE_APPEND = "append"
    MODE_CHOICES = [
        (MODE_REPLACE, "Replace - hapus soal lama pada CBT yang sama"),
        (MODE_APPEND, "Append - tambahkan soal ke CBT yang sudah ada"),
    ]

    file = forms.FileField(
        label="File Excel (.xlsx)",
        help_text="Upload file .xlsx sesuai format kolom yang disediakan.",
    )
    mode = forms.ChoiceField(
        label="Mode import",
        choices=MODE_CHOICES,
        initial=MODE_REPLACE,
        widget=forms.RadioSelect,
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("File harus berformat .xlsx.")
        return uploaded


class UBTPackageForm(forms.ModelForm):
    class Meta:
        model = UBTPackage
        fields = ["name", "description", "price", "access_duration_days", "is_active"]
        labels = {
            "name": "Nama paket",
            "description": "Deskripsi",
            "price": "Nominal biaya",
            "access_duration_days": "Masa berlaku voucher UBT (hari)",
            "is_active": "Aktif",
        }


class UBTForm(forms.ModelForm):
    class Meta:
        model = UBT
        fields = ["title", "description", "passing_score", "duration_minutes", "is_active"]
        labels = {
            "title": "Judul UBT",
            "description": "Deskripsi",
            "passing_score": "Nilai kelulusan",
            "duration_minutes": "Durasi pengerjaan (menit)",
            "is_active": "Aktif",
        }


class UBTRegistrationForm(forms.ModelForm):
    class Meta:
        model = UBTRegistration
        fields = ["package", "full_name", "email", "whatsapp_number", "note"]
        labels = {
            "package": "Paket UBT",
            "full_name": "Nama lengkap",
            "email": "Email",
            "whatsapp_number": "Nomor WhatsApp",
            "note": "Tujuan mengikuti UBT / catatan",
        }
        widgets = {
            "note": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["package"].queryset = UBTPackage.objects.filter(is_active=True)
        if user and not self.is_bound:
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            self.fields["full_name"].initial = full_name
            self.fields["email"].initial = user.email


class UBTRegistrationStatusForm(forms.ModelForm):
    class Meta:
        model = UBTRegistration
        fields = ["status"]
        labels = {"status": "Status pendaftaran"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = [
            (UBTRegistration.STATUS_PENDING_PAYMENT, "Pending payment"),
            (UBTRegistration.STATUS_WAITING_CONFIRMATION, "Waiting confirmation"),
            (UBTRegistration.STATUS_APPROVED, "Approved - terbitkan voucher"),
            (UBTRegistration.STATUS_REJECTED, "Rejected"),
        ]


class UBTQuestionForm(forms.ModelForm):
    class Meta:
        model = UBTQuestion
        fields = ["text", "media_type", "media_file", "media_url", "explanation", "order", "is_active"]
        labels = {
            "text": "Teks soal",
            "media_type": "Tipe media",
            "media_file": "Upload media",
            "media_url": "URL media",
            "explanation": "Pembahasan",
            "order": "Urutan",
            "is_active": "Aktif",
        }
        help_texts = {
            "media_file": "Upload gambar/audio/video lokal. Kosongkan jika memakai URL.",
            "media_url": "Gunakan untuk YouTube atau media eksternal. Kosongkan jika upload file.",
        }

    def clean(self):
        cleaned = super().clean()
        media_type = cleaned.get("media_type")
        media_file = cleaned.get("media_file")
        media_url = cleaned.get("media_url")
        if media_type == UBTQuestion.MEDIA_NONE:
            return cleaned
        if media_type == UBTQuestion.MEDIA_YOUTUBE and not media_url:
            self.add_error("media_url", "URL YouTube wajib diisi jika tipe media YouTube.")
        if media_type in {UBTQuestion.MEDIA_IMAGE, UBTQuestion.MEDIA_AUDIO, UBTQuestion.MEDIA_VIDEO} and not (media_file or media_url):
            self.add_error("media_file", "Upload media atau isi URL media untuk tipe ini.")
        return cleaned


class UBTChoiceForm(forms.ModelForm):
    class Meta:
        model = UBTChoice
        fields = ["text", "is_correct"]


class UBTImportForm(forms.Form):
    MODE_REPLACE = "replace"
    MODE_APPEND = "append"
    MODE_CHOICES = [
        (MODE_REPLACE, "Replace - hapus soal lama pada UBT yang sama"),
        (MODE_APPEND, "Append - tambahkan soal ke UBT yang sudah ada"),
    ]

    file = forms.FileField(
        label="File Excel (.xlsx)",
        help_text="Upload file .xlsx sesuai format kolom UBT.",
    )
    mode = forms.ChoiceField(
        label="Mode import",
        choices=MODE_CHOICES,
        initial=MODE_REPLACE,
        widget=forms.RadioSelect,
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("File harus berformat .xlsx.")
        return uploaded













