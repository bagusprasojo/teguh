import uuid
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from django.utils.text import slugify





class BlogContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.first_image_url = ""
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        if tag != "img" or self.first_image_url:
            return
        attrs_dict = dict(attrs)
        self.first_image_url = attrs_dict.get("src", "")

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text_parts.append(text)


def parse_blog_content(content):
    parser = BlogContentParser()
    parser.feed(content or "")
    return parser.first_image_url, " ".join(parser.text_parts)

def make_unique_slug(model_class, value):
    base_slug = slugify(value) or uuid.uuid4().hex[:8]
    slug = base_slug
    counter = 2
    while model_class.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
class BlogCategory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Blog category"
        verbose_name_plural = "Blog categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(BlogCategory, self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="blog_posts")
    excerpt = models.TextField(max_length=320, blank=True)
    content = CKEditor5Field("Konten", config_name="default")
    cover = models.ImageField(upload_to="blog-covers/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def first_content_image_url(self):
        image_url, _ = parse_blog_content(self.content)
        return image_url

    @property
    def cover_url(self):
        if self.cover:
            return self.cover.url
        return self.first_content_image_url

    @property
    def excerpt_text(self):
        if self.excerpt:
            return self.excerpt
        _, text = parse_blog_content(self.content)
        return text[:220]

    @property
    def read_count(self):
        return self.reads.count()
    @property
    def is_published(self):
        return self.status == self.STATUS_PUBLISHED and bool(self.published_at and self.published_at <= timezone.now())

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(BlogPost, self.title)
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class BlogPostRead(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="reads")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="blog_reads")
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["post", "session_key"], name="unique_blog_read_per_session"),
        ]

    def __str__(self):
        return f"{self.post.title} read"

