from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cover_image = models.ImageField(upload_to='covers/', null=True)
    description = models.TextField()
    genre = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    USER_ROLES = [
        ('customer', 'Customer'),
        ('content_admin', 'Content Admin'),
        ('superadmin', 'Superadmin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='customer')

    def __str__(self):
        return self.user.username


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Book, through='CartItem')

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        return self.items.aggregate(total=Sum('cartitem__total_price'))['total'] or 0.00

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.quantity}"

    def get_total_price(self):
        return self.book.price * self.quantity

