"""
URL configuration for portfolio_project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('core.urls')),
]

# Django should only serve local media while developing.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Legacy production media fallback kept for future reference.
# from django.views.static import serve
# from django.urls import re_path
# urlpatterns += [
#     re_path(r'^media/(?P<path>.*)$', serve, {
#         'document_root': settings.MEDIA_ROOT,
#     }),
# ]

# Custom error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
