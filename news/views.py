from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.db.models import Q, Count, Prefetch
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError
from taggit.models import Tag
from .models import News, Category, Comment, NewsView, NewsBookmark
from .forms import EmailNewsForm, CommentForm, NewsSearchForm
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


def news_list(request, category_slug=None):
    """
    Enhanced news listing view with filtering, caching, and optimized queries
    """
    category = None
    categories = Category.objects.all()
    
    # Get base queryset with optimizations
    news_queryset = News.objects.select_related(
        'author', 'category'
    ).prefetch_related(
        'tags'
    ).filter(
        status=News.Status.PUBLISHED,
        publish__lte=timezone.now()
    )
    
    # Apply category filter
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        news_queryset = news_queryset.filter(category=category)
    
    # Apply sticky posts first
    news_queryset = news_queryset.order_by(
        '-is_sticky', '-publish'
    )
    
    # Pagination
    paginator = Paginator(news_queryset, 9)  # Show 9 news per page
    page_number = request.GET.get('page', 1)
    
    # Try to get from cache for better performance
    cache_key = f'news_list_{category_slug}_{page_number}'
    news = cache.get(cache_key)
    
    if not news:
        try:
            news = paginator.page(page_number)
        except PageNotAnInteger:
            news = paginator.page(1)
        except EmptyPage:
            news = paginator.page(paginator.num_pages)
        
        # Cache for 5 minutes
        cache.set(cache_key, news, 300)
    
    # Get breaking news (with caching)
    breaking_news = cache.get('breaking_news')
    if not breaking_news:
        breaking_news = News.objects.filter(
            status=News.Status.PUBLISHED,
            news_type=News.NewsType.BREAKING,
            publish__lte=timezone.now()
        ).select_related('category')[:5]
        cache.set('breaking_news', breaking_news, 60)  # 1 minute cache
    
    # Get most viewed news (with caching)
    most_viewed_news = cache.get('most_viewed_news')
    if not most_viewed_news:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        most_viewed_news = News.objects.filter(
            status=News.Status.PUBLISHED,
            publish__gte=thirty_days_ago
        ).annotate(
            total_views=Count('view_records')
        ).order_by('-total_views')[:5]
        cache.set('most_viewed_news', most_viewed_news, 3600)  # 1 hour cache
    
    # Get popular tags
    popular_tags = cache.get('popular_tags')
    if not popular_tags:
        popular_tags = Tag.objects.annotate(
            news_count=Count('taggit_taggeditem_items')
        ).filter(news_count__gt=0).order_by('-news_count')[:10]
        cache.set('popular_tags', popular_tags, 3600)
    
    # Get featured categories with counts
    featured_categories = Category.objects.filter(
        is_featured=True
    ).annotate(
        news_count=Count('news', filter=Q(news__status=News.Status.PUBLISHED))
    )[:6]
    
    context = {
        'category': category,
        'categories': categories,
        'featured_categories': featured_categories,
        'breaking_news': breaking_news,
        'news': news,
        'most_viewed_news': most_viewed_news,
        'popular_tags': popular_tags,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': news,
        'paginator': paginator,
    }
    
    return render(request, 'news/news/list.html', context)


@cache_page(60 * 15)  # Cache for 15 minutes
@vary_on_headers('User-Agent')
def news_detail(request, slug):
    """
    Enhanced news detail view with proper comment display
    """
    # Get news with optimized queries
    news = get_object_or_404(
        News.objects.select_related('author', 'category'),
        slug=slug,
        status=News.Status.PUBLISHED,
        publish__lte=timezone.now()
    )
    
    # Increment views
    news.increment_views(request)
    
    # Get comments - only show approved and active comments
    # Also include comments pending approval for the commenter (optional)
    comments = news.comments.filter(
        active=True,
        is_approved=True
    ).select_related('parent').order_by('-created')
    
    # Optional: Show pending comments to the commenter based on session
    # This allows users to see their own pending comments
    if not request.user.is_authenticated:
        # For anonymous users, show their recent pending comment
        recent_comment = Comment.objects.filter(
            news=news,
            ip_address=request.META.get('REMOTE_ADDR'),
            active=False,
            is_approved=False,
            created__gte=timezone.now() - timezone.timedelta(minutes=30)
        ).first()
        if recent_comment:
            comments = comments | Comment.objects.filter(id=recent_comment.id)
    
    # Get categories for sidebar
    categories = Category.objects.annotate(
        news_count=Count('news', filter=Q(news__status=News.Status.PUBLISHED))
    ).filter(news_count__gt=0)[:8]
    
    # Get similar news
    similar_news = News.objects.filter(
        category=news.category,
        status=News.Status.PUBLISHED
    ).exclude(id=news.id)[:4]
    
    # Get popular news
    popular_news = News.objects.filter(
        status=News.Status.PUBLISHED
    ).annotate(
        view_count=Count('view_records')
    ).order_by('-view_count')[:5]
    
    # Initialize comment form
    form = CommentForm()
    
    context = {
        'news': news,
        'comments': comments,
        'form': form,
        'categories': categories,
        'similar_news': similar_news,
        'popular_news': popular_news,
        'comment_count': comments.count(),
    }
    
    return render(request, 'news/news/detail.html', context)


