from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth import get_user_model
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def is_top_reviewer(self):
        """Check if user is in the 90th percentile of reviewers"""
        from django.db.models import Count
        
        # Get review count for this user
        user_review_count = Review.objects.filter(user=self.user).count()
        
        if user_review_count == 0:
            return False
        
        # Get all users with their review counts
        User = get_user_model()
        users_with_reviews = User.objects.annotate(
            review_count=Count('review')
        ).filter(review_count__gt=0).values_list('review_count', flat=True)
        
        if not users_with_reviews:
            return False
        
        # Calculate 90th percentile threshold
        review_counts = sorted(users_with_reviews, reverse=True)
        percentile_index = int(len(review_counts) * 0.1)  # Top 10%
        threshold = review_counts[percentile_index] if percentile_index < len(review_counts) else review_counts[-1]
        
        return user_review_count >= threshold

class Follow(models.Model):
    follower = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

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
	happy_hour = models.TextField(blank=True, null=True, help_text="Happy hour details (days, times, specials)")
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


class HappyHour(models.Model):
	DAYS_OF_WEEK = [
		('monday', 'Monday'),
		('tuesday', 'Tuesday'),
		('wednesday', 'Wednesday'),
		('thursday', 'Thursday'),
		('friday', 'Friday'),
		('saturday', 'Saturday'),
		('sunday', 'Sunday'),
	]
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='happy_hours')
	day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
	start_time = models.TimeField()
	end_time = models.TimeField()
	specials = models.TextField(help_text="e.g., $5 appetizers, $6 cocktails")
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['day_of_week', 'start_time']
	
	def __str__(self):
		return f"{self.restaurant.name} - {self.get_day_of_week_display()} {self.start_time.strftime('%I:%M%p')}-{self.end_time.strftime('%I:%M%p')}"


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

	def get_rating_stats(self):
		"""Calculate rating statistics for this menu item"""
		from django.db.models import Avg, Min, Max
		reviews = self.reviews.all()
		if reviews.exists():
			stats = reviews.aggregate(
				avg_rating=Avg('rating'),
				min_rating=Min('rating'),
				max_rating=Max('rating')
			)
			return {
				'avg': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
				'min': round(stats['min_rating'], 1) if stats['min_rating'] else 0,
				'max': round(stats['max_rating'], 1) if stats['max_rating'] else 0
			}
		return None

	def __str__(self):
		return f"{self.name} - ${self.price}"


class Review(models.Model):
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
	rating = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(1.0), MaxValueValidator(10.0)])
	review_text = models.TextField(blank=True)
	image = models.ImageField(upload_to='review_images/', blank=True, null=True)
	is_public = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		username = self.user.username if self.user else 'Anonymous'
		return f"{username}'s review of {self.menu_item.name} - {self.rating} stars"


class ReviewLike(models.Model):
	review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('review', 'user')  # Prevent duplicate likes

	def __str__(self):
		return f"{self.user.username} likes review of {self.review.menu_item.name}"


class RestaurantList(models.Model):
	LIST_TYPES = [
		('favorite', 'Favorite'),
		('want_to_try', 'Want to Try'),
	]
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='restaurant_lists')
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='user_lists')
	list_type = models.CharField(max_length=20, choices=LIST_TYPES)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('user', 'restaurant', 'list_type')  # Prevent duplicates

	def __str__(self):
		return f"{self.user.username}'s {self.list_type}: {self.restaurant.name}"


class Comment(models.Model):
	review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f"{self.user.username} on {self.review.menu_item.name}"


class CustomList(models.Model):
	LIST_TYPE_CHOICES = [
		('dish', 'Dishes'),
		('restaurant', 'Restaurants'),
	]
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='custom_lists')
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True, null=True)
	list_type = models.CharField(max_length=20, choices=LIST_TYPE_CHOICES)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.title} by {self.user.username}"
	
	def item_count(self):
		return self.items.count()


class CustomListItem(models.Model):
	custom_list = models.ForeignKey(CustomList, on_delete=models.CASCADE, related_name='items')
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
	added_at = models.DateTimeField(auto_now_add=True)
	note = models.TextField(blank=True, null=True)

	class Meta:
		ordering = ['added_at']

	def __str__(self):
		if self.menu_item:
			return f"{self.menu_item.name} in {self.custom_list.title}"
		elif self.restaurant:
			return f"{self.restaurant.name} in {self.custom_list.title}"
		return f"Item in {self.custom_list.title}"


class Notification(models.Model):
	NOTIFICATION_TYPES = [
		('menu_item_added', 'New menu item at favorite restaurant'),
		('review_like', 'Someone liked your review'),
		('comment', 'Someone commented on your review'),
		('follow', 'Someone followed you'),
		('post_like', 'Someone liked your post'),
		('post_comment', 'Someone commented on your post'),
	]
	
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='notifications')
	notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
	review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
	post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, null=True, blank=True)
	triggered_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True, related_name='triggered_notifications')
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['-created_at']
	
	def __str__(self):
		return f"{self.notification_type} for {self.user.username}"
	
	def get_message(self):
		if self.notification_type == 'menu_item_added' and self.menu_item and self.restaurant:
			return f"New item '{self.menu_item.name}' added to {self.restaurant.name}"
		elif self.notification_type == 'review_like' and self.triggered_by:
			return f"{self.triggered_by.username} liked your review"
		elif self.notification_type == 'comment' and self.triggered_by:
			return f"{self.triggered_by.username} commented on your review"
		elif self.notification_type == 'follow' and self.triggered_by:
			return f"{self.triggered_by.username} started following you"
		elif self.notification_type == 'post_like' and self.triggered_by:
			return f"{self.triggered_by.username} liked your post"
		elif self.notification_type == 'post_comment' and self.triggered_by:
			return f"{self.triggered_by.username} commented on your post"
		return "New notification"
