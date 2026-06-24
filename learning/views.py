from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CBTForm, QuestionForm, RegisterForm, UserPreferenceForm, VideoForm, VoucherForm, VoucherRedeemForm
from .models import CBT, CBTAttempt, CBTAttemptAnswer, Choice, Question, UserAccess, UserPreference, Video, Voucher


BRAND_NAME = "Koready"



class UserLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.user.is_staff:
            self.request.session["show_access_notice"] = True
        return response

def get_access(user):
    access, _ = UserAccess.objects.get_or_create(user=user)
    return access


def has_active_access(user):
    return user.is_authenticated and get_access(user).is_active


def admin_required(view_func):
    return login_required(user_passes_test(lambda user: user.is_staff)(view_func))


def home(request):
    return render(request, "learning/home.html", {"brand_name": BRAND_NAME})


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.save()
        UserAccess.objects.create(user=user)
        login(request, user)
        if not user.is_staff:
            request.session["show_access_notice"] = True
        messages.success(request, "Akun berhasil dibuat. Masukkan voucher untuk membuka akses belajar.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form, "brand_name": BRAND_NAME})


@login_required
def dashboard(request):
    access = get_access(request.user)
    return render(request, "learning/dashboard.html", {
        "access": access,
        "video_count": Video.objects.filter(is_active=True).count(),
        "cbt_count": CBT.objects.filter(is_active=True).count(),
        "attempts": CBTAttempt.objects.filter(user=request.user)[:5],
        "show_access_notice": request.session.pop("show_access_notice", False),
    })


@login_required
def redeem_voucher(request):
    form = VoucherRedeemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"].strip()
        try:
            voucher = Voucher.objects.select_for_update().get(code__iexact=code)
        except Voucher.DoesNotExist:
            messages.error(request, "Kode voucher tidak ditemukan.")
            return redirect("redeem_voucher")
        with transaction.atomic():
            voucher = Voucher.objects.select_for_update().get(pk=voucher.pk)
            if not voucher.is_active:
                messages.error(request, "Voucher ini tidak aktif.")
            elif voucher.is_redeemed:
                messages.error(request, "Voucher ini sudah pernah digunakan.")
            else:
                access = get_access(request.user)
                access.add_days(voucher.duration_days)
                voucher.redeemed_by = request.user
                voucher.redeemed_at = timezone.now()
                voucher.save(update_fields=["redeemed_by", "redeemed_at"])
                messages.success(request, f"Voucher berhasil digunakan. Akses bertambah {voucher.duration_days} hari.")
                return redirect("dashboard")
    return render(request, "learning/redeem_voucher.html", {"form": form, "access": get_access(request.user)})


@login_required
def appearance_settings(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    form = UserPreferenceForm(request.POST or None, instance=preference)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengaturan tampilan berhasil disimpan.")
        return redirect("appearance_settings")
    return render(request, "learning/appearance_settings.html", {"form": form, "preference": preference})


def access_required(request):
    if not has_active_access(request.user):
        messages.warning(request, "Masukkan voucher aktif untuk membuka konten ini.")
        return False
    return True


@login_required
def video_list(request):
    if not access_required(request):
        return redirect("redeem_voucher")
    return render(request, "learning/video_list.html", {"videos": Video.objects.filter(is_active=True)})


@login_required
def video_detail(request, pk):
    if not access_required(request):
        return redirect("redeem_voucher")
    video = get_object_or_404(Video, pk=pk, is_active=True)
    return render(request, "learning/video_detail.html", {"video": video})


@login_required
def cbt_list(request):
    if not access_required(request):
        return redirect("redeem_voucher")
    cbts = CBT.objects.filter(is_active=True).prefetch_related("questions")
    return render(request, "learning/cbt_list.html", {"cbts": cbts})


@login_required
def cbt_take(request, pk):
    if not access_required(request):
        return redirect("redeem_voucher")
    cbt = get_object_or_404(CBT.objects.prefetch_related("questions__choices"), pk=pk, is_active=True)
    questions = list(cbt.questions.all())
    if request.method == "POST":
        attempt = CBTAttempt.objects.create(user=request.user, cbt=cbt, total_questions=len(questions))
        correct = 0
        for question in questions:
            choice_id = request.POST.get(f"question_{question.id}")
            selected = Choice.objects.filter(pk=choice_id, question=question).first() if choice_id else None
            is_correct = bool(selected and selected.is_correct)
            correct += 1 if is_correct else 0
            CBTAttemptAnswer.objects.create(attempt=attempt, question=question, selected_choice=selected, is_correct=is_correct)
        attempt.correct_answers = correct
        attempt.score = round((correct / len(questions)) * 100) if questions else 0
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["correct_answers", "score", "submitted_at"])
        return redirect("attempt_detail", pk=attempt.pk)
    return render(request, "learning/cbt_take.html", {"cbt": cbt, "questions": questions})


@login_required
def history(request):
    attempts = CBTAttempt.objects.filter(user=request.user).select_related("cbt")
    return render(request, "learning/history.html", {"attempts": attempts})


@login_required
def attempt_detail(request, pk):
    attempt = get_object_or_404(CBTAttempt.objects.select_related("cbt"), pk=pk, user=request.user)
    answers = attempt.answers.select_related("question", "selected_choice").prefetch_related("question__choices")
    return render(request, "learning/attempt_detail.html", {"attempt": attempt, "answers": answers})


@admin_required
def admin_dashboard(request):
    return render(request, "learning/admin/dashboard.html", {
        "video_count": Video.objects.count(),
        "cbt_count": CBT.objects.count(),
        "voucher_count": Voucher.objects.count(),
        "user_count": User.objects.filter(is_staff=False).count(),
        "recent_attempts": CBTAttempt.objects.select_related("user", "cbt")[:8],
    })


@admin_required
def admin_video_list(request):
    return render(request, "learning/admin/video_list.html", {"videos": Video.objects.all()})


@admin_required
def admin_video_form(request, pk=None):
    video = get_object_or_404(Video, pk=pk) if pk else None
    form = VideoForm(request.POST or None, request.FILES or None, instance=video)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Video berhasil disimpan.")
        return redirect("admin_video_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "Video", "back_url": "admin_video_list"})


@admin_required
def admin_voucher_list(request):
    return render(request, "learning/admin/voucher_list.html", {"vouchers": Voucher.objects.select_related("redeemed_by")})


@admin_required
def admin_voucher_form(request, pk=None):
    voucher = get_object_or_404(Voucher, pk=pk) if pk else None
    form = VoucherForm(request.POST or None, instance=voucher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Voucher berhasil disimpan.")
        return redirect("admin_voucher_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "Voucher", "back_url": "admin_voucher_list"})


@admin_required
def admin_cbt_list(request):
    cbts = CBT.objects.prefetch_related("questions")
    return render(request, "learning/admin/cbt_list.html", {"cbts": cbts})


@admin_required
def admin_cbt_form(request, pk=None):
    cbt = get_object_or_404(CBT, pk=pk) if pk else None
    form = CBTForm(request.POST or None, instance=cbt)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "CBT berhasil disimpan.")
        return redirect("admin_cbt_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "CBT", "back_url": "admin_cbt_list"})


@admin_required
def admin_question_form(request, cbt_pk=None, pk=None):
    question = get_object_or_404(Question, pk=pk) if pk else None
    cbt = question.cbt if question else get_object_or_404(CBT, pk=cbt_pk)
    form = QuestionForm(request.POST or None, instance=question)
    existing = list(question.choices.all()) if question else []
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.cbt = cbt
        question.save()
        correct_index = request.POST.get("correct_choice")
        question.choices.all().delete()
        for index in range(1, 5):
            text = request.POST.get(f"choice_{index}", "").strip()
            if text:
                Choice.objects.create(question=question, text=text, is_correct=str(index) == correct_index)
        messages.success(request, "Soal berhasil disimpan.")
        return redirect("admin_cbt_list")
    return render(request, "learning/admin/question_form.html", {"form": form, "cbt": cbt, "question": question, "choices": existing})


@admin_required
def admin_user_list(request):
    users = User.objects.filter(is_staff=False).select_related("access").order_by("username")
    return render(request, "learning/admin/user_list.html", {"users": users})


@admin_required
def admin_attempt_list(request):
    attempts = CBTAttempt.objects.select_related("user", "cbt")
    return render(request, "learning/admin/attempt_list.html", {"attempts": attempts})



