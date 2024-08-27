from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import Book, Cart, Order, Review, UserProfile
from django.contrib import messages
from .forms import BookForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import gettext as _
from django.utils import translation
from django.db.models import Q, Count, Sum
from django.urls import reverse
from django.contrib.postgres.aggregates import ArrayAgg
from decimal import Decimal
from collections import defaultdict


def is_admin(user):
    return user.is_superuser or user.userprofile.role == 'admin'


@login_required
def user_profile(request):
    return render(request, 'books/profile.html', {'user': request.user})


@login_required
def book_list(request):
    books = Book.objects.all()
    query = request.GET.get('q')
    genre = request.GET.get('genre')
    author = request.GET.get('author')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort_by = request.GET.get('sort_by')

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(genre__icontains=query))
    if genre:
        books = books.filter(genre__iexact=genre)
    if author:
        books = books.filter(author__icontains=author)
    if price_min:
        books = books.filter(price__gte=price_min)
    if price_max:
        books = books.filter(price__lte=price_max)

    if sort_by == 'most_reviews':
        books = books.annotate(num_reviews=Count('reviews')).order_by('-num_reviews')
    elif sort_by == 'price_asc':
        books = books.order_by('price')
    elif sort_by == 'price_desc':
        books = books.order_by('-price')

    cart_items = Cart.objects.filter(user=request.user).select_related('book')
    cart_count = cart_items.count()
    cart_total = cart_items.aggregate(total=Sum('book__price'))['total'] or 0

    user_role = request.user.userprofile.role if hasattr(request.user, 'userprofile') else None

    return render(request, 'books/book_list.html', {
        'books': books,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'user_role': user_role,
    })


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = Review.objects.filter(book=book).order_by('-created_at')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating and comment:
            Review.objects.create(
                book=book,
                user=request.user,
                rating=rating,
                comment=comment
            )
            return redirect('book_detail', pk=pk)

    context = {
        'book': book,
        'reviews': reviews,
    }
    return render(request, 'books/book_detail.html', context)


def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _("Book created successfully!"))
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, _("Book updated successfully!"))
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form, 'book': book})


@login_required
@user_passes_test(is_admin)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, _("Book deleted successfully!"))
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})


@user_passes_test(lambda u: u.groups.filter(name='Admin').exists())
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Book added successfully!"))
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()  # Delete the book
    return redirect('book_list')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(user=user, role='customer')
            messages.success(request, _("Registration successful! You can now log in."))
            return redirect('login')
        else:
            messages.error(request, _("Please correct the errors below."))
            print(form.errors)
    else:
        form = UserCreationForm()

    return render(request, 'books/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        language = request.POST.get('language', 'en')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            translation.activate(language)
            request.session['django_language'] = language
            messages.success(request, _("Login successful!"))
            return redirect('book_list')
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, _("Incorrect password. Please try again."))
            else:
                messages.error(request, _("Invalid username or password."))

    return render(request, 'books/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, _("You have logged out successfully."))
    return redirect(reverse('login'))



@login_required
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user)

    if request.method == 'POST':
        if not cart_items.exists():
            messages.error(request, _("Your cart is empty."))
            return redirect('view_cart')

        total_order_price = 0

        for item in cart_items:
            if item.book.quantity < item.quantity:
                messages.error(request, _(f"Cannot place order for {item.book.title}. Not enough stock available."))
                return redirect('view_cart')

            item_total_price = item.book.price * item.quantity
            total_order_price += item_total_price

            Order.objects.create(
                user=request.user,
                book=item.book,
                quantity=item.quantity
            )

            item.book.quantity -= item.quantity
            item.book.save()

        cart_items.delete()
        messages.success(request, _("Order placed successfully!"))

        return redirect('order_success')

    total_order_price = sum(item.book.price * item.quantity for item in cart_items)

    return render(request, 'books/place_order.html', {
        'cart_items': cart_items,
        'total_order_price': total_order_price
    })

def order_success(request):
    return render(request, 'books/order_success.html')


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart_item = Cart.objects.filter(user=request.user, book=book).first()

    if book.quantity > 0:
        if cart_item:
            if cart_item.quantity < book.quantity:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, _("Book quantity increased in cart."))
            else:
                messages.error(request, _("Cannot add more of this book. Not enough stock available."))
        else:
            cart_item = Cart.objects.create(user=request.user, book=book, quantity=1)
            messages.success(request, _("Book added to cart successfully."))
    else:
        messages.error(request, _("Book is out of stock."))

    return redirect('book_list')


