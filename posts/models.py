from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

class Post(models.Model):
    POST_TYPES = [
        ('review', 'Review'),
        ('diary', 'Diary Entry'),
        ('list', 'List'),
    ]
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='review')
    title = models.CharField(max_length=255, blank=True, null =True)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE, null=True, blank=True)
    custom_list = models.ForeignKey('restaurants.CustomList', on_delete=models.CASCADE, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(1.0), MaxValueValidator(10.0)], null=True, blank=True)
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"{self.user.username if self.user else 'Anonymous'}'s post"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.post.title}"
