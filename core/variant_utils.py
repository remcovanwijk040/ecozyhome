from decimal import Decimal
import re


SPEEDCOMFORT_PRICES = {
    "Mono": Decimal("69.25"),
    "Duo": Decimal("120.70"),
    "Trio": Decimal("173.19"),
    "Uitbreiding": Decimal("49.95"),
}


def format_price(price):
    if price is None:
        return None
    return f"{Decimal(price):.2f}".replace(".", ",")


def normalize_variant(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def variant_image(option_value, images):
    option_key = normalize_variant(option_value)
    for image_url in images:
        image_key = normalize_variant(image_url)
        if option_key and option_key in image_key:
            return image_url
    return images[0] if images else ""


def product_variant_context(product):
    images = [img.image_url for img in product.images.all()]
    if product.image_url and product.image_url not in images:
        images.insert(0, product.image_url)

    from django.urls import reverse
    from core.models import Product

    speedcomfort_prices = {}
    if product.options and product.options.get("Uitvoering") == ["Mono", "Duo", "Trio", "Uitbreiding"]:
        speedcomfort_prices = SPEEDCOMFORT_PRICES

    # Build a map of variant key -> product URL for related products
    variant_url_map = {}
    variant_price_map = {}
    if product.category_id and product.options:
        related_products = Product.objects.filter(category_id=product.category_id)
        for rp in related_products:
            if rp.specifications:
                for opt_name, opt_values in product.options.items():
                    rp_val = rp.specifications.get(opt_name)
                    if rp_val and rp_val in opt_values:
                        key = f"{opt_name}:{rp_val}"
                        # Prefer exact match if possible
                        if key not in variant_url_map or rp.pk == product.pk:
                            variant_url_map[key] = reverse('core:product_detail', args=[rp.pk])
                            if rp.retail_price is not None:
                                variant_price_map[key] = rp.retail_price

    fallback_amount = product.retail_price
    fallback_price = format_price(fallback_amount)
    variant_data = {}
    variant_groups = []

    for option_name, option_values in (product.options or {}).items():
        group = {"name": option_name, "values": []}
        for value in option_values:
            key = f"{option_name}:{value}"
            
            amount = speedcomfort_prices.get(value)
            if amount is None:
                amount = variant_price_map.get(key, fallback_amount)
                
            price = format_price(amount)
            image_url = variant_image(value, images)
            product_url = variant_url_map.get(key, "")

            variant = {
                "name": option_name,
                "value": value,
                "key": key,
                "price": price,
                "amount": str(amount) if amount is not None else "",
                "image": image_url,
                "product_url": product_url,
            }
            variant_data[variant["key"]] = {
                "name": option_name,
                "value": value,
                "price": price,
                "amount": variant["amount"],
                "priceLabel": f"\u20ac{price}" if price else "Prijs op aanvraag",
                "image": image_url,
                "alt": f"{product.title} - {value}",
                "product_url": product_url,
            }
            group["values"].append(variant)
        variant_groups.append(group)

    current_variant_value = (product.specifications or {}).get("Uitvoering", "")
    current_variant_key = normalize_variant(str(current_variant_value or product.title))
    initial_variant = None
    for group in variant_groups:
        for variant in group["values"]:
            if normalize_variant(variant["value"]) in current_variant_key:
                initial_variant = variant
                break
        if initial_variant:
            break
    if not initial_variant:
        initial_variant = variant_groups[0]["values"][0] if variant_groups else None

    return {
        "variant_groups": variant_groups,
        "variant_data": variant_data,
        "initial_variant": initial_variant,
    }


def selected_variant(product, post_data):
    context = product_variant_context(product)
    for variant in context["variant_data"].values():
        if post_data.get(f"opt-{variant['name']}") == variant["value"]:
            return variant
    if context["initial_variant"]:
        return context["variant_data"].get(context["initial_variant"]["key"])
    return None
