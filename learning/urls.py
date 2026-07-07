from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("email-verification-sent/", views.email_verification_sent, name="email_verification_sent"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify_email"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("voucher/", views.redeem_voucher, name="redeem_voucher"),
    path("settings/appearance/", views.appearance_settings, name="appearance_settings"),
    path("ubt/", views.ubt_dashboard, name="ubt_dashboard"),
    path("ubt/register/", views.ubt_register, name="ubt_register"),
    path("ubt/registrations/<uuid:uuid>/", views.ubt_registration_detail, name="ubt_registration_detail"),
    path("ubt/<uuid:uuid>/take/", views.ubt_take, name="ubt_take"),
    path("ubt/history/", views.ubt_history, name="ubt_history"),
    path("ubt/history/<uuid:uuid>/", views.ubt_attempt_detail, name="ubt_attempt_detail"),
    path("ubt/history/<uuid:uuid>/certificate/", views.ubt_attempt_certificate, name="ubt_attempt_certificate"),
    path("certificates/ubt/<uuid:uuid>/", views.ubt_certificate_verify, name="ubt_certificate_verify"),
    path("videos/", views.video_list, name="video_list"),
    path("videos/<uuid:uuid>/", views.video_detail, name="video_detail"),
    path("cbt/", views.cbt_list, name="cbt_list"),
    path("cbt/<uuid:uuid>/", views.cbt_take, name="cbt_take"),
    path("history/", views.history, name="history"),
    path("history/<uuid:uuid>/", views.attempt_detail, name="attempt_detail"),
    path("manage/", views.admin_dashboard, name="admin_dashboard"),
    path("manage/blog/", views.admin_blog_post_list, name="admin_blog_post_list"),
    path("manage/blog/new/", views.admin_blog_post_form, name="admin_blog_post_new"),
    path("manage/blog/<uuid:uuid>/edit/", views.admin_blog_post_form, name="admin_blog_post_edit"),
    path("manage/blog/categories/", views.admin_blog_category_list, name="admin_blog_category_list"),
    path("manage/blog/categories/new/", views.admin_blog_category_form, name="admin_blog_category_new"),
    path("manage/blog/categories/<uuid:uuid>/edit/", views.admin_blog_category_form, name="admin_blog_category_edit"),
    path("manage/videos/", views.admin_video_list, name="admin_video_list"),
    path("manage/videos/new/", views.admin_video_form, name="admin_video_new"),
    path("manage/videos/<uuid:uuid>/edit/", views.admin_video_form, name="admin_video_edit"),
    path("manage/vouchers/", views.admin_voucher_list, name="admin_voucher_list"),
    path("manage/vouchers/new/", views.admin_voucher_form, name="admin_voucher_new"),
    path("manage/vouchers/<uuid:uuid>/edit/", views.admin_voucher_form, name="admin_voucher_edit"),
    path("manage/cbt/", views.admin_cbt_list, name="admin_cbt_list"),
    path("manage/cbt/new/", views.admin_cbt_form, name="admin_cbt_new"),
    path("manage/cbt/import/", views.admin_cbt_import, name="admin_cbt_import"),
    path("manage/cbt/import/template/", views.admin_cbt_import_template, name="admin_cbt_import_template"),
    path("manage/cbt/<uuid:uuid>/edit/", views.admin_cbt_form, name="admin_cbt_edit"),
    path("manage/cbt/<uuid:cbt_uuid>/questions/new/", views.admin_question_form, name="admin_question_new"),
    path("manage/questions/<uuid:uuid>/edit/", views.admin_question_form, name="admin_question_edit"),
    path("manage/questions/<uuid:uuid>/delete/", views.admin_question_delete, name="admin_question_delete"),
    path("manage/users/", views.admin_user_list, name="admin_user_list"),
    path("manage/users/<int:user_id>/action/", views.admin_user_action, name="admin_user_action"),
    path("manage/attempts/", views.admin_attempt_list, name="admin_attempt_list"),
    path("manage/ubt/packages/", views.admin_ubt_package_list, name="admin_ubt_package_list"),
    path("manage/ubt/packages/new/", views.admin_ubt_package_form, name="admin_ubt_package_new"),
    path("manage/ubt/packages/<uuid:uuid>/edit/", views.admin_ubt_package_form, name="admin_ubt_package_edit"),
    path("manage/ubt/", views.admin_ubt_list, name="admin_ubt_list"),
    path("manage/ubt/new/", views.admin_ubt_form, name="admin_ubt_new"),
    path("manage/ubt/import/", views.admin_ubt_import, name="admin_ubt_import"),
    path("manage/ubt/import/template/", views.admin_ubt_import_template, name="admin_ubt_import_template"),
    path("manage/ubt/<uuid:uuid>/edit/", views.admin_ubt_form, name="admin_ubt_edit"),
    path("manage/ubt/<uuid:ubt_uuid>/questions/new/", views.admin_ubt_question_form, name="admin_ubt_question_new"),
    path("manage/ubt/questions/<uuid:uuid>/edit/", views.admin_ubt_question_form, name="admin_ubt_question_edit"),
    path("manage/ubt/questions/<uuid:uuid>/delete/", views.admin_ubt_question_delete, name="admin_ubt_question_delete"),
    path("manage/ubt/registrations/", views.admin_ubt_registration_list, name="admin_ubt_registration_list"),
    path("manage/ubt/registrations/<uuid:uuid>/", views.admin_ubt_registration_detail, name="admin_ubt_registration_detail"),
]









