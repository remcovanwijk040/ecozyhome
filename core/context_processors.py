from core.models import Product

def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_items = 0

    if cart:
        products = Product.objects.filter(id__in=cart.keys())
        for product in products:
            quantity = cart[str(product.id)]
            total_items += quantity
            price = product.retail_price or 0
            subtotal = price * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

    return {
        'cart_items': cart_items,
        'cart_total_items': total_items,
        'cart_total_price': total_price,
    }
