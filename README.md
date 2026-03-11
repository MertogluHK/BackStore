# Stok Kontrol Uygulaması

Django tabanlı, zincir giyim mağazaları için web üzerinde çalışan mağaza stok yönetim sistemi.

## 🌟 Özellikler

- **Kullanıcı Yönetimi**: Kayıt, giriş/çıkış sistemi
- **Rol Bazlı Erişim**: Çalışan, Mağaza Müdürü, Admin
- **Ürün Yönetimi**: Ekleme, güncelleme, silme, arama
- **Stok Takibi**: Mağaza bazında gerçek zamanlı stok yönetimi
- **Düşük Stok Uyarıları**: Stok seviyeleri minimum seviyenin altına düştüğünde uyarı
- **Stok Hareketleri**: Giriş, çıkış, iade, düzeltme operasyonları
- **Raporlar**: Detaylı stok raporları ve analiz
- **Admin Paneli**: Django admin interface ile tam kontrol

## 📋 Sistem Gereksinimleri

- Python 3.10+
- PostgreSQL 12+
- pip (Python paket yöneticisi)
- Git (opsiyonel)

## 🚀 Kurulum

### 1. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. PostgreSQL Veritabanını Yapılandırın

PostgreSQL'de yeni bir veritabanı ve kullanıcı oluşturun:

```sql
CREATE DATABASE stock_control_db;
CREATE USER postgres WITH PASSWORD 'postgres';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET default_transaction_deferrable TO on;
ALTER ROLE postgres SET default_transaction_read_committed TO 'on';
GRANT ALL PRIVILEGES ON DATABASE stock_control_db TO postgres;
```

### 3. Migration'ları Çalıştırın

```bash
python manage.py migrate
```

### 4. Süper Kullanıcı (Admin) Oluşturun

```bash
python manage.py createsuperuser
```

İstendiğinde:
- Kullanıcı Adı: `admin`
- Email: `admin@example.com`
- Şifre: Güvenli bir şifre girin

### 5. Geliştirme Sunucusunu Başlatın

```bash
python manage.py runserver
```

Uygulama şu adreste kullanılabilir olacaktır: `http://127.0.0.1:8000`

## 🔑 Kullanıcı Rolleri ve İzinleri

### Admin
- Tüm mağazaları yönet
- Tüm ürünleri ve stokları görüntüle
- Kullanıcı yönetimi
- Admin paneline tam erişim

### Mağaza Müdürü
- Kendi mağazasının stok ve ürünlerini yönet
- Stok hareketleri kaydet
- Kendi mağazasının raporu
- Çalışanları yönet

### Çalışan
- Stok bilgilerini görüntüle
- Stok hareketleri kaydet (müdür onayıyla)
- Ürün arama

## 📁 Proje Yapısı

```
BackStore/
├── stock_control/          # Django proje ayarları
│   ├── settings.py         # Proje konfigürasyonu
│   ├── urls.py            # Ana URL yönlendiricisi
│   ├── wsgi.py            # WSGI ayarları
│   └── asgi.py            # ASGI ayarları
├── inventory/             # Ana Django uygulaması
│   ├── models.py          # Veritabanı modelleri
│   ├── views.py           # View fonksiyonları
│   ├── forms.py           # Django formları
│   ├── urls.py            # Uygulama URL'leri
│   ├── admin.py           # Admin konfigürasyonu
│   └── migrations/        # Veritabanı migrasyonları
├── templates/             # HTML şablonları
│   ├── base.html          # Ana şablon
│   ├── registration/      # Kullanıcı işlemleri
│   └── inventory/         # Uygulamaya özgü şablonlar
├── static/                # Statik dosyalar
│   ├── css/              # Stiller
│   ├── js/               # JavaScript dosyaları
│   └── images/           # Görseller
├── manage.py              # Django yönetim betiği
└── requirements.txt       # Python bağımlılıkları
```

## 🗄️ Veritabanı Modelleri

### Store (Mağaza)
- Ad, adres, şehir, telefon
- Durum (aktif/pasif)

### Product (Ürün)
- Ad, SKU, Barkod
- Kategori, cinsiyet, beden, renk
- Maliyet ve satış fiyatları
- Yeniden sipariş seviyesi

