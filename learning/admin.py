from django.contrib import admin

from .models import CBT, CBTAttempt, CBTAttemptAnswer, Choice, Question, UBT, UBTAttempt, UBTAttemptAnswer, UBTChoice, UBTPackage, UBTQuestion, UBTRegistration, LandingPageVisit, UserAccess, UserUBTAccess, UserPreference, UserProfile, Video, Voucher

admin.site.register(LandingPageVisit)
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


