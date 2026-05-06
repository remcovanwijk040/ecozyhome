from core.models import Product
from decimal import Decimal

def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_items = 0

    if cart:
        product_ids = []
        for cart_key, cart_value in cart.items():
            if isinstance(cart_value, dict):
                product_ids.append(cart_value.get('product_id'))
            else:
                product_ids.append(int(cart_key))

        products = Product.objects.in_bulk(product_ids)
        for cart_key, cart_value in cart.items():
            if isinstance(cart_value, dict):
                product = products.get(cart_value.get('product_id'))
                if not product:
                    continue
                quantity = cart_value.get('quantity', 1)
                price = Decimal(str(cart_value.get('price') or product.retail_price or 0))
                image_url = cart_value.get('image_url') or product.image_url
                variant_name = cart_value.get('variant_name')
                variant_value = cart_value.get('variant_value')
            else:
                product = products.get(int(cart_key))
                if not product:
                    continue
                quantity = cart_value
                price = product.retail_price or Decimal('0')
                image_url = product.image_url
                variant_name = None
                variant_value = None

            total_items += quantity
            subtotal = price * quantity
            total_price += subtotal
            cart_items.append({
                'cart_key': cart_key,
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
                'image_url': image_url,
                'variant_name': variant_name,
                'variant_value': variant_value,
            })

    return {
        'cart_items': cart_items,
        'cart_total_items': total_items,
        'cart_total_price': total_price,
    }

def category_processor(request):
    from core.models import Category
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    return {
        'global_categories': categories
    }
