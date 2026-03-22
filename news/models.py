# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, MaxLengthValidator
from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField
from django.db.models import Q, Count

# Custom User Model
class User(AbstractUser):
    """Custom User model with additional fields"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    is_author = models.BooleanField(default=False)  # Can write news
    is_editor = models.BooleanField(default=False)  # Can approve/reject
    date_joined = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        permissions = [
            ("can_publish_news", "Can publish news"),
            ("can_edit_news", "Can edit news"),
            ("can_delete_news", "Can delete news"),
            ("can_approve_comments", "Can approve comments"),
        ]
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


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
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True, max_length=320)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('news:news_list_by_category', args=[self.slug])


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
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL instead of importing User
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_posts'
    )
    
    # Content fields
    body = RichTextField(config_name='default', help_text="Main news content with rich formatting")
    summary = models.TextField(max_length=500, blank=True, help_text="Brief summary for preview")
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news'
    )
    tags = TaggableManager(blank=True, help_text="Add tags for better searchability")
    news_type = models.CharField(max_length=20, choices=NewsType.choices, default=NewsType.GENERAL)
    
    # Media
    image = models.ImageField(upload_to='news_images/%Y/%m/%d/', blank=True)
    image_caption = models.CharField(max_length=300, blank=True)
    image_alt_text = models.CharField(max_length=125, blank=True)
    og_image = models.ImageField(upload_to='news_og_images/', blank=True)
    twitter_image = models.ImageField(upload_to='news_twitter_images/', blank=True)
    
    # Metadata
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    
    # Statistics
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=1)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)
    
    # Featured and sticky options
    is_featured = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False)
    sticky_until = models.DateTimeField(null=True, blank=True)
    
    # Related content
    related_news = models.ManyToManyField('self', blank=True)
    
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
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        
        if not self.summary and self.body:
            from django.utils.html import strip_tags
            plain_text = strip_tags(self.body)
            self.summary = plain_text[:300] + '...' if len(plain_text) > 300 else plain_text
        
        if self.body:
            word_count = len(self.body.split())
            self.reading_time = max(1, round(word_count / 200))
        
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
        from django.db.models import F
        News.objects.filter(id=self.id).update(views=F('views') + 1)
        self.refresh_from_db()


class Comment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    name = models.CharField(max_length=80, validators=[MinLengthValidator(2)])
    email = models.EmailField()
    website = models.URLField(blank=True)
    body = models.TextField(validators=[MaxLengthValidator(2000)])
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


class NewsView(models.Model):
    """Track individual news views for analytics"""
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='view_records')
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True, null=True)
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
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='bookmarks')
    created = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'news']
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.user} bookmarked {self.news}"