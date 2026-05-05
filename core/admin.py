from django.contrib import admin
from .models import Category, Product, ProductImage, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'retail_price', 'stock_status', 'category')
    list_filter = ('brand', 'category', 'stock_status')
    search_fields = ('title', 'brand', 'ean')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'full_name', 'stripe_checkout_id')
    readonly_fields = ('stripe_checkout_id', 'total_amount')
    inlines = [OrderItemInline]
