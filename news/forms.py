from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Comment

# forms.py - Add these forms
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import User, News, Comment

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    """Custom user registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'example@email.com'
        })
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Last Name'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm Password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    """Custom login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Email or Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password'
        })
    )
    
    class Meta:
        fields = ['username', 'password']


class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'bio', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class NewsForm(forms.ModelForm):
    """Form for creating/editing news"""
    class Meta:
        model = News
        fields = ['title', 'category', 'body', 'summary', 'image', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter news title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Write your news content here...'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief summary of the news'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma separated tags'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('draft', 'Draft'), ('published', 'Published')]


class EmailNewsForm(forms.Form):
    """Modernized email sharing form with enhanced validation and styling"""
    
    name = forms.CharField(
        max_length=25,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
            'placeholder': 'আপনার নাম',
            'id': 'shareer_name',
            'data-cy': 'share-name-input',
            'autocomplete': 'name',
            'aria-label': 'Your name'
        }),
        label='আপনার নাম',
        error_messages={
            'required': 'নাম প্রদান করুন',
            'max_length': 'নাম ২৫ অক্ষরের কম হতে হবে'
        }
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
            'placeholder': 'আপনার ইমেইল',
            'id': 'shareer_email',
            'data-cy': 'share-email-input',
            'autocomplete': 'email',
            'aria-label': 'Your email address'
        }),
        label='আপনার ইমেইল',
        error_messages={
            'required': 'ইমেইল প্রদান করুন',
            'invalid': 'সঠিক ইমেইল ঠিকানা দিন'
        }
    )
    
    to = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
            'placeholder': 'প্রাপকের ইমেইল',
            'id': 'recipient_email',
            'data-cy': 'recipient-email-input',
            'autocomplete': 'email',
            'aria-label': "Recipient's email address"
        }),
        label='প্রাপকের ইমেইল',
        error_messages={
            'required': 'প্রাপকের ইমেইল দিন',
            'invalid': 'সঠিক ইমেইল ঠিকানা দিন'
        }
    )
    
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
            'placeholder': 'ঐচ্ছিক মন্তব্য...',
            'id': 'share_comments',
            'data-cy': 'share-comments-input',
            'rows': 4,
            'aria-label': 'Additional comments (optional)'
        }),
        label='মন্তব্য (ঐচ্ছিক)',
        help_text='আপনার মন্তব্য এখানে লিখুন (সর্বোচ্চ ৫০০ অক্ষর)'
    )
    
    def clean_name(self):
        """Validate name doesn't contain inappropriate content"""
        name = self.cleaned_data.get('name', '')
        
        # Check for minimum length
        if len(name.strip()) < 2:
            raise ValidationError('নাম কমপক্ষে ২ অক্ষর হতে হবে')
        
        # Optional: Check for profanity or inappropriate content
        # You can integrate with a profanity filter here
        
        return name.strip()
    
    def clean_email(self):
        """Validate sender email"""
        email = self.cleaned_data.get('email', '')
        
        # Additional email validation beyond Django's built-in
        if email and not self.is_valid_email_domain(email):
            raise ValidationError('ইমেইল ডোমেইন বৈধ নয়')
            
        return email
    
    def clean_to(self):
        """Validate recipient email and check if different from sender"""
        to_email = self.cleaned_data.get('to', '')
        from_email = self.cleaned_data.get('email', '')
        
        if to_email and from_email and to_email.lower() == from_email.lower():
            raise ValidationError('প্রাপকের ইমেইল আপনার ইমেইল থেকে আলাদা হতে হবে')
            
        return to_email
    
    def clean_comments(self):
        """Validate and sanitize comments"""
        comments = self.cleaned_data.get('comments', '')
        
        if comments and len(comments) > 500:
            raise ValidationError('মন্তব্য ৫০০ অক্ষরের কম হতে হবে')
            
        # Remove any potentially harmful HTML/script tags
        import re
        comments = re.sub(r'<[^>]*>', '', comments)
        
        return comments
    
    @staticmethod
    def is_valid_email_domain(email):
        """Check if email domain has valid MX records"""
        # This is a placeholder - you can implement actual MX record checking
        # using dnspython library or similar
        domain = email.split('@')[1]
        blocked_domains = ['tempmail.com', 'throwaway.com']  # Add more as needed
        return domain.lower() not in blocked_domains


