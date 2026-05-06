from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, null=True, blank=True)
    icon = models.CharField(max_length=10, blank=True, default='🌿')

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_parent(self):
        return self.parent is None

    def product_count(self):
        """Count products in this category and all children."""
        count = self.products.count()
        for child in self.children.all():
            count += child.products.count()
        return count

class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    ean = models.CharField(max_length=50, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Inkoopprijs excl. BTW")
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Adviesprijs incl. BTW")
    stock_status = models.CharField(max_length=255, blank=True, null=True, help_text="Beschikbaarheid/Levertijd")
    specifications = models.JSONField(blank=True, null=True, help_text="Productdetails en eigenschappen")
    options = models.JSONField(blank=True, null=True, help_text="Beschikbare opties (bijv. kleur)")
    original_url = models.URLField(max_length=1000, unique=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Cancelled', 'Cancelled'),
    )
    email = models.EmailField(max_length=255)
    full_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="NL")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_checkout_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title if self.product else 'Deleted Product'}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nieuwsbrief Abonnee'
        verbose_name_plural = 'Nieuwsbrief Abonnees'

    def __str__(self):
        return self.email
