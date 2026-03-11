# Stok Kontrol Uygulaması - Copilot Talimatları

Bu workspace, zincir giyim mağazaları için Django tabanlı bir stok kontrol uygulamasıdır.

## Teknoloji Stack
- **Backend**: Django 4.x
- **Database**: PostgreSQL
- **Frontend**: HTML5 + CSS3 + JavaScript (Vanilla)
- **Python Version**: 3.10+

## Proje Özellikleri
- Kullanıcı Kayıt ve Giriş Sistemi
- Ürün Yönetimi (Ekleme, Güncelleme, Silme)
- Mağaza Bazında Stok Takibi
- Düşük Stok Uyarıları
- Mağaza Müdürü ve Çalışan Rolleri

## Kurulum ve Çalıştırma
1. Python gereksinimlerini yükleyin: `pip install -r requirements.txt`
2. PostgreSQL veritabanını yapılandırın
3. Migration'ları çalıştırın: `python manage.py migrate`
4. Geliştirme sunucusunu başlatın: `python manage.py runserver`

## Klasör Yapısı
- `/stock_control/` - Ana Django uygulaması
- `/templates/` - HTML şablonları
- `/static/` - CSS, JavaScript, görseller
- `/manage.py` - Django yönetim betiği
- `requirements.txt` - Python bağımlılıkları
