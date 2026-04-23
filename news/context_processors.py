# news/context_processors.py
from .models import Category

def categories(request):
    """সব ক্যাটাগরি টেমপ্লেটে পাঠানোর জন্য"""
    return {
        'categories': Category.objects.all()
    }