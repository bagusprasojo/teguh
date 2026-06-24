from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("voucher/", views.redeem_voucher, name="redeem_voucher"),
    path("settings/appearance/", views.appearance_settings, name="appearance_settings"),
    path("videos/", views.video_list, name="video_list"),
    path("videos/<int:pk>/", views.video_detail, name="video_detail"),
    path("cbt/", views.cbt_list, name="cbt_list"),
    path("cbt/<int:pk>/", views.cbt_take, name="cbt_take"),
    path("history/", views.history, name="history"),
    path("history/<int:pk>/", views.attempt_detail, name="attempt_detail"),
    path("manage/", views.admin_dashboard, name="admin_dashboard"),
    path("manage/videos/", views.admin_video_list, name="admin_video_list"),
    path("manage/videos/new/", views.admin_video_form, name="admin_video_new"),
    path("manage/videos/<int:pk>/edit/", views.admin_video_form, name="admin_video_edit"),
    path("manage/vouchers/", views.admin_voucher_list, name="admin_voucher_list"),
    path("manage/vouchers/new/", views.admin_voucher_form, name="admin_voucher_new"),
    path("manage/vouchers/<int:pk>/edit/", views.admin_voucher_form, name="admin_voucher_edit"),
    path("manage/cbt/", views.admin_cbt_list, name="admin_cbt_list"),
    path("manage/cbt/new/", views.admin_cbt_form, name="admin_cbt_new"),
    path("manage/cbt/<int:pk>/edit/", views.admin_cbt_form, name="admin_cbt_edit"),
    path("manage/cbt/<int:cbt_pk>/questions/new/", views.admin_question_form, name="admin_question_new"),
    path("manage/questions/<int:pk>/edit/", views.admin_question_form, name="admin_question_edit"),
    path("manage/users/", views.admin_user_list, name="admin_user_list"),
    path("manage/attempts/", views.admin_attempt_list, name="admin_attempt_list"),
]


