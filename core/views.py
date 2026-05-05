from django.shortcuts import render, get_object_or_404
from .models import Product, Category


from django.db.models import F

def index(request):
    # Only show parent categories (those without a parent)
    parent_categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__products')
    
    # Feature products with the highest profit margin
    featured_products = Product.objects.filter(
        retail_price__isnull=False,
        purchase_price__isnull=False,
        image_url__isnull=False,
    ).exclude(image_url='').annotate(
        margin=F('retail_price') - F('purchase_price')
    ).order_by('-margin')[:8]
    
    total_products = Product.objects.count()
    total_brands = Product.objects.exclude(brand='').exclude(brand__isnull=True).values('brand').distinct().count()

    return render(request, 'core/index.html', {
        'parent_categories': parent_categories,
        'featured_products': featured_products,
        'total_products': total_products,
        'total_brands': total_brands,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('images'),
        pk=pk,
    )
    related_products = Product.objects.filter(
        category=product.category,
    ).exclude(pk=product.pk).order_by('?')[:4]

    return render(request, 'core/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)

    # If it's a parent category, show products from ALL children
    if category.is_parent:
        child_ids = category.children.values_list('id', flat=True)
        products = Product.objects.filter(category_id__in=child_ids).order_by('-created_at')
        subcategories = category.children.all()
    else:
        products = Product.objects.filter(category=category).order_by('-created_at')
        subcategories = None

    # Filtering
    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand=brand)

    subcategory_filter = request.GET.get('sub')
    if subcategory_filter:
        products = products.filter(category__slug=subcategory_filter)

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products = products.order_by('retail_price')
    elif sort == 'price_desc':
        products = products.order_by('-retail_price')
    elif sort == 'name':
        products = products.order_by('title')

    brands = products.exclude(brand='').exclude(brand__isnull=True).values_list('brand', flat=True).distinct().order_by('brand')

    return render(request, 'core/category_detail.html', {
        'category': category,
        'products': products,
        'subcategories': subcategories,
        'brands': brands,
        'current_brand': brand,
        'current_sub': subcategory_filter,
        'current_sort': sort,
    })

# ==========================================
# CART VIEWS (HTMX)
# ==========================================
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
import stripe
import json

@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})
    
    quantity = int(request.POST.get('quantity', 1))
    
    if str(pk) in cart:
        cart[str(pk)] += quantity
    else:
        cart[str(pk)] = quantity
        
    request.session['cart'] = cart
    
    # Return the updated cart slideover content to replace #cart-content
    return render(request, 'core/partials/cart_slideover_content.html')

@require_POST
def cart_update(request, pk):
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart[str(pk)] = quantity
    else:
        cart.pop(str(pk), None)
        
    request.session['cart'] = cart
    # Render updated cart items partial
    return render(request, 'core/partials/cart_slideover_content.html')

@require_POST
def cart_remove(request, pk):
    cart = request.session.get('cart', {})
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return render(request, 'core/partials/cart_slideover_content.html')

# ==========================================
# STRIPE CHECKOUT VIEWS
# ==========================================

stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout_session(request):
    from .context_processors import cart_processor
    cart_data = cart_processor(request)
    
    if cart_data['cart_total_price'] < 40:
        # Minimum order limit not met
        # You would typically redirect back to cart with an error message using django messages
        from django.contrib import messages
        messages.error(request, "Minimale bestelwaarde is €40. Voeg meer producten toe.")
        return HttpResponse("Minimale bestelwaarde is €40.", status=400)
    
    line_items = []
    for item in cart_data['cart_items']:
        product = item['product']
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(product.retail_price * 100), # Stripe requires cents
                'product_data': {
                    'name': product.title,
                },
            },
            'quantity': item['quantity'],
        })
        
    domain_url = request.build_absolute_uri('/')[:-1]
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['ideal', 'card'],
            line_items=line_items,
            mode='payment',
            success_url=domain_url + reverse('core:checkout_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + reverse('core:checkout_cancel'),
            billing_address_collection='required',
        )
        return HttpResponse(f'<script>window.location.href = "{checkout_session.url}";</script>')
    except Exception as e:
        return JsonResponse({'error': str(e)})

def checkout_success(request):
    request.session['cart'] = {} # Empty cart
    return render(request, 'core/checkout_success.html')

def checkout_cancel(request):
    return render(request, 'core/checkout_cancel.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # You can fulfill the order here by creating Order and OrderItem instances.
        
        from .models import Order
        Order.objects.create(
            email=session.get('customer_details', {}).get('email', 'unknown@email.com'),
            full_name=session.get('customer_details', {}).get('name', 'Unknown'),
            total_amount=session.get('amount_total', 0) / 100.0,
            stripe_checkout_id=session.get('id'),
            status='Paid'
        )

    return HttpResponse(status=200)

def info_retour(request):
    return render(request, 'core/pages/retour.html')

def info_privacy(request):
    return render(request, 'core/pages/privacy.html')

def info_bestel(request):
    return render(request, 'core/pages/bestel.html')
