from django.urls import path
from . import views

from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/new/', views.book_create, name='book_create'),
    path('book/<int:pk>/edit/', views.book_update, name='book_update'),
    path('book/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('add/', views.add_book, name='add_book'),
    path('login/', views.user_login, name='login'),
    path('add-book/', views.add_book, name='add_book'),
    path('logout/', LogoutView.as_view(), name='logout'),


]
