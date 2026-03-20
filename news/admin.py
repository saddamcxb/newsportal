from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.db.models import Count, Sum
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import News, Category, Comment, NewsView, NewsBookmark
import csv
from django.http import HttpResponse
from django.db import models

# Custom filters
class PublishDateFilter(SimpleListFilter):
    title = 'publish period'
    parameter_name = 'publish_period'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('this_week', 'This week'),
            ('this_month', 'This month'),
            ('last_month', 'Last month'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(publish__date=timezone.now().date())
        if self.value() == 'this_week':
            week_ago = timezone.now() - timezone.timedelta(days=7)
            return queryset.filter(publish__gte=week_ago)
        if self.value() == 'this_month':
            month_ago = timezone.now() - timezone.timedelta(days=30)
            return queryset.filter(publish__gte=month_ago)
        if self.value() == 'last_month':
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            sixty_days_ago = timezone.now() - timezone.timedelta(days=60)
            return queryset.filter(publish__range=[sixty_days_ago, thirty_days_ago])


class PopularNewsFilter(SimpleListFilter):
    title = 'popularity'
    parameter_name = 'popularity'

    def lookups(self, request, model_admin):
        return (
            ('high', 'High Views (>1000)'),
            ('medium', 'Medium Views (500-1000)'),
            ('low', 'Low Views (<500)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(views__gte=1000)
        if self.value() == 'medium':
            return queryset.filter(views__gte=500, views__lt=1000)
        if self.value() == 'low':
            return queryset.filter(views__lt=500)


# Inline admins
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('name', 'email', 'body', 'active', 'created')
    readonly_fields = ('name', 'email', 'body', 'created')
    can_delete = True
    show_change_link = True


class NewsViewInline(admin.TabularInline):
    model = NewsView
    extra = 0
    fields = ('ip_address', 'user', 'viewed_at')
    readonly_fields = ('ip_address', 'user', 'viewed_at')
    can_delete = False
    max_num = 10


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'news_count', 'is_featured', 'order', 'status_badge')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_featured')
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'order'),
            'classes': ('wide',)
        }),
    )
    
    actions = ['make_featured', 'remove_featured', 'export_categories']
    
    def news_count(self, obj):
        count = obj.news.filter(status=News.Status.PUBLISHED).count()
        url = reverse('admin:news_news_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    news_count.short_description = 'Published News'
    news_count.admin_order_field = 'news_count'
    
    def status_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 4px;">Featured</span>',)
        return format_html('<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 4px;">Regular</span>',)
    status_badge.short_description = 'Status'
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} categories marked as featured.")
    make_featured.short_description = "Mark selected as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} categories removed from featured.")
    remove_featured.short_description = "Remove featured from selected"
    
    def export_categories(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="categories.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Slug', 'Description', 'News Count'])
        
        for category in queryset:
            writer.writerow([
                category.name,
                category.slug,
                category.description,
                category.news_set.count()
            ])
        
        return response
    export_categories.short_description = "Export selected to CSV"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(news_count=Count('news'))


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title_preview', 'author_link', 'category_badge', 'publish_date', 
                   'status_badge', 'views_count', 'shares_count', 'comments_count', 'featured_badge')
    list_filter = (
        'status',
        'news_type',
        'is_featured',
        'is_sticky',
        'is_approved',
        'category',
        PublishDateFilter,
        PopularNewsFilter,
        'author',
    )
    search_fields = ('title', 'body', 'summary', 'meta_keywords')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author', 'approved_by', 'related_news')
    date_hierarchy = 'publish'
    ordering = ('-publish', '-is_sticky', '-is_featured')
    list_per_page = 50
    save_on_top = True
    list_select_related = ('author', 'category')
    
    fieldsets = (
        ('Main Content', {
            'fields': ('title', 'slug', 'author', 'category', 'body', 'summary'),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('image', 'image_caption', 'image_alt_text', 'og_image', 'twitter_image'),
            'classes': ('collapse',)
        }),
        ('Categorization', {
            'fields': ('tags', 'news_type', 'related_news'),
            'classes': ('collapse',)
        }),
        ('Publication Settings', {
            'fields': ('status', 'publish', 'is_featured', 'is_sticky', 'sticky_until'),
            'classes': ('wide',)
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Moderation', {
            'fields': ('is_approved', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CommentInline, NewsViewInline]
    
    actions = ['make_published', 'make_draft', 'make_featured', 'make_sticky', 
               'approve_news', 'export_news', 'bulk_update_category']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            comments_count=Count('comments', filter=models.Q(comments__active=True))
        )
    
    def title_preview(self, obj):
        return format_html(
            '<a href="{}" target="_blank"><strong>{}</strong></a>',
            obj.get_absolute_url(),
            obj.title[:50] + ('...' if len(obj.title) > 50 else '')
        )
    title_preview.short_description = 'Title'
    title_preview.admin_order_field = 'title'
    
    def author_link(self, obj):
        if obj.author:
            url = reverse('admin:auth_user_change', args=[obj.author.id])
            return format_html('<a href="{}">{}</a>', url, obj.author.get_full_name() or obj.author.username)
        return "-"
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author'
    
    def category_badge(self, obj):
        if obj.category:
            url = reverse('admin:news_category_change', args=[obj.category.id])
            return format_html('<a href="{}"><span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px;">{}</span></a>', 
                             url, obj.category.name)
        return "-"
    category_badge.short_description = 'Category'
    category_badge.admin_order_field = 'category'
    
    def publish_date(self, obj):
        if obj.publish > timezone.now():
            return format_html('<span style="color: #28a745;">{}</span>', obj.publish.strftime('%Y-%m-%d %H:%M'))
        return obj.publish.strftime('%Y-%m-%d %H:%M')
    publish_date.short_description = 'Publish Date'
    publish_date.admin_order_field = 'publish'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'archived': '#dc3545',
            'featured': '#ffc107'
        }
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            'white' if obj.status != 'featured' else 'black',
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def featured_badge(self, obj):
        badges = []
        if obj.is_featured:
            badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; margin-right: 2px;">Featured</span>')
        if obj.is_sticky:
            badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px;">Sticky</span>')
        return mark_safe(' '.join(badges)) if badges else '-'
    featured_badge.short_description = 'Featured/Sticky'
    
    def views_count(self, obj):
        return format_html(
            '<span title="Unique: {}">{}</span>',
            obj.unique_views,
            obj.views
        )
    views_count.short_description = 'Views'
    views_count.admin_order_field = 'views'
    
    def shares_count(self, obj):
        return obj.shares
    shares_count.short_description = 'Shares'
    shares_count.admin_order_field = 'shares'
    
    def comments_count(self, obj):
        count = getattr(obj, 'comments_count', 0)
        url = reverse('admin:news_comment_changelist') + f'?news__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    comments_count.short_description = 'Comments'
    comments_count.admin_order_field = 'comments_count'
    
    # Actions
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f"{updated} news articles marked as published.")
    make_published.short_description = "Mark selected as published"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} news articles marked as draft.")
    make_draft.short_description = "Mark selected as draft"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} news articles marked as featured.")
    make_featured.short_description = "Mark selected as featured"
    
    def make_sticky(self, request, queryset):
        updated = queryset.update(is_sticky=True, sticky_until=timezone.now() + timezone.timedelta(days=7))
        self.message_user(request, f"{updated} news articles marked as sticky (7 days).")
    make_sticky.short_description = "Mark selected as sticky for 7 days"
    
    def approve_news(self, request, queryset):
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} news articles approved.")
    approve_news.short_description = "Approve selected news"
    
    def export_news(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="news_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Author', 'Category', 'Status', 'Views', 'Shares', 'Comments', 'Publish Date'])
        
        for news in queryset:
            writer.writerow([
                news.title,
                str(news.author),
                str(news.category),
                news.get_status_display(),
                news.views,
                news.shares,
                news.comments.count(),
                news.publish.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_news.short_description = "Export selected to CSV"
    
    def bulk_update_category(self, request, queryset):
        if 'apply' in request.POST:
            category_id = request.POST.get('new_category')
            if category_id:
                updated = queryset.update(category_id=category_id)
                self.message_user(request, f"{updated} news articles moved to new category.")
                return HttpResponseRedirect(request.get_full_path())
        
        # Show intermediate page with category selection
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'admin/bulk_update_category.html', {
            'news': queryset,
            'categories': Category.objects.all(),
            'action': 'bulk_update_category',
        })
    bulk_update_category.short_description = "Bulk update category"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_preview', 'name_email', 'news_link', 'created_date', 
                   'status_badge', 'likes_count', 'spam_score_display')
    list_filter = ('active', 'is_approved', 'is_spam', 'created', 'news__category')
    search_fields = ('name', 'email', 'body', 'website')
    list_per_page = 50
    date_hierarchy = 'created'
    raw_id_fields = ('news', 'parent', 'approved_by')
    readonly_fields = ('ip_address', 'user_agent', 'likes', 'dislikes', 'spam_score')
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('news', 'parent', 'name', 'email', 'website', 'body')
        }),
        ('Moderation', {
            'fields': ('active', 'is_approved', 'is_spam', 'spam_score', 'approved_by', 'approved_at'),
            'classes': ('wide',)
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'likes', 'dislikes'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_comments', 'mark_as_spam', 'unmark_spam', 'delete_comments']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('news')
    
    def comment_preview(self, obj):
        return obj.body[:75] + ('...' if len(obj.body) > 75 else '')
    comment_preview.short_description = 'Comment'
    
    def name_email(self, obj):
        return format_html('<strong>{}</strong><br><small>{}</small>', obj.name, obj.email)
    name_email.short_description = 'Commenter'
    
    def news_link(self, obj):
        url = reverse('admin:news_news_change', args=[obj.news.id])
        return format_html('<a href="{}">{}</a>', url, obj.news.title[:30] + '...')
    news_link.short_description = 'News Article'
    
    def created_date(self, obj):
        if obj.created > timezone.now() - timezone.timedelta(days=1):
            return format_html('<span style="color: #28a745;">{}</span>', 
                             obj.created.strftime('%Y-%m-%d %H:%M'))
        return obj.created.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Created'
    
    def status_badge(self, obj):
        badges = []
        if obj.is_spam:
            badges.append('<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px;">Spam</span>')
        elif not obj.active:
            badges.append('<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">Inactive</span>')
        elif obj.is_approved:
            badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">Approved</span>')
        else:
            badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px;">Pending</span>')
        
        return mark_safe(' '.join(badges)) if badges else '-'
    status_badge.short_description = 'Status'
    
    def likes_count(self, obj):
        return format_html('<span style="color: #28a745;">👍 {}</span> <span style="color: #dc3545;">👎 {}</span>', 
                         obj.likes, obj.dislikes)
    likes_count.short_description = 'Likes/Dislikes'
    
    def spam_score_display(self, obj):
        if obj.spam_score > 0:
            color = '#dc3545' if obj.spam_score > 0.7 else '#ffc107'
            return format_html('<span style="color: {};">{:.0%}</span>', color, obj.spam_score)
        return '-'
    spam_score_display.short_description = 'Spam Score'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True, active=True)
        self.message_user(request, f"{updated} comments approved.")
    approve_comments.short_description = "Approve selected comments"
    
    def mark_as_spam(self, request, queryset):
        updated = queryset.update(is_spam=True, active=False, spam_score=1.0)
        self.message_user(request, f"{updated} comments marked as spam.")
    mark_as_spam.short_description = "Mark selected as spam"
    
    def unmark_spam(self, request, queryset):
        updated = queryset.update(is_spam=False, spam_score=0.0)
        self.message_user(request, f"{updated} comments unmarked as spam.")
    unmark_spam.short_description = "Unmark selected as spam"
    
    def delete_comments(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} comments deleted.", messages.WARNING)
    delete_comments.short_description = "Delete selected comments"


@admin.register(NewsView)
class NewsViewAdmin(admin.ModelAdmin):
    list_display = ('news_title', 'ip_address', 'user', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('news__title', 'ip_address', 'user__username')
    date_hierarchy = 'viewed_at'
    readonly_fields = ('news', 'ip_address', 'user', 'session_key', 'user_agent', 'viewed_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def news_title(self, obj):
        return obj.news.title
    news_title.short_description = 'News Article'
    news_title.admin_order_field = 'news__title'


@admin.register(NewsBookmark)
class NewsBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'news_title', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'news__title', 'notes')
    date_hierarchy = 'created'
    
    def news_title(self, obj):
        return obj.news.title
    news_title.short_description = 'News Article'