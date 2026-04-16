#!/usr/bin/env python
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import UserProfile, Store

print("🔧 Admin kullanıcılarını oluşturuluyor...\n")

# Tüm mağazaları al
stores = Store.objects.all().order_by('code')

for store in stores:
    username = f'admin{store.code}'
    password = store.code  # Şifre = Mağaza Kodu (M1, M2, vb)
    user_id_code = username  # adminM1, adminM2, vb.

    # Mevcut user'ı bul
    try:
        user = User.objects.get(username=username)
        print(f"✓ {username} kullanıcısı bulundu")
        
        # Profile varsa sil ve yeniden oluştur
        UserProfile.objects.filter(user=user).delete()
        
        # Yeni profile oluştur
        profile = UserProfile.objects.create(
            user=user,
            user_id_code=user_id_code,
            role='admin',
            store=store,  # Store object vermek gerekiyor!
            store_code=store.code,  # CharField de store code
            is_active=True
        )
        print(f"  → Profile güncellendi")
        print(f"    User ID Code: {user_id_code}")
        print(f"    Store: {store.code}")
        
    except User.DoesNotExist:
        print(f"⚠ {username} kullanıcısı bulunamadı")

print("\n✅ Tamamlandı!")
print("\n=== LOGİN BİLGİLERİ ===")
for store in stores:
    print(f"Mağaza {store.code}: admin{store.code} / {store.code}")
