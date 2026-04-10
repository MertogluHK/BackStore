#!/usr/bin/env python
import psycopg2
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
    
    # Drop ALL tables
    cur.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
    """)
    
    tables = cur.fetchall()
    for table in tables:
        table_name = table[0]
        try:
            cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
            print(f'✓ {table_name} silindi')
        except Exception as e:
            print(f'⚠ {table_name} silinirken hata: {e}')
    
    cur.close()
    conn.close()
    print('\n✓ Tüm tablolar temizlendi')
    
except Exception as e:
    print(f'❌ Hata: {e}')
