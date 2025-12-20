
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required
from .models import Restaurant, Menu, MenuItem, Review
from posts.models import Post
from django import forms

class RestaurantForm(forms.ModelForm):
	class Meta:
		model = Restaurant
		fields = [
			'name', 'cuisine_type', 'address_line1', 'address_line2', 'city', 'province', 'postal_code', 'country'
		]

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
	query = request.GET.get('q', '')
	page_number = request.GET.get('page', 1)
	selected_types = request.GET.getlist('cuisine_type')
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
	paginator = Paginator(restaurants.order_by('-created_at'), 10)
	page_obj = paginator.get_page(page_number)
	if request.method == 'POST':
		form = RestaurantForm(request.POST)
		if form.is_valid():
			restaurant = form.save(commit=False)
			restaurant.created_by = request.user
			restaurant.save()
			return redirect('restaurant_search')
	else:
		form = RestaurantForm()
	# Get all cuisine types in use for the filter dropdown
	cuisine_choices = Restaurant.CUISINE_CHOICES
	
	# Check if this is an AJAX request
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		# Return only the restaurant list HTML
		return render(request, 'restaurants_list_partial.html', {
			'page_obj': page_obj,
			'query': query,
		})
	
	return render(request, 'restaurant_search.html', {
		'form': form,
		'page_obj': page_obj,
		'query': query,
		'cuisine_choices': cuisine_choices,
		'selected_types': selected_types,
	})


@login_required
def restaurant_detail(request, restaurant_id):
	restaurant = get_object_or_404(Restaurant, id=restaurant_id)
	return render(request, 'restaurant_detail.html', {'restaurant': restaurant})


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
	
	return render(request, 'view_menu.html', {'restaurant': restaurant, 'menu': menu})


@login_required
def add_review(request, menu_item_id):
	menu_item = get_object_or_404(MenuItem, id=menu_item_id)
	if request.method == 'POST':
		rating = request.POST.get('rating')
		review_text = request.POST.get('review_text', '')
		is_public = request.POST.get('is_public') == 'on'
		user = request.user if is_public else None
		review = Review.objects.create(
			menu_item=menu_item,
			user=user,
			rating=float(rating),
			review_text=review_text,
			is_public=is_public
		)
		if is_public:
			username = request.user.username if is_public else 'Anonymous'
			title = f"{username} reviewed {menu_item.name} at {menu_item.menu.restaurant.name}"
			Post.objects.create(
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
	posts = Post.objects.all().order_by('-created_at')[:20]  # Show latest 20
	return render(request, 'feed.html', {'posts': posts})


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
