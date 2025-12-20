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
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', restaurant_views.root_redirect, name='root'),
    path('feed/', restaurant_views.feed, name='feed'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('signup/', restaurant_views.signup, name='signup'),
    path('restaurants/', restaurant_views.restaurant_search, name='restaurant_search'),
    path('restaurants/<int:restaurant_id>/', restaurant_views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:restaurant_id>/add-menu/', restaurant_views.add_menu, name='add_menu'),
    path('restaurants/<int:restaurant_id>/menu/', restaurant_views.view_menu, name='view_menu'),
    path('menu-items/<int:menu_item_id>/review/', restaurant_views.add_review, name='add_review'),
]
