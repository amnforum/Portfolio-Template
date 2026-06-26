from django.conf import settings

class AdminIPRestrictMiddleware:
    """
    Admin is protected by Django's credentials and an obscured
    URL. Requests to the default /admin route should look like
    a normal 404 in production.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info == '/admin' or request.path_info.startswith('/admin/'):
            from django.http import Http404

            raise Http404()
        return self.get_response(request)
