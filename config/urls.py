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
    path('restaurants/', restaurant_views.restaurant_search, name='restaurant_search'),
    path('restaurants/<int:restaurant_id>/', restaurant_views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:restaurant_id>/add-menu/', restaurant_views.add_menu, name='add_menu'),
    path('restaurants/<int:restaurant_id>/menu/', restaurant_views.view_menu, name='view_menu'),
    path('menu-items/<int:menu_item_id>/review/', restaurant_views.add_review, name='add_review'),
    path('create-diary-entry/', post_views.create_diary_entry, name='create_diary_entry'),
    path('profile/', restaurant_views.user_profile, name='user_profile'),
    path('profile/edit/', restaurant_views.edit_profile, name='edit_profile'),
    path('user/<str:username>/', restaurant_views.view_user_profile, name='view_user_profile'),
    path('user/<str:username>/follow/', restaurant_views.follow_user, name='follow_user'),
    path('user/<str:username>/unfollow/', restaurant_views.unfollow_user, name='unfollow_user'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
