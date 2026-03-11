from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import UserProfile, Product
from .forms import UserRegistrationForm


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role='employee')
            return render(request, 'registration/register_success.html')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Boş alan kontrolü
        if not username or not password:
            messages.error(request, '❌ Kullanıcı adı ve şifre alanları boş bırakılamaz.')
            return render(request, 'registration/login.html', {'username': username})
        
        # Kullanıcı adı ile user var mı kontrol et
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, '❌ Kullanıcı bulunamadı.')
            return render(request, 'registration/login.html', {'username': username})
        
        # Şifreyi kontrol et
        if user.check_password(password):
            # Şifre doğru, login yap
            authenticated_user = authenticate(request, username=username, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                
                # UserProfile yoksa oluştur
                UserProfile.objects.get_or_create(
                    user=authenticated_user,
                    defaults={'role': 'employee'}
                )
                
                messages.success(request, f'✅ Hoşgeldiniz, {user.first_name}!')
                return redirect('dashboard')
        else:
            # Şifre yanlış
            messages.error(request, '❌ Şifre yanlış.')
            return render(request, 'registration/login.html', {'username': username})
    
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
