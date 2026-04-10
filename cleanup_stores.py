#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from inventory.models import Store

# Boş code'lu mağazaları sil
deleted_count, _ = Store.objects.filter(code='').delete()
print(f'✓ {deleted_count} boş code\'lu mağaza silindi')

# Mağazaları listele
stores = Store.objects.all()
print(f'✓ {stores.count()} mağaza kaldı')
for store in stores:
    print(f'  - {store.code}: {store.name}')
