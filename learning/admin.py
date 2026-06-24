from django.contrib import admin

from .models import CBT, CBTAttempt, CBTAttemptAnswer, Choice, Question, UserAccess, Video, Voucher

admin.site.register(UserAccess)
admin.site.register(Voucher)
admin.site.register(Video)
admin.site.register(CBT)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(CBTAttempt)
admin.site.register(CBTAttemptAnswer)

