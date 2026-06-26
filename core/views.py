from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Prefetch
from .models import Project, ProjectCategory, ProjectScreenshot, ChatSession, GuestUser
from .forms import ContactForm
# from .rag_service import rag_query_stream (Moved to function for lazy loading)
from .utils import get_client_ip, get_homepage_content

def home_view(request):
    """Main single-page portfolio - all sections."""
    public_content = get_homepage_content()

    contact_form = ContactForm()

    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, " Message sent! I'll get back to you soon.")
            return redirect(f"{reverse('home')}#contact")
        else:
            messages.error(request, "Something went wrong. Please check your inputs.")

    context = {
        **public_content,
        'contact_form': contact_form,
        'page': 'home',
    }
    return render(request, 'home.html', context)

def projects_view(request):
    """Full projects listing with category filter."""
    categories = ProjectCategory.objects.all().only('name', 'slug')
    selected_category = request.GET.get('category', '')

    projects = Project.objects.select_related('category').only(
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
    )
    if selected_category:
        projects = projects.filter(category__slug=selected_category)

    paginator = Paginator(projects, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'selected_category': selected_category,
        'page_obj': page_obj,
        'page': 'projects',
    }
    return render(request, 'projects.html', context)


def about_view(request):
    """Indexable profile/about page for search engines and visitors."""
    public_content = get_homepage_content()
    context = {
        **public_content,
        'page': 'about',
    }
    return render(request, 'about.html', context)


def project_detail_view(request, slug):
    """Detailed view for a specific project with screenshot gallery."""
    project = get_object_or_404(
        Project.objects.select_related('category').prefetch_related(
            Prefetch(
                'screenshots',
                queryset=ProjectScreenshot.objects.only(
                    'project_id',
                    'image',
                    'caption',
                    'order',
                ),
            )
        ),
        slug=slug,
    )
    
    context = {
        'project': project,
        'page': 'projects',
    }
    return render(request, 'project_detail.html', context)


def contact_view(request):
    """Dedicated contact page."""
    contact_form = ContactForm()

    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, " Message sent! I'll get back to you soon.")
            return redirect(f"{reverse('contact')}#contact-form")
        else:
            messages.error(request, "Something went wrong. Please check your inputs.")

    context = {
        'contact_form': contact_form,
        'page': 'contact',
    }
    return render(request, 'contact.html', context)

# --- CHATBOT VIEWS ------------------------------------------

def quick_login_view(request):
    """Simple assistant-login/register that creates a guest based just on username."""
    if request.method == 'POST':
        username = request.POST.get('username')
        if username:
            guest, created = GuestUser.objects.get_or_create(username=username)
            request.session['guest_id'] = str(guest.id)
            return redirect('chat_ui')
    return render(request, 'login.html')

def chat_ui_view(request):
    guest_id = request.session.get('guest_id')
    if not guest_id:
        return redirect('quick_login')
        
    guest = GuestUser.objects.filter(id=guest_id).first()
    if not guest:
        return redirect('quick_login')

    session = ChatSession.objects.filter(guest=guest).order_by('-created_at').first()
    if not session:
        session = ChatSession.objects.create(guest=guest)
        
    context = {
        'session_id': str(session.id),
        'user_id': str(guest.id)
    }
    return render(request, 'chat.html', context)

@csrf_exempt
def chat_api_view(request):
    from .rag_service import rag_query_stream
    if request.method == 'POST':
        question = request.POST.get('question')
        session_id = request.POST.get('session_id')
        user_id = request.POST.get('user_id') # This is the GuestUser UUID
        context_page = request.POST.get('context_page', 'Unknown')
        
        if not question or not session_id or not user_id:
            return JsonResponse({"error": "Missing parameters"}, status=400)
            
        response = StreamingHttpResponse(
            rag_query_stream(question, user_id, session_id, context_page),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        return response
    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def init_chat_api(request):
    """Creates an anonymous guest session and returns session_id + user_id."""
    if request.method == 'POST':
        username = request.POST.get('username')
        real_name = request.POST.get('real_name', '')
        if not username:
            import uuid
            username = f"Guest_{uuid.uuid4().hex[:6]}"
            
        guest = GuestUser.objects.filter(username=username).first()
        if guest:
            if real_name and not guest.real_name:
                guest.real_name = real_name
                guest.save()
        else:
            ip = get_client_ip(request)
            guest = GuestUser.objects.create(
                username=username,
                real_name=real_name,
                ip_address=ip
            )
            
        session = ChatSession.objects.filter(guest=guest).last()
        if not session:
            session = ChatSession.objects.create(guest=guest)
            
        return JsonResponse({
            'user_id': str(guest.id),
            'session_id': str(session.id),
            'username': guest.username,
            'real_name': guest.real_name
        })
    return JsonResponse({"error": "Invalid request"}, status=405)

def robots_view(request):
    return render(request, 'robots.txt', content_type='text/plain')

def sitemap_view(request):
    projects = Project.objects.select_related('category').only(
        'slug',
        'title',
        'short_description',
        'image',
        'created_at',
        'category__name',
    )
    context = {
        'projects': projects,
        **get_homepage_content(),
    }
    return render(request, 'sitemap.xml', context, content_type='application/xml')

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    import traceback
    import sys
    from django.http import HttpResponse

    # Print traceback once to the console
    type_, value, tb = sys.exc_info()
    if type_:
        print("======== MATRIX 500 CRASH DETAILS ========", file=sys.stderr)
        traceback.print_exception(type_, value, tb, file=sys.stderr)
        print("==========================================", file=sys.stderr)

    # Attempt to render the pretty 500 page
    try:
        return render(request, '500.html', status=500)
    except Exception as e:
        # If rendering 500.html fails (e.g. static file issue), return plain text
        # to prevent infinite recursion loop
        return HttpResponse(
            f"500 Internal Server Error\n\nAdditionally, an error occurred while rendering the error page: {e}",
            content_type="text/plain",
            status=500
        )
