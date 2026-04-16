#!/usr/bin/env python
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from inventory.models import UserProfile

# Tüm user profile'ları store_code ile güncelle
updated = 0
for profile in UserProfile.objects.filter(store__isnull=False):
    if not profile.store_code:
        profile.store_code = profile.store.code
        profile.save()
        updated += 1

print(f"✅ {updated} user profile güncellendi")
