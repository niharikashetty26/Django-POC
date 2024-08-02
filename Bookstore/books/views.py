from django.shortcuts import render, get_object_or_404, redirect
from .models import Book
from .forms import BookForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required, user_passes_test


def is_admin(user):
    return user.is_superuser or user.userprofile.role == 'admin'


def book_list(request):
    books = Book.objects.all()
    is_admin = request.user.groups.filter(name='Admin').exists() or request.user.is_superuser

    return render(request, 'books/book_list.html', {
        'books': books,
        'is_admin': is_admin,
    })

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'books/book_detail.html', {'book': book})


def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})

@user_passes_test(lambda u: u.groups.filter(name='Admin').exists())
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')  # Redirect to book list or a success page
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role='customer')  # Default role
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# User login
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('book_list')  # Redirect to the book list after successful login
        else:
            return render(request, 'books/login.html', {'error': 'Invalid username or password'})

    return render(request, 'books/login.html')  # Render the login form for GET requests


def user_logout(request):
    logout(request)
    return redirect('book_list')
