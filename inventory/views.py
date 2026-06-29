from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import UserProfile, Product, Store, Stock, StockMovement, Shipment, ShipmentItem
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
    multiple_fields_error = False

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

    # Kaç alanın doldurulduğunu kontrol et
    filled_fields_count = (1 if spec_code else 0) + (1 if barcode else 0) + (1 if prod_name else 0)

    # Birden fazla alan doldurulduysa hata göster
    if filled_fields_count > 1:
        multiple_fields_error = True
        searched = True
        no_results = True
    # En az bir arama parametresi varsa arama yap
    elif filled_fields_count > 0:
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
        'multiple_fields_error': multiple_fields_error,
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


@login_required(login_url='login')
def warehouse_acceptance(request):
    """
    Gelen koli kabulü: Başka mağazadan gönderilen sevkiyatları kabul et
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, '❌ Kullanıcı profili bulunamadı.')
        return redirect('dashboard')

    if not profile.store_code:
        messages.error(request, '❌ Bir mağazaya atanmamışsınız.')
        return redirect('dashboard')

    receiver_store_code = profile.store_code
    try:
        receiver_store = Store.objects.get(code=receiver_store_code)
    except Store.DoesNotExist:
        messages.error(request, '❌ Mağaza bulunamadı.')
        return redirect('dashboard')

    pending_shipments = Shipment.objects.filter(
        receiver_store__code=receiver_store_code,
        status='sent'
    ).order_by('-sent_at')

    accepted_shipments = Shipment.objects.filter(
        receiver_store__code=receiver_store_code,
        status='received'
    ).order_by('-received_at')[:10]

    context = {
        'receiver_store': receiver_store,
        'pending_shipments': pending_shipments,
        'accepted_shipments': accepted_shipments,
    }

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'load_shipment':
            try:
                shipment_id = request.POST.get('shipment_id')
                shipment = Shipment.objects.get(
                    id=shipment_id,
                    receiver_store__code=receiver_store_code,
                    status__in=['sent', 'received']
                )

                items = []
                for item in shipment.items.all():
                    items.append({
                        'id': item.id,
                        'product_name': item.product.prodName if item.product else '-',
                        'product_size': item.product.sizeAge if item.product else '-',
                        'product_color': item.product.colour if item.product else '-',
                        'spec_code': item.product.specCode if item.product else '-',
                        'barcode': item.barcode,
                        'quantity': item.quantity,
                        'price': item.product.price if item.product else 0,
                    })

                return JsonResponse({
                    'success': True,
                    'shipment_id': shipment.id,
                    'shipment_code': shipment.shipment_code,
                    'sender_store_name': shipment.sender_store.name,
                    'sender_store_code': shipment.sender_store.code,
                    'status': shipment.status,
                    'total_items': shipment.item_count,
                    'unique_products': shipment.unique_products,
                    'sent_at': shipment.sent_at.strftime('%d.%m.%Y %H:%M') if shipment.sent_at else '-',
                    'items': items,
                })
            except Shipment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Koli bulunamadı.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'accept_shipment':
            shipment_id = request.POST.get('shipment_id')

            try:
                shipment = Shipment.objects.get(
                    id=shipment_id,
                    receiver_store__code=receiver_store_code,
                    status='sent'
                )
            except Shipment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Kabul edilecek koli bulunamadı.'})

            if shipment.item_count == 0:
                return JsonResponse({'success': False, 'error': 'Boş koli kabul edilemez.'})

            with transaction.atomic():
                for item in shipment.items.all():
                    warehouse_stock, _ = Stock.objects.get_or_create(
                        barcode=item.barcode,
                        store_code=receiver_store_code,
                        location='warehouse',
                        defaults={'quantity': 0}
                    )
                    warehouse_stock.quantity += item.quantity
                    warehouse_stock.save()

                    StockMovement.objects.create(
                        barcode=item.barcode,
                        store_code=receiver_store_code,
                        movement_type='in',
                        quantity=item.quantity,
                        from_location='warehouse',
                        to_location='warehouse',
                        location='warehouse',
                        created_by=request.user,
                        notes=f'Koli kabul: {shipment.shipment_code} | {shipment.sender_store.code} → {receiver_store_code}'
                    )

                shipment.status = 'received'
                shipment.received_at = timezone.now()
                shipment.save()

            return JsonResponse({
                'success': True,
                'message': f'Koli kabul edildi. Toplam {shipment.item_count} ürün depoya eklendi.'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Geçersiz işlem türü.'})

    return render(request, 'inventory/warehouse_acceptance.html', context)


@login_required(login_url='login')
def warehouse_shipment(request):
    """
    Koli sistemi ile mağaza ↔ mağaza stok transferi
    1. Mağaza seçilince koli oluşturulur
    2. Ürünler barkod okutarak koliye eklenir
    3. Ürün çıkartılabilir
    4. Koli kapatılıp gönderilir
    """
    import uuid
    
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, '❌ Kullanıcı profili bulunamadı.')
        return redirect('dashboard')
    
    if not profile.store_code:
        messages.error(request, '❌ Bir mağazaya atanmamışsınız.')
        return redirect('dashboard')
    
    sender_store_code = profile.store_code
    try:
        sender_store = Store.objects.get(code=sender_store_code)
    except Store.DoesNotExist:
        messages.error(request, '❌ Mağaza bulunamadı.')
        return redirect('dashboard')
    
    # Alıcı mağaza seçenekleri
    available_stores = Store.objects.filter(is_active=True).exclude(code=sender_store_code)
    
    # Aktif koli (açık, kapalı ve gönderildi durumda)
    active_shipments = Shipment.objects.filter(
        sender_store__code=sender_store_code,
        status__in=['open', 'closed', 'sent']
    ).order_by('-created_at')
    open_shipments_count = active_shipments.filter(status='open').count()
    closed_shipments_count = active_shipments.filter(status='closed').count()
    sent_shipments_count = active_shipments.filter(status='sent').count()
    
    context = {
        'sender_store': sender_store,
        'available_stores': available_stores,
        'active_shipments': active_shipments,
        'open_shipments_count': open_shipments_count,
        'closed_shipments_count': closed_shipments_count,
        'sent_shipments_count': sent_shipments_count,
    }
    
    # POST işlemleri (AJAX istekleri)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        # 0. Koli detaylarını yükle (AJAX)
        if action == 'load_shipment':
            try:
                shipment_id = request.POST.get('shipment_id')
                print(f"DEBUG: load_shipment çağrıldı, shipment_id={shipment_id}, sender_store_code={sender_store_code}")
                
                shipment = Shipment.objects.get(id=shipment_id, sender_store__code=sender_store_code)
                print(f"DEBUG: Shipment bulundu: {shipment.shipment_code}")
                
                # Koli öğelerini getir
                items = []
                for item in shipment.items.all():
                    items.append({
                        'id': item.id,
                        'product_name': item.product.prodName if item.product else '',
                        'product_size': item.product.sizeAge if item.product else '',
                        'product_color': item.product.colour if item.product else '',
                        'spec_code': item.product.specCode if item.product else '',
                        'barcode': item.barcode,
                        'quantity': item.quantity,
                        'price': (item.product.price if item.product else 0) or 0
                    })
                
                print(f"DEBUG: {len(items)} ürün bulundu")
                print(f"DEBUG: item_count={shipment.item_count}, unique_products={shipment.unique_products}")
                
                return JsonResponse({
                    'success': True,
                    'shipment_id': shipment.id,
                    'shipment_code': shipment.shipment_code,
                    'receiver_store_name': shipment.receiver_store.name,
                    'status': shipment.status,
                    'total_items': shipment.item_count,
                    'unique_products': shipment.unique_products,
                    'items': items
                })
            except Shipment.DoesNotExist:
                print(f"ERROR: Shipment bulunamadı: id={shipment_id}")
                return JsonResponse({'success': False, 'error': 'Koli bulunamadı.'})
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"ERROR in load_shipment: {error_msg}")
                return JsonResponse({'success': False, 'error': str(e)})
        
        # 1. Yeni koli oluştur
        if action == 'create_shipment':
            receiver_store_code = request.POST.get('receiver_store_code', '').strip()
            
            if not receiver_store_code:
                return JsonResponse({'success': False, 'error': 'Alıcı mağaza seçilmelidir.'})
            
            if receiver_store_code == sender_store_code:
                return JsonResponse({'success': False, 'error': 'Alıcı mağaza gönderenden farklı olmalıdır.'})
            
            try:
                receiver_store = Store.objects.get(code=receiver_store_code)
            except Store.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Alıcı mağaza bulunamadı.'})
            
            # Yeni koli oluştur
            shipment_code = f"KOL-{sender_store_code}-{int(uuid.uuid4().int) % 10000000:07d}"
            shipment = Shipment.objects.create(
                shipment_code=shipment_code,
                sender_store=sender_store,
                receiver_store=receiver_store,
                status='open',
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'shipment_id': shipment.id,
                'shipment_code': shipment.shipment_code,
                'receiver_store_name': receiver_store.name,
                'status': shipment.status,
                'total_items': shipment.item_count,
                'unique_products': shipment.unique_products,
                'items': []
            })
        
        # 2. Koliye ürün ekle
        elif action == 'add_item':
            shipment_id = request.POST.get('shipment_id')
            barcode = request.POST.get('barcode', '').strip().upper()
            
            if not shipment_id or not barcode:
                return JsonResponse({'success': False, 'error': 'Koli ve barkod gerekli.'})
            
            try:
                shipment = Shipment.objects.get(id=shipment_id, sender_store__code=sender_store_code)
            except Shipment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Koli bulunamadı.'})
            
            if shipment.status != 'open':
                return JsonResponse({'success': False, 'error': 'Kapalı koliye ürün eklenemez.'})
            
            # Ürün ve stok kontrolü
            try:
                product = Product.objects.get(barcode=barcode)
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Barkod "{barcode}" sisteme kayıtlı değil.'})
            
            # Stok kontrol - Depo stoğunu kontrol et, sonra reyon stoğunu
            from django.db.models import Sum
            stock_in_shipment = ShipmentItem.objects.filter(
                shipment=shipment,
                barcode=barcode
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Depo stoğu
            warehouse_stock = Stock.objects.filter(
                barcode=barcode,
                store_code=sender_store_code,
                location='warehouse'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Reyon stoğu
            shelf_stock = Stock.objects.filter(
                barcode=barcode,
                store_code=sender_store_code,
                location='shelf'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            total_available_stock = warehouse_stock + shelf_stock
            
            if total_available_stock - stock_in_shipment <= 0:
                return JsonResponse({'success': False, 'error': 'Bu ürün mağazada mevcut değil.'})
            
            # Koliye ürün ekle ya da miktarını artır
            item, created = ShipmentItem.objects.get_or_create(
                shipment=shipment,
                barcode=barcode,
                defaults={'product': product, 'quantity': 1}
            )
            
            if item.product is None:
                item.product = product
            
            if not created:
                item.quantity += 1
            item.save()
            
            # Return the refreshed shipment state from the database
            items = []
            for shipment_item in shipment.items.select_related('product').all():
                items.append({
                    'id': shipment_item.id,
                    'product_name': shipment_item.product.prodName if shipment_item.product else '',
                    'product_size': shipment_item.product.sizeAge if shipment_item.product else '',
                    'product_color': shipment_item.product.colour if shipment_item.product else '',
                    'spec_code': shipment_item.product.specCode if shipment_item.product else '',
                    'barcode': shipment_item.barcode,
                    'quantity': shipment_item.quantity,
                    'price': (shipment_item.product.price if shipment_item.product else 0) or 0
                })
            
            return JsonResponse({
                'success': True,
                'shipment_id': shipment.id,
                'shipment_code': shipment.shipment_code,
                'receiver_store_name': shipment.receiver_store.name,
                'status': shipment.status,
                'total_items': shipment.item_count,
                'unique_products': shipment.unique_products,
                'items': items
            })
        
        # 3. Koliden ürün çıkart
        elif action == 'remove_item':
            item_id = request.POST.get('item_id')
            
            try:
                item = ShipmentItem.objects.get(id=item_id, shipment__sender_store__code=sender_store_code)
            except ShipmentItem.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Ürün bulunamadı.'})
            
            if item.shipment.status != 'open':
                return JsonResponse({'success': False, 'error': 'Kapalı koliden ürün çıkartılamaz.'})
            
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
                quantity = item.quantity
            else:
                item.delete()
                quantity = 0
            
            return JsonResponse({
                'success': True,
                'quantity': quantity
            })
        
        # 4. Koliyi kapat
        elif action == 'close_shipment':
            shipment_id = request.POST.get('shipment_id')
            
            try:
                shipment = Shipment.objects.get(id=shipment_id, sender_store__code=sender_store_code)
            except Shipment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Koli bulunamadı.'})
            
            if shipment.status != 'open':
                return JsonResponse({'success': False, 'error': 'Koli zaten kapalı.'})
            
            shipment.status = 'closed'
            shipment.closed_at = timezone.now()
            shipment.save()
            
            return JsonResponse({'success': True, 'message': 'Koli kapatıldı.'})
        
        # 5. Koliyi gönder
        elif action == 'send_shipment':
            shipment_id = request.POST.get('shipment_id')
            
            try:
                shipment = Shipment.objects.get(id=shipment_id, sender_store__code=sender_store_code)
            except Shipment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Koli bulunamadı.'})
            
            if shipment.status != 'closed':
                return JsonResponse({'success': False, 'error': 'Kapalı olmayan koliler gönderilemez.'})
            
            if shipment.item_count == 0:
                return JsonResponse({'success': False, 'error': 'Boş koli gönderilemez.'})
            
            # Transfer işlemi
            with transaction.atomic():
                for item in shipment.items.all():
                    # Gönderen mağazadan çıkart - ÖNCELİK: Depo stoğu → Reyon stoğu
                    warehouse_stock = Stock.objects.filter(
                        barcode=item.barcode,
                        store_code=sender_store_code,
                        location='warehouse'
                    ).first()
                    
                    shelf_stock = Stock.objects.filter(
                        barcode=item.barcode,
                        store_code=sender_store_code,
                        location='shelf'
                    ).first()
                    
                    remaining = item.quantity
                    
                    # İlk olarak depo stoğundan al
                    if warehouse_stock and warehouse_stock.quantity > 0:
                        take = min(warehouse_stock.quantity, remaining)
                        warehouse_stock.quantity -= take
                        warehouse_stock.save()
                        remaining -= take
                    
                    # Eksik kısmı reyon stoğundan al
                    if remaining > 0 and shelf_stock and shelf_stock.quantity > 0:
                        take = min(shelf_stock.quantity, remaining)
                        shelf_stock.quantity -= take
                        shelf_stock.save()

                    StockMovement.objects.create(
                        barcode=item.barcode,
                        store_code=sender_store_code,
                        movement_type='shipment',
                        quantity=item.quantity,
                        from_location='warehouse',
                        to_location='warehouse',
                        location='warehouse',
                        created_by=request.user,
                        notes=f'Koli: {shipment.shipment_code} | {sender_store_code} → {shipment.receiver_store.code}'
                    )
                
                # Koliyi gönderildi olarak işaretle
                shipment.status = 'sent'
                shipment.sent_at = timezone.now()
                shipment.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Koli başarıyla gönderildi. Toplam {shipment.item_count} ürün aktarıldı.'
            })
        
        # 6. Açık koli sil
        elif action == 'delete_shipment':
            shipment_id = request.POST.get('shipment_id')
            
            try:
                shipment = Shipment.objects.get(id=shipment_id, sender_store__code=sender_store_code)
            except Shipment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Koli bulunamadı.'})

            if shipment.status != 'open':
                return JsonResponse({'success': False, 'error': 'Sadece açık koli silinebilir.'})

            with transaction.atomic():
                shipment.delete()

            return JsonResponse({'success': True, 'message': 'Açık koli başarıyla silindi.'})
    
    return render(request, 'inventory/warehouse_shipment.html', context)


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
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, f'❌ {error}')
    
    context = {
        'form': form,
        'products': products,
        'total_products': products.count(),
    }
    return render(request, 'inventory/admin/stocks_management.html', context)


@admin_required
def admin_delete_product(request, product_id):
    """Ürün silme işlemi"""
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, '❌ Ürün bulunamadı.')
        return redirect('admin_stocks_management')

    if ShipmentItem.objects.filter(product=product).exists():
        messages.error(request, '❌ Bu ürün koli kayıtlarında kullanıldığı için silinemez.')
        return redirect('admin_stocks_management')

    product_name = product.prodName or product.barcode or 'Ürün'
    barcode = product.barcode

    with transaction.atomic():
        if barcode:
            Stock.objects.filter(barcode=barcode).delete()
        product.delete()

    messages.success(request, f'✅ "{product_name}" ürünü başarıyla silindi.')
    return redirect('admin_stocks_management')


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

