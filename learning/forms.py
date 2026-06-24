from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import CBT, Choice, Question, UserPreference, Video, Voucher


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class VoucherRedeemForm(forms.Form):
    code = forms.CharField(max_length=40, label="Kode voucher")


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ["title", "description", "youtube_url", "cover", "is_active"]


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
