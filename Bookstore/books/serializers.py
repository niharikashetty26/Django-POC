# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, Cart


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
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Cart
        fields = ['id', 'book', 'quantity', 'total_price']
        read_only_fields = ['total_price']  # Mark total_price as read-only

    def create(self, validated_data):
        user = self.context['request'].user
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            book=validated_data['book'],
            defaults={'quantity': validated_data['quantity']}
        )
        if not created:
            cart_item.quantity += validated_data['quantity']
            cart_item.save()
        return cart_item

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance