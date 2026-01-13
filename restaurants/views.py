
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Restaurant, Menu, MenuItem, Review, Profile, Follow, ReviewLike, RestaurantList, Comment, CustomList, CustomListItem
from posts.models import Post
from django import forms
from django.http import JsonResponse
from django.db import models

class RestaurantForm(forms.ModelForm):
	class Meta:
		model = Restaurant
		fields = [
			'name', 'cuisine_type', 'address_line1', 'address_line2', 'city', 'province', 'postal_code', 'country', 'happy_hour'
		]
		widgets = {
			'happy_hour': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., Mon-Fri 3-6pm: $5 appetizers, $6 cocktails'})
		}

	def clean(self):
		cleaned_data = super().clean()
		address_line1 = cleaned_data.get('address_line1', '').strip().lower()
		address_line2 = cleaned_data.get('address_line2', '').strip().lower() if cleaned_data.get('address_line2') else ''
		city = cleaned_data.get('city', '').strip().lower()
		province = cleaned_data.get('province', '').strip().lower()
		postal_code = cleaned_data.get('postal_code', '').replace(' ', '').lower()
		country = cleaned_data.get('country', '').strip().lower()
		normalized_address = '|'.join([
			address_line1,
			address_line2,
			city,
			province,
			postal_code,
			country,
		])
		if Restaurant.objects.filter(normalized_address=normalized_address).exists():
			raise forms.ValidationError('A restaurant at this address already exists.')
		return cleaned_data

class ProfileForm(forms.ModelForm):
	class Meta:
		model = Profile
		fields = ['display_name', 'profile_picture']

def root_redirect(request):
	if request.user.is_authenticated:
		return redirect('feed')
	return redirect('login')



@login_required
def feed(request):
	return render(request, 'feed.html')


# New view for searching and adding restaurants
from django.db.models import Q
from django.core.paginator import Paginator


@login_required

def restaurant_search(request):
	from django.db.models import Avg
	from django.conf import settings
	query = request.GET.get('q', '')
	page_number = request.GET.get('page', 1)
	selected_types = request.GET.getlist('cuisine_type')
	selected_location = request.GET.get('location', '')
	happy_hour_only = request.GET.get('happy_hour') == 'true'
	restaurants = Restaurant.objects.all()
	if query:
		restaurants = restaurants.filter(
			Q(name__icontains=query) |
			Q(cuisine_type__icontains=query) |
			Q(address_line1__icontains=query) |
			Q(address_line2__icontains=query) |
			Q(city__icontains=query) |
			Q(province__icontains=query) |
			Q(postal_code__icontains=query) |
			Q(country__icontains=query)
		)
	if selected_types:
		restaurants = restaurants.filter(cuisine_type__in=selected_types)
	if selected_location:
		restaurants = restaurants.filter(city__iexact=selected_location)
	if happy_hour_only:
		restaurants = restaurants.exclude(happy_hour__isnull=True).exclude(happy_hour='')
	paginator = Paginator(restaurants.order_by('-created_at'), 10)
	page_obj = paginator.get_page(page_number)
	
	# Calculate ratings for each restaurant
	restaurants_with_ratings = []
	for restaurant in page_obj:
		avg_rating = None
		review_count = 0
		if hasattr(restaurant, 'menu'):
			menu_items = restaurant.menu.items.all()
			reviews = Review.objects.filter(menu_item__in=menu_items)
			review_count = reviews.count()
			if review_count > 0:
				avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
		restaurants_with_ratings.append({
			'restaurant': restaurant,
			'avg_rating': round(avg_rating, 1) if avg_rating else None,
			'review_count': review_count
		})
	
	form_errors = None
	if request.method == 'POST':
		form = RestaurantForm(request.POST)
		if form.is_valid():
			restaurant = form.save(commit=False)
			restaurant.created_by = request.user
			restaurant.save()
			return redirect('restaurant_search')
		else:
			form_errors = form.non_field_errors()
	else:
		form = RestaurantForm()
	# Get all cuisine types in use for the filter dropdown
	cuisine_choices = Restaurant.CUISINE_CHOICES
	# Get unique cities for location filter
	locations = Restaurant.objects.values_list('city', flat=True).distinct().order_by('city')
	
	# Check if this is an AJAX request
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		# Return only the restaurant list HTML
		return render(request, 'restaurants_list_partial.html', {
			'restaurants_with_ratings': restaurants_with_ratings,
			'page_obj': page_obj,
			'query': query,
		})
	
	return render(request, 'restaurant_search.html', {
		'form': form,
		'restaurants_with_ratings': restaurants_with_ratings,
		'page_obj': page_obj,
		'query': query,
		'cuisine_choices': cuisine_choices,
		'locations': locations,
		'selected_types': selected_types,
		'selected_location': selected_location,
		'form_errors': form_errors,
		'happy_hour_only': happy_hour_only,
		'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
	})


