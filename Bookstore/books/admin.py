# books/admin.py

from django.contrib import admin
from .models import Book

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'genre')  # Fields to display in the admin list view
    search_fields = ('title', 'author', 'genre')  # Fields to search by in the admin

# Register the Book model with the admin site
admin.site.register(Book, BookAdmin)
