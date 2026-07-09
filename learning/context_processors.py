from django.conf import settings

from .models import UserPreference, UserProfile


def format_phone_display(number):
    cleaned = str(number or "").strip().lstrip("+")
    if cleaned.startswith("62") and len(cleaned) > 2:
        local = cleaned[2:]
        groups = [local[:3], local[3:7], local[7:]]
        return "+62 " + "-".join(group for group in groups if group)
    return str(number or "")


def appearance(request):
    default_classes = "theme-light accent-rose text-normal"
    whatsapp_context = {
        "admin_whatsapp_number": settings.ADMIN_WHATSAPP_NUMBER,
        "admin_whatsapp_display": format_phone_display(settings.ADMIN_WHATSAPP_NUMBER),
    }
    if not request.user.is_authenticated:
        return {"appearance_classes": default_classes, **whatsapp_context}
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {
        "appearance_classes": preference.body_classes,
        "nav_profile": profile,
        "nav_display_name": profile.display_name,
        "nav_initials": profile.initials,
        **whatsapp_context,
    }