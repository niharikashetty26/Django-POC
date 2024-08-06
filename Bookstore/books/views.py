from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from .models import Book, Cart
from django.contrib import messages
from .forms import BookForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import gettext as _
from django.utils import translation
from django.db.models import Q, Count, Sum
from django.urls import reverse


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
        books = books.filter(genre__icontains=genre)
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


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    context = {
        'book': book,
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


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role='customer')
            messages.success(request, _("Registration successful! You can now log in."))
            return redirect('login')
        else:
            messages.error(request, _("Please correct the errors below."))
            print(form.errors)  # Print form errors to console for debugging
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
            messages.error(request, _("Invalid username or password."))

    return render(request, 'books/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, _("You have logged out successfully."))  # Translation
    return redirect(reverse('login'))


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.quantity > 0:
        cart_item, created = Cart.objects.get_or_create(user=request.user, book=book)
        if created:
            cart_item.quantity = 1
        else:
            cart_item.quantity += 1
        cart_item.save()
        book.quantity -= 1
        book.save()
        messages.success(request, _("Book added to cart successfully."))
    else:
        messages.error(request, _("Book is out of stock."))
    return redirect('book_list')


@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('book')
    cart_total = sum(item.book.price * item.quantity for item in cart_items)
    cart_details = []
    for item in cart_items:
        item_total_price = item.book.price * item.quantity
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
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    cart_item.delete()
    messages.success(request, _("Book removed from cart successfully."))
    return redirect('view_cart')


def set_language(request):
    language = request.GET.get('language', 'en')
    translation.activate(language)
    request.session['django_language'] = language
    return redirect(request.META.get('HTTP_REFERER', '/'))
