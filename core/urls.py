from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('projects/', views.projects_view, name='projects'),
    path('projects/<slug:slug>/', views.project_detail_view, name='project_detail'),
    path('contact/', views.contact_view, name='contact'),
    
    # Chatbot URLs
    path('assistant-login/', views.quick_login_view, name='quick_login'),
    path('assistant/', views.chat_ui_view, name='chat_ui'),
    path('api/assistant/', views.chat_api_view, name='chat_api'),
    path('api/init-assistant/', views.init_chat_api, name='init_chat_api'),
    path('robots.txt', views.robots_view, name='robots_text'),
    path('sitemap.xml', views.sitemap_view, name='sitemap_xml'),
]
