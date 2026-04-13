#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # inventory_stock tablosunun şemasını görmek
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'inventory_stock'
        ORDER BY ordinal_position;
    """)
    
    print("=" * 80)
    print("inventory_stock TABLO ŞEMASI")
    print("=" * 80)
    
    columns = cursor.fetchall()
    if columns:
        for col in columns:
            print(f"\nSütun: {col[0]}")
            print(f"  Tip: {col[1]}")
            print(f"  Boş Kabul: {col[2]}")
            print(f"  Default: {col[3]}")
    else:
        print("Tablo bulunamadı!")
    
    # Foreign key constraints kontrol et
    print("\n" + "=" * 80)
    print("FOREIGN KEY CONSTRAINTS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT tc.constraint_name, kcu.column_name, ccu.table_name, ccu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public' AND tc.table_name = 'inventory_stock' AND tc.constraint_type = 'FOREIGN KEY';
    """)
    
    fks = cursor.fetchall()
    if fks:
        for fk in fks:
            print(f"\nConstraint: {fk[0]}")
            print(f"  Kolon: {fk[1]} -> {fk[2]}.{fk[3]}")
    else:
        print("\nForeign key bulunamadı!")
    
    # Mağazaları görüntüle
    print("\n" + "=" * 80)
    print("MAĞAZALAR")
    print("=" * 80)
    
    cursor.execute("SELECT code, name FROM inventory_store ORDER BY code;")
    stores = cursor.fetchall()
    
    if stores:
        for store in stores:
            print(f"  {store[0]} - {store[1]}")
    else:
        print("  Mağaza bulunamadı!")

