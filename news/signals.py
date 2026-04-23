from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import News, Comment, NewsletterSubscriber

@receiver(post_save, sender=News)
def notify_subscribers_on_news(sender, instance, created, **kwargs):
    """নতুন নিউজ পোস্ট হলে সাবস্ক্রাইবারদের ইমেইল নোটিফিকেশন"""
    if created:
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        subject = f"নতুন সংবাদ: {instance.title}"
        message = f"""
        প্রিয় সাবস্ক্রাইবার,
        
        আমাদের ওয়েবসাইটে একটি নতুন সংবাদ পোস্ট করা হয়েছে:
        
        শিরোনাম: {instance.title}
        বিভাগ: {instance.category.name}
        
        বিস্তারিত পড়তে ভিজিট করুন: {settings.SITE_URL}/news/{instance.slug}/
        
        ধন্যবাদ,
        নিউজপোর্টাল টিম
        """
        
        for subscriber in subscribers:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [subscriber.email],
                    fail_silently=True,
                )
            except:
                pass

@receiver(post_save, sender=Comment)
def notify_author_on_comment(sender, instance, created, **kwargs):
    """নতুন কমেন্ট পোস্ট হলে নিউজের লেখককে নোটিফিকেশন"""
    if created:
        try:
            send_mail(
                f"আপনার নিউজে নতুন মন্তব্য: {instance.news.title}",
                f"""
                {instance.user.username} আপনার "{instance.news.title}" নিউজটিতে মন্তব্য করেছেন:
                
                "{instance.text}"
                
                মন্তব্যটি দেখুন: {settings.SITE_URL}/news/{instance.news.slug}/#comments
                """,
                settings.DEFAULT_FROM_EMAIL,
                [instance.news.author.email],
                fail_silently=True,
            )
        except:
            pass