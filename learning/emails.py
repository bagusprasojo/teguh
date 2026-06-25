from django.conf import settings
from django.core.mail import send_mail


def format_rupiah(value):
    return "Rp{:,.0f}".format(value).replace(",", ".")


def send_ubt_payment_email(registration):
    subject = f"Instruksi Pembayaran UBT - {registration.package.name}"
    message = f"""Halo {registration.full_name},

Pendaftaran UBT kamu telah diterima.

Paket: {registration.package.name}
Nominal pembayaran: {format_rupiah(registration.package.price)}
Masa berlaku voucher setelah diterbitkan: {registration.package.access_duration_days} hari

Silakan lakukan pembayaran sesuai nominal di atas. Setelah membayar, konfirmasi ke admin melalui WhatsApp.

Terima kasih,
Koready
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [registration.email], fail_silently=True)


def send_ubt_voucher_email(registration):
    if not registration.voucher:
        return
    subject = f"Voucher UBT Kamu - {registration.package.name}"
    message = f"""Halo {registration.full_name},

Pembayaran UBT kamu telah disetujui.

Paket: {registration.package.name}
Kode voucher UBT: {registration.voucher.code}
Masa berlaku: {registration.voucher.duration_days} hari setelah voucher digunakan

Voucher ini hanya bisa digunakan oleh akun kamu.

Terima kasih,
Koready
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [registration.email], fail_silently=True)
