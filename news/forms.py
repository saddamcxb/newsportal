from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import News, Comment, UserProfile, ContactMessage

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ইমেইল এড্রেস'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'প্রথম নাম'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'শেষ নাম'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'ইউজারনেম'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'পাসওয়ার্ড'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'পাসওয়ার্ড নিশ্চিত করুন'})

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'website', 'facebook', 'twitter', 'instagram', 'phone', 'address']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'আপনার সম্পর্কে বলুন...'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Facebook প্রোফাইল URL'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Twitter প্রোফাইল URL'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Instagram প্রোফাইল URL'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '০১XXXXXXXXX'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'আপনার ঠিকানা'}),
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'slug', 'category', 'image', 'summary', 'content', 'status', 'is_featured', 'is_breaking']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'নিউজের শিরোনাম'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'url-slug'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'সংক্ষিপ্ত বিবরণ'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'বিস্তারিত সংবাদ...'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_breaking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].help_text = "শিরোনামের উপর ভিত্তি করে স্বয়ংক্রিয়ভাবে তৈরি হবে"

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'আপনার মন্তব্য লিখুন...'})
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'আপনার নাম'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'আপনার ইমেইল'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'বিষয়'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'আপনার বার্তা লিখুন...'}),
        }