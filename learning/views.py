import base64
import os
import secrets
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .importers import build_cbt_import_template_xlsx, build_ubt_import_template_xlsx, import_cbt_from_excel, import_ubt_from_excel
from .forms import BlogCategoryForm, BlogPostForm, CBTForm, CBTImportForm, EmailOrUsernameAuthenticationForm, QuestionForm, RegisterForm, UBTForm, UBTImportForm, UBTPackageForm, UBTQuestionForm, UBTRegistrationForm, UBTRegistrationStatusForm, UserPhotoForm, UserPreferenceForm, UserProfileForm, VideoForm, VoucherForm, VoucherRedeemForm
from .emails import send_ubt_payment_email, send_ubt_voucher_email
from .models import BlogCategory, BlogPost, BlogPostRead, CBT, CBTAttempt, CBTAttemptAnswer, Choice, Question, UBT, UBTAttempt, UBTAttemptAnswer, UBTChoice, UBTPackage, UBTQuestion, UBTRegistration, LandingPageVisit, UserAccess, UserUBTAccess, UserPreference, UserProfile, Video, Voucher


BRAND_NAME = "Koready"

def build_certificate_number(attempt):
    return f"KRD-UBT-{attempt.uuid}"


def build_qr_code_data_uri(value):
    import qrcode

    image = qrcode.make(value)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

def prepare_weasyprint_environment():
    if not hasattr(os, "add_dll_directory"):
        return
    for directory in getattr(settings, "WEASYPRINT_DLL_DIRECTORIES", []):
        if os.path.isdir(directory):
            os.add_dll_directory(directory)



class UserLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = EmailOrUsernameAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.user.is_staff:
            self.request.session["show_access_notice"] = True
        return response

def get_access(user):
    access, _ = UserAccess.objects.get_or_create(user=user)
    return access


def get_ubt_access(user):
    access, _ = UserUBTAccess.objects.get_or_create(user=user)
    return access


def has_active_access(user):
    return user.is_authenticated and get_access(user).is_active


def admin_required(view_func):
    return login_required(user_passes_test(lambda user: user.is_staff)(view_func))


def format_indonesian_number(value):
    return f"{value:,}".replace(",", ".")


