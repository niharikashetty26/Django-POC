from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Book, UserProfile
from .forms import BookForm

def is_content_admin(user):
    return user.is_superuser or user.userprofile.role == 'content_admin'

def home(request):
    return render(request, 'books/home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, 'Registration successful. You can now log in.')
        return redirect('login')
    return render(request, 'books/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'books/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def list_books(request):
    books = Book.objects.all()
    return render(request, 'books/list_books.html', {'books': books})

@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(request, 'books/book_detail.html', {'book': book})

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added successfully.')
            return redirect('list_books')
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})

@login_required
@user_passes_test(is_content_admin)
def update_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully.')
            return redirect('list_books')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/update_book.html', {'form': form})

@login_required
@user_passes_test(is_content_admin)
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('list_books')
    return render(request, 'books/delete_book.html', {'book': book})

def search_books(request):
    query = request.GET.get('q')
    if query:
        books = Book.objects.filter(title__icontains=query)
    else:
        books = Book.objects.all()
    return render(request, 'books/search_results.html', {'books': books})
