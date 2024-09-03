import uuid
from django.db.models import Sum
from rest_framework import generics, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly

from .serializers import RegisterSerializer, BookSerializer, CartSerializer, OrderSerializer
from ..models import UserProfile, Book, Cart, Order, OrderItem


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.userprofile.role in ['admin', 'superadmin']


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if not UserProfile.objects.filter(user=user).exists():
            UserProfile.objects.create(user=user, role='customer')

        return Response({
            "user": {
                "username": user.username,
                "email": user.email,
            }
        }, status=status.HTTP_201_CREATED)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='add_books')
    def add_books(self, request):
        user = request.user
        books_data = request.data.get('books', [])
        added_cart_items = []

        if not books_data:
            return Response({'detail': 'No books provided.'}, status=status.HTTP_400_BAD_REQUEST)

        for book_data in books_data:
            book_id = book_data.get('book_id')
            quantity = book_data.get('quantity', 1)

            if not book_id:
                return Response({'detail': 'Book ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                book = Book.objects.get(id=book_id)
            except Book.DoesNotExist:
                return Response({'detail': f'Book with ID {book_id} does not exist.'},
                                status=status.HTTP_400_BAD_REQUEST)

            cart_item, created = Cart.objects.get_or_create(user=user, book=book)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()
            serialized_item = CartSerializer(cart_item)
            added_cart_items.append(serialized_item.data)

        return Response(added_cart_items, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items:
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user, status='pending')
        for item in cart_items:
            OrderItem.objects.create(order=order, book=item.book, quantity=item.quantity)
        cart_items.delete()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user != order.user and request.user.userprofile.role not in ['admin', 'superadmin']:
            raise PermissionDenied("You do not have permission to delete this order.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.user != request.user and request.user.userprofile.role not in ['admin', 'superadmin']:
            raise PermissionDenied("You do not have permission to cancel this order.")
        if order.status != 'pending':
            return Response({'detail': 'Only pending orders can be canceled.'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'cancelled'
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_superuser and not request.user.userprofile.role in ['admin', 'superadmin']:
            raise PermissionDenied("Only admins or superadmins can update the status of orders.")
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status == 'completed' or instance.status == 'Completed':
            for item in instance.items.all():
                item.book.quantity -= item.quantity
                item.book.save()
