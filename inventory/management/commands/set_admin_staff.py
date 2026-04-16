from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile


class Command(BaseCommand):
    help = 'Admin kullanıcıların is_staff flagini True yapar'

    def handle(self, *args, **options):
        # Admin rolüne sahip tüm kullanıcıları bul
        admin_profiles = UserProfile.objects.filter(role='admin')
        
        if not admin_profiles.exists():
            self.stdout.write(self.style.WARNING('❌ Admin kullanıcısı bulunamadı'))
            return
        
        self.stdout.write('🔧 Admin Kullanıcılarına is_staff Veriliyor...\n')
        updated = 0
        
        for profile in admin_profiles:
            user = profile.user
            if not user.is_staff:
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ {user.username} → is_staff=True'))
                updated += 1
            else:
                self.stdout.write(f'✓ {user.username} zaten is_staff=True')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ {updated} kullanıcı güncellendi'))
