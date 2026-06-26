from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Profile, Project, ProjectCategory, ProjectScreenshot, Skill
from .utils import clear_public_content_cache


PUBLIC_CONTENT_MODELS = (Profile, Project, ProjectCategory, ProjectScreenshot, Skill)


@receiver(post_save, sender=Profile)
@receiver(post_save, sender=Project)
@receiver(post_save, sender=ProjectCategory)
@receiver(post_save, sender=ProjectScreenshot)
@receiver(post_save, sender=Skill)
@receiver(post_delete, sender=Profile)
@receiver(post_delete, sender=Project)
@receiver(post_delete, sender=ProjectCategory)
@receiver(post_delete, sender=ProjectScreenshot)
@receiver(post_delete, sender=Skill)
def clear_public_cache_on_content_change(sender, **kwargs):
    if sender in PUBLIC_CONTENT_MODELS:
        clear_public_content_cache()
