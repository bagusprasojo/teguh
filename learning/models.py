import uuid
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.db import models
from django.utils import timezone


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
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    code = models.CharField(max_length=40, unique=True)
    duration_days = models.PositiveIntegerField()
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
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cbt = models.ForeignKey(CBT, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.cbt.title} - {self.order}"


class Choice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


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
