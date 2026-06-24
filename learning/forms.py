from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import CBT, Choice, Question, UserPreference, Video, Voucher


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
        fields = ["text", "explanation", "order"]


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
