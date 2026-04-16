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
    
    # Admin Panel
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/create/', views.admin_create_user, name='admin_create_user'),
    path('admin-panel/users/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/stocks-management/', views.admin_stocks_management, name='admin_stocks_management'),
]
