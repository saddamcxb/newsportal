from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField
from django.db.models import Q, Count
from django.utils.functional import cached_property
import logging

logger = logging.getLogger(__name__)

class Category(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text="Category name (minimum 2 characters)"
    )
    slug = models.SlugField(
        max_length=100, 
        null=True, 
        blank=True, 
        unique=True, 
        allow_unicode=True,
        help_text="URL-friendly version of the name"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of the category"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Font Awesome icon class (e.g., 'fas fa-news')"
    )
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="SEO meta title"
    )
    meta_description = models.TextField(
        blank=True,
        max_length=320,
        help_text="SEO meta description"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show on homepage"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('news:news_list_by_category', args=[self.slug])
    
    def news_count(self):
        """Get count of published news in this category"""
        return self.news.filter(status=News.Status.PUBLISHED).count()
    
    @cached_property
    def latest_news(self):
        """Get latest 5 news in this category"""
        return self.news.filter(status=News.Status.PUBLISHED)[:5]


class News(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
        FEATURED = 'featured', 'Featured'
    
    class NewsType(models.TextChoices):
        GENERAL = 'general', 'General'
        BREAKING = 'breaking', 'Breaking News'
        EXCLUSIVE = 'exclusive', 'Exclusive'
        INTERVIEW = 'interview', 'Interview'
        OPINION = 'opinion', 'Opinion'
    
    # Core fields
    title = models.CharField(
        max_length=250,
        validators=[MinLengthValidator(10)],
        help_text="News title (minimum 10 characters)"
    )
    slug = models.SlugField(
        max_length=250, 
        unique_for_date='publish', 
        allow_unicode=True,
        help_text="URL-friendly title"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_posts'
    )
    
    # Content fields
    body = RichTextField(
        config_name='default',
        help_text="Main news content with rich formatting"
    )
    summary = models.TextField(
        max_length=500,
        blank=True,
        help_text="Brief summary for preview (max 500 characters)"
    )
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news'
    )
    tags = TaggableManager(
        blank=True,
        help_text="Add tags for better searchability"
    )
    news_type = models.CharField(
        max_length=20,
        choices=NewsType.choices,
        default=NewsType.GENERAL
    )
    
    # Media
    image = models.ImageField(
        upload_to='news_images/%Y/%m/%d/',
        blank=True,
        help_text="Main article image"
    )
    image_caption = models.CharField(
        max_length=300,
        blank=True,
        help_text="Caption for the main image"
    )
    image_alt_text = models.CharField(
        max_length=125,
        blank=True,
        help_text="SEO-friendly image description"
    )
    
    # Metadata
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Statistics
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(
        default=0,
        help_text="Unique visitor count"
    )
    shares = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(
        default=1,
        help_text="Estimated reading time in minutes"
    )
    
    # SEO fields
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Override default title for SEO"
    )
    meta_description = models.TextField(
        max_length=320,
        blank=True,
        help_text="Meta description for search engines"
    )
    meta_keywords = models.CharField(
        max_length=300,
        blank=True,
        help_text="Comma-separated keywords"
    )
    
    # Featured and sticky options
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature on homepage"
    )
    is_sticky = models.BooleanField(
        default=False,
        help_text="Stick to top in category"
    )
    sticky_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to remove sticky status"
    )
    
    # Social sharing
    og_image = models.ImageField(
        upload_to='news_og_images/',
        blank=True,
        help_text="Custom Open Graph image for social sharing"
    )
    twitter_image = models.ImageField(
        upload_to='news_twitter_images/',
        blank=True,
        help_text="Custom Twitter card image"
    )
    
    # Related content
    related_news = models.ManyToManyField(
        'self',
        blank=True,
        help_text="Manually related articles"
    )
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_news'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "News"
        ordering = ('-publish',)
        indexes = [
            models.Index(fields=['-publish', 'status']),
            models.Index(fields=['slug', 'publish']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', '-publish']),
        ]
        permissions = [
            ("can_publish_news", "Can publish news"),
            ("can_feature_news", "Can feature news"),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        
        # Auto-generate summary if not provided
        if not self.summary and self.body:
            # Strip HTML and truncate
            from django.utils.html import strip_tags
            plain_text = strip_tags(self.body)
            self.summary = plain_text[:300] + '...' if len(plain_text) > 300 else plain_text
        
        # Calculate reading time
        if self.body:
            word_count = len(self.body.split())
            self.reading_time = max(1, round(word_count / 200))
        
        # Handle sticky expiry
        if self.sticky_until and self.sticky_until < timezone.now():
            self.is_sticky = False
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('news:news_detail', args=[self.slug])
    
    def get_meta_title(self):
        return self.meta_title or self.title
    
    def get_meta_description(self):
        return self.meta_description or self.summary or self.body[:160]
    
    def increment_views(self, request=None):
        """Increment view count with unique visitor tracking"""
        self.views = models.F('views') + 1
        self.save(update_fields=['views'])
        
        # Track unique views using session or IP
        if request:
            session_key = f'viewed_news_{self.id}'
            if not request.session.get(session_key):
                self.unique_views = models.F('unique_views') + 1
                self.save(update_fields=['unique_views'])
                request.session[session_key] = True
    
    def increment_shares(self, platform=None):
        self.shares = models.F('shares') + 1
        self.save(update_fields=['shares'])
        
        # Log sharing analytics
        logger.info(f"News {self.id} shared on {platform}")
    
    def get_previous_news(self):
        """Get previous published news"""
        return News.objects.filter(
            status=self.Status.PUBLISHED,
            publish__lt=self.publish
        ).order_by('-publish').first()
    
    def get_next_news(self):
        """Get next published news"""
        return News.objects.filter(
            status=self.Status.PUBLISHED,
            publish__gt=self.publish
        ).order_by('publish').first()
    
    def get_related_by_tags(self, limit=5):
        """Get related news based on shared tags"""
        if not self.tags.exists():
            return News.objects.none()
        
        return News.objects.filter(
            status=self.Status.PUBLISHED,
            tags__in=self.tags.all()
        ).exclude(
            id=self.id
        ).distinct().annotate(
            relevance=Count('tags')
        ).order_by('-relevance', '-publish')[:limit]
    
    def get_comments_count(self):
        """Get count of active comments"""
        return self.comments.filter(active=True).count()
    
    @cached_property
    def has_image(self):
        return bool(self.image)
    
    def clean(self):
        """Custom validation"""
        if self.publish and self.publish > timezone.now() + timezone.timedelta(days=30):
            raise ValidationError('Publish date cannot be more than 30 days in the future')


class Comment(models.Model):
    news = models.ForeignKey(
        News, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    name = models.CharField(
        max_length=80,
        validators=[MinLengthValidator(2)]
    )
    email = models.EmailField()
    website = models.URLField(blank=True, help_text="Optional website URL")
    body = models.TextField(
        validators=[MaxLengthValidator(2000)]
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    # Moderation fields
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Spam protection
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    is_spam = models.BooleanField(default=False)
    spam_score = models.FloatField(default=0.0)
    
    # Engagement
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('-created',)
        indexes = [
            models.Index(fields=['news', 'active', '-created']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.news}'
    
    def save(self, *args, **kwargs):
        # Check for spam if new comment
        if not self.pk and not self.is_spam:
            self.check_spam()
        super().save(*args, **kwargs)
    
    def check_spam(self):
        """Basic spam detection"""
        spam_keywords = ['viagra', 'casino', 'lottery', 'prize']
        text_lower = self.body.lower()
        
        # Check for spam keywords
        for keyword in spam_keywords:
            if keyword in text_lower:
                self.is_spam = True
                self.spam_score = 1.0
                break
        
        # Check for excessive links
        import re
        links = re.findall(r'http[s]?://', text_lower)
        if len(links) > 3:
            self.is_spam = True
            self.spam_score = 0.8
    
    def get_replies(self):
        """Get approved replies"""
        return self.replies.filter(active=True, is_approved=True)
    
    def like(self):
        self.likes = models.F('likes') + 1
        self.save(update_fields=['likes'])
    
    def dislike(self):
        self.dislikes = models.F('dislikes') + 1
        self.save(update_fields=['dislikes'])


class NewsView(models.Model):
    """Track individual news views for analytics"""
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name='view_records'
    )
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['news', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"View of {self.news} at {self.viewed_at}"


class NewsBookmark(models.Model):
    """User bookmarks for news articles"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    created = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'news']
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.user} bookmarked {self.news}"