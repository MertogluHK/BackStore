from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class Store(models.Model):
    code = models.CharField(max_length=10, primary_key=True, verbose_name=_('Mağaza Kodu'))
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Mağaza Adı'))
    address = models.CharField(max_length=255, verbose_name=_('Adres'))
    city = models.CharField(max_length=100, verbose_name=_('Şehir'))
    phone = models.CharField(max_length=20, verbose_name=_('Telefon'))
    is_active = models.BooleanField(default=True, verbose_name=_('Aktif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Oluşturma Tarihi'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Güncelleme Tarihi'))

    class Meta:
        verbose_name = _('Mağaza')
        verbose_name_plural = _('Mağazalar')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('employee', _('Çalışan')),
        ('manager', _('Mağaza Müdürü')),
        ('admin', _('Admin')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_id_code = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('Kullanıcı ID'))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_('Mağaza'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Kullanıcı Profili')
        verbose_name_plural = _('Kullanıcı Profilleri')

    def __str__(self):
        return f"{self.user_id_code} - {self.user.username} - {self.get_role_display()}"


class Product(models.Model):
    specCode = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Özel Kod'))
    barcode = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Barkod'))
    prodName = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Ürün Adı'))
    sizeAge = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Beden/Yaş'))
    colour = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Renk'))
    gender = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Cinsiyet'))
    price = models.IntegerField(null=True, blank=True, verbose_name=_('Fiyat'))
    discount = models.IntegerField(default=0, verbose_name=_('İndirim'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Oluşturma Tarihi'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Güncelleme Tarihi'))

    class Meta:
        verbose_name = _('Ürün')
        verbose_name_plural = _('Ürünler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['specCode']),
            models.Index(fields=['barcode']),
        ]

    def __str__(self):
        return f"{self.prodName} - {self.sizeAge} ({self.colour})"


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks', verbose_name=_('Ürün'))
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stocks', verbose_name=_('Mağaza'))
    quantity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_('Miktar'))
    last_checked = models.DateTimeField(auto_now=True, verbose_name=_('Son Kontrol'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Oluşturma Tarihi'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Güncelleme Tarihi'))

    class Meta:
        unique_together = ('barcode', 'store_code')
        verbose_name = _('Stok')
        verbose_name_plural = _('Stoklar')
        indexes = [
            models.Index(fields=['barcode', 'store_code']),
        ]

    def __str__(self):
        return f"{self.barcode} - {self.store_code}: {self.quantity}"

    @property
    def is_low_stock(self):
        # Ürün bilgisi almak için barcode üzerinden Product'ı sorgula
        try:
            product = Product.objects.get(barcode=self.barcode)
            return self.quantity <= getattr(product, 'reorder_level', 10)
        except Product.DoesNotExist:
            return False


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', _('Giriş')),
        ('out', _('Çıkış')),
        ('adjustment', _('Ayarlama')),
        ('return', _('İade')),
    ]

    barcode = models.CharField(max_length=50, default='', verbose_name=_('Barkod'))
    store_code = models.CharField(max_length=10, default='', verbose_name=_('Mağaza Kodu'))
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name=_('Hareket Türü'))
    quantity = models.IntegerField(verbose_name=_('Miktar'))
    reference = models.CharField(max_length=100, blank=True, verbose_name=_('Referans'))
    notes = models.TextField(blank=True, verbose_name=_('Notlar'))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_('Oluşturan'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Oluşturma Tarihi'))

    class Meta:
        verbose_name = _('Stok Hareketi')
        verbose_name_plural = _('Stok Hareketleri')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['barcode', 'store_code']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.barcode} - {self.get_movement_type_display()} ({self.quantity})"