def home(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    if not request.session.get("landing_visit_counted"):
        LandingPageVisit.objects.get_or_create(session_key=session_key)
        request.session["landing_visit_counted"] = True
    visitor_count = LandingPageVisit.objects.count()
    return render(request, "learning/home.html", {
        "brand_name": BRAND_NAME,
        "visitor_count": visitor_count,
        "visitor_count_display": format_indonesian_number(visitor_count),
        "video_count": Video.objects.filter(is_active=True).count(),
        "cbt_count": CBT.objects.filter(is_active=True).count(),
        "user_count": User.objects.filter(is_staff=False).count(),
        "latest_posts": BlogPost.objects.filter(status=BlogPost.STATUS_PUBLISHED, published_at__lte=timezone.now()).select_related("category")[:3],
    })


def published_blog_posts():
    return BlogPost.objects.filter(status=BlogPost.STATUS_PUBLISHED, published_at__lte=timezone.now()).select_related("category", "author")


def blog_list(request):
    posts = published_blog_posts()
    categories = BlogCategory.objects.filter(posts__in=posts).distinct()
    category_slug = request.GET.get("category")
    active_category = None
    if category_slug:
        active_category = get_object_or_404(BlogCategory, slug=category_slug)
        posts = posts.filter(category=active_category)
    return render(request, "learning/blog/list.html", {
        "posts": posts,
        "categories": categories,
        "active_category": active_category,
    })


def blog_detail(request, slug):
    post = get_object_or_404(published_blog_posts(), slug=slug)
    if not request.session.session_key:
        request.session.create()
    BlogPostRead.objects.get_or_create(
        post=post,
        session_key=request.session.session_key,
        defaults={"user": request.user if request.user.is_authenticated else None},
    )
    latest_posts = published_blog_posts().exclude(pk=post.pk)[:3]
    return render(request, "learning/blog/detail.html", {"post": post, "latest_posts": latest_posts})

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
def profile(request):
    access = get_access(request.user) if not request.user.is_staff else None
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(request.POST or None, instance=request.user)
    photo_form = UserPhotoForm(request.POST or None, request.FILES or None, instance=user_profile)
    if request.method == "POST" and form.is_valid() and photo_form.is_valid():
        form.save()
        photo_form.save()
        messages.success(request, "Profil berhasil disimpan.")
        return redirect("profile")
    attempts = CBTAttempt.objects.filter(user=request.user).select_related("cbt")[:5]
    return render(request, "learning/profile.html", {
        "form": form,
        "photo_form": photo_form,
        "user_profile": user_profile,
        "access": access,
        "preference": preference,
        "attempts": attempts,
    })

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
                if voucher.assigned_user_id and voucher.assigned_user_id != request.user.id:
                    messages.error(request, "Voucher ini hanya bisa digunakan oleh user yang ditentukan.")
                    return redirect("redeem_voucher")
                if voucher.voucher_type == Voucher.VOUCHER_UBT:
                    access = get_ubt_access(request.user)
                    access.add_days(voucher.duration_days)
                    success_url = "ubt_dashboard"
                    success_message = f"Voucher UBT berhasil digunakan. Akses UBT bertambah {voucher.duration_days} hari."
                else:
                    access = get_access(request.user)
                    access.add_days(voucher.duration_days)
                    success_url = "dashboard"
                    success_message = f"Voucher berhasil digunakan. Akses bertambah {voucher.duration_days} hari."
                voucher.redeemed_by = request.user
                voucher.redeemed_at = timezone.now()
                voucher.save(update_fields=["redeemed_by", "redeemed_at"])
                messages.success(request, success_message)
                return redirect(success_url)
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


def generate_ubt_voucher_code():
    while True:
        code = f"UBT-{secrets.token_hex(4).upper()}"
        if not Voucher.objects.filter(code=code).exists():
            return code


def issue_ubt_voucher(registration):
    if registration.voucher:
        return registration.voucher
    voucher = Voucher.objects.create(
        code=generate_ubt_voucher_code(),
        duration_days=registration.package.access_duration_days,
        voucher_type=Voucher.VOUCHER_UBT,
        assigned_user=registration.user,
        is_active=True,
    )
    registration.voucher = voucher
    registration.status = UBTRegistration.STATUS_VOUCHER_ISSUED
    registration.save(update_fields=["voucher", "status", "updated_at"])
    send_ubt_voucher_email(registration)
    return voucher


def ubt_access_required(request):
    if not get_ubt_access(request.user).is_active:
        messages.warning(request, "Masukkan voucher UBT aktif untuk membuka UBT.")
        return False
    return True


def access_required(request):
    if not has_active_access(request.user):
        messages.warning(request, "Masukkan voucher aktif untuk membuka konten ini.")
        return False
    return True


@login_required
def ubt_dashboard(request):
    ubt_access = get_ubt_access(request.user)
    packages = UBTPackage.objects.filter(is_active=True)
    registrations = UBTRegistration.objects.filter(user=request.user).select_related("package", "voucher")
    ubts = UBT.objects.filter(is_active=True) if ubt_access.is_active else UBT.objects.none()
    return render(request, "learning/ubt/dashboard.html", {
        "ubt_access": ubt_access,
        "packages": packages,
        "registrations": registrations,
        "ubts": ubts,
    })


@login_required
def ubt_register(request):
    form = UBTRegistrationForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        registration = form.save(commit=False)
        registration.user = request.user
        registration.status = UBTRegistration.STATUS_PENDING_PAYMENT
        registration.save()
        send_ubt_payment_email(registration)
        messages.success(request, "Pendaftaran UBT berhasil dibuat. Instruksi pembayaran telah dikirim ke email.")
        return redirect("ubt_registration_detail", uuid=registration.uuid)
    return render(request, "learning/ubt/register.html", {"form": form})


@login_required
def ubt_registration_detail(request, uuid):
    registration = get_object_or_404(UBTRegistration.objects.select_related("package", "voucher"), uuid=uuid, user=request.user)
    whatsapp_text = (
        f"Halo Koready, saya ingin konfirmasi pembayaran UBT. "
        f"Nama: {registration.full_name}. Paket: {registration.package.name}. "
        f"Nominal: Rp{registration.package.price}. Kode pendaftaran: {registration.uuid}"
    )
    return render(request, "learning/ubt/registration_detail.html", {
        "registration": registration,
        "admin_whatsapp": settings.ADMIN_WHATSAPP_NUMBER,
        "whatsapp_text": whatsapp_text,
    })


@login_required
def ubt_take(request, uuid):
    if not ubt_access_required(request):
        return redirect("ubt_dashboard")
    ubt = get_object_or_404(UBT.objects.prefetch_related("questions__choices"), uuid=uuid, is_active=True)
    questions = list(ubt.questions.all())
    session_key = f"ubt_started_at_{ubt.uuid}"
    now = timezone.now()
    started_at_raw = request.session.get(session_key)
    started_at = parse_datetime(started_at_raw) if started_at_raw else None
    if not started_at:
        started_at = now
        request.session[session_key] = started_at.isoformat()
    deadline = started_at + timezone.timedelta(minutes=ubt.duration_minutes)
    remaining_seconds = max(0, int((deadline - now).total_seconds()))

    if request.method == "POST":
        submitted_at = timezone.now()
        is_late = submitted_at > deadline
        attempt = UBTAttempt.objects.create(user=request.user, ubt=ubt, total_questions=len(questions))
        correct = 0
        for question in questions:
            choice_id = request.POST.get(f"question_{question.id}")
            selected = UBTChoice.objects.filter(pk=choice_id, question=question).first() if choice_id else None
            is_correct = bool(selected and selected.is_correct)
            correct += 1 if is_correct else 0
            UBTAttemptAnswer.objects.create(attempt=attempt, question=question, selected_choice=selected, is_correct=is_correct)
        attempt.correct_answers = correct
        attempt.score = round((correct / len(questions)) * 100) if questions else 0
        attempt.submitted_at = submitted_at
        attempt.save(update_fields=["correct_answers", "score", "submitted_at"])
        request.session.pop(session_key, None)
        if is_late:
            messages.warning(request, "Waktu pengerjaan UBT sudah habis. Jawaban yang terkirim tetap diproses.")
        return redirect("ubt_attempt_detail", uuid=attempt.uuid)
    return render(request, "learning/ubt/take.html", {
        "ubt": ubt,
        "questions": questions,
        "remaining_seconds": remaining_seconds,
        "duration_minutes": ubt.duration_minutes,
    })

@login_required
def ubt_history(request):
    attempts = UBTAttempt.objects.filter(user=request.user).select_related("ubt")
    return render(request, "learning/ubt/history.html", {"attempts": attempts})


@login_required
def ubt_attempt_detail(request, uuid):
    attempt = get_object_or_404(UBTAttempt.objects.select_related("ubt"), uuid=uuid, user=request.user)
    answers = attempt.answers.select_related("question", "selected_choice").prefetch_related("question__choices")
    return render(request, "learning/ubt/attempt_detail.html", {"attempt": attempt, "answers": answers, "wrong_answers": max(attempt.total_questions - attempt.correct_answers, 0)})



@login_required
def ubt_attempt_certificate(request, uuid):
    attempt = get_object_or_404(UBTAttempt.objects.select_related("ubt", "user"), uuid=uuid, user=request.user)
    if not attempt.passed:
        messages.warning(request, "Sertifikat hanya tersedia untuk hasil UBT yang lulus.")
        return redirect("ubt_attempt_detail", uuid=attempt.uuid)
    try:
        prepare_weasyprint_environment()
        from weasyprint import HTML
    except Exception:
        messages.error(request, "WeasyPrint belum siap di environment ini. Install dependency Python dan library sistem WeasyPrint terlebih dahulu.")
        return redirect("ubt_attempt_detail", uuid=attempt.uuid)

    display_name = attempt.user.get_full_name().strip() or attempt.user.username
    verification_url = request.build_absolute_uri(reverse("ubt_certificate_verify", kwargs={"uuid": attempt.uuid}))
    html = render_to_string("learning/ubt/certificate.html", {
        "attempt": attempt,
        "display_name": display_name,
        "certificate_number": build_certificate_number(attempt),
        "verification_url": verification_url,
        "qr_code_data_uri": build_qr_code_data_uri(verification_url),
    })
    try:
        pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
    except Exception:
        messages.error(request, "Sertifikat PDF belum bisa dibuat. Periksa instalasi dependency sistem WeasyPrint di environment ini.")
        return redirect("ubt_attempt_detail", uuid=attempt.uuid)

    filename = f"sertifikat-koready-{attempt.uuid}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def ubt_certificate_verify(request, uuid):
    attempt = get_object_or_404(UBTAttempt.objects.select_related("ubt", "user"), uuid=uuid, submitted_at__isnull=False)
    if not attempt.passed:
        raise Http404("Sertifikat tidak ditemukan.")
    display_name = attempt.user.get_full_name().strip() or attempt.user.username
    return render(request, "learning/ubt/certificate_verify.html", {
        "attempt": attempt,
        "display_name": display_name,
        "certificate_number": build_certificate_number(attempt),
    })

@login_required
def video_list(request):
    if not access_required(request):
        return redirect("redeem_voucher")
    return render(request, "learning/video_list.html", {"videos": Video.objects.filter(is_active=True)})


@login_required
def video_detail(request, uuid):
    if not access_required(request):
        return redirect("redeem_voucher")
    video = get_object_or_404(Video, uuid=uuid, is_active=True)
    return render(request, "learning/video_detail.html", {"video": video})


@login_required
def cbt_list(request):
    if not access_required(request):
        return redirect("redeem_voucher")
    cbts = CBT.objects.filter(is_active=True).prefetch_related("questions")
    return render(request, "learning/cbt_list.html", {"cbts": cbts})


@login_required
def cbt_take(request, uuid):
    if not access_required(request):
        return redirect("redeem_voucher")
    cbt = get_object_or_404(CBT.objects.prefetch_related("questions__choices"), uuid=uuid, is_active=True)
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
        return redirect("attempt_detail", uuid=attempt.uuid)
    return render(request, "learning/cbt_take.html", {"cbt": cbt, "questions": questions})


@login_required
def history(request):
    attempts = CBTAttempt.objects.filter(user=request.user).select_related("cbt")
    return render(request, "learning/history.html", {"attempts": attempts})


@login_required
def attempt_detail(request, uuid):
    attempt = get_object_or_404(CBTAttempt.objects.select_related("cbt"), uuid=uuid, user=request.user)
    answers = attempt.answers.select_related("question", "selected_choice").prefetch_related("question__choices")
    return render(request, "learning/attempt_detail.html", {"attempt": attempt, "answers": answers})



@admin_required
def admin_blog_post_list(request):
    posts = BlogPost.objects.select_related("category", "author").prefetch_related("reads")
    return render(request, "learning/admin/blog_post_list.html", {"posts": posts})


@admin_required
def admin_blog_post_form(request, uuid=None):
    post = get_object_or_404(BlogPost, uuid=uuid) if uuid else None
    form = BlogPostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        if not post.author_id:
            post.author = request.user
        post.save()
        form.save_m2m()
        messages.success(request, "Artikel blog berhasil disimpan.")
        return redirect("admin_blog_post_list")
    return render(request, "learning/admin/blog_post_form.html", {"form": form, "title": "Artikel Blog"})


@admin_required
def admin_blog_category_list(request):
    categories = BlogCategory.objects.all()
    return render(request, "learning/admin/blog_category_list.html", {"categories": categories})


@admin_required
def admin_blog_category_form(request, uuid=None):
    category = get_object_or_404(BlogCategory, uuid=uuid) if uuid else None
    form = BlogCategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Kategori blog berhasil disimpan.")
        return redirect("admin_blog_category_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "Kategori Blog", "back_url": "admin_blog_category_list"})

@admin_required
def admin_dashboard(request):
    return render(request, "learning/admin/dashboard.html", {
        "video_count": Video.objects.count(),
        "cbt_count": CBT.objects.count(),
        "voucher_count": Voucher.objects.count(),
        "user_count": User.objects.filter(is_staff=False).count(),
        "latest_posts": BlogPost.objects.filter(status=BlogPost.STATUS_PUBLISHED, published_at__lte=timezone.now()).select_related("category")[:3],
        "recent_attempts": CBTAttempt.objects.select_related("user", "cbt")[:8],
    })


@admin_required
def admin_video_list(request):
    return render(request, "learning/admin/video_list.html", {"videos": Video.objects.all()})


@admin_required
def admin_video_form(request, uuid=None):
    video = get_object_or_404(Video, uuid=uuid) if uuid else None
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
def admin_voucher_form(request, uuid=None):
    voucher = get_object_or_404(Voucher, uuid=uuid) if uuid else None
    form = VoucherForm(request.POST or None, instance=voucher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Voucher berhasil disimpan.")
        return redirect("admin_voucher_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "Voucher", "back_url": "admin_voucher_list"})


@admin_required
def admin_cbt_import_template(request):
    content = build_cbt_import_template_xlsx()
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="template_import_cbt.xlsx"'
    return response


@admin_required
def admin_cbt_import(request):
    form = CBTImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        result = import_cbt_from_excel(
            form.cleaned_data["file"],
            form.cleaned_data["mode"],
        )
        if result.ok:
            messages.success(
                request,
                f"Import berhasil. CBT baru: {result.created_cbts}, CBT diperbarui: {result.updated_cbts}, soal: {result.created_questions}, pilihan: {result.created_choices}.",
            )
            return redirect("admin_cbt_list")
        messages.error(request, "Import gagal. Periksa daftar error di bawah.")
    return render(request, "learning/admin/cbt_import.html", {"form": form, "result": result})


@admin_required
def admin_cbt_list(request):
    cbts = CBT.objects.prefetch_related("questions")
    return render(request, "learning/admin/cbt_list.html", {"cbts": cbts})


@admin_required
def admin_cbt_form(request, uuid=None):
    cbt = get_object_or_404(CBT, uuid=uuid) if uuid else None
    form = CBTForm(request.POST or None, instance=cbt)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "CBT berhasil disimpan.")
        return redirect("admin_cbt_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "CBT", "back_url": "admin_cbt_list"})


@admin_required
def admin_question_form(request, cbt_uuid=None, uuid=None):
    question = get_object_or_404(Question, uuid=uuid) if uuid else None
    cbt = question.cbt if question else get_object_or_404(CBT, uuid=cbt_uuid)
    form = QuestionForm(request.POST or None, request.FILES or None, instance=question)
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





@admin_required
def admin_ubt_package_list(request):
    packages = UBTPackage.objects.all()
    return render(request, "learning/admin/ubt_package_list.html", {"packages": packages})


@admin_required
def admin_ubt_package_form(request, uuid=None):
    package = get_object_or_404(UBTPackage, uuid=uuid) if uuid else None
    form = UBTPackageForm(request.POST or None, instance=package)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Paket UBT berhasil disimpan.")
        return redirect("admin_ubt_package_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "Paket UBT", "back_url": "admin_ubt_package_list"})


@admin_required
def admin_ubt_import_template(request):
    content = build_ubt_import_template_xlsx()
    response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="template_import_ubt.xlsx"'
    return response


@admin_required
def admin_ubt_import(request):
    form = UBTImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        result = import_ubt_from_excel(form.cleaned_data["file"], form.cleaned_data["mode"])
        if result.ok:
            messages.success(request, f"Import berhasil. UBT baru: {result.created_cbts}, UBT diperbarui: {result.updated_cbts}, soal: {result.created_questions}, pilihan: {result.created_choices}.")
            return redirect("admin_ubt_list")
        messages.error(request, "Import gagal. Periksa daftar error di bawah.")
    return render(request, "learning/admin/ubt_import.html", {"form": form, "result": result})


@admin_required
def admin_ubt_list(request):
    ubts = UBT.objects.all()
    return render(request, "learning/admin/ubt_list.html", {"ubts": ubts})


@admin_required
def admin_ubt_form(request, uuid=None):
    ubt = get_object_or_404(UBT, uuid=uuid) if uuid else None
    form = UBTForm(request.POST or None, instance=ubt)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "UBT berhasil disimpan.")
        return redirect("admin_ubt_list")
    return render(request, "learning/admin/model_form.html", {"form": form, "title": "UBT", "back_url": "admin_ubt_list"})


@admin_required
def admin_ubt_question_form(request, ubt_uuid=None, uuid=None):
    question = get_object_or_404(UBTQuestion, uuid=uuid) if uuid else None
    ubt = question.ubt if question else get_object_or_404(UBT, uuid=ubt_uuid)
    form = UBTQuestionForm(request.POST or None, request.FILES or None, instance=question)
    existing = list(question.choices.all()) if question else []
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.ubt = ubt
        question.save()
        correct_index = request.POST.get("correct_choice")
        question.choices.all().delete()
        for index in range(1, 5):
            text = request.POST.get(f"choice_{index}", "").strip()
            if text:
                UBTChoice.objects.create(question=question, text=text, is_correct=str(index) == correct_index)
        messages.success(request, "Soal UBT berhasil disimpan.")
        return redirect("admin_ubt_list")
    return render(request, "learning/admin/ubt_question_form.html", {"form": form, "ubt": ubt, "question": question, "choices": existing})


@admin_required
def admin_ubt_registration_list(request):
    registrations = UBTRegistration.objects.select_related("user", "package", "voucher")
    return render(request, "learning/admin/ubt_registration_list.html", {"registrations": registrations})


@admin_required
def admin_ubt_registration_detail(request, uuid):
    registration = get_object_or_404(UBTRegistration.objects.select_related("user", "package", "voucher"), uuid=uuid)
    form = UBTRegistrationStatusForm(request.POST or None, instance=registration)
    if request.method == "POST" and form.is_valid():
        registration = form.save(commit=False)
        if registration.status == UBTRegistration.STATUS_APPROVED:
            registration.save(update_fields=["status", "updated_at"])
            issue_ubt_voucher(registration)
            messages.success(request, "Pendaftaran disetujui dan voucher UBT otomatis diterbitkan.")
        else:
            registration.save(update_fields=["status", "updated_at"])
            messages.success(request, "Status pendaftaran UBT berhasil diperbarui.")
        return redirect("admin_ubt_registration_detail", uuid=registration.uuid)
    return render(request, "learning/admin/ubt_registration_detail.html", {"registration": registration, "form": form})













