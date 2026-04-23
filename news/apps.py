from django.apps import AppConfig

class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'
    verbose_name = 'নিউজপোর্টাল ম্যানেজমেন্ট'
    
    def ready(self):
        import news.signals
        

