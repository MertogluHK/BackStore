#!/usr/bin/env python
import psycopg2
from psycopg2 import sql
import os
import django

# Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from django.conf import settings

# Database config
db_config = settings.DATABASES['default']

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        database=db_config['NAME'],
        port=db_config['PORT']
    )
    cur = conn.cursor()
    
    # Enable autocommit for DROP commands
    conn.set_session(autocommit=True)
    
    # Drop all inventory tables
    tables_to_drop = [
        'django_migrations',
        'inventory_stockmovement',
        'inventory_stock',
        'inventory_userprofile',
        'inventory_product',
        'inventory_store',
    ]
    
    for table in tables_to_drop:
        try:
            cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
            print(f'✓ {table} silindi')
        except Exception as e:
            print(f'⚠ {table} silinirken hata: {e}')
    
    cur.close()
    conn.close()
    print('\n✓ Tüm tablolar temizlendi')
    
except Exception as e:
    print(f'❌ Hata: {e}')
