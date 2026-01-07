from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import Restaurant, Review

def trending_restaurants(request):
    """Add trending restaurants to context for all templates"""
    if request.user.is_authenticated:
        # Get reviews from the last 24 hours
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        # Find restaurants with most reviews in last 24 hours
        trending = Restaurant.objects.filter(
            menu__items__reviews__created_at__gte=twenty_four_hours_ago
        ).annotate(
            review_count=Count('menu__items__reviews')
        ).order_by('-review_count')[:5]
        
        return {'trending_restaurants': trending}
    return {}