def news_share(request, news_id):
    """
    Share news via email with enhanced validation and feedback
    """
    news = get_object_or_404(
        News,
        id=news_id,
        status=News.Status.PUBLISHED
    )
    sent = False
    form = EmailNewsForm()
    
    if request.method == 'POST':
        form = EmailNewsForm(request.POST)
        if form.is_valid():
            try:
                cd = form.cleaned_data
                news_url = request.build_absolute_uri(news.get_absolute_url())
                
                # Enhanced email template
                subject = f"{cd['name']} recommends you read: {news.title}"
                
                message = f"""
                Hi!
                
                {cd['name']} thinks you might be interested in this article:
                
                {news.title}
                {news_url}
                
                {cd['name']}'s message:
                {cd['comments'] if cd['comments'] else 'No additional comments.'}
                
                ---
                This email was sent via Bangladesh Kantho News Portal.
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [cd['to']],
                    fail_silently=False
                )
                
                # Increment share count
                news.increment_shares(platform='email')
                
                sent = True
                messages.success(request, 'Email sent successfully!')
                
                # Log the share
                logger.info(f"News {news.id} shared via email by {cd['name']}")
                
            except Exception as e:
                logger.error(f"Error sending email: {e}")
                messages.error(request, 'Failed to send email. Please try again.')
    
    context = {
        'news': news,
        'form': form,
        'sent': sent,
    }
    
    return render(request, 'news/news/share.html', context)


@require_POST
def news_comment(request, news_id):
    """
    Add comment with spam protection and moderation
    """
    # Get the news article
    news = get_object_or_404(
        News.objects.select_related('category'),
        id=news_id,
        status=News.Status.PUBLISHED
    )
    
    # Initialize form with POST data
    form = CommentForm(data=request.POST)
    
    if form.is_valid():
        # Create comment without saving to database yet
        comment = form.save(commit=False)
        comment.news = news
        
        # Add metadata for spam detection
        comment.ip_address = request.META.get('REMOTE_ADDR')
        comment.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
        
        # Check if user is authenticated and populate fields
        if request.user.is_authenticated:
            comment.name = request.user.get_full_name() or request.user.username
            comment.email = request.user.email
        
        # Set initial status
        comment.active = False  # Comments need approval by default
        comment.is_approved = False
        comment.created = timezone.now()
        
        # Validate and save
        try:
            # Check for duplicate comments (same name and body within 5 minutes)
            recent_comment = Comment.objects.filter(
                news=news,
                name=comment.name,
                body=comment.body,
                created__gte=timezone.now() - timezone.timedelta(minutes=5)
            ).exists()
            
            if recent_comment:
                messages.warning(request, 'You already posted this comment. Please wait a few minutes before posting again.')
                return redirect(news.get_absolute_url() + '#comments')
            
            # Perform full validation
            comment.full_clean()
            comment.save()
            
            # Log successful comment
            logger.info(f"New comment on news {news.id} by {comment.name} from IP {comment.ip_address}")
            
            # Set success message with helpful info
            messages.success(
                request, 
                'Your comment has been submitted successfully and is pending moderation. '
                'It will appear once approved by our team.'
            )
            
        except ValidationError as e:
            # Handle validation errors
            error_messages = []
            for field, errors in e.message_dict.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, ' '.join(error_messages))
            logger.warning(f"Comment validation failed: {e}")
            
        except Exception as e:
            # Handle unexpected errors
            messages.error(request, 'An error occurred while submitting your comment. Please try again.')
            logger.error(f"Unexpected error saving comment: {e}")
            
    else:
        # Handle form validation errors
        for field, errors in form.errors.items():
            field_label = form.fields[field].label if field in form.fields else field
            for error in errors:
                messages.error(request, f"{field_label}: {error}")
        
        logger.info(f"Invalid comment form for news {news.id}: {form.errors}")
    
    # Redirect back to the news detail page with comments anchor
    return redirect(news.get_absolute_url() + '#comments')


def news_search(request):
    """
    Advanced search with filtering and pagination
    """
    form = NewsSearchForm(request.GET or None)
    results = News.objects.none()
    query = ''
    paginator = None
    page_obj = None
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        category = form.cleaned_data.get('category')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        sort_by = form.cleaned_data.get('sort_by', '-publish')
        
        # Build search queryset
        results = News.objects.select_related(
            'author', 'category'
        ).filter(
            status=News.Status.PUBLISHED,
            publish__lte=timezone.now()
        )
        
        if query:
            results = results.filter(
                Q(title__icontains=query) |
                Q(body__icontains=query) |
                Q(summary__icontains=query) |
                Q(meta_keywords__icontains=query)
            )
        
        if category:
            results = results.filter(category_id=category)
        
        if date_from:
            results = results.filter(publish__date__gte=date_from)
        
        if date_to:
            results = results.filter(publish__date__lte=date_to)
        
        # Apply sorting
        if sort_by:
            results = results.order_by(sort_by)
        
        # Pagination
        paginator = Paginator(results, 10)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Log search for analytics
        if query:
            logger.info(f"Search query: '{query}' returned {paginator.count} results")
    
    # Get popular searches or categories for sidebar
    popular_categories = Category.objects.annotate(
        news_count=Count('news', filter=Q(news__status=News.Status.PUBLISHED))
    ).filter(news_count__gt=0).order_by('-news_count')[:5]
    
    context = {
        'form': form,
        'query': query,
        'results': page_obj if page_obj else results,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1 if paginator else False,
        'page_obj': page_obj,
        'popular_categories': popular_categories,
        'result_count': paginator.count if paginator else 0,
    }
    
    return render(request, 'news/news/search.html', context)


@require_POST
def news_bookmark(request, news_id):
    """
    Toggle bookmark for authenticated users
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    news = get_object_or_404(News, id=news_id, status=News.Status.PUBLISHED)
    
    bookmark, created = NewsBookmark.objects.get_or_create(
        user=request.user,
        news=news
    )
    
    if not created:
        bookmark.delete()
        bookmarked = False
        message = 'Bookmark removed'
    else:
        bookmarked = True
        message = 'Bookmark added'
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'bookmarked': bookmarked,
            'message': message
        })
    
    messages.success(request, message)
    return redirect(news.get_absolute_url())


