import json
import logging

from app.context_processors import cart_item_count
logger = logging.getLogger(__name__)

import uuid
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
import requests
from . models import Cart, CartItem, Customer, Product, Payment, OrderPlaced
from . forms import CustomerProfileForm, CustomerRegistrationForm
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
    add = get_object_or_404(Customer, pk=pk)  # Get the customer instance
    form = CustomerProfileForm(request.POST, instance=add)  # Bind the form to the instance
    if form.is_valid():
        form.save()  # Save the form directly, which updates the instance
        success = True
    else:
        success = False   
    return render(request, 'app/updateAddress.html', {'form': form, 'success': success})
  
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('address')  # Redirect to address page after deletion

@login_required(login_url='login')  # Ensures the user is logged in, redirects to login if not
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

@login_required(login_url='login')  # Redirect to login if user is not authenticated
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
        data = json.loads(request.body)
        reference = data.get('reference')
        customer_id = data.get('customerID')
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
            
            # Check if payment was successful
            if response_data['status'] and response_data['data']['status'] == 'success':
                # Retrieve payment amount (convert from kobo to naira)
                amount = response_data['data']['amount'] / 100
                
                # Retrieve user based on email (assuming user email matches payment email)
                customer = Customer.objects.get(id=customer_id)  # Get the customer object
                user = customer.user  # Assuming each customer is tied to a user
                
                with transaction.atomic():
                    # Get the user's cart
                    cart = Cart.objects.get(user=user)
                    cart_items = cart.items.all()

                    # Calculate total order cost
                    total_order_cost = sum(item.product.selling_price * item.quantity for item in cart_items)
                    
                    # Additional fee (e.g., shipping)
                    additional_fee = 1000
                    total_order_cost += additional_fee

                    # Create payment record in your database
                    payment = Payment.objects.create(
                        user=user,
                        amount=amount,
                        paystack_reference=reference,
                        paystack_payment_status='success',
                        paid=True
                    )

                    # Handle the user customer relation (assuming a customer exists)
                    customer = Customer.objects.filter(user=user).first()
                    if not customer:
                        return render(request, 'app/payment_error.html', {'error': 'No customer found for this user.'})

                    # Create orders for each cart item
                    for item in cart_items:
                        OrderPlaced.objects.create(
                            user=user,
                            customer=customer,
                            product=item.product,
                            quantity=item.quantity,
                            payment=payment,
                            total_order_cost=total_order_cost,
                            status='Pending'
                        )

                    # Clear the user's cart after placing the order
                    cart.items.all().delete()

                print("Payment verified, redirecting to success page...")  
                return JsonResponse({'message': 'Payment verified, orders created.'}, status=200)
            else:
                # Handle payment failure response from Paystack
                return JsonResponse({'error': 'Payment verification failed.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

def orders(request):
    totalitem = 0
    if request.user.is_authenticated:
       totalitem = len(Cart.objects.filter(user=request.user))
    order_placed = OrderPlaced.objects.filter(user=request.user)
    return render(request, 'app/orders.html', locals()) 

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
    
def search(request):
    query = request.GET.get('search', '')
    if not query:
        return HttpResponseBadRequest("Search query cannot be empty.")
    products = Product.objects.filter(Q(title__icontains=query))
    cart_info = cart_item_count(request)
    context = {
        'products': products,
        'query': query,
        **cart_info  
    }
    return render(request, "app/search.html", context)

# def custom_404_view(request, exception):
#     return render(request, '404.html', status=404)
