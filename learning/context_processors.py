from .models import UserPreference, UserProfile


def appearance(request):
    default_classes = "theme-light accent-rose text-normal"
    if not request.user.is_authenticated:
        return {"appearance_classes": default_classes}
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {
        "appearance_classes": preference.body_classes,
        "nav_profile": profile,
        "nav_display_name": profile.display_name,
        "nav_initials": profile.initials,
    }
