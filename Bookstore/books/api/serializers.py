from rest_framework import serializers, viewsets
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

from books.models import Book, UserProfile, Review, Cart, OrderItem, Order


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'role']


class BookSerializer(serializers.ModelSerializer):
    reviews = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())  # Book ID only

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'book']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'book', 'quantity']
        read_only_fields = ['user']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class AddMultipleBooksToCartSerializer(serializers.Serializer):
    books = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        write_only=True
    )

    def validate_books(self, value):
        for item in value:
            if 'book_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError("Each book item must contain 'book_id' and 'quantity'")
            if not Book.objects.filter(id=item['book_id']).exists():
                raise serializers.ValidationError(f"Book with id {item['book_id']} does not exist.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        for item in validated_data['books']:
            book = Book.objects.get(id=item['book_id'])
            Cart.objects.create(user=user, book=book, quantity=item['quantity'])
        return validated_data


class OrderItemSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'order_date', 'total_price', 'items']  # Ensure 'status' is included

    def get_total_price(self, obj):
        return sum(item.book.price * item.quantity for item in obj.items.all())


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Review.objects.all()
        book_id = self.request.query_params.get('book_id')
        if book_id is not None:
            queryset = queryset.filter(book_id=book_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