@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('book')

    cart_total = Decimal('0.00')
    cart_details = []

    for item in cart_items:
        item_total_price = item.book.price * item.quantity
        cart_total += item_total_price

        cart_details.append({
            'book': item.book,
            'quantity': item.quantity,
            'price': item.book.price,
            'total_price': item_total_price,
            'cart_item_id': item.id,
        })

    return render(request, 'books/cart.html', {
        'cart_items': cart_details,
        'cart_total': cart_total,
    })


@login_required
def remove_from_cart(request, cart_item_id):
    print(f"Trying to remove cart item with ID: {cart_item_id}")
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    cart_item.delete()
    messages.success(request, _("Book removed from cart successfully."))
    return redirect('view_cart')



def view_orders(request):
    orders = (
        Order.objects
        .select_related('user', 'book')
        .values('user__username', 'order_date')
        .annotate(total_quantity=Sum('quantity'), books=ArrayAgg('book__title', distinct=True))
        .order_by('order_date')
    )

    context = {
        'orders': orders,
    }
    return render(request, 'books/view_orders.html', context)


def set_language(request):
    language = request.GET.get('language', 'en')
    translation.activate(language)
    request.session['django_language'] = language
    return redirect(request.META.get('HTTP_REFERER', '/'))


#
# @login_required
# def admin_dashboard(request):
#     orders = Order.objects.all()
#     books = Book.objects.all()
#     users = UserProfile.objects.filter(role='customer')
#     admins = UserProfile.objects.filter(role='admin')
#
#     ratings_data = {
#         'labels': [],
#         'data': [],
#     }
#
#     for book in books:
#         average_rating = Review.objects.filter(book=book).aggregate(average=Sum('rating'))['average'] or 0
#         ratings_data['labels'].append(book.title)
#         ratings_data['data'].append(average_rating)
#
#     highest_bought_data = {
#         'labels': [],
#         'data': [],
#     }
#
#     highest_bought_books = Order.objects.values('book__title').annotate(total_quantity=Sum('quantity')).order_by(
#         '-total_quantity')[:5]
#
#     for entry in highest_bought_books:
#         highest_bought_data['labels'].append(entry['book__title'])
#         highest_bought_data['data'].append(entry['total_quantity'])
#
#     context = {
#         'orders': orders,
#         'books': books,
#         'users': users,
#         'admins': admins,
#         'ratings_data': ratings_data,
#         'highest_bought_data': highest_bought_data,
#     }
#
#     return render(request, 'books/admin_dashboard.html', context)


@login_required
def admin_dashboard(request):
    orders = Order.objects.all()
    books = Book.objects.all()
    users = UserProfile.objects.filter(role='customer')
    admins = UserProfile.objects.filter(role='admin')

    ratings_data = {
        'labels': [],
        'data': [],
    }

    for book in books:
        average_rating = Review.objects.filter(book=book).aggregate(average=Sum('rating'))['average'] or 0
        ratings_data['labels'].append(book.title)
        ratings_data['data'].append(average_rating)

    highest_bought_data = {
        'labels': [],
        'data': [],
    }

    highest_bought_books = Order.objects.values('book__title').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]

    for entry in highest_bought_books:
        highest_bought_data['labels'].append(entry['book__title'])
        highest_bought_data['data'].append(entry['total_quantity'])

    context = {
        'orders': orders,
        'books': books,
        'users': users,
        'admins': admins,
        'ratings_data': ratings_data,
        'highest_bought_data': highest_bought_data,
    }

    return render(request, 'books/admin_dashboard.html', context)


def order_history_view(request):
    orders = Order.objects.select_related('user', 'book').all()
    order_summary = defaultdict(lambda: {'books': [], 'quantity': 0})

    for order in orders:
        order_summary[order.user.username]['books'].append(order.book.title)
        order_summary[order.user.username]['quantity'] += order.quantity
    order_summary = dict(order_summary)

    return render(request, 'your_template.html', {'order_summary': order_summary})

