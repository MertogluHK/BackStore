from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from .models import UserProfile, Product, Store
from .forms import UserRegistrationForm


@login_required(login_url='login')
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
            user_id = form.cleaned_data.get('user_id')
            UserProfile.objects.create(user=user, role='employee', store=store, user_id_code=user_id)
            return render(request, 'registration/register_success.html')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        store_code = request.POST.get('store_code', '').strip()
        user_id = request.POST.get('user_id', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Boş alan kontrolü
        if not store_code or not user_id or not password:
            messages.error(request, '❌ Mağaza kodu, kullanıcı ID ve şifre alanları boş bırakılamaz.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'user_id': user_id
            })
        
        # Mağaza kontrol et
        try:
            store = Store.objects.get(code=store_code)
        except Store.DoesNotExist:
            messages.error(request, '❌ Mağaza kodu geçersiz.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'user_id': user_id
            })
        
        # Kullanıcı profili bul
        try:
            profile = UserProfile.objects.get(user_id_code=user_id, store=store)
        except UserProfile.DoesNotExist:
            messages.error(request, '❌ Kullanıcı ID veya mağaza kodu hatalı.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'user_id': user_id
            })
        
        # Şifreyi kontrol et
        user = profile.user
        if user.check_password(password):
            login(request, user)
            messages.success(request, f'✅ Hoşgeldiniz, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Şifre yanlış.')
            return render(request, 'registration/login.html', {
                'store_code': store_code,
                'user_id': user_id
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
    
    return render(request, 'inventory/dashboard.html')


@login_required(login_url='login')
def product_browser(request):
    search_results = []
    searched = False
    no_results = False

    # Arama parametreleri
    spec_code = request.GET.get('spec_code', '').strip()
    barcode = request.GET.get('barcode', '').strip()
    prod_name = request.GET.get('prod_name', '').strip()
    colour = request.GET.get('colour', '').strip()

    # En az bir arama parametresi varsa arama yap
    if spec_code or barcode or prod_name or colour:
        searched = True
        query = Q()
        
        if spec_code:
            query |= Q(specCode__icontains=spec_code)
        if barcode:
            query |= Q(barcode__icontains=barcode)
        if prod_name:
            query |= Q(prodName__icontains=prod_name)
        if colour:
            query |= Q(colour__icontains=colour)
        
        search_results = Product.objects.filter(query)
        
        # Sonuç yoksa no_results flag'ı set et
        if not search_results:
            no_results = True

    context = {
        'search_results': search_results,
        'searched': searched,
        'no_results': no_results,
        'spec_code': spec_code,
        'barcode': barcode,
        'prod_name': prod_name,
        'colour': colour,
    }
    return render(request, 'inventory/product_browser.html', context)
