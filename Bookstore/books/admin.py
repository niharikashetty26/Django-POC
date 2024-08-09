from django.contrib import admin
from .models import Book, UserProfile

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'genre')
    search_fields = ('title', 'author', 'genre')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'role')

admin.site.register(Book, BookAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
