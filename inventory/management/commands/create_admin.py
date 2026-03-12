from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile, Store


class Command(BaseCommand):
    help = 'İlk admin kullanıcıyı oluştur'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=str, help='Admin kullanıcı ID')
        parser.add_argument('--store-code', type=str, help='Mağaza kodu')

    def handle(self, *args, **options):
        # Argümanları veya varsayılan değerleri al
        user_id = options.get('user_id') or 'ADMIN001'
        store_code = options.get('store_code') or 'M01'

        # Store'u bul
        try:
            store = Store.objects.get(code=store_code)
        except Store.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ {store_code} mağazası bulunamadı'))
            return

        # Admin kullanıcı var mı kontrol et
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('⚠ Admin kullanıcı zaten mevcut'))
            return

        # Admin User oluştur
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@backstore.com',
            password='admin123',
            first_name='Sistem',
            last_name='Admin'
        )

        # AdminProfile oluştur
        UserProfile.objects.create(
            user=admin_user,
            user_id_code=user_id,
            role='admin',
            store=store,
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'✓ Admin kullanıcı oluşturuldu'))
        self.stdout.write(self.style.SUCCESS(f'  Mağaza Kodu: {store_code}'))
        self.stdout.write(self.style.SUCCESS(f'  Kullanıcı ID: {user_id}'))
        self.stdout.write(self.style.SUCCESS(f'  Kullanıcı Adı: admin'))
        self.stdout.write(self.style.SUCCESS(f'  Şifre: admin123'))
        self.stdout.write(self.style.WARNING('⚠ ŞİFREYİ DEĞİŞTİRMEYİ UNUTMAYIN!'))
