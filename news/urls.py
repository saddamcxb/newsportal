from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # Frontend URLs
    path('', views.home, name='home'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('category/<slug:slug>/', views.category_news, name='category_news'),
    path('all-news/', views.all_news, name='all_news'),
    path('search/', views.search_news, name='search'),
    path('contact/', views.contact, name='contact'),
    path('newsletter/', views.newsletter_subscribe, name='newsletter'),
    
    # Authentication URLs
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # News Management URLs
    path('news/create/', views.news_create, name='news_create'),
    path('news/manage/', views.news_manage, name='news_manage'),
    path('news/edit/<int:pk>/', views.news_edit, name='news_edit'),
    path('news/delete/<int:pk>/', views.news_delete, name='news_delete'),
    
    # AJAX URLs
    path('like/<int:pk>/', views.like_news, name='like_news'),
]