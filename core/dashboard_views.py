from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
import json

from core.models import Order, OrderItem, Product, Category, NewsletterSubscriber


@staff_member_required
def dashboard_overview(request):
    """Main dashboard overview with KPIs and charts."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # KPIs
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='Paid').aggregate(total=Sum('total_amount'))['total'] or 0
    orders_this_month = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    revenue_this_month = Order.objects.filter(status='Paid', created_at__gte=thirty_days_ago).aggregate(total=Sum('total_amount'))['total'] or 0
    total_products = Product.objects.count()
    total_subscribers = NewsletterSubscriber.objects.count()
    new_subscribers_week = NewsletterSubscriber.objects.filter(created_at__gte=seven_days_ago).count()
    avg_order_value = Order.objects.filter(status='Paid').aggregate(avg=Avg('total_amount'))['avg'] or 0

    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]

    # Orders per day (last 30 days) for chart
    orders_per_day = (
        Order.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'), revenue=Sum('total_amount'))
        .order_by('day')
    )
    chart_labels = [entry['day'].strftime('%d %b') for entry in orders_per_day]
    chart_orders = [entry['count'] for entry in orders_per_day]
    chart_revenue = [float(entry['revenue'] or 0) for entry in orders_per_day]

    # Orders by status
    status_counts = dict(Order.objects.values_list('status').annotate(count=Count('id')).values_list('status', 'count'))

    # Top products by order count
    top_products = (
        OrderItem.objects
        .values('product__title', 'product__pk')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('price'))
        .order_by('-total_qty')[:5]
    )

    # Recent subscribers
    recent_subscribers = NewsletterSubscriber.objects.order_by('-created_at')[:5]

    context = {
        'active_page': 'overview',
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders_this_month': orders_this_month,
        'revenue_this_month': revenue_this_month,
        'total_products': total_products,
        'total_subscribers': total_subscribers,
        'new_subscribers_week': new_subscribers_week,
        'avg_order_value': avg_order_value,
        'recent_orders': recent_orders,
        'chart_labels': json.dumps(chart_labels),
        'chart_orders': json.dumps(chart_orders),
        'chart_revenue': json.dumps(chart_revenue),
        'status_counts': status_counts,
        'top_products': top_products,
        'recent_subscribers': recent_subscribers,
    }
    return render(request, 'core/dashboard/overview.html', context)


@staff_member_required
def dashboard_orders(request):
    """All orders list with filtering."""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')

    orders = Order.objects.order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(email__icontains=search) | orders.filter(full_name__icontains=search)

    context = {
        'active_page': 'orders',
        'orders': orders[:100],
        'status_filter': status_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'core/dashboard/orders.html', context)


@staff_member_required
def dashboard_order_detail(request, pk):
    """Single order detail with status update."""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return redirect('core:dashboard_order_detail', pk=pk)

    context = {
        'active_page': 'orders',
        'order': order,
        'items': order.items.select_related('product'),
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'core/dashboard/order_detail.html', context)


@staff_member_required
def dashboard_subscribers(request):
    """Newsletter subscribers list."""
    subscribers = NewsletterSubscriber.objects.order_by('-created_at')
    context = {
        'active_page': 'subscribers',
        'subscribers': subscribers,
        'total': subscribers.count(),
    }
    return render(request, 'core/dashboard/subscribers.html', context)
