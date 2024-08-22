# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, Cart, Order, OrderItem


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


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'book', 'quantity']
        read_only_fields = ['user']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance

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
    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)  # Optional if you want to include items in the response

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'status', 'items']  # Ensure 'user' is included if needed