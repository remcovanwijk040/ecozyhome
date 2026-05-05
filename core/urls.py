from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('categorie/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Cart
    path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    
    # Checkout
    path('checkout/', views.checkout_session, name='checkout_session'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('checkout/cancel/', views.checkout_cancel, name='checkout_cancel'),
    
    # Webhooks
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Info pages
    path('info/retourvoorwaarden/', views.info_retour, name='info_retour'),
    path('info/privacy-statement/', views.info_privacy, name='info_privacy'),
    path('info/bestelinformatie/', views.info_bestel, name='info_bestel'),
]
