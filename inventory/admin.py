from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Store, Product, Stock, UserProfile, StockMovement, Shipment, ShipmentItem


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fields = ('role', 'store_code', 'user_id_code', 'is_active')
    extra = 0


# User modelini unregister et ve özel admin ile register et
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'first_name', 'email', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'city', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'created_at')
    search_fields = ('name', 'address', 'city', 'code')
    ordering = ('code',)
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('code', 'name', 'address')
        }),
        ('İletişim Bilgileri', {
            'fields': ('city', 'phone')
        }),
        ('Durum', {
            'fields': ('is_active',)
        }),
        ('Sistem Bilgisi', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_email', 'role', 'store_code', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'store_code', 'created_at')
    search_fields = ('user__username', 'user__email', 'user_id_code', 'store_code')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Kullanıcı Bilgisi', {
            'fields': ('user', 'user_id_code')
        }),
        ('Rol ve İzinler', {
            'fields': ('role', 'is_active')
        }),
        ('Mağaza Ataması', {
            'fields': ('store_code',)
        }),
        ('Sistem Bilgisi', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Kullanıcı Adı'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'E-posta'


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
    list_display = ('barcode', 'store_code', 'location', 'quantity', 'is_low_stock', 'updated_at')
    list_filter = ('store_code', 'location', 'updated_at')
    search_fields = ('barcode', 'store_code')
    readonly_fields = ('created_at', 'updated_at', 'last_checked')
    fieldsets = (
        ('Ürün Bilgisi', {
            'fields': ('barcode',)
        }),
        ('Mağaza Bilgisi', {
            'fields': ('store_code', 'location')
        }),
        ('Stok Bilgisi', {
            'fields': ('quantity', 'is_low_stock')
        }),
        ('Zaman Bilgisi', {
            'fields': ('created_at', 'updated_at', 'last_checked'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Admin değilse sadece kendi mağazasını görsün
        if request.user.is_superuser:
            return qs
        try:
            store_code = request.user.profile.store_code
            return qs.filter(store_code=store_code)
        except:
            return qs.none()
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Düşük Stok'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'store_code', 'location', 'movement_type', 'quantity', 'created_by', 'created_at')
    list_filter = ('movement_type', 'store_code', 'location', 'created_at')
    search_fields = ('barcode', 'store_code', 'reference', 'notes')
    readonly_fields = ('created_by', 'created_at')
    fieldsets = (
        ('Ürün Bilgisi', {
            'fields': ('barcode', 'reference')
        }),
        ('Mağaza Bilgisi', {
            'fields': ('store_code', 'location')
        }),
        ('Hareket Bilgisi', {
            'fields': ('movement_type', 'quantity', 'from_location', 'to_location')
        }),
        ('İlave Notlar', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Sistem Bilgisi', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Admin değilse sadece kendi mağazasını görsün
        if request.user.is_superuser:
            return qs
        try:
            store_code = request.user.profile.store_code
            return qs.filter(store_code=store_code)
        except:
            return qs.none()


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    fields = ('barcode', 'product', 'quantity', 'added_at')
    readonly_fields = ('added_at',)
    extra = 0


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('shipment_code', 'sender_store', 'receiver_store', 'status', 'item_count', 'unique_products', 'created_by', 'created_at')
    list_filter = ('status', 'sender_store', 'receiver_store', 'created_at')
    search_fields = ('shipment_code', 'sender_store__code', 'receiver_store__code')
    readonly_fields = ('created_by', 'created_at', 'closed_at', 'sent_at')
    inlines = [ShipmentItemInline]
    
    fieldsets = (
        ('Koli Bilgisi', {
            'fields': ('shipment_code', 'status')
        }),
        ('Mağazalar', {
            'fields': ('sender_store', 'receiver_store')
        }),
        ('Sistem Bilgisi', {
            'fields': ('created_by', 'created_at', 'closed_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            store_code = request.user.profile.store_code
            return qs.filter(sender_store__code=store_code)
        except:
            return qs.none()


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'get_shipment_code', 'quantity', 'added_at')
    list_filter = ('shipment__status', 'added_at')
    search_fields = ('barcode', 'shipment__shipment_code')
    readonly_fields = ('added_at',)
    
    def get_shipment_code(self, obj):
        return obj.shipment.shipment_code
    get_shipment_code.short_description = 'Koli'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            store_code = request.user.profile.store_code
            return qs.filter(shipment__sender_store__code=store_code)
        except:
            return qs.none()