def news_by_tag(request, tag_slug):
    """
    Display news filtered by tag
    """
    tag = get_object_or_404(Tag, slug=tag_slug)
    
    news_list = News.objects.filter(
        tags__slug=tag_slug,
        status=News.Status.PUBLISHED,
        publish__lte=timezone.now()
    ).select_related('author', 'category').order_by('-publish')
    
    paginator = Paginator(news_list, 9)
    page_number = request.GET.get('page', 1)
    
    try:
        news = paginator.page(page_number)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)
    
    # Get related tags
    related_tags = Tag.objects.filter(
        taggit_taggeditem_items__content_object__in=news_list
    ).annotate(
        count=Count('taggit_taggeditem_items')
    ).order_by('-count')[:10]
    
    context = {
        'tag': tag,
        'news': news,
        'related_tags': related_tags,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': news,
        'paginator': paginator,
    }
    
    return render(request, 'news/news/by_tag.html', context)


def news_archive(request, year, month=None):
    """
    Archive view by date
    """
    # Build date filters
    if month:
        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, month + 1, 1)
        date_title = f"{start_date.strftime('%B')} {year}"
    else:
        start_date = timezone.datetime(year, 1, 1)
        end_date = timezone.datetime(year + 1, 1, 1)
        date_title = f"Year {year}"
    
    news_list = News.objects.filter(
        status=News.Status.PUBLISHED,
        publish__gte=start_date,
        publish__lt=end_date
    ).select_related('author', 'category').order_by('-publish')
    
    # Group by month if yearly view
    if not month:
        months = {}
        for news_item in news_list:
            month_key = news_item.publish.strftime('%Y-%m')
            if month_key not in months:
                months[month_key] = {
                    'name': news_item.publish.strftime('%B %Y'),
                    'count': 0,
                    'first_day': news_item.publish.replace(day=1)
                }
            months[month_key]['count'] += 1
    else:
        months = None
    
    paginator = Paginator(news_list, 15)
    page_number = request.GET.get('page', 1)
    
    try:
        news = paginator.page(page_number)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)
    
    context = {
        'date_title': date_title,
        'year': year,
        'month': month,
        'news': news,
        'months': months,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': news,
        'paginator': paginator,
    }
    
    return render(request, 'news/news/archive.html', context)


@require_POST
def increment_share_count(request, news_id, platform):
    """
    AJAX endpoint to increment share count
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            news = News.objects.get(id=news_id)
            news.increment_shares(platform=platform)
            return JsonResponse({'success': True, 'shares': news.shares})
        except News.DoesNotExist:
            return JsonResponse({'error': 'News not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def news_list_by_category(request, category_slug):
    """
    Simple version - Display news articles filtered by category
    """
    # Get the category
    category = get_object_or_404(Category, slug=category_slug)
    
    # Get all categories for sidebar
    categories = Category.objects.annotate(
        news_count=Count('news', filter=Q(news__status=News.Status.PUBLISHED))
    ).filter(news_count__gt=0)
    
    # Get breaking news
    breaking_news = News.objects.filter(
        status=News.Status.PUBLISHED
    ).order_by('-publish')[:3]
    
    # Get most viewed news
    most_viewed_news = News.objects.filter(
        category=category,
        status=News.Status.PUBLISHED
    ).order_by('-views')[:5]
    
    # Get news for this category
    news_list = News.objects.filter(
        category=category,
        status=News.Status.PUBLISHED,
        publish__lte=timezone.now()
    ).order_by('-publish')
    
    # Pagination
    paginator = Paginator(news_list, 9)
    page_number = request.GET.get('page', 1)
    
    try:
        news = paginator.page(page_number)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'categories': categories,
        'breaking_news': breaking_news,
        'most_viewed_news': most_viewed_news,
        'news': news,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': news,
        'paginator': paginator,
    }
    
    return render(request, 'news/list.html', context)
