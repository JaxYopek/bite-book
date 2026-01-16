"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin


from django.urls import path, include
from restaurants import views as restaurant_views
from posts import views as post_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', restaurant_views.root_redirect, name='root'),
    path('feed/', restaurant_views.feed, name='feed'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', restaurant_views.signup, name='signup'),
    path('search/', restaurant_views.search, name='search'),
    path('api/live-search/', restaurant_views.live_search, name='live_search'),
    path('restaurants/', restaurant_views.restaurant_search, name='restaurant_search'),
    path('restaurants/<int:restaurant_id>/', restaurant_views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:restaurant_id>/list/<str:list_type>/', restaurant_views.toggle_restaurant_list, name='toggle_restaurant_list'),
    path('restaurants/<int:restaurant_id>/add-menu/', restaurant_views.add_menu, name='add_menu'),
    path('restaurants/<int:restaurant_id>/menu/', restaurant_views.view_menu, name='view_menu'),
    path('menu-items/<int:menu_item_id>/review/', restaurant_views.add_review, name='add_review'),
    path('reviews/<int:review_id>/like/', restaurant_views.like_review, name='like_review'),
    path('reviews/<int:review_id>/comment/', restaurant_views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/delete/', restaurant_views.delete_comment, name='delete_comment'),
    path('create-diary-entry/', post_views.create_diary_entry, name='create_diary_entry'),
    path('posts/<int:post_id>/', post_views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/like/', post_views.like_post, name='like_post'),
    path('posts/<int:post_id>/comment/', post_views.add_post_comment, name='add_post_comment'),
    path('posts/<int:post_id>/delete/', post_views.delete_post, name='delete_post'),
    path('post-comments/<int:comment_id>/delete/', post_views.delete_post_comment, name='delete_post_comment'),
    path('profile/', restaurant_views.user_profile, name='user_profile'),
    path('profile/edit/', restaurant_views.edit_profile, name='edit_profile'),
    path('user/<str:username>/', restaurant_views.view_user_profile, name='view_user_profile'),
    path('user/<str:username>/follow/', restaurant_views.follow_user, name='follow_user'),
    path('user/<str:username>/unfollow/', restaurant_views.unfollow_user, name='unfollow_user'),
    path('lists/create/', restaurant_views.create_list, name='create_list'),
    path('lists/my/', restaurant_views.my_lists, name='my_lists'),
    path('lists/<int:list_id>/', restaurant_views.view_list, name='view_list'),
    path('lists/<int:list_id>/delete/', restaurant_views.delete_list, name='delete_list'),
    path('lists/<int:list_id>/remove/<int:item_id>/', restaurant_views.remove_from_list, name='remove_from_list'),
    path('lists/add/', restaurant_views.add_to_list, name='add_to_list'),
    path('api/get-user-lists/', restaurant_views.get_user_lists, name='get_user_lists'),
    path('api/search-restaurants/', restaurant_views.search_restaurants_for_list, name='search_restaurants_for_list'),
    path('api/search-dishes/', restaurant_views.search_dishes_for_list, name='search_dishes_for_list'),
    path('notifications/', restaurant_views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', restaurant_views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/unread-count/', restaurant_views.get_unread_notification_count, name='get_unread_notification_count'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
