import json
import logging
logger = logging.getLogger(__name__)

import uuid
from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
import requests
from . models import Cart, CartItem, Customer, Product, Payment, OrderPlaced
from . forms import CustomerProfileForm, CustomerRegistrationForm
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

# Create your views here.
def home(request):
  return render(request, 'app/home.html')

def contact(request):
  return render(request, 'app/contact.html')

def about(request):
  return render(request, 'app/about.html')

class CategoryView(View):
  def get(self, request, val):
    product = Product.objects.filter(category=val)
    title = Product.objects.filter(category=val).values('title')
    return render(request, "app/category.html", locals())
  
class CategoryTitle(View):
  def get(self, request, val):
    product = Product.objects.filter(title=val)
    title = Product.objects.filter(category=product[0].category).values('title')
    return render(request, "app/category.html", locals())

class ProductDetail(View):
  def get(self, request, pk):
    product = Product.objects.get(pk=pk)
    return render(request, "app/productdetail.html", locals())
  
class CustomerRegistrationView(View):
  def get(self, request):
    form = CustomerRegistrationForm()
    return render(request, "app/customerregistration.html", locals())
  def post(self, request):
    form = CustomerRegistrationForm(request.POST)
    if form.is_valid():
      form.save() 
      messages.success(request, "Congratulations! User Registeration Successful")
    else:
      messages.warning(request, "Invalid Input Data")
    return render(request, "app/customerregistration.html", locals())
  
class ProfileView(View):
  def get(self,request):
    form = CustomerProfileForm()
    return render(request, 'app/profile.html', locals())
  def post(self,request):
    form = CustomerProfileForm(request.POST)
    if form.is_valid():
      user = request.user
      name = form.cleaned_data['name']
      locality = form.cleaned_data['locality']
      city = form.cleaned_data['city']
      mobile = form.cleaned_data['mobile']
      state = form.cleaned_data['state']
      zipcode = form.cleaned_data['zipcode']
      reg = Customer(user=user, name=name, locality=locality, mobile=mobile, city=city, state=state, zipcode=zipcode)
      reg.save()
      messages.success(request, "Congratulations! Profile Save Successfully")
    else:
      messages.warning(request, "Invalid Input Data")
    return render(request, 'app/profile.html', locals()) 

def address(request):
  add = Customer.objects.filter(user=request.user)
  return render(request, 'app/address.html', locals())

class updateAddress(View):
  def get(self,request,pk):
    add = Customer.objects.get(pk=pk)
    form = CustomerProfileForm(instance=add)
    return render(request, 'app/updateAddress.html', locals())   
  def post(self,request,pk):
    form = CustomerProfileForm(request.POST)
    if form.is_valid():
      add = Customer.objects.get(pk=pk)
      add.name = form.cleaned_data['name']
      add.locality = form.cleaned_data['locality']
      add.city = form.cleaned_data['city']
      add.mobile = form.cleaned_data['mobile']
      add.state = form.cleaned_data['state']
      add.zipcode = form.cleaned_data['zipcode']
      add.save()
      messages.success(request, "Congratulations! Profile Update Successfully")
    else:
      messages.warning(request, "Invalid Input Data")
    return redirect('address')

def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = get_object_or_404(Product, id=product_id)
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=user)
    # Try to get the CartItem for the product; if it doesn't exist, create it
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        # If the CartItem already exists, increment the quantity
        cart_item.increment_quantity()
    return redirect('/cart')

def show_cart(request):
    user = request.user
    cart = Cart.objects.get(user=user)
    cart_items = cart.items.all()
    amount = 0
    # Calculate the total amount for the cart
    for item in cart_items:
        value = item.quantity * item.product.discounted_price
        amount += value
    totalamount = amount + 1000
    return render(request, 'app/addtocart.html', {'cart': cart, 'cart_items': cart_items, 'amount': amount, 'totalamount': totalamount})

