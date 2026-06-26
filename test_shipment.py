import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')
django.setup()

from inventory.models import Shipment, ShipmentItem

# Get the latest shipment
try:
    shipment = Shipment.objects.latest('created_at')
    print(f"✓ Latest Shipment: {shipment.shipment_code}")
    print(f"  - ID: {shipment.id}")
    print(f"  - Sender: {shipment.sender_store.code}")
    print(f"  - Receiver: {shipment.receiver_store.code}")
    print(f"  - Status: {shipment.status}")
    print(f"  - Created By: {shipment.created_by}")
    
    # Try to access items
    print(f"\n  - Items count: {shipment.items.count()}")
    print(f"  - Item count (property): {shipment.item_count}")
    print(f"  - Unique products: {shipment.unique_products}")
    
    # List items
    for item in shipment.items.all():
        print(f"    • Item {item.id}: {item.barcode} - Qty: {item.quantity}")
        print(f"      Product: {item.product.prodName if item.product else 'NULL'}")
    
    print("\n✓ Test PASSED")
except Shipment.DoesNotExist:
    print("✗ No shipments found")
except Exception as e:
    import traceback
    print(f"✗ Error: {e}")
    traceback.print_exc()
