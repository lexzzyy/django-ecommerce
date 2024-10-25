from django.contrib import admin
from django.urls import reverse
from . models import Cart, CartItem, Customer, Product, Payment, OrderPlaced
from django.utils.html import format_html

# Register your models here.

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'discounted_price', 'category', 'product_image']

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'locality', 'city', 'state', 'mobile']

@admin.register(Cart) 
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at'] 

@admin.register(CartItem)
class CartItemModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'products', 'quantity', 'total_price']
    def products(self, obj):
        link = reverse('admin:app_product_change', args=[obj.product.pk]) 
        return format_html('<a href="{}">{}</a>', link, obj.product.title)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'paystack_reference', 'paystack_payment_status', 'paid']

@admin.register(OrderPlaced)
class OrderPlacedAdmin(admin.ModelAdmin):
    list_display = ['user', 'customers', 'products', 'quantity', 'status', 'ordered_date', 'total_cost', 'payments']

    def customers(self, obj):
        link = reverse('admin:app_customer_change', args=[obj.customer.pk]) 
        return format_html('<a href="{}">{}</a>', link, obj.customer.name)

    def products(self, obj):
        link = reverse('admin:app_product_change', args=[obj.product.pk]) 
        return format_html('<a href="{}">{}</a>', link, obj.product.title)
    
    def payments(self, obj):
        link = reverse('admin:app_payment_change', args=[obj.payment.pk]) 
        return format_html('<a href="{}">{}</a>', link, obj.payment.paystack_reference)
