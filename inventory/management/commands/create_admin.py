from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile, Store


class Command(BaseCommand):
    help = 'Tüm mağazalar için admin kullanıcılarını oluştur'

    def handle(self, *args, **options):
        # Tüm mağazaları al
        stores = Store.objects.all().order_by('code')
        
        if not stores.exists():
            self.stdout.write(self.style.ERROR('❌ Mağaza bulunamadı. Önce mağazaları oluşturunuz.'))
            return
        
        self.stdout.write(self.style.SUCCESS('🔧 Mağaza Admin Kullanıcıları Oluşturuluyor...\n'))
        
        created_count = 0
        skipped_count = 0
        
        for store in stores:
            username = f'admin{store.code}'
            password = store.code
            user_id_code = username  # adminM1, adminM2, vb.
            
            # Kullanıcı var mı kontrol et
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'⚠ {username} zaten mevcut, atlandı'))
                skipped_count += 1
                continue
            
            try:
                # Admin User oluştur
                admin_user = User.objects.create_user(
                    username=username,
                    email=f'admin{store.code.lower()}@backstore.com',
                    password=password,
                    first_name='Mağaza',
                    last_name=f'Admin-{store.code}'
                )
                
                # AdminProfile oluştur
                UserProfile.objects.create(
                    user=admin_user,
                    user_id_code=user_id_code,
                    role='admin',
                    store=store,
                    is_active=True
                )
                
                self.stdout.write(self.style.SUCCESS(f'✓ {username} oluşturuldu'))
                self.stdout.write(f'  └─ Mağaza: {store.name}')
                self.stdout.write(f'  └─ Şifre: {password}')
                created_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ {username} oluşturulurken hata: {str(e)}'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Toplam {created_count} admin kullanıcı oluşturuldu'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ {skipped_count} kullanıcı zaten mevcut idi'))