class LandingPageVisit(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Landing visit {self.session_key}"

class UserAccess(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access")
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} access"

    @property
    def is_active(self):
        return bool(self.expires_at and self.expires_at > timezone.now())

    def add_days(self, days):
        start = self.expires_at if self.is_active else timezone.now()
        self.expires_at = start + timezone.timedelta(days=days)
        self.save(update_fields=["expires_at"])


class Voucher(models.Model):
    VOUCHER_GENERAL = "general"
    VOUCHER_UBT = "ubt"
    VOUCHER_TYPE_CHOICES = [
        (VOUCHER_GENERAL, "Voucher umum"),
        (VOUCHER_UBT, "Voucher UBT"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    code = models.CharField(max_length=40, unique=True)
    duration_days = models.PositiveIntegerField()
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPE_CHOICES, default=VOUCHER_GENERAL)
    assigned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_vouchers")
    is_active = models.BooleanField(default=True)
    redeemed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    @property
    def is_redeemed(self):
        return self.redeemed_by_id is not None


class Video(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=180)
    description = models.TextField()
    youtube_url = models.URLField()
    cover = models.ImageField(upload_to="video-covers/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def youtube_id(self):
        parsed = urlparse(self.youtube_url)
        if parsed.hostname == "youtu.be":
            return parsed.path.strip("/")
        if parsed.hostname and "youtube.com" in parsed.hostname:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [""])[0]
            if parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
                parts = parsed.path.split("/")
                return parts[2] if len(parts) > 2 else ""
        return ""

    @property
    def embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}" if self.youtube_id else self.youtube_url

    @property
    def thumbnail_url(self):
        if self.cover:
            return self.cover.url
        if self.youtube_id:
            return f"https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg"
        return ""


class CBT(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    passing_score = models.PositiveIntegerField(default=70)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CBT"
        verbose_name_plural = "CBT"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Question(models.Model):
    MEDIA_NONE = "none"
    MEDIA_IMAGE = "image"
    MEDIA_AUDIO = "audio"
    MEDIA_VIDEO = "video"
    MEDIA_YOUTUBE = "youtube"
    MEDIA_CHOICES = [
        (MEDIA_NONE, "Tanpa media"),
        (MEDIA_IMAGE, "Gambar"),
        (MEDIA_AUDIO, "Audio"),
        (MEDIA_VIDEO, "Video upload"),
        (MEDIA_YOUTUBE, "YouTube"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cbt = models.ForeignKey(CBT, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(blank=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_CHOICES, default=MEDIA_NONE)
    media_file = models.FileField(upload_to="question-media/", blank=True)
    media_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.cbt.title} - {self.order}"

    @property
    def media_source_url(self):
        if self.media_file:
            return self.media_file.url
        return self.media_url

    @property
    def youtube_id(self):
        parsed = urlparse(self.media_url)
        if parsed.hostname == "youtu.be":
            return parsed.path.strip("/")
        if parsed.hostname and "youtube.com" in parsed.hostname:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [""])[0]
            if parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
                parts = parsed.path.split("/")
                return parts[2] if len(parts) > 2 else ""
        return ""

    @property
    def youtube_embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}" if self.youtube_id else self.media_url

    @property
    def has_media(self):
        return self.media_type != self.MEDIA_NONE and bool(self.media_source_url)


class Choice(models.Model):
    ANSWER_TEXT = "text"
    ANSWER_IMAGE = "image"
    ANSWER_AUDIO = "audio"
    ANSWER_VIDEO = "video"
    ANSWER_CHOICES = [
        (ANSWER_TEXT, "Text"),
        (ANSWER_IMAGE, "Gambar"),
        (ANSWER_AUDIO, "Audio"),
        (ANSWER_VIDEO, "Video"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=500, blank=True)
    answer_type = models.CharField(max_length=20, choices=ANSWER_CHOICES, default=ANSWER_TEXT)
    media_file = models.FileField(upload_to="choice-media/", blank=True)
    media_url = models.URLField(blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text or self.media_source_url or "Pilihan jawaban"

    @property
    def media_source_url(self):
        if self.media_file:
            return self.media_file.url
        return self.media_url

    @property
    def youtube_id(self):
        parsed = urlparse(self.media_url)
        if parsed.hostname == "youtu.be":
            return parsed.path.strip("/")
        if parsed.hostname and "youtube.com" in parsed.hostname:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [""])[0]
            if parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
                parts = parsed.path.split("/")
                return parts[2] if len(parts) > 2 else ""
        return ""

    @property
    def youtube_embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}" if self.youtube_id else ""

    @property
    def has_media(self):
        return self.answer_type != self.ANSWER_TEXT and bool(self.media_source_url)

class CBTAttempt(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cbt_attempts")
    cbt = models.ForeignKey(CBT, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    @property
    def passed(self):
        return self.score >= self.cbt.passing_score


class CBTAttemptAnswer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    attempt = models.ForeignKey(CBTAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)



class UserPreference(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_SOFT = "soft"
    THEME_CHOICES = [
        (THEME_LIGHT, "Light"),
        (THEME_DARK, "Dark"),
        (THEME_SOFT, "Soft"),
    ]

    ACCENT_ROSE = "rose"
    ACCENT_EMERALD = "emerald"
    ACCENT_BLUE = "blue"
    ACCENT_VIOLET = "violet"
    ACCENT_AMBER = "amber"
    ACCENT_CHOICES = [
        (ACCENT_ROSE, "Rose"),
        (ACCENT_EMERALD, "Emerald"),
        (ACCENT_BLUE, "Blue"),
        (ACCENT_VIOLET, "Violet"),
        (ACCENT_AMBER, "Amber"),
    ]

    TEXT_NORMAL = "normal"
    TEXT_LARGE = "large"
    TEXT_XL = "xl"
    TEXT_SIZE_CHOICES = [
        (TEXT_NORMAL, "Normal"),
        (TEXT_LARGE, "Besar"),
        (TEXT_XL, "Ekstra besar"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference")
    theme_mode = models.CharField(max_length=20, choices=THEME_CHOICES, default=THEME_LIGHT)
    accent_color = models.CharField(max_length=20, choices=ACCENT_CHOICES, default=ACCENT_ROSE)
    text_size = models.CharField(max_length=20, choices=TEXT_SIZE_CHOICES, default=TEXT_NORMAL)

    def __str__(self):
        return f"{self.user.username} preference"

    @property
    def body_classes(self):
        return f"theme-{self.theme_mode} accent-{self.accent_color} text-{self.text_size}"


class UserProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    photo = models.ImageField(upload_to="user-photos/", blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} profile"

    @property
    def display_name(self):
        full_name = self.user.get_full_name().strip()
        return full_name or self.user.username

    @property
    def initials(self):
        parts = [part[0] for part in self.display_name.split() if part]
        return "".join(parts[:2]).upper() or self.user.username[:1].upper()

class UserUBTAccess(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ubt_access")
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} UBT access"

    @property
    def is_active(self):
        return bool(self.expires_at and self.expires_at > timezone.now())

    def add_days(self, days):
        start = self.expires_at if self.is_active else timezone.now()
        self.expires_at = start + timezone.timedelta(days=days)
        self.save(update_fields=["expires_at"])


class UBTPackage(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    access_duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UBT(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    passing_score = models.PositiveIntegerField(default=70)
    duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class UBTQuestion(models.Model):
    MEDIA_NONE = "none"
    MEDIA_IMAGE = "image"
    MEDIA_AUDIO = "audio"
    MEDIA_VIDEO = "video"
    MEDIA_YOUTUBE = "youtube"
    MEDIA_CHOICES = [
        (MEDIA_NONE, "Tanpa media"),
        (MEDIA_IMAGE, "Gambar"),
        (MEDIA_AUDIO, "Audio"),
        (MEDIA_VIDEO, "Video upload"),
        (MEDIA_YOUTUBE, "YouTube"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    ubt = models.ForeignKey(UBT, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(blank=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_CHOICES, default=MEDIA_NONE)
    media_file = models.FileField(upload_to="ubt-question-media/", blank=True)
    media_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.ubt.title} - {self.order}"

    @property
    def media_source_url(self):
        if self.media_file:
            return self.media_file.url
        return self.media_url

    @property
    def youtube_id(self):
        parsed = urlparse(self.media_url)
        if parsed.hostname == "youtu.be":
            return parsed.path.strip("/")
        if parsed.hostname and "youtube.com" in parsed.hostname:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [""])[0]
            if parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
                parts = parsed.path.split("/")
                return parts[2] if len(parts) > 2 else ""
        return ""

    @property
    def youtube_embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}" if self.youtube_id else self.media_url

    @property
    def has_media(self):
        return self.media_type != self.MEDIA_NONE and bool(self.media_source_url)


class UBTChoice(models.Model):
    ANSWER_TEXT = "text"
    ANSWER_IMAGE = "image"
    ANSWER_AUDIO = "audio"
    ANSWER_VIDEO = "video"
    ANSWER_CHOICES = [
        (ANSWER_TEXT, "Text"),
        (ANSWER_IMAGE, "Gambar"),
        (ANSWER_AUDIO, "Audio"),
        (ANSWER_VIDEO, "Video"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question = models.ForeignKey(UBTQuestion, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=500, blank=True)
    answer_type = models.CharField(max_length=20, choices=ANSWER_CHOICES, default=ANSWER_TEXT)
    media_file = models.FileField(upload_to="ubt-choice-media/", blank=True)
    media_url = models.URLField(blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text or self.media_source_url or "Pilihan jawaban UBT"

    @property
    def media_source_url(self):
        if self.media_file:
            return self.media_file.url
        return self.media_url

    @property
    def youtube_id(self):
        parsed = urlparse(self.media_url)
        if parsed.hostname == "youtu.be":
            return parsed.path.strip("/")
        if parsed.hostname and "youtube.com" in parsed.hostname:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [""])[0]
            if parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
                parts = parsed.path.split("/")
                return parts[2] if len(parts) > 2 else ""
        return ""

    @property
    def youtube_embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}" if self.youtube_id else ""

    @property
    def has_media(self):
        return self.answer_type != self.ANSWER_TEXT and bool(self.media_source_url)

class UBTAttempt(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ubt_attempts")
    ubt = models.ForeignKey(UBT, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    @property
    def passed(self):
        return self.score >= self.ubt.passing_score


class UBTAttemptAnswer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    attempt = models.ForeignKey(UBTAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(UBTQuestion, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(UBTChoice, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)


class UBTRegistration(models.Model):
    STATUS_PENDING_PAYMENT = "pending_payment"
    STATUS_WAITING_CONFIRMATION = "waiting_confirmation"
    STATUS_APPROVED = "approved"
    STATUS_VOUCHER_ISSUED = "voucher_issued"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, "Pending payment"),
        (STATUS_WAITING_CONFIRMATION, "Waiting confirmation"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_VOUCHER_ISSUED, "Voucher issued"),
        (STATUS_REJECTED, "Rejected"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ubt_registrations")
    package = models.ForeignKey(UBTPackage, on_delete=models.PROTECT, related_name="registrations")
    full_name = models.CharField(max_length=180)
    email = models.EmailField()
    whatsapp_number = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT)
    voucher = models.OneToOneField(Voucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="ubt_registration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"















