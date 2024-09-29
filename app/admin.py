from django.contrib import admin
from . models import Cart, CartItem, Customer, Product, Payment, OrderPlaced

# Register your models here.

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'discounted_price', 'category', 'product_image']

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'locality', 'city', 'state', 'zipcode']

@admin.register(Cart) 
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at'] 

@admin.register(CartItem)
class CartItemModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'total_price']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'paystack_reference', 'paystack_payment_status', 'paid']

@admin.register(OrderPlaced)
class OrderPlacedAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'status', 'ordered_date', 'total_cost', 'payment']