class checkout(View):
    def get(self, request):
        user = request.user
        add = Customer.objects.filter(user=user)
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.all()
        famount = 0
        for item in cart_items:
            famount += item.total_price
        totalamount = famount + 1000
        reference = str(uuid.uuid4())  # Generate a unique reference
        request.session['paystack_reference'] = reference  # Store reference in session
        return render(request, 'app/checkout.html', locals())
    
    def post(self, request):
        user = request.user  
        email = user.email  
        amount = request.POST.get('totalamount')
        reference = request.session.get('paystack_reference')  # Retrieve reference from session
        if not reference:
            return render(request, 'app/checkout.html', {'error': 'Unable to initialize payment. Please try again.'})
        # Prepare the request to initialize Paystack payment
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'email': email,  
            'amount': int(float(amount)) * 100,  # Paystack uses amount in kobo
            'reference': reference,  # Include the reference
            'callback_url': 'http://localhost:8000/payment/callback',  # URL to redirect to after payment
        }
        # Make the request to Paystack API
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for bad responses
            response_data = response.json()
            if response_data['status']:
                authorization_url = response_data['data']['authorization_url']
                return redirect(authorization_url)
            else:
                return render(request, 'app/checkout.html', {'error': response_data['message']})
        
        except requests.RequestException as e:
            return render(request, 'app/checkout.html', {'error': 'Payment initialization failed: ' + str(e)})

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':  
        return render(request, 'order_success.html')    
        data = json.loads(request.body)
        reference = data.get('reference')
        print(f"Received reference: {reference}")

        if not reference:
            return JsonResponse({'error': 'No reference provided'}, status=400)

        try:
            # Verify payment with Paystack API
            url = f'https://api.paystack.co/transaction/verify/{reference}'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
            }
            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response_data['status'] and response_data['data']['status'] == 'success':
                user = request.user
                amount = response_data['data']['amount'] / 100  # Convert from kobo to naira

                with transaction.atomic():
                    # Get the user's cart
                    cart = Cart.objects.get(user=user)
                    cart_items = cart.items.all()

                    # Calculate total order cost
                    total_order_cost = sum(item.product.selling_price * item.quantity for item in cart_items)

                    # Optionally, add shipping or additional costs
                    additional_fee = 1000  # Assuming an additional fixed fee
                    total_order_cost += additional_fee

                    # Create payment record
                    payment = Payment.objects.create(
                        user=user,
                        amount=amount,
                        paystack_reference=reference,
                        paystack_payment_status='success',
                        paid=True
                    )

                    # Safely handle the case of multiple Customers
                    customers = Customer.objects.filter(user=user)
                    if customers.exists():
                        customer = customers.first()
                    else:
                        return render(request, 'app/payment_error.html', {'error': 'No customer found for this user.'})

                    # Create orders for each cart item
                    for item in cart_items:
                        OrderPlaced.objects.create(
                            user=user,
                            customer=customer,
                            product=item.product,
                            quantity=item.quantity,
                            payment=payment,
                            total_order_cost=total_order_cost,  # Add the total order cost here
                            status='Pending'
                        )

                    # Clear the cart after order placement
                    cart.items.all().delete()
                print("Payment verified, redirecting to success page...")  
                
       
                
                   


                


            else:
                return render(request, 'app/payment_error.html', {'error': response_data['data'].get('gateway_response', 'Payment failed.')})

        except Payment.DoesNotExist:
            logger.error(f'Payment not found for reference: {reference}')
            return render(request, 'app/payment_error.html', {'error': 'Payment not found.'})
        except Exception as e:
            logger.exception(f'An error occurred during payment processing: {e}')
            return render(request, 'app/payment_error.html', {'error': 'An unexpected error occurred.'})

def order_success(request):
    return render(request, 'app/order_success.html') 

def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        user = request.user
        product = Product.objects.get(id=prod_id)
        cart, created = Cart.objects.get_or_create(user=user)
        # Fetch the CartItem for the product, or create it if it doesn't exist
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.increment_quantity()

        amount = cart.total_amount
        shipping_charge = 1000
        totalamount = amount + shipping_charge

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'totalamount': totalamount,
        }
        return JsonResponse(data)


def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        user = request.user
        product = Product.objects.get(id=prod_id)
        cart = Cart.objects.get(user=user)
        # Fetch the CartItem for the product
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.decrement_quantity()

        amount = cart.total_amount
        shipping_charge = 1000 if cart.items.exists() else 0
        totalamount = amount + shipping_charge

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'totalamount': totalamount,
        }
        return JsonResponse(data)


def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        user = request.user
        product = Product.objects.get(id=prod_id)
        cart = Cart.objects.get(user=user)

        # Fetch and delete the CartItem for the product
        CartItem.objects.filter(cart=cart, product=product).delete()

        amount = cart.total_amount
        shipping_charge = 1000 if cart.items.exists() else 0
        totalamount = amount + shipping_charge

        data = {
            'amount': amount,
            'totalamount': totalamount,
        }
        return JsonResponse(data)