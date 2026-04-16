from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile, Store


class Command(BaseCommand):
    help = 'AdminM1-M5 kullanıcılarının rollerini admin yapar'

    def handle(self, *args, **options):
        stores = Store.objects.all().order_by('code')
        
        if not stores.exists():
            self.stdout.write(self.style.ERROR('❌ Mağaza bulunamadı'))
            return
        
        self.stdout.write('🔧 Admin Rollerini Güncelleniyor...\n')
        updated = 0
        
        for store in stores:
            username = f'admin{store.code}'
            try:
                user = User.objects.get(username=username)
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                if profile.role != 'admin':
                    profile.role = 'admin'
                    profile.store_code = store.code
                    profile.is_active = True
                    profile.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ {username} → admin rolü verildi'))
                    updated += 1
                else:
                    self.stdout.write(f'✓ {username} zaten admin')
                    
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ {username} kullanıcısı bulunamadı'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ {updated} kullanıcı güncellendi'))
