from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from .models import UserProfile, Product, Store, Stock, StockMovement
from .forms import UserRegistrationForm, ProductForm
def register(request):
    # Sadece admin kullanıcıları kayıt oluşturabilir
    try:
        profile = request.user.profile
        if profile.role != 'admin':
            return HttpResponseForbidden('❌ Yalnızca Admin kullanıcılar yeni kullanıcı kaydı oluşturabilir.')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('❌ Yalnızca Admin kullanıcılar yeni kullanıcı kaydı oluşturabilir.')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            store = form.cleaned_data.get('store')
            UserProfile.objects.create(
                user=user, 
                role='employee', 
                store_code=store.code if store else None
            )
            return render(request, 'registration/register_success.html')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        store_code = request.POST.get('store_code', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Boş alan kontrolü
        if not store_code or not username or not password:
            messages.error(request, '❌ Mağaza kodu, kullanıcı adı ve şifre alanları boş bırakılamaz.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'username': username
            })
        
        # Mağaza kontrol et
        try:
            store = Store.objects.get(code=store_code)
        except Store.DoesNotExist:
            messages.error(request, '❌ Mağaza kodu geçersiz.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'username': username
            })
        
        # Kullanıcıyı adıyla bul
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, '❌ Kullanıcı adı veya şifre hatalı.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'username': username
            })
        
        # Profili kontrol et - mağaza uyumu
        try:
            profile = user.profile
            if profile.store_code != store_code:
                messages.error(request, '❌ Bu kullanıcı bu mağazada çalışmıyor.')
                return render(request, 'registration/login.html', {
                    'store_code': store_code,
                    'username': username
                })
        except UserProfile.DoesNotExist:
            messages.error(request, '❌ Kullanıcı profili bulunamadı.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'username': username
            })
        
        # Şifreyi kontrol et
        if user.check_password(password):
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Şifre yanlış.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'username': username
            })
    
    return render(request, 'registration/login.html')


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Profil yoksa oluştur
        profile = UserProfile.objects.create(
            user=request.user,
            role='employee'
        )
    
    # Giriş yapılan mağazadaki toplam stok adedi
    total_stock_quantity = 0
    if profile.store_code:
        from django.db.models import Sum
        result = Stock.objects.filter(store_code=profile.store_code).aggregate(Sum('quantity'))
        total_stock_quantity = result['quantity__sum'] or 0
    
    context = {
        'total_users': User.objects.count(),
        'total_stores': Store.objects.count(),
        'total_products': Product.objects.count(),
        'total_stock_quantity': total_stock_quantity,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required(login_url='login')
@login_required(login_url='login')
def product_browser(request):
    search_results = []
    grouped_results = {}
    searched = False
    no_results = False
    show_color_selector = False
    available_colors = []
    selected_color = None
    selected_product = None
    product_variants = []
    variant_stocks = {}

    # Kullanıcının mağazasını al
    user_store_code = None
    try:
        user_store_code = request.user.profile.store_code
    except (UserProfile.DoesNotExist, AttributeError):
        pass

    # Arama parametreleri
    spec_code = request.GET.get('spec_code', '').strip()
    barcode = request.GET.get('barcode', '').strip()
    prod_name = request.GET.get('prod_name', '').strip()

    # En az bir arama parametresi varsa arama yap
    if spec_code or barcode or prod_name:
        searched = True
        
        # Arama yap
        query = Q()
        
        if spec_code:
            query |= Q(specCode__icontains=spec_code)
        
        if barcode:
            # Barkod araması - o barkoda ait specCode'u bul
            barcode_product = Product.objects.filter(barcode__icontains=barcode).first()
            if barcode_product:
                query |= Q(specCode=barcode_product.specCode)
            else:
                query |= Q(barcode__icontains=barcode)
        
        if prod_name:
            query |= Q(prodName__icontains=prod_name)
        
        search_results = Product.objects.filter(query).order_by('specCode', 'colour')
        
        if search_results.exists():
            # Benzersiz specCode'ları kontrol et
            unique_spec_codes = set(p.specCode for p in search_results)
            
            # Eğer sadece 1 specCode varsa - renk seçim ekranı göster
            if len(unique_spec_codes) == 1:
                show_color_selector = True
                all_products = search_results
                
                # Benzersiz renkleri al
                available_colors = sorted(set(p.colour for p in all_products if p.colour))
                
                # İlk rengi default olarak seç
                if available_colors:
                    selected_color = request.GET.get('selected_color', available_colors[0])
                    # Seçili renge göre ürünleri filtrele
                    filtered_products = all_products.filter(colour=selected_color).order_by('barcode')
                    if filtered_products.exists():
                        selected_product = filtered_products.first()
                        product_variants = list(filtered_products)
                        
                        # Stok bilgisini al
                        for variant in product_variants:
                            stocks = {}
                            if user_store_code:
                                warehouse_stock = Stock.objects.filter(
                                    barcode=variant.barcode,
                                    store_code=user_store_code,
                                    location='warehouse'
                                ).first()
                                shelf_stock = Stock.objects.filter(
                                    barcode=variant.barcode,
                                    store_code=user_store_code,
                                    location='shelf'
                                ).first()
                                stocks['warehouse'] = warehouse_stock.quantity if warehouse_stock else 0
                                stocks['shelf'] = shelf_stock.quantity if shelf_stock else 0
                            else:
                                stocks['warehouse'] = 0
                                stocks['shelf'] = 0
                            
                            variant_stocks[variant.barcode] = stocks
                    else:
                        no_results = True
                else:
                    no_results = True
            else:
                # Birden fazla specCode varsa - normal sonuçları göster
                # Ürünleri spec_code'a göre grupla
                for product in search_results:
                    spec = product.specCode
                    if spec not in grouped_results:
                        grouped_results[spec] = {
                            'main_product': product,
                            'variants': []
                        }
                    grouped_results[spec]['variants'].append(product)
                
                # Tüm sonuçlar için stok bilgisini al
                for product in search_results:
                    stocks = {}
                    if user_store_code:
                        warehouse_stock = Stock.objects.filter(
                            barcode=product.barcode,
                            store_code=user_store_code,
                            location='warehouse'
                        ).first()
                        shelf_stock = Stock.objects.filter(
                            barcode=product.barcode,
                            store_code=user_store_code,
                            location='shelf'
                        ).first()
                        stocks['warehouse'] = warehouse_stock.quantity if warehouse_stock else 0
                        stocks['shelf'] = shelf_stock.quantity if shelf_stock else 0
                    else:
                        stocks['warehouse'] = 0
                        stocks['shelf'] = 0
                    
                    variant_stocks[product.barcode] = stocks
        else:
            no_results = True

    context = {
        'search_results': search_results,
        'grouped_results': grouped_results,
        'searched': searched,
        'no_results': no_results,
        'spec_code': spec_code,
        'barcode': barcode,
        'prod_name': prod_name,
        'show_color_selector': show_color_selector,
        'available_colors': available_colors,
        'selected_color': selected_color,
        'selected_product': selected_product,
        'product_variants': product_variants,
        'variant_stocks': variant_stocks,
    }
    return render(request, 'inventory/product_browser.html', context)


@login_required(login_url='login')
def warehouse_shelf(request):
    """
    Depo ↔ Reyon stok transferi
    Sadece bir mağaza içinde depo ve reyon arasında ürün hareketi
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, '❌ Kullanıcı profili bulunamadı.')
        return redirect('dashboard')
    
    if not profile.store_code:
        messages.error(request, '❌ Bir mağazaya atanmamışsınız.')
        return redirect('dashboard')
    
    store_code = profile.store_code
    context = {'store_code': store_code}
    
    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        from_location = request.POST.get('from_location', '').strip()
        to_location = request.POST.get('to_location', '').strip()
        quantity_str = request.POST.get('quantity', '0').strip()
        
        # Validasyon
        errors = []
        
        if not barcode:
            errors.append('Barkod zorunludur.')
        
        if not from_location or not to_location:
            errors.append('Nereden ve nereye seçilmelidir.')
        elif from_location == to_location:
            errors.append('Aynı yerden aynı yere transfer yapılamaz.')
        
        if not quantity_str:
            errors.append('Miktar zorunludur.')
        else:
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    errors.append('Miktar pozitif olmalıdır.')
            except ValueError:
                errors.append('Miktar sayı olmalıdır.')
        
        # Ürün ve stok kontrolü
        if not errors:
            try:
                Product.objects.get(barcode=barcode)
            except Product.DoesNotExist:
                errors.append(f'Barkod "{barcode}" sisteme kayıtlı değil.')
            
            # Gönderenen yerde yeterli stok var mı?
            if not errors:
                from .models import Stock
                stock_from = Stock.objects.filter(
                    barcode=barcode,
                    store_code=store_code,
                    location=from_location
                ).first()
                
                if not stock_from or stock_from.quantity < quantity:
                    current_qty = stock_from.quantity if stock_from else 0
                    errors.append(
                        f'{["Depo", "Reyon"][from_location == "shelf"]}\'de yeterli stok yok. '
                        f'Mevcut: {current_qty}, İstenen: {quantity}'
                    )
        
        if errors:
            for error in errors:
                messages.error(request, f'❌ {error}')
        else:
            # Transfer işlemi
            with transaction.atomic():
                from .models import Stock, StockMovement
                
                # Gönderenden çıkart
                stock_from = Stock.objects.get(
                    barcode=barcode,
                    store_code=store_code,
                    location=from_location
                )
                stock_from.quantity -= quantity
                stock_from.save()
                
                # Alıcıya ekle
                stock_to, created = Stock.objects.get_or_create(
                    barcode=barcode,
                    store_code=store_code,
                    location=to_location,
                    defaults={'quantity': 0}
                )
                stock_to.quantity += quantity
                stock_to.save()
                
                # Hareket kaydı
                location_names = {'warehouse': 'Depo', 'shelf': 'Reyon'}
                StockMovement.objects.create(
                    barcode=barcode,
                    store_code=store_code,
                    movement_type='transfer',
                    quantity=quantity,
                    from_location=from_location,
                    to_location=to_location,
                    location=from_location,
                    created_by=request.user
                )
                
                messages.success(
                    request,
                    f'✅ {quantity} adet "{barcode}" {location_names[from_location]}\'den '
                    f'{location_names[to_location]}\'a aktarıldı.'
                )
            
            # Form temizle
            return redirect('warehouse_shelf')
    
    return render(request, 'inventory/warehouse_shelf.html', context)


# Admin Panel Decorators
def admin_required(view_func):
    """Admin rolü gerektiren decorator"""
    def wrapper(request, *args, **kwargs):
        try:
            profile = request.user.profile
            if profile.role != 'admin' and not request.user.is_superuser:
                messages.error(request, '❌ Bu sayfaya erişim izniniz yok.')
                return redirect('dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, '❌ Bu sayfaya erişim izniniz yok.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@admin_required
def admin_panel(request):
    """Admin dashboard sayfası"""
    context = {
        'total_users': User.objects.count(),
        'total_stores': Store.objects.count(),
        'total_products': Product.objects.count(),
        'total_stocks': Stock.objects.count(),
    }
    return render(request, 'inventory/admin/dashboard.html', context)


@admin_required
def admin_users(request):
    """Kullanıcı yönetimi sayfası"""
    users = User.objects.all().order_by('id')
    context = {'users': users}
    return render(request, 'inventory/admin/users.html', context)


@admin_required
def admin_delete_user(request, user_id):
    """Kullanıcı silme işlemi"""
    try:
        user_to_delete = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '❌ Kullanıcı bulunamadı.')
        return redirect('admin_users')
    
    # Kendi kendini silemez
    if request.user.id == user_id:
        messages.error(request, '❌ Kendi hesabınızı silemezsiniz.')
        return redirect('admin_users')
    
    # Admin başka admin silemez
    if request.user.profile.role == 'admin':
        try:
            deleted_user_profile = user_to_delete.profile
            if deleted_user_profile.role == 'admin':
                messages.error(request, '❌ Adminler başka adminleri silemez.')
                return redirect('admin_users')
        except UserProfile.DoesNotExist:
            pass
    
    username = user_to_delete.username
    user_to_delete.delete()
    messages.success(request, f'✅ {username} kullanıcısı başarıyla silindi.')
    return redirect('admin_users')


def admin_stores(request):
    """Mağaza yönetimi sayfası"""
    stores = Store.objects.all()
    context = {'stores': stores}
    return render(request, 'inventory/admin/stores.html', context)


@admin_required
def admin_products(request):
    """Ürün yönetimi sayfası"""
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'inventory/admin/products.html', context)


@admin_required
def admin_stocks(request):
    """Ürün yönetimi sayfası"""
    stocks = Stock.objects.all()
    context = {'stocks': stocks}
    return render(request, 'inventory/admin/stocks.html', context)


@admin_required
def admin_stocks_management(request):
    """Ürün yönetimi sayfası - Yeni ürün kaydı ve listeleme"""
    form = ProductForm()
    products = Product.objects.all().order_by('-barcode')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            messages.success(request, f'✅ "{product.prodName}" ürünü başarıyla kaydedildi.')
            return redirect('admin_stocks_management')
        else:
            messages.error(request, '❌ Ürün kaydı sırasında hata oluştu. Lütfen kontrol ediniz.')
    
    context = {
        'form': form,
        'products': products,
        'total_products': products.count(),
    }
    return render(request, 'inventory/admin/stocks_management.html', context)


@admin_required
def admin_create_user(request):
    """Yeni kullanıcı oluşturma sayfası"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        store_code = request.POST.get('store_code', '').strip()
        
        # Rol ve Kullanıcı ID kodu sabit değerler
        role = 'employee'
        user_id_code = ''
        
        # Validasyon
        errors = []
        
        if not username:
            errors.append('Kullanıcı adı zorunludur.')
        elif User.objects.filter(username=username).exists():
            errors.append('Bu kullanıcı adı zaten kullanılıyor.')
        
        if not email:
            errors.append('E-posta zorunludur.')
        elif User.objects.filter(email=email).exists():
            errors.append('Bu e-posta zaten kayıtlı.')
        
        if not first_name:
            errors.append('Ad alanı zorunludur.')
        
        if not last_name:
            errors.append('Soyad alanı zorunludur.')
        
        if not password:
            errors.append('Şifre zorunludur.')
        elif password != password_confirm:
            errors.append('Şifreler eşleşmiyor.')
        elif len(password) < 6:
            errors.append('Şifre en az 6 karakter olmalıdır.')
        
        if not store_code:
            errors.append('Mağaza seçilmelidir.')
        elif not Store.objects.filter(code=store_code).exists():
            errors.append('Geçersiz mağaza kodu.')
        
        if errors:
            stores = Store.objects.all()
            context = {
                'stores': stores,
                'errors': errors,
                'form_data': {
                    'username': username,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'store_code': store_code,
                }
            }
            return render(request, 'inventory/admin/create_user.html', context)
        
        # Kullanıcı oluştur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Profil oluştur
        UserProfile.objects.create(
            user=user,
            role=role,
            store_code=store_code if store_code else None,
            is_active=True
        )
        
        messages.success(request, f'✅ {username} kullanıcısı başarıyla oluşturuldu.')
        return redirect('admin_users')
    
    stores = Store.objects.all()
    context = {'stores': stores}
    return render(request, 'inventory/admin/create_user.html', context)

