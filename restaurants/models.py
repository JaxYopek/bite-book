from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth import get_user_model
from django.utils import timezone

class Restaurant(models.Model):
	name = models.CharField(max_length=255)
	CUISINE_CHOICES = [
		('Italian', 'Italian'),
		('Chinese', 'Chinese'),
		('Indian', 'Indian'),
		('Mexican', 'Mexican'),
		('Japanese', 'Japanese'),
		('American', 'American'),
		('Thai', 'Thai'),
		('Other', 'Other'),
	]
	cuisine_type = models.CharField(max_length=100, choices=CUISINE_CHOICES, verbose_name='Type of Food')
	address_line1 = models.CharField(max_length=255)
	address_line2 = models.CharField(max_length=255, blank=True, null=True)
	city = models.CharField(max_length=100)
	province = models.CharField(max_length=100)
	postal_code = models.CharField(max_length=20)
	country = models.CharField(max_length=100)
	lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
	lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
	normalized_address = models.CharField(max_length=512, unique=True, editable=False)

	def save(self, *args, **kwargs):
		# Normalize address for uniqueness
		parts = [
			self.address_line1.strip().lower() if self.address_line1 else '',
			self.address_line2.strip().lower() if self.address_line2 else '',
			self.city.strip().lower() if self.city else '',
			self.province.strip().lower() if self.province else '',
			self.postal_code.strip().replace(' ', '').lower() if self.postal_code else '',
			self.country.strip().lower() if self.country else '',
		]
		self.normalized_address = '|'.join(parts)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.name} ({self.city})"


class Menu(models.Model):
	restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='menu')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Menu for {self.restaurant.name}"


class MenuItem(models.Model):
	menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	price = models.DecimalField(max_digits=6, decimal_places=2)

	def __str__(self):
		return f"{self.name} - ${self.price}"


class Review(models.Model):
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
	rating = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(1.0), MaxValueValidator(10.0)])
	review_text = models.TextField(blank=True)
	is_public = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		username = self.user.username if self.user else 'Anonymous'
		return f"{username}'s review of {self.menu_item.name} - {self.rating} stars"
