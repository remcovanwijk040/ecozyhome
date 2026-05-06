from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from .variant_utils import product_variant_context, selected_variant


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

    specifications = product.specifications or {}
    visible_specs = {
        key: value for key, value in specifications.items()
        if not str(key).startswith('_')
    }

    from datetime import date, timedelta
    price_valid_until = date.today() + timedelta(days=90)

    return render(request, 'core/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'visible_specs': visible_specs,
        'product_info_sections': specifications.get('_sections', []),
        'product_documents': specifications.get('_documents', []),
        'product_videos': specifications.get('_videos', []),
        'price_valid_until': price_valid_until,
        **product_variant_context(product),
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

    # Extract available brands before applying filters
    brands = products.exclude(brand='').exclude(brand__isnull=True).values_list('brand', flat=True).distinct().order_by('brand')

    # Filtering
    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand=brand)

    subcategory_filter = request.GET.get('sub')
    if subcategory_filter:
        products = products.filter(category__slug=subcategory_filter)

    min_price = request.GET.get('min_price')
    if min_price and min_price.strip():
        try:
            products = products.filter(retail_price__gte=float(min_price))
        except ValueError:
            pass

    max_price = request.GET.get('max_price')
    if max_price and max_price.strip():
        try:
            products = products.filter(retail_price__lte=float(max_price))
        except ValueError:
            pass

    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        products = products.exclude(stock_status__icontains='niet op voorraad').exclude(stock_status__icontains='uitverkocht')

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products = products.order_by('retail_price')
    elif sort == 'price_desc':
        products = products.order_by('-retail_price')
    elif sort == 'name':
        products = products.order_by('title')


    return render(request, 'core/category_detail.html', {
        'category': category,
        'products': products,
        'subcategories': subcategories,
        'brands': brands,
        'current_brand': brand,
        'current_sub': subcategory_filter,
        'current_sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
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
from decimal import Decimal

@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})
    
    quantity = int(request.POST.get('quantity', 1))

    variant = selected_variant(product, request.POST)
    cart_key = str(pk)
    if variant:
        cart_key = f"{pk}:{variant['name']}:{variant['value']}"

    if cart_key in cart:
        if isinstance(cart[cart_key], dict):
            cart[cart_key]['quantity'] += quantity
        else:
            cart[cart_key] += quantity
    else:
        if variant:
            cart[cart_key] = {
                'product_id': pk,
                'quantity': quantity,
                'variant_name': variant['name'],
                'variant_value': variant['value'],
                'price': variant['amount'] or str(product.retail_price or Decimal('0')),
                'image_url': variant['image'] or product.image_url or '',
            }
        else:
            cart[cart_key] = quantity
        
    request.session['cart'] = cart
    
    # Return the updated cart slideover content to replace #cart-content
    return render(request, 'core/partials/cart_slideover_content.html')

@require_POST
def cart_update(request, pk):
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    cart_key = request.POST.get('cart_key', str(pk))
    
    if quantity > 0:
        if isinstance(cart.get(cart_key), dict):
            cart[cart_key]['quantity'] = quantity
        else:
            cart[cart_key] = quantity
    else:
        cart.pop(cart_key, None)
        
    request.session['cart'] = cart
    # Render updated cart items partial
    return render(request, 'core/partials/cart_slideover_content.html')

@require_POST
def cart_remove(request, pk):
    cart = request.session.get('cart', {})
    cart_key = request.POST.get('cart_key', str(pk))
    cart.pop(cart_key, None)
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
        product_name = product.title
        if item.get('variant_value'):
            product_name = f"{product.title} - {item['variant_value']}"
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(item['price'] * 100), # Stripe requires cents
                'product_data': {
                    'name': product_name,
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

def contact_page(request):
    return render(request, 'core/pages/contact.html')

from django.core.mail import send_mail

@require_POST
def contact_submit(request):
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    message = request.POST.get('message', '').strip()
    
    if name and email and message:
        subject = f"Nieuw contactbericht via Ecozyhome van {name}"
        body = f"Naam: {name}\nE-mail: {email}\n\nBericht:\n{message}"
        to_email = settings.EMAIL_HOST_USER or 'info@ecozyhome.nl'
        
        try:
            send_mail(
                subject,
                body,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@ecozyhome.nl'),
                [to_email],
                fail_silently=False,
            )
            return HttpResponse('<div class="rounded-xl bg-green-50 border border-green-100 p-6 text-center"><div class="text-4xl mb-4">✅</div><h3 class="text-lg font-bold text-green-800 mb-2">Bedankt voor je bericht!</h3><p class="text-green-700">We hebben je e-mail ontvangen en nemen zo snel mogelijk contact met je op.</p></div>')
        except Exception as e:
            return HttpResponse('<div class="rounded-xl bg-red-50 border border-red-100 p-6 text-center"><div class="text-4xl mb-4">⚠️</div><h3 class="text-lg font-bold text-red-800 mb-2">Oeps, er ging iets mis</h3><p class="text-red-700">Je bericht kon niet verstuurd worden. Controleer de e-mail instellingen of probeer het later opnieuw.</p></div>')
            
    return HttpResponse('<div class="rounded-xl bg-red-50 p-4 text-red-700 font-medium text-center">Vul a.u.b. alle velden in.</div>')


@require_POST
def newsletter_subscribe(request):
    from .models import NewsletterSubscriber
    email = request.POST.get('email', '').strip()

    if not email:
        return HttpResponse(
            '<div class="flex items-center gap-3 text-red-600 text-sm font-medium">'
            '<svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" /></svg>'
            'Vul je e-mailadres in.</div>'
        )

    _, created = NewsletterSubscriber.objects.get_or_create(email=email)

    if created:
        return HttpResponse(
            '<div class="flex items-center gap-3 text-green-600 text-sm font-semibold">'
            '<svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>'
            'Welkom! Je bent aangemeld voor onze nieuwsbrief. 🎉</div>'
        )
    else:
        return HttpResponse(
            '<div class="flex items-center gap-3 text-eco-600 text-sm font-medium">'
            '<svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>'
            'Je bent al aangemeld — we houden je op de hoogte!</div>'
        )