@login_required
def restaurant_detail(request, restaurant_id):
	restaurant = get_object_or_404(Restaurant, id=restaurant_id)
	
	# Calculate rating statistics if menu exists
	rating_stats = None
	review_count = 0
	if hasattr(restaurant, 'menu'):
		from django.db.models import Avg, Min, Max
		menu_items = restaurant.menu.items.all()
		all_reviews = Review.objects.filter(menu_item__in=menu_items)
		review_count = all_reviews.count()
		if all_reviews.exists():
			stats = all_reviews.aggregate(
				avg_rating=Avg('rating'),
				min_rating=Min('rating'),
				max_rating=Max('rating')
			)
			rating_stats = {
				'avg': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
				'min': round(stats['min_rating'], 1) if stats['min_rating'] else 0,
				'max': round(stats['max_rating'], 1) if stats['max_rating'] else 0
			}
	
	# Check if restaurant is in user's lists
	is_favorite = RestaurantList.objects.filter(
		user=request.user,
		restaurant=restaurant,
		list_type='favorite'
	).exists()
	
	is_want_to_try = RestaurantList.objects.filter(
		user=request.user,
		restaurant=restaurant,
		list_type='want_to_try'
	).exists()
	
	return render(request, 'restaurant_detail.html', {
		'restaurant': restaurant,
		'rating_stats': rating_stats,
		'review_count': review_count,
		'is_favorite': is_favorite,
		'is_want_to_try': is_want_to_try
	})


@login_required
def add_menu(request, restaurant_id):
	restaurant = get_object_or_404(Restaurant, id=restaurant_id)
	if hasattr(restaurant, 'menu'):
		return redirect('view_menu', restaurant_id=restaurant_id)
	
	if request.method == 'POST':
		menu = Menu.objects.create(restaurant=restaurant)
		for key, value in request.POST.items():
			if key.startswith('item_name_'):
				index = key.split('_')[-1]
				name = value
				description = request.POST.get(f'item_description_{index}', '')
				price = request.POST.get(f'item_price_{index}')
				if name and price:
					MenuItem.objects.create(menu=menu, name=name, description=description, price=price)
		return redirect('view_menu', restaurant_id=restaurant_id)
	
	return render(request, 'add_menu.html', {'restaurant': restaurant})


@login_required
def view_menu(request, restaurant_id):
	restaurant = get_object_or_404(Restaurant, id=restaurant_id)
	menu = getattr(restaurant, 'menu', None)
	if not menu:
		return redirect('add_menu', restaurant_id=restaurant_id)
	
	if request.method == 'POST':
		# Handle adding new item
		name = request.POST.get('name')
		description = request.POST.get('description', '')
		price = request.POST.get('price')
		if name and price:
			MenuItem.objects.create(menu=menu, name=name, description=description, price=price)
		return redirect('view_menu', restaurant_id=restaurant_id)
	
	# Get search query
	search_query = request.GET.get('search', '').strip()
	
	# Filter menu items based on search
	menu_items = menu.items.all()
	if search_query:
		menu_items = menu_items.filter(
			Q(name__icontains=search_query) |
			Q(description__icontains=search_query)
		)
	
	# Calculate rating stats for each menu item
	menu_items_with_stats = []
	for item in menu_items:
		has_photos = item.reviews.filter(image__isnull=False).exists()
		
		# Add like information for each review
		reviews_with_likes = []
		for review in item.reviews.all():
			review_data = {
				'review': review,
				'like_count': review.likes.count(),
				'user_has_liked': review.likes.filter(user=request.user).exists()
			}
			reviews_with_likes.append(review_data)
		
		item_data = {
			'item': item,
			'rating_stats': item.get_rating_stats(),
			'has_photos': has_photos,
			'reviews_with_likes': reviews_with_likes
		}
		menu_items_with_stats.append(item_data)
	
	# Check if this is an AJAX request
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return render(request, 'menu_items_partial.html', {
			'menu_items_with_stats': menu_items_with_stats,
		})
	
	return render(request, 'view_menu.html', {
		'restaurant': restaurant,
		'menu': menu,
		'menu_items_with_stats': menu_items_with_stats,
		'search_query': search_query
	})


