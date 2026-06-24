# Koready

MVP platform belajar Bahasa Korea dengan Django, Tailwind CDN, Alpine.js CDN, dan SQLite.

## Fitur
- Landing page elegan bertema belajar Korea dengan tombol WhatsApp melayang.
- Register/login user.
- Voucher sekali pakai untuk satu user; masa akses bertambah jika user redeem voucher baru.
- Video library dari YouTube dengan cover manual dan fallback thumbnail YouTube.
- CBT pilihan ganda, bisa dikerjakan berkali-kali.
- History hasil CBT tersimpan di database.
- Dashboard admin custom di `/manage/`.
- Django admin teknis tetap tersedia di `/django-admin/`.

## Jalankan lokal
```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\env\Scripts\python.exe manage.py migrate
.\env\Scripts\python.exe manage.py createsuperuser
.\env\Scripts\python.exe manage.py runserver
```

Login dengan superuser untuk membuka dashboard admin custom di `/manage/`.

## Catatan deploy
- Set `DEBUG=False` di `.env`.
- Isi `SECRET_KEY` yang kuat.
- Isi `ALLOWED_HOSTS` dengan domain/IP server.
- Jalankan `collectstatic` sebelum production.
- Untuk VPS/shared hosting, pastikan folder `media/` writable untuk upload cover video.

"# teguh" 