### Stock (Stok)
- Ürün ve mağaza referansları
- Mevcut miktar
- Son kontrol tarihi

### StockMovement (Stok Hareketi)
- Hareket türü (giriş, çıkış, iade, ayarlama)
- Miktar ve referans
- Notlar ve oluşturan kullanıcı

### UserProfile (Kullanıcı Profili)
- Kullanıcı bilgileri
- Rol (çalışan, müdür, admin)
- Atandığı mağaza

## 🎯 Ana Özellikler

### Dashboard
- Mağaza müdürü/çalışan için: Mağaza verileri ve düşük stok uyarıları
- Admin için: Sistem geneli istatistikleri ve mağaza listesi

### Ürün Yönetimi
- Ürün listesi ve detay sayfaları
- Ürün ekle/düzenle/sil işlemleri
- Kategori ve özelliklere göre filtreleme
- Barkod ve SKU arama

### Stok Yönetimi
- Mağaza bazında stok envanteri
- Stok hareketi kayıt (giriş, çıkış, iade, ayarlama)
- Otomatik stok güncelleme
- Düşük stok uyarıları

### Raporlar
- Mağaza stok raporu
- Düşük stok ürünleri listesi
- Stok hareket geçmişi
- CSV dışa aktarma ve yazdırma

## 🔧 Yönetici Paneli

Django admin paneline erişmek için:

1. `http://127.0.0.1:8000/admin/` adresine gidin
2. Admin kullanıcı adı ve şifre ile giriş yapın
3. Tüm modelleri yönetebileceğiniz interface

## 📝 Kullanım Örnekleri

### Ürün Ekleme
1. Navigation'dan "Ürünler" → "Yeni Ürün Ekle" seçin
2. Ürün bilgilerini doldurun
3. Kaydet butonuna tıklayın

### Stok Hareketi Kayıt Etme
1. "Stok" → "Hareket" seçin
2. Ürün, mağaza, hareket türü ve miktarı seçin
3. Referans kodu ve notlar ekleyin (opsiyonel)
4. Kaydet butonuna tıklayın

### Rapor Görüntüleme
1. "Stok Raporu" seçin
2. Mağaza verilerini ve stok listesini görüntüleyin
3. Tabloyu yazdırın veya CSV olarak dışa aktarın

## 🛡️ Güvenlik Özellikleri

- CSRF koruması
- Kullanıcı kimlik doğrulaması
- İzin kontrolleri
- SQL injection koruması (Django ORM)
- Şifre hashleme

## 🌐 Dikkat Edilmesi Gerekenler

- **Üretim ortamında**:
  - `DEBUG = False` yapın
  - `SECRET_KEY` değiştirin
  - HTTPS kullanın
  - Veritabanı şifresi değiştirin
  - Host ayarlarını yapılandırın

## 📞 Sorun Giderme

### Veritabanı bağlantısı hataları
```bash
# PostgreSQL hizmetinin çalışıp çalışmadığını kontrol edin
# settings.py'da veritabanı ayarlarını kontrol edin
```

### Migration hataları
```bash
# Migration dosyalarını sıfırla
python manage.py showmigrations
python manage.py migrate inventory zero
python manage.py migrate
```

### Port meşgul hatası
```bash
# Farklı port kullan
python manage.py runserver 8001
```

## 📚 Bağımlılıklar

- Django 4.2.0
- psycopg2-binary 2.9.6 (PostgreSQL adaptörü)
- python-decouple 3.8 (Ortam değişkenleri)
- django-cors-headers 4.0.0 (CORS desteği)

## 👨‍💻 Geliştirme

### Yeni feature ekleme
1. Model oluşturun (`models.py`)
2. Migration oluşturun
3. View/form oluşturun
4. Template oluşturun
5. URL konfigürasyonu ekleyin

### Test çalıştırma
```bash
python manage.py test inventory
```

## 📄 Lisans

Bu proje özel proje olup ticari amaç doğrultusunda kullanılmaktadır.

## 📧 İletişim

Sorgulamalarınız için lütfen proje yöneticisi ile iletişime geçin.

---

**Son Güncelleme**: Mart 2024
**Versiyon**: 1.0.0