@login_required
def add_review(request, menu_item_id):
	menu_item = get_object_or_404(MenuItem, id=menu_item_id)
	if request.method == 'POST':
		rating = request.POST.get('rating')
		review_text = request.POST.get('review_text', '')
		is_public = request.POST.get('is_public') == 'on'
		user = request.user if is_public else None
		image = request.FILES.get('image')
		review = Review.objects.create(
			menu_item=menu_item,
			user=user,
			rating=float(rating),
			review_text=review_text,
			is_public=is_public,
			image=image
		)
		if is_public:
			username = request.user.username if is_public else 'Anonymous'
			title = f"{username} reviewed {menu_item.name}"
			Post.objects.create(
				post_type='review',
				title=title,
				menu_item=menu_item,
				user=user,
				rating=float(rating),
				review_text=review_text
			)
		return redirect('view_menu', restaurant_id=menu_item.menu.restaurant.id)
	
	return render(request, 'add_review.html', {'menu_item': menu_item})


@login_required
def feed(request):
	# Get users that the current user is following
	following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
	
	# Filter posts to only show from followed users
	posts = Post.objects.select_related('user', 'user__profile', 'menu_item').filter(
		user__in=following_users
	).order_by('-created_at')[:20]
	
	# For each post, get the associated review and like info
	posts_with_likes = []
	for post in posts:
		post_data = {
			'post': post,
			'review': None,
			'like_count': 0,
			'user_has_liked': False,
			'is_top_reviewer': post.user.profile.is_top_reviewer() if hasattr(post.user, 'profile') else False,
			'comments': []
		}
		
		# Find the associated review if it's a review post
		if post.post_type == 'review' and post.menu_item:
			review = Review.objects.filter(
				menu_item=post.menu_item,
				user=post.user,
				rating=post.rating
			).first()
			
			if review:
				post_data['review'] = review
				post_data['like_count'] = review.likes.count()
				post_data['user_has_liked'] = review.likes.filter(user=request.user).exists()
				post_data['comments'] = review.comments.select_related('user', 'user__profile').all()
		
		posts_with_likes.append(post_data)
	
	return render(request, 'feed.html', {
		'posts_with_likes': posts_with_likes,
		'following_count': len(following_users)
	})

@login_required
def user_profile(request):
	user_posts = Post.objects.filter(user=request.user).order_by('-created_at')
	user_reviews = Review.objects.filter(user=request.user).order_by('-created_at')
	profile, created = Profile.objects.get_or_create(user=request.user)
	following_count = Follow.objects.filter(follower=request.user).count()
	followers_count = Follow.objects.filter(following=request.user).count()
	is_top_reviewer = profile.is_top_reviewer()
	
	# Get favorite and want-to-try restaurants
	favorite_restaurants = RestaurantList.objects.filter(
		user=request.user,
		list_type='favorite'
	).select_related('restaurant')
	
	want_to_try_restaurants = RestaurantList.objects.filter(
		user=request.user,
		list_type='want_to_try'
	).select_related('restaurant')
	
	# Calculate flavor profile from favorite restaurants
	from collections import Counter
	favorite_cuisines = [fav.restaurant.cuisine_type for fav in favorite_restaurants]
	cuisine_counts = Counter(favorite_cuisines)
	# Get top 3 cuisines
	flavor_profile = cuisine_counts.most_common(3) if cuisine_counts else []
	
	# Get user's custom lists
	user_lists = CustomList.objects.filter(user=request.user).prefetch_related('items')[:6]
	
	return render(request, 'user_profile.html', {
		'user_posts': user_posts,
		'user_reviews': user_reviews,
		'profile': profile,
		'following_count': following_count,
		'followers_count': followers_count,
		'is_top_reviewer': is_top_reviewer,
		'favorite_restaurants': favorite_restaurants,
		'want_to_try_restaurants': want_to_try_restaurants,
		'flavor_profile': flavor_profile,
		'user_lists': user_lists,
	})

