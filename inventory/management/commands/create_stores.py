from django.core.management.base import BaseCommand
from inventory.models import Store

class Command(BaseCommand):
    help = 'Mağazaları oluştur'

    def handle(self, *args, **options):
        stores_data = [
            {
                'code': 'M01',
                'name': 'İstanbul Mağazası',
                'address': 'Sultanbeyli, İstanbul',
                'city': 'İstanbul',
                'phone': '0212-XXX-XXXX',
            },
            {
                'code': 'M02',
                'name': 'Ankara Mağazası',
                'address': 'Çankaya, Ankara',
                'city': 'Ankara',
                'phone': '0312-XXX-XXXX',
            },
            {
                'code': 'M03',
                'name': 'İzmir Mağazası',
                'address': 'Alsancak, İzmir',
                'city': 'İzmir',
                'phone': '0232-XXX-XXXX',
            },
            {
                'code': 'M04',
                'name': 'Bursa Mağazası',
                'address': 'Osmangazi, Bursa',
                'city': 'Bursa',
                'phone': '0224-XXX-XXXX',
            },
            {
                'code': 'M05',
                'name': 'Antalya Mağazası',
                'address': 'Muratpaşa, Antalya',
                'city': 'Antalya',
                'phone': '0242-XXX-XXXX',
            },
        ]

        for store_data in stores_data:
            store, created = Store.objects.get_or_create(
                code=store_data['code'],
                defaults=store_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {store.code} - {store.name} oluşturuldu')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ {store.code} - {store.name} zaten mevcut')
                )

        self.stdout.write(self.style.SUCCESS('\n✓ Mağaza oluşturma tamamlandı'))
