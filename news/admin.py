# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from .models import User, Category, News, Comment, NewsView, NewsBookmark
from django.db import models

# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin interface for User model"""
    
    list_display = ('username', 'email', 'get_full_name', 'is_author', 'is_editor', 
                   'is_staff', 'is_active', 'date_joined', 'profile_thumbnail')
    list_filter = ('is_author', 'is_editor', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('phone', 'bio', 'profile_picture', 'is_author', 'is_editor', 'last_active'),
            'classes': ('wide',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'bio', 'profile_picture', 'is_author', 'is_editor'),
            'classes': ('wide',)
        }),
    )
    
    readonly_fields = ('date_joined', 'last_active', 'profile_thumbnail')
    
    actions = ['make_author', 'make_editor', 'remove_author', 'remove_editor', 'activate_users', 'deactivate_users']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def profile_thumbnail(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />', 
                             obj.profile_picture.url)
        return format_html('<div style="width: 50px; height: 50px; background: #6c757d; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;">{}</div>', 
                         obj.username[0].upper())
    profile_thumbnail.short_description = 'Profile'
    
    def make_author(self, request, queryset):
        updated = queryset.update(is_author=True)
        self.message_user(request, f'{updated} users have been granted author status.')
    make_author.short_description = "Grant author status"
    
    def remove_author(self, request, queryset):
        updated = queryset.update(is_author=False)
        self.message_user(request, f'{updated} users have had author status removed.')
    remove_author.short_description = "Remove author status"
    
    def make_editor(self, request, queryset):
        updated = queryset.update(is_editor=True)
        self.message_user(request, f'{updated} users have been granted editor status.')
    make_editor.short_description = "Grant editor status"
    
    def remove_editor(self, request, queryset):
        updated = queryset.update(is_editor=False)
        self.message_user(request, f'{updated} users have had editor status removed.')
    remove_editor.short_description = "Remove editor status"
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users have been activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users have been deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(news_count=Count('news_posts'))


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin interface"""
    
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
    
    actions = ['make_featured', 'remove_featured']
    
    def news_count(self, obj):
        count = obj.news.filter(status=News.Status.PUBLISHED).count()
        url = reverse('admin:news_news_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    news_count.short_description = 'Published News'
    news_count.admin_order_field = 'news_count'
    
    def status_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 4px;">★ Featured</span>')
        return format_html('<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 4px;">Regular</span>')
    status_badge.short_description = 'Status'
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} categories marked as featured.")
    make_featured.short_description = "Mark selected as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} categories removed from featured.")
    remove_featured.short_description = "Remove featured from selected"
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(news_count=Count('news', filter=models.Q(news__status=News.Status.PUBLISHED)))


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """News admin interface"""
    
    list_display = ('title_preview', 'author_link', 'category_badge', 'publish_date', 
                   'status_badge', 'views_count', 'comments_count', 'featured_badge')
    list_filter = ('status', 'news_type', 'is_featured', 'is_sticky', 'is_approved', 'category')
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
        ('Statistics', {
            'fields': ('views', 'unique_views', 'shares', 'reading_time'),
            'classes': ('collapse',)
        }),
        ('Moderation', {
            'fields': ('is_approved', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created', 'updated')
    
    actions = ['make_published', 'make_draft', 'make_featured', 'make_sticky', 
               'approve_news', 'reset_views']
    
    def title_preview(self, obj):
        return format_html(
            '<a href="{}" target="_blank"><strong>{}</strong></a>',
            obj.get_absolute_url(),
            obj.title[:70] + ('...' if len(obj.title) > 70 else '')
        )
    title_preview.short_description = 'Title'
    title_preview.admin_order_field = 'title'
    
    def author_link(self, obj):
        if obj.author:
            url = reverse('admin:news_user_change', args=[obj.author.id])
            return format_html('<a href="{}">{}</a>', url, obj.author.get_full_name() or obj.author.username)
        return "-"
    author_link.short_description = 'Author'
    
    def category_badge(self, obj):
        if obj.category:
            url = reverse('admin:news_category_change', args=[obj.category.id])
            return format_html('<a href="{}"><span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px;">{}</span></a>', 
                             url, obj.category.name)
        return "-"
    category_badge.short_description = 'Category'
    
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
    
    def featured_badge(self, obj):
        badges = []
        if obj.is_featured:
            badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; margin-right: 2px;">★ Featured</span>')
        if obj.is_sticky:
            badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px;">📌 Sticky</span>')
        return format_html(' '.join(badges)) if badges else '-'
    featured_badge.short_description = 'Featured/Sticky'
    
    def views_count(self, obj):
        return format_html(
            '<span title="Unique: {}">{}</span>',
            obj.unique_views,
            obj.views
        )
    views_count.short_description = 'Views'
    views_count.admin_order_field = 'views'
    
    def comments_count(self, obj):
        count = obj.comments.filter(active=True).count()
        url = reverse('admin:news_comment_changelist') + f'?news__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    comments_count.short_description = 'Comments'
    
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
        self.message_user(request, f"{updated} news articles marked as sticky for 7 days.")
    make_sticky.short_description = "Mark selected as sticky for 7 days"
    
    def approve_news(self, request, queryset):
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} news articles approved.")
    approve_news.short_description = "Approve selected news"
    
    def reset_views(self, request, queryset):
        updated = queryset.update(views=0, unique_views=0)
        self.message_user(request, f"{updated} news articles view count reset.")
    reset_views.short_description = "Reset view counts"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment admin interface"""
    
    list_display = ('comment_preview', 'name_email', 'news_link', 'created_date', 
                   'status_badge', 'spam_score_display')
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
    
    def comment_preview(self, obj):
        return obj.body[:75] + ('...' if len(obj.body) > 75 else '')
    comment_preview.short_description = 'Comment'
    
    def name_email(self, obj):
        return format_html('<strong>{}</strong><br><small>{}</small>', obj.name, obj.email)
    name_email.short_description = 'Commenter'
    
    def news_link(self, obj):
        url = reverse('admin:news_news_change', args=[obj.news.id])
        return format_html('<a href="{}">{}</a>', url, obj.news.title[:50] + '...')
    news_link.short_description = 'News Article'
    
    def created_date(self, obj):
        if obj.created > timezone.now() - timezone.timedelta(days=1):
            return format_html('<span style="color: #28a745;">{}</span>', 
                             obj.created.strftime('%Y-%m-%d %H:%M'))
        return obj.created.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Created'
    
    def status_badge(self, obj):
        if obj.is_spam:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px;">🚫 Spam</span>')
        elif not obj.active:
            return format_html('<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">Inactive</span>')
        elif obj.is_approved:
            return format_html('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">✓ Approved</span>')
        else:
            return format_html('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px;">⏳ Pending</span>')
    status_badge.short_description = 'Status'
    
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
        self.message_user(request, f"{count} comments deleted.")
    delete_comments.short_description = "Delete selected comments"


@admin.register(NewsView)
class NewsViewAdmin(admin.ModelAdmin):
    """News view tracking admin"""
    
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
    """Bookmark admin interface"""
    
    list_display = ('user', 'news_title', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'news__title', 'notes')
    date_hierarchy = 'created'
    
    def news_title(self, obj):
        return obj.news.title
    news_title.short_description = 'News Article'