@login_required
def edit_profile(request):
	profile, created = Profile.objects.get_or_create(user=request.user)
	if request.method == 'POST':
		form = ProfileForm(request.POST, request.FILES, instance=profile)
		if form.is_valid():
			form.save()
			return redirect('user_profile')
	else:
		form = ProfileForm(instance=profile)
	return render(request, 'edit_profile.html', {'form': form})

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login

def signup(request):
	if request.user.is_authenticated:
		return redirect('feed')
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			auth_login(request, user)
			return redirect('feed')
	else:
		form = UserCreationForm()
	return render(request, 'registration/signup.html', {'form': form})

@login_required
def follow_user(request, username):
	user_to_follow = get_object_or_404(get_user_model(), username=username)
	if user_to_follow != request.user:
		Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
	return redirect('view_user_profile', username=username)

@login_required
def unfollow_user(request, username):
	user_to_unfollow = get_object_or_404(get_user_model(), username=username)
	Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
	return redirect('view_user_profile', username=username)

@login_required
def view_user_profile(request, username):
	profile_user = get_object_or_404(get_user_model(), username=username)
	user_posts = Post.objects.filter(user=profile_user).order_by('-created_at')
	user_reviews = Review.objects.filter(user=profile_user).order_by('-created_at')
	profile, created = Profile.objects.get_or_create(user=profile_user)
	following_count = Follow.objects.filter(follower=profile_user).count()
	followers_count = Follow.objects.filter(following=profile_user).count()
	is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
	is_own_profile = request.user == profile_user
	is_top_reviewer = profile.is_top_reviewer()
	
	# Get favorite and want-to-try restaurants for this user
	favorite_restaurants = RestaurantList.objects.filter(
		user=profile_user,
		list_type='favorite'
	).select_related('restaurant')
	
	want_to_try_restaurants = RestaurantList.objects.filter(
		user=profile_user,
		list_type='want_to_try'
	).select_related('restaurant')
	
	# Calculate flavor profile from favorite restaurants
	from collections import Counter
	favorite_cuisines = [fav.restaurant.cuisine_type for fav in favorite_restaurants]
	cuisine_counts = Counter(favorite_cuisines)
	# Get top 3 cuisines
	flavor_profile = cuisine_counts.most_common(3) if cuisine_counts else []
	
	# Get user's custom lists
	user_lists = CustomList.objects.filter(user=profile_user).prefetch_related('items')[:6]
	
	return render(request, 'view_user_profile.html', {
		'profile_user': profile_user,
		'user_posts': user_posts,
		'user_reviews': user_reviews,
		'profile': profile,
		'following_count': following_count,
		'followers_count': followers_count,
		'is_following': is_following,
		'is_own_profile': is_own_profile,
		'is_top_reviewer': is_top_reviewer,
		'favorite_restaurants': favorite_restaurants,
		'want_to_try_restaurants': want_to_try_restaurants,
		'flavor_profile': flavor_profile,
		'user_lists': user_lists,
	})


@login_required
def like_review(request, review_id):
	review = get_object_or_404(Review, id=review_id)
	like, created = ReviewLike.objects.get_or_create(review=review, user=request.user)
	
	if not created:
		# Unlike if already liked
		like.delete()
		liked = False
	else:
		liked = True
	
	# Return JSON for AJAX or redirect for regular requests
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'liked': liked,
			'like_count': review.likes.count()
		})
	
	# Redirect back to the previous page
	return redirect(request.META.get('HTTP_REFERER', 'feed'))


@login_required
def toggle_restaurant_list(request, restaurant_id, list_type):
	restaurant = get_object_or_404(Restaurant, id=restaurant_id)
	
	if list_type not in ['favorite', 'want_to_try']:
		return redirect('restaurant_detail', restaurant_id=restaurant_id)
	
	list_item = RestaurantList.objects.filter(
		user=request.user,
		restaurant=restaurant,
		list_type=list_type
	).first()
	
	if list_item:
		# Remove from list
		list_item.delete()
	else:
		# Add to list
		RestaurantList.objects.create(
			user=request.user,
			restaurant=restaurant,
			list_type=list_type
		)
	
	return redirect('restaurant_detail', restaurant_id=restaurant_id)


