from django.contrib import admin
from .models import Store, Product, Stock, UserProfile, StockMovement


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'city')
    search_fields = ('name', 'address', 'city')
    ordering = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'role', 'store', 'is_active')
    list_filter = ('role', 'is_active', 'store')
    search_fields = ('user__username', 'user__email')
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Kullanıcı Adı'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('prodName', 'specCode', 'sizeAge', 'colour', 'price', 'discount')
    list_filter = ('gender', 'created_at')
    search_fields = ('prodName', 'specCode', 'barcode')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('specCode', 'barcode', 'prodName')
        }),
        ('Özellikler', {
            'fields': ('sizeAge', 'colour', 'gender')
        }),
        ('Fiyatlandırma', {
            'fields': ('price', 'discount')
        }),
        ('Durum', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'store_code', 'quantity', 'is_low_stock')
    list_filter = ('store_code', 'created_at')
    search_fields = ('barcode', 'store_code')
    readonly_fields = ('created_at', 'updated_at', 'last_checked')
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Düşük Stok'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'store_code', 'movement_type', 'quantity', 'created_by', 'created_at')
    list_filter = ('movement_type', 'store_code', 'created_at')
    search_fields = ('barcode', 'store_code', 'reference', 'notes')
    readonly_fields = ('created_by', 'created_at')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
