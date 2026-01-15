from django.contrib import admin
from .models import Restaurant, Menu, MenuItem, Review, Profile, Follow, ReviewLike, RestaurantList, Comment, CustomList, CustomListItem, HappyHour, Notification

admin.site.register(Restaurant)
admin.site.register(Menu)
admin.site.register(MenuItem)
admin.site.register(Review)
admin.site.register(Profile)
admin.site.register(Follow)
admin.site.register(ReviewLike)
admin.site.register(RestaurantList)
admin.site.register(Comment)
admin.site.register(CustomList)
admin.site.register(CustomListItem)
admin.site.register(HappyHour)
admin.site.register(Notification)
