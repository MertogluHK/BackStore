from django.core.management.base import BaseCommand
from inventory.models import Shipment, Store
from django.http import JsonResponse
import traceback

class Command(BaseCommand):
    help = 'Test load_shipment action logic'

    def handle(self, *args, **options):
        """Test load_shipment by simulating the action"""
        
        try:
            # Get the latest shipment
            shipment = Shipment.objects.latest('created_at')
            self.stdout.write(f"✓ Latest shipment: {shipment.shipment_code} (ID: {shipment.id})")
            
            # Simulate load_shipment action
            sender_store_code = shipment.sender_store.code
            self.stdout.write(f"  Sender store: {sender_store_code}")
            
            # This is what the view does
            shipment = Shipment.objects.get(id=shipment.id, sender_store__code=sender_store_code)
            self.stdout.write(f"✓ Shipment query successful")
            
            # Get items
            items = []
            for item in shipment.items.all():
                items.append({
                    'id': item.id,
                    'product_name': item.product.prodName,
                    'product_size': item.product.sizeAge,
                    'product_color': item.product.colour,
                    'spec_code': item.product.specCode,
                    'barcode': item.barcode,
                    'quantity': item.quantity,
                    'price': item.product.price or 0
                })
            
            self.stdout.write(f"✓ Items fetched: {len(items)}")
            
            # Access properties
            self.stdout.write(f"  item_count property: {shipment.item_count}")
            self.stdout.write(f"  unique_products property: {shipment.unique_products}")
            
            # Try to build JSON response
            response_data = {
                'success': True,
                'shipment_id': shipment.id,
                'shipment_code': shipment.shipment_code,
                'receiver_store_name': shipment.receiver_store.name,
                'status': shipment.status,
                'total_items': shipment.item_count,
                'unique_products': shipment.unique_products,
                'items': items
            }
            
            self.stdout.write(f"✓ Response data built successfully")
            self.stdout.write(f"  Response: {response_data}")
            
        except Exception as e:
            error_msg = traceback.format_exc()
            self.stdout.write(self.style.ERROR(f"✗ Error occurred:\n{error_msg}"))
