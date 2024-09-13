import uuid
from django.db.models import Sum, F
from rest_framework import generics, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User, Group
from rest_framework.permissions import AllowAny, IsAuthenticated

from books.models import Book, Cart, Order, OrderItem, UserProfile
from .serializers import RegisterSerializer, BookSerializer, CartSerializer, OrderSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role in ['admin', 'superadmin']


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'customer'


class IsCustomerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'POST']:
            return request.user.is_authenticated and (
                request.user.userprofile.role in ['customer', 'admin', 'superadmin']
            )
        if request.method in ['PUT', 'DELETE']:
            return request.user.is_authenticated and request.user.userprofile.role in ['admin', 'superadmin']
        return False


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
        user_group, created = Group.objects.get_or_create(name='Customer')
        user.groups.add(user_group)

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
    permission_classes = [IsCustomerOrAdmin]

    @action(detail=False, methods=['post'])
    def add_books(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'},
                            status=status.HTTP_401_UNAUTHORIZED)

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

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'cancel']:
            return [permissions.IsAuthenticated(), IsCustomerOrAdmin()]
        return [permissions.IsAuthenticated(), IsAdminOrReadOnly()]

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Pass the user from request to the serializer
        serializer.save(user=self.request.user)

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
        if request.user.userprofile.role not in ['admin', 'superadmin']:
            raise PermissionDenied("Only admins can update the status of orders.")
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status == 'completed':
            for item in instance.items.all():
                item.book.quantity -= item.quantity
                item.book.save()
