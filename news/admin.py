# news/admin.py - সরলীকৃত ভার্সন
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Category, News, Like, Comment, UserProfile, NewsletterSubscriber, ContactMessage

# সরলীকৃত ক্লাস - কোন related field নেই
class SimpleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class SimpleNewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'views', 'published_date']
    list_filter = ['status', 'category']
    search_fields = ['title']

class SimpleUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['username', 'email']

# Register
try:
    admin.site.unregister(User)
except:
    pass
admin.site.register(User, SimpleUserAdmin)
admin.site.register(Category, SimpleCategoryAdmin)
admin.site.register(News, SimpleNewsAdmin)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(UserProfile)
admin.site.register(NewsletterSubscriber)
admin.site.register(ContactMessage)

admin.site.site_header = "নিউজপোর্টাল অ্যাডমিন"