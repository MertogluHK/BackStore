#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Tüm tabloları sil
    cursor.execute("""
        DROP TABLE IF EXISTS inventory_stockmovement CASCADE;
        DROP TABLE IF EXISTS inventory_stock CASCADE;
        DROP TABLE IF EXISTS inventory_userprofile CASCADE;
        DROP TABLE IF EXISTS inventory_product CASCADE;
        DROP TABLE IF EXISTS inventory_store CASCADE;
    """)
    
    # Migration history'yi sıfırla
    cursor.execute("DELETE FROM django_migrations WHERE app = 'inventory'")
    
    print("✅ Tüm inventory tabloları ve migration history silindi")
