from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from paystackapi.paystack import Paystack
from django.conf import settings

# Create your models here.
STATE_CHOICES = (
    ('Abia', 'Abia'),
    ('Adamawa', 'Adamawa'),
    ('Akwa Ibom', 'Akwa Ibom'),
    ('Anambra', 'Anambra'),
    ('Bauchi', 'Bauchi'),
    ('Bayelsa', 'Bayelsa'),
    ('Benue', 'Benue'),
    ('Borno', 'Borno'),
    ('Cross River', 'Cross River'),
    ('Delta', 'Delta'),
    ('Ebonyi', 'Ebonyi'),
    ('Edo', 'Edo'),
    ('Ekiti', 'Ekiti'),
    ('Enugu', 'Enugu'),
    ('Gombe', 'Gombe'),
    ('Imo', 'Imo'),
    ('Jigawa', 'Jigawa'),
    ('Kaduna', 'Kaduna'),
    ('Kano', 'Kano'),
    ('Katsina', 'Katsina'),
    ('Kebbi', 'Kebbi'),
    ('Kogi', 'Kogi'),
    ('Kwara', 'Kwara'),
    ('Lagos', 'Lagos'),
    ('Nasarawa', 'Nasarawa'),
    ('Niger', 'Niger'),
    ('Ogun', 'Ogun'),
    ('Ondo', 'Ondo'),
    ('Osun', 'Osun'),
    ('Oyo', 'Oyo'),
    ('Plateau', 'Plateau'),
    ('Rivers', 'Rivers'),
    ('Sokoto', 'Sokoto'),
    ('Taraba', 'Taraba'),
    ('Yobe', 'Yobe'),
    ('Zamfara', 'Zamfara'),
)


CATEGORY_CHOICES = (
    ('PY', 'Primary'),
    ('SY', 'Secondary'),
    ('TY', 'Tertiary'),
    ('IL', 'Inspirational'),
    ('SL', 'Spiritual'),
    ('OT', 'Others'),
)

class Product(models.Model):
    title = models.CharField(max_length=100)
    selling_price = models.FloatField()
    discounted_price = models.FloatField()
    description = models.TextField()
    composition = models.TextField(default='')
    prodapp = models.TextField(default='')
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    product_image = models.ImageField(upload_to='product')
    def __str__(self):
        return self.title

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    mobile = models.IntegerField(default=0)
    zipcode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES, max_length=100)
    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart ({self.user.username})"

    @property
    def total_amount(self):
        total = sum(item.total_price for item in self.items.all())
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    @property
    def total_price(self):
        return self.product.discounted_price * self.quantity

    def increment_quantity(self, amount=1):
        """Increase the quantity of the product in the cart."""
        self.quantity += amount
        self.save()

    def decrement_quantity(self, amount=1):
        """Decrease the quantity of the product in the cart. If quantity becomes 0, delete the item."""
        if self.quantity > amount:
            self.quantity -= amount
            self.save()
       

STATUS_CHOICES = (
    ('Accepted', 'Accepted'),
    ('Packed', 'Packed'),
    ('On The Way', 'On The Way'),
    ('Delivered', 'Delivered'),
    ('Cancel', 'Cancel'),
    ('Pending', 'Pending'),
)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    paystack_payment_status = models.CharField(max_length=50, blank=True, null=True)
    paid = models.BooleanField(default=False)
    
    def verify_payment(self):
        paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)
        response = paystack.transaction.verify(reference=self.paystack_reference)
        return response['status'], response['message'], response['data']['status']


class OrderPlaced(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, default="")
    delivery_address = models.TextField(blank=True, null=True)  # Optional if multiple addresses exist
    delivery_date = models.DateTimeField(blank=True, null=True)  # Track delivery date
    total_order_cost = models.FloatField()  # To store the order cost at the time of purchase
    
    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price

    def __str__(self):
        return f"Order ({self.user.username}) - {self.product.title} ({self.status})"

