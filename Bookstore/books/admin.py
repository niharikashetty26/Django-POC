from django.contrib import admin
from .models import Book, UserProfile

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'genre')  # Fields to display in the admin list view
    search_fields = ('title', 'author', 'genre')  # Fields to search by in the admin

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Display user and their role in the admin panel
    search_fields = ('user__username', 'role')  # Search functionality

# Register the Book model with the admin site
admin.site.register(Book, BookAdmin)
# Register the UserProfile model with the admin site
admin.site.register(UserProfile, UserProfileAdmin)