@login_required
def add_comment(request, review_id):
	if request.method == 'POST':
		review = get_object_or_404(Review, id=review_id)
		text = request.POST.get('text', '').strip()
		
		if text:
			comment = Comment.objects.create(
				review=review,
				user=request.user,
				text=text
			)
			
			# Return JSON for AJAX requests
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				# Get profile info
				profile = None
				display_name = request.user.username
				profile_picture_url = None
				
				if hasattr(request.user, 'profile'):
					profile = request.user.profile
					if profile.display_name:
						display_name = profile.display_name
					if profile.profile_picture:
						profile_picture_url = profile.profile_picture.url
				
				return JsonResponse({
					'success': True,
					'comment': {
						'id': comment.id,
						'text': comment.text,
						'username': request.user.username,
						'display_name': display_name,
						'profile_picture_url': profile_picture_url,
						'created_at': 'just now'
					}
				})
	
	return redirect(request.META.get('HTTP_REFERER', 'feed'))


class CustomListForm(forms.ModelForm):
	class Meta:
		model = CustomList
		fields = ['title', 'description', 'list_type']
		widgets = {
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional description...'}),
			'title': forms.TextInput(attrs={'placeholder': 'e.g., Best Pizza Places or Must-Try Pasta Dishes'}),
			'list_type': forms.RadioSelect(),
		}
		labels = {
			'list_type': 'List Type',
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Override choices to only include the actual choices, not the blank option
		self.fields['list_type'].choices = CustomList.LIST_TYPE_CHOICES


@login_required
def create_list(request):
	if request.method == 'POST':
		form = CustomListForm(request.POST)
		if form.is_valid():
			custom_list = form.save(commit=False)
			custom_list.user = request.user
			custom_list.save()
			
			# Add initial items if provided
			item_ids = request.POST.getlist('items')
			for item_id in item_ids:
				if custom_list.list_type == 'restaurant':
					restaurant = Restaurant.objects.filter(id=item_id).first()
					if restaurant:
						CustomListItem.objects.create(custom_list=custom_list, restaurant=restaurant)
				elif custom_list.list_type == 'dish':
					menu_item = MenuItem.objects.filter(id=item_id).first()
					if menu_item:
						CustomListItem.objects.create(custom_list=custom_list, menu_item=menu_item)
			
			# Create a post about the list
			list_type_display = 'Restaurants' if custom_list.list_type == 'restaurant' else 'Dishes'
			title = f"{request.user.username} created \"{custom_list.title}\" - check it out!"
			Post.objects.create(
				post_type='list',
				title=title,
				user=request.user,
				custom_list=custom_list
			)
			
			return redirect('view_list', list_id=custom_list.id)
	else:
		form = CustomListForm()
	return render(request, 'create_list.html', {'form': form})


@login_required
def view_list(request, list_id):
	custom_list = get_object_or_404(CustomList, id=list_id)
	items = custom_list.items.select_related('menu_item__menu__restaurant', 'restaurant').all()
	is_owner = custom_list.user == request.user
	
	# Calculate ratings for each item
	items_with_ratings = []
	for item in items:
		item_data = {
			'item': item,
			'rating_stats': None
		}
		
		if item.menu_item:
			# Get rating stats for menu item
			base_stats = item.menu_item.get_rating_stats()
			if base_stats:
				review_count = item.menu_item.reviews.count()
				item_data['rating_stats'] = {
					'avg': base_stats['avg'],
					'min': base_stats['min'],
					'max': base_stats['max'],
					'count': review_count
				}
		elif item.restaurant:
			# Calculate rating stats for restaurant
			from django.db.models import Avg
			if hasattr(item.restaurant, 'menu'):
				menu_items = item.restaurant.menu.items.all()
				reviews = Review.objects.filter(menu_item__in=menu_items)
				review_count = reviews.count()
				if review_count > 0:
					avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
					item_data['rating_stats'] = {
						'avg': round(avg_rating, 1) if avg_rating else None,
						'count': review_count
					}
		
		items_with_ratings.append(item_data)
	
	return render(request, 'view_list.html', {
		'custom_list': custom_list,
		'items_with_ratings': items_with_ratings,
		'is_owner': is_owner
	})


@login_required
def my_lists(request):
	lists = CustomList.objects.filter(user=request.user).prefetch_related('items')
	return render(request, 'my_lists.html', {'lists': lists})


@login_required
def add_to_list(request):
	if request.method == 'POST':
		list_id = request.POST.get('list_id')
		item_type = request.POST.get('item_type')
		item_id = request.POST.get('item_id')
		
		custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)
		
		# Check if item type matches list type
		if (item_type == 'menu_item' and custom_list.list_type != 'dish') or \
		   (item_type == 'restaurant' and custom_list.list_type != 'restaurant'):
			return JsonResponse({'success': False, 'error': 'Item type does not match list type'})
		
		# Create list item
		if item_type == 'menu_item':
			menu_item = get_object_or_404(MenuItem, id=item_id)
			# Check if already in list
			if CustomListItem.objects.filter(custom_list=custom_list, menu_item=menu_item).exists():
				return JsonResponse({'success': False, 'error': 'Item already in list'})
			CustomListItem.objects.create(custom_list=custom_list, menu_item=menu_item)
		elif item_type == 'restaurant':
			restaurant = get_object_or_404(Restaurant, id=item_id)
			# Check if already in list
			if CustomListItem.objects.filter(custom_list=custom_list, restaurant=restaurant).exists():
				return JsonResponse({'success': False, 'error': 'Restaurant already in list'})
			CustomListItem.objects.create(custom_list=custom_list, restaurant=restaurant)
		
		return JsonResponse({'success': True})
	
	return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def remove_from_list(request, list_id, item_id):
	custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)
	list_item = get_object_or_404(CustomListItem, id=item_id, custom_list=custom_list)
	list_item.delete()
	return redirect('view_list', list_id=list_id)


