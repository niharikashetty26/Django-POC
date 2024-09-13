from django.contrib import admin
from .models import UserProfile, Book, Review, Cart


# Custom Admin for UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'role')
    list_filter = ('role',)
    ordering = ('user__username',)


# Custom Admin for Book
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'price', 'quantity')
    search_fields = ('title', 'author', 'genre')
    list_filter = ('genre', 'author')
    ordering = ('title',)


# Custom Admin for Review
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    ordering = ('-created_at',)


# Custom Admin for Cart
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'quantity', 'total_price')
    search_fields = ('user__username', 'book__title')
    list_filter = ('user',)
    ordering = ('user__username',)


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Cart, CartAdmin)
