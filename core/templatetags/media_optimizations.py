from django import template

register = template.Library()


@register.filter
def cloudinary_auto(url, width=900):
    """Request lighter Cloudinary images while leaving non-Cloudinary URLs alone."""
    if not url:
        return url

    value = str(url)
    if 'res.cloudinary.com' not in value or '/upload/' not in value:
        return value

    try:
        requested_width = max(120, min(int(width), 2000))
    except (TypeError, ValueError):
        requested_width = 900

    transform = f'f_auto,q_auto,w_{requested_width},c_limit'
    if f'/upload/{transform}/' in value:
        return value
    return value.replace('/upload/', f'/upload/{transform}/', 1)
