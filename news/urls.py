from django.urls import path, re_path
from . import views

app_name = 'news'

urlpatterns = [
    # Home & List Views
    path('', views.news_list, name='news_list'),

     # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # News Management
    path('create-news/', views.create_news, name='create_news'),
    path('edit-news/<int:news_id>/', views.edit_news, name='edit_news'),
    path('delete-news/<int:news_id>/', views.delete_news, name='delete_news'),
    path('my-news/', views.my_news, name='my_news'),
    

    path('search/', views.news_search, name='search'),
    
    # Category & Tag Views
    re_path(r'^category/(?P<category_slug>[\w\u0980-\u09FF-]+)/$', 
            views.news_list, name='news_list_by_category'),
    re_path(r'^tag/(?P<tag_slug>[\w\u0980-\u09FF-]+)/$', 
            views.news_by_tag, 
            name='news_by_tag'),
    
    # Archive Views
    path('archive/<int:year>/', views.news_archive, name='news_archive_year'),
    path('archive/<int:year>/<int:month>/', views.news_archive, name='news_archive_month'),
    
    # Detail & Interaction Views
    path('<str:slug>/', views.news_detail, name='news_detail'), 
    path('<int:news_id>/share/', views.news_share, name='news_share'),
    path('<int:news_id>/comment/', views.news_comment, name='news_comment'),
    path('<int:news_id>/bookmark/', views.news_bookmark, name='news_bookmark'),
    
    # AJAX Endpoints
    path('<int:news_id>/share-count/<str:platform>/', 
         views.increment_share_count, name='increment_share_count'),
    
    # Breaking News (optional)
    path('breaking/', views.news_list, {'news_type': 'breaking'}, name='breaking_news'),
    
    # Featured News (optional)
    path('featured/', views.news_list, {'featured_only': True}, name='featured_news'),
    path('api/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('api/trending/', views.search_trending, name='search_trending'),
    path('api/instant-results/', views.search_instant_results, name='search_instant_results'),
]
