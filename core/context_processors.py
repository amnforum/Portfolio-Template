from django.conf import settings

from .utils import get_public_profile


def global_context(request):
    """Makes Profile available globally across all templates. Fail-safe for missing data."""
    try:
        profile = get_public_profile()
    except Exception:
        profile = None

    site_url = f"{request.scheme}://{request.get_host()}"
    return {
        'profile': profile,
        'site_url': site_url,
        'current_url': request.build_absolute_uri(),
        'admin_url': f"/{settings.ADMIN_URL}",
    }
