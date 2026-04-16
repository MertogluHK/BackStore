#!/usr/bin/env python
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from inventory.models import UserProfile

print("=== Tüm User Profiles ===\n")
for profile in UserProfile.objects.all():
    print(f"Username: {profile.user.username}")
    print(f"User ID Code: {profile.user_id_code}")
    print(f"Store: {profile.store}")
    print(f"Store Code: {profile.store_code}")
    print(f"Role: {profile.role}")
    print("-" * 50)
