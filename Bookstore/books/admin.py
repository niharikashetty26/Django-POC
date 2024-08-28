# from django.contrib import admin
# from .models import Book, UserProfile, Cart, Order
#
# @admin.register(Book)
# class BookAdmin(admin.ModelAdmin):
#     list_display = ('title', 'author', 'price', 'quantity')
#     search_fields = ('title', 'author')
#
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'role')
#     search_fields = ('user__username',)
#
# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'book', 'quantity', 'total_price')
#     search_fields = ('user__username', 'book__title')
#
# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('user', 'book', 'quantity', 'total_price', 'order_date')
#     search_fields = ('user__username', 'book__title')
