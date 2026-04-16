from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .models import UserProfile, Store, Product


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta Adresi'})
    )
    first_name = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad'})
    )
    last_name = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyad'})
    )
    store = forms.ModelChoiceField(
        queryset=Store.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Çalıştığı Mağaza',
        empty_label='Mağaza Seçiniz'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kullanıcı Adı'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre Onayla'})
        
        # Help text'leri kaldır
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['username'].help_text = ''

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 3:
                raise forms.ValidationError('Şifre en az 3 karakter olmalıdır.')
            if len(password1) > 8:
                raise forms.ValidationError('Şifre maksimum 8 karakter olmalıdır.')
        elif password1 is None or password1 == '':
            raise forms.ValidationError('Şifre gereklidir.')
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Şifreler eşleşmiyor.')
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Email format validasyonu
        if email:
            email_validator = EmailValidator()
            try:
                email_validator(email)
            except ValidationError:
                raise forms.ValidationError('Geçersiz email adresi. Lütfen geçerli bir email giriniz.')
        
        # Mükerrer email kontrolü
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu email adresi zaten kullanılmaktadır.')
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError('Ad alanı boş bırakılamaz.')
        if len(first_name) < 2:
            raise forms.ValidationError('Ad en az 2 karakter olmalıdır.')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError('Soyad alanı boş bırakılamaz.')
        if len(last_name) < 2:
            raise forms.ValidationError('Soyad en az 2 karakter olmalıdır.')
        return last_name


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kullanıcı Adı'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre'})
    )


class ProductForm(forms.ModelForm):
    """Ürün oluşturma ve düzenleme formu"""
    
    class Meta:
        model = Product
        fields = ['specCode', 'barcode', 'prodName', 'sizeAge', 'colour', 'gender', 'price', 'discount']
        labels = {
            'specCode': 'Özel Kod',
            'barcode': 'Barkod',
            'prodName': 'Ürün Adı',
            'sizeAge': 'Beden/Yaş',
            'colour': 'Renk',
            'gender': 'Cinsiyet',
            'price': 'Fiyat',
            'discount': 'İndirim (%)',
        }
        widgets = {
            'specCode': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False
            }),
            'prodName': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False
            }),
            'sizeAge': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False
            }),
            'colour': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False
            }),
            'gender': forms.TextInput(attrs={
                'class': 'form-control',
                'required': False
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': False,
                'min': 0
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': False,
                'min': 0,
                'max': 100,
                'value': 0
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Fiyat negatif olamaz.')
        return price

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None:
            if discount < 0 or discount > 100:
                raise forms.ValidationError('İndirim 0 ile 100 arasında olmalıdır.')
        return discount
