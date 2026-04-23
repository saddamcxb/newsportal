from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils.text import slugify
from .models import Category, News, Like, Comment, UserProfile, NewsletterSubscriber, ContactMessage
from .forms import (
    UserRegistrationForm, UserProfileForm, UserUpdateForm, 
    NewsForm, CommentForm, ContactForm
)

def home(request):
    categories = Category.objects.all()
    featured_news = News.objects.filter(status='published', is_featured=True).order_by('-published_date')[:5]
    breaking_news = News.objects.filter(status='published', is_breaking=True).order_by('-published_date')[:5]
    latest_news = News.objects.filter(status='published').order_by('-published_date')[:6]
    popular_news = News.objects.filter(status='published').order_by('-views')[:5]
    
    context = {
        'categories': categories,
        'featured_news': featured_news,
        'breaking_news': breaking_news,
        'latest_news': latest_news,
        'popular_news': popular_news,
    }
    return render(request, 'news/home.html', context)

def news_detail(request, slug):
    news = get_object_or_404(News, slug=slug, status='published')
    news.views += 1
    news.save()
    
    user_liked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, news=news).exists()
    
    comments = news.comments.filter(is_approved=True)
    related_news = News.objects.filter(category=news.category, status='published').exclude(id=news.id)[:3]
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.news = news
            comment.save()
            messages.success(request, 'আপনার মন্তব্য যোগ করা হয়েছে!')
            return redirect('news:news_detail', slug=news.slug)
    else:
        form = CommentForm()
    
    context = {
        'news': news,
        'user_liked': user_liked,
        'comments': comments,
        'related_news': related_news,
        'form': form,
    }
    return render(request, 'news/news_detail.html', context)

@login_required
def like_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, news=news)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'total_likes': news.total_likes()})

def category_news(request, slug):
    category = get_object_or_404(Category, slug=slug)
    news_list = News.objects.filter(category=category, status='published').order_by('-published_date')
    paginator = Paginator(news_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'news/category_news.html', {'category': category, 'page_obj': page_obj})

def search_news(request):
    query = request.GET.get('q', '')
    if query:
        news_list = News.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(category__name__icontains=query),
            status='published'
        ).distinct().order_by('-published_date')
    else:
        news_list = News.objects.none()
    
    paginator = Paginator(news_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'news/search.html', {'query': query, 'page_obj': page_obj})

def all_news(request):
    news_list = News.objects.filter(status='published').order_by('-published_date')
    paginator = Paginator(news_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'news/all_news.html', {'page_obj': page_obj})

# Authentication Views
def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'আপনার অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে!')
            return redirect('news:home')
        else:
            messages.error(request, 'দয়া করে সঠিক তথ্য দিন।')
    else:
        form = UserRegistrationForm()
    return render(request, 'news/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'স্বাগতম {username}!')
            return redirect('news:home')
        else:
            messages.error(request, 'ইউজারনেম বা পাসওয়ার্ড ভুল!')
    return render(request, 'news/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'আপনি লগআউট করেছেন।')
    return redirect('news:home')

# Profile Views
@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_news = News.objects.filter(author=request.user).order_by('-published_date')[:5]
    total_news = News.objects.filter(author=request.user).count()
    total_likes = Like.objects.filter(news__author=request.user).count()
    total_comments = Comment.objects.filter(user=request.user).count()
    
    context = {
        'profile': profile,
        'user_news': user_news,
        'total_news': total_news,
        'total_likes': total_likes,
        'total_comments': total_comments,
    }
    return render(request, 'news/profile.html', context)

@login_required
def profile_edit(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'প্রোফাইল আপডেট করা হয়েছে!')
            return redirect('news:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'news/profile_edit.html', context)

# News Management Views
@login_required
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.slug = slugify(news.title)
            news.save()
            messages.success(request, 'নিউজ সফলভাবে তৈরি করা হয়েছে!')
            return redirect('news:news_manage')
    else:
        form = NewsForm()
    
    return render(request, 'news/news_create.html', {'form': form})

@login_required
def news_manage(request):
    news_list = News.objects.filter(author=request.user).order_by('-published_date')
    paginator = Paginator(news_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'news/news_manage.html', {'page_obj': page_obj})

@login_required
def news_edit(request, pk):
    news = get_object_or_404(News, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            news = form.save(commit=False)
            if not news.slug:
                news.slug = slugify(news.title)
            news.save()
            messages.success(request, 'নিউজ আপডেট করা হয়েছে!')
            return redirect('news:news_manage')
    else:
        form = NewsForm(instance=news)
    
    return render(request, 'news/news_edit.html', {'form': form, 'news': news})

@login_required
def news_delete(request, pk):
    news = get_object_or_404(News, pk=pk, author=request.user)
    if request.method == 'POST':
        news.delete()
        messages.success(request, 'নিউজ ডিলিট করা হয়েছে!')
        return redirect('news:news_manage')
    return render(request, 'news/news_delete.html', {'news': news})

# Contact View
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'আপনার বার্তা পাঠানো হয়েছে!')
            return redirect('news:contact')
    else:
        form = ContactForm()
    return render(request, 'news/contact.html', {'form': form})

def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                messages.success(request, 'নিউজলেটারে সাবস্ক্রাইব করেছেন!')
            else:
                messages.info(request, 'আপনি ইতিমধ্যে সাবস্ক্রাইব করেছেন!')
        return redirect('news:home')
    return redirect('news:home')

@login_required
def dashboard(request):
    total_news = News.objects.filter(author=request.user).count()
    published_news = News.objects.filter(author=request.user, status='published').count()
    draft_news = News.objects.filter(author=request.user, status='draft').count()
    total_views = News.objects.filter(author=request.user).aggregate(Sum('views'))['views__sum'] or 0
    total_likes = Like.objects.filter(news__author=request.user).count()
    recent_comments = Comment.objects.filter(news__author=request.user)[:5]
    
    context = {
        'total_news': total_news,
        'published_news': published_news,
        'draft_news': draft_news,
        'total_views': total_views,
        'total_likes': total_likes,
        'recent_comments': recent_comments,
    }
    return render(request, 'news/dashboard.html', context)

