#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from inventory.models import Store

print("=" * 80)
print("DATABASE'DEKİ MAĞAZALAR")
print("=" * 80)

stores = Store.objects.all()

if stores.exists():
    for store in stores:
        print(f"\nKod: {store.code}")
        print(f"  Ad: {store.name}")
        print(f"  Adres: {store.address}")
        print(f"  Şehir: {store.city}")
        print(f"  Telefon: {store.phone}")
        print(f"  Aktif: {store.is_active}")
        print(f"  Oluşturulma: {store.created_at}")
else:
    print("\n⚠️ Database'de mağaza kaydı yoktur!")
    print("\nMağaza oluşturmak için: python manage.py create_stores")

print("\n" + "=" * 80)
print(f"Toplam Mağaza: {stores.count()}")
print("=" * 80)
