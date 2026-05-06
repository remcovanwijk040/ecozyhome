from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'core:index',
            'core:contact_page',
            'core:info_retour',
            'core:info_privacy',
            'core:info_bestel',
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.objects.filter(
            retail_price__isnull=False,
        ).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('core:product_detail', kwargs={'pk': obj.pk})


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def lastmod(self, obj):
        return None

    def location(self, obj):
        return reverse('core:category_detail', kwargs={'slug': obj.slug})