class CommentForm(forms.ModelForm):
    """Modernized comment form with enhanced UX and validation"""
    
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
                'placeholder': 'আপনার নাম',
                'id': 'comment_name',
                'data-cy': 'comment-name-input',
                'autocomplete': 'name',
                'aria-label': 'Your name for the comment'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
                'placeholder': 'আপনার ইমেইল',
                'id': 'comment_email',
                'data-cy': 'comment-email-input',
                'autocomplete': 'email',
                'aria-label': 'Your email address'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control form-control-lg rounded-3 border-0 bg-light',
                'placeholder': 'আপনার মন্তব্য লিখুন...',
                'id': 'comment_body',
                'data-cy': 'comment-body-input',
                'rows': 4,
                'maxlength': 1000,
                'aria-label': 'Your comment',
                'data-character-limit': '1000'
            })
        }
        labels = {
            'name': 'নাম',
            'email': 'ইমেইল',
            'body': 'মন্তব্য'
        }
        error_messages = {
            'name': {
                'required': 'নাম প্রদান করুন',
                'max_length': 'নাম ৫০ অক্ষরের কম হতে হবে'
            },
            'email': {
                'required': 'ইমেইল প্রদান করুন',
                'invalid': 'সঠিক ইমেইল ঠিকানা দিন'
            },
            'body': {
                'required': 'মন্তব্য লিখুন',
                'max_length': 'মন্তব্য ১০০০ অক্ষরের কম হতে হবে'
            }
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with additional attributes and dynamic behavior"""
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes and additional attributes
        for field_name, field in self.fields.items():
            # Add common attributes
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = ''
            
            field.widget.attrs['class'] += ' form-control-lg'
            
            # Add data attributes for frontend validation
            field.widget.attrs['data-validate'] = 'true'
            
            if field.required:
                field.widget.attrs['required'] = 'required'
                field.widget.attrs['data-required'] = 'true'
            
            # Add pattern for specific fields
            if field_name == 'email':
                field.widget.attrs['pattern'] = '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
                field.widget.attrs['data-type'] = 'email'
            
            if field_name == 'name':
                field.widget.attrs['minlength'] = '2'
                field.widget.attrs['data-minlength'] = '2'
    
    def clean_name(self):
        """Validate and sanitize name"""
        name = self.cleaned_data.get('name', '').strip()
        
        if len(name) < 2:
            raise ValidationError('নাম কমপক্ষে ২ অক্ষর হতে হবে')
        
        # Remove multiple spaces
        name = ' '.join(name.split())
        
        # Optional: Check for profanity
        # profanity_check(name)
        
        return name
    
    def clean_email(self):
        """Validate email with additional checks"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # Check for disposable email domains
        disposable_domains = ['tempmail.com', 'throwaway.com']  # Expand this list
        domain = email.split('@')[1] if '@' in email else ''
        
        if domain in disposable_domains:
            raise ValidationError('ডিসপোজেবল ইমেইল ব্যবহার করা যাবে না')
        
        return email
    
    def clean_body(self):
        """Sanitize comment body and check for spam"""
        body = self.cleaned_data.get('body', '').strip()
        
        # Remove excessive whitespace
        body = ' '.join(body.split())
        
        # Check for spam patterns
        spam_patterns = [
            r'http[s]?://',  # URLs
            r'www\.',         # www links
            r'[$\!\?]{5,}',   # excessive punctuation
        ]
        
        import re
        for pattern in spam_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                # Log potential spam for admin review
                # You might want to mark this comment for moderation
                raise ValidationError('স্প্যাম সনাক্ত করা হয়েছে। দয়া করে বৈধ মন্তব্য করুন।')
        
        return body
    
    def save(self, commit=True):
        """Override save to add additional processing"""
        comment = super().save(commit=False)
        
        # Add metadata
        comment.ip_address = self.get_client_ip()
        comment.user_agent = self.get_user_agent()
        
        if commit:
            comment.save()
            
            # Optional: Send notification to admin
            # self.notify_admin(comment)
            
        return comment
    
    def get_client_ip(self):
        """Get client IP from request (if available)"""
        request = getattr(self, 'request', None)
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0]
            return request.META.get('REMOTE_ADDR')
        return None
    
    def get_user_agent(self):
        """Get user agent from request"""
        request = getattr(self, 'request', None)
        if request:
            return request.META.get('HTTP_USER_AGENT', '')
        return None

# Optional: Add a search form for better UX
class NewsSearchForm(forms.Form):
    """Advanced search form for news articles"""
    
    query = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg rounded-pill',
            'placeholder': 'সংবাদ অনুসন্ধান...',
            'id': 'search_query',
            'data-cy': 'search-input',
            'aria-label': 'Search news articles'
        }),
        label='অনুসন্ধান'
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'সব বিভাগ')] + [],  # Will be populated dynamically
        widget=forms.Select(attrs={
            'class': 'form-select rounded-pill',
            'id': 'search_category',
            'data-cy': 'search-category'
        }),
        label='বিভাগ'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control rounded-pill',
            'type': 'date',
            'id': 'search_date_from',
            'data-cy': 'search-date-from'
        }),
        label='তারিখ থেকে'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control rounded-pill',
            'type': 'date',
            'id': 'search_date_to',
            'data-cy': 'search-date-to'
        }),
        label='তারিখ পর্যন্ত'
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('-publish', 'সর্বশেষ'),
            ('-views', 'সবচেয়ে পঠিত'),
            ('title', 'শিরোনাম (ক-ঝ)')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select rounded-pill',
            'id': 'search_sort',
            'data-cy': 'search-sort'
        }),
        label='সাজান'
    )
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('শেষ তারিখ শুরু তারিখের পরে হতে হবে')
        
        return cleaned_data