@login_required
def delete_list(request, list_id):
	custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)
	custom_list.delete()
	return redirect('my_lists')


@login_required
def get_user_lists(request):
	list_type = request.GET.get('type')
	
	# Map item types to list types
	if list_type == 'restaurant':
		filter_type = 'restaurant'
	elif list_type == 'menu_item':
		filter_type = 'dish'
	else:
		return JsonResponse({'lists': []})
	
	lists = CustomList.objects.filter(user=request.user, list_type=filter_type).annotate(
		item_count=models.Count('items')
	).values('id', 'title', 'item_count')
	
	return JsonResponse({'lists': list(lists)})


@login_required
def search_restaurants_for_list(request):
	query = request.GET.get('q', '').strip()
	if not query or len(query) < 2:
		return JsonResponse({'results': []})
	
	restaurants = Restaurant.objects.filter(
		models.Q(name__icontains=query) |
		models.Q(city__icontains=query) |
		models.Q(cuisine_type__icontains=query)
	)[:10]
	
	results = [{
		'id': r.id,
		'name': r.name,
		'cuisine_type': r.cuisine_type,
		'location': f"{r.city}, {r.province}"
	} for r in restaurants]
	
	return JsonResponse({'results': results})


@login_required
def search_dishes_for_list(request):
	query = request.GET.get('q', '').strip()
	restaurant_id = request.GET.get('restaurant_id', '').strip()
	
	if not query or len(query) < 2:
		return JsonResponse({'results': []})
	
	# If restaurant_id is provided, only search within that restaurant
	if restaurant_id:
		try:
			menu_items = MenuItem.objects.select_related('menu__restaurant').filter(
				menu__restaurant_id=restaurant_id
			).filter(
				models.Q(name__icontains=query) |
				models.Q(description__icontains=query)
			)[:10]
		except ValueError:
			return JsonResponse({'results': []})
	else:
		# Search all dishes
		menu_items = MenuItem.objects.select_related('menu__restaurant').filter(
			models.Q(name__icontains=query) |
			models.Q(description__icontains=query) |
			models.Q(menu__restaurant__name__icontains=query)
		)[:10]
	
	results = [{
		'id': item.id,
		'name': item.name,
		'restaurant': item.menu.restaurant.name,
		'price': str(item.price)
	} for item in menu_items]
	
	return JsonResponse({'results': results})
