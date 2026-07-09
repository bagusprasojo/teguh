from django.contrib import admin
from django.utils import timezone

from .models import BlogCategory, BlogPost, BlogPostRead, CBT, CBTAttempt, CBTAttemptAnswer, Choice, Question, UBT, UBTAttempt, UBTAttemptAnswer, UBTChoice, UBTPackage, UBTQuestion, UBTRegistration, LandingPageVisit, UserAccess, UserUBTAccess, UserPreference, UserProfile, Video, Voucher

admin.site.register(BlogCategory)
admin.site.register(BlogPost)
admin.site.register(BlogPostRead)
@admin.register(LandingPageVisit)
class LandingPageVisitAdmin(admin.ModelAdmin):
    list_display = ("session_key", "ip_address", "visit_time")
    list_filter = ("created_at",)
    search_fields = ("session_key", "ip_address")
    readonly_fields = ("uuid", "session_key", "ip_address", "created_at")

    @admin.display(ordering="created_at", description="Jam kunjungan")
    def visit_time(self, obj):
        return timezone.localtime(obj.created_at).strftime("%d %b %Y %H:%M:%S")
admin.site.register(UserAccess)
admin.site.register(UserPreference)
admin.site.register(UserProfile)
admin.site.register(Voucher)
admin.site.register(Video)
admin.site.register(CBT)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(CBTAttempt)
admin.site.register(CBTAttemptAnswer)

admin.site.register(UserUBTAccess)
admin.site.register(UBTPackage)
admin.site.register(UBT)
admin.site.register(UBTRegistration)
admin.site.register(UBTQuestion)
admin.site.register(UBTChoice)
admin.site.register(UBTAttempt)
admin.site.register(UBTAttemptAnswer)




