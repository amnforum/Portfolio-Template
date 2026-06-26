from django.core.cache import cache
from django.db.models import Count


PUBLIC_CONTENT_CACHE_SECONDS = 300
PUBLIC_CONTENT_CACHE_KEYS = [
    'portfolio:profile:v1',
    'portfolio:homepage-content:v2',
]


def get_client_ip(request):
    """
    Utility function to extract the client's IP address from a request,
    handling potential proxies (X-Forwarded-For).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_public_profile():
    """Return the portfolio profile with a short warm cache for public pages."""
    from .models import Profile

    cache_key = 'portfolio:profile:v1'
    profile = cache.get(cache_key)
    if profile is None:
        profile = Profile.objects.first()
        cache.set(cache_key, profile, PUBLIC_CONTENT_CACHE_SECONDS)
    return profile


def get_homepage_content():
    """Collect homepage data without re-querying it on every warm request."""
    from .models import Project, Skill

    cache_key = 'portfolio:homepage-content:v2'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    featured_projects = list(
        Project.objects.filter(featured=True)
        .select_related('category')
        .annotate(screenshot_count=Count('screenshots'))
        .only(
            'id',
            'title',
            'short_description',
            'image',
            'slug',
            'live_url',
            'github_url',
            'tech_stack',
            'category__name',
            'category__slug',
            'featured',
            'order',
            'created_at',
        )[:3]
    )

    skills_by_category = {}
    for skill in Skill.objects.all().only('name', 'category', 'icon_class', 'image', 'url'):
        category = skill.get_category_display()
        skills_by_category.setdefault(category, []).append(skill)

    content = {
        'profile': get_public_profile(),
        'featured_projects': featured_projects,
        'skills_by_category': skills_by_category,
    }
    cache.set(cache_key, content, PUBLIC_CONTENT_CACHE_SECONDS)
    return content


def clear_public_content_cache():
    cache.delete_many(PUBLIC_CONTENT_CACHE_KEYS)
