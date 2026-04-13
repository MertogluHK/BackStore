from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Product Browser
    path('products/', views.product_browser, name='product_browser'),
    
    # Warehouse - Shelf
    path('warehouse-shelf/', views.warehouse_shelf, name='warehouse_shelf'),
]
