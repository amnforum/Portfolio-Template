from django.contrib import admin
from .models import Profile, Project, ProjectCategory, Skill, ContactMessage, ProjectScreenshot


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'tagline', 'email', 'location']
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'tagline', 'bio', 'avatar', 'location', 'years_experience')}),
        ('Links', {'fields': ('resume_url', 'github', 'linkedin', 'twitter', 'email')}),
    )


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}



class ProjectScreenshotInline(admin.TabularInline):
    model = ProjectScreenshot
    extra = 3

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'featured', 'order', 'created_at']
    list_filter = ['featured', 'category']
    list_editable = ['featured', 'order']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectScreenshotInline]
    fieldsets = (
        ('Project Info', {'fields': ('title', 'slug', 'short_description', 'full_description', 'category', 'image')}),
        ('Links', {'fields': ('live_url', 'github_url', 'tech_stack')}),
        ('Display', {'fields': ('featured', 'order')}),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon_class', 'url')
    list_filter = ('category',)
    search_fields = ('name',)
    fieldsets = (
        ('Basic', {'fields': ('name', 'category')}),
        ('Visual & Link', {'fields': ('icon_class', 'image', 'url')}),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)

    def has_add_permission(self, request):
        return False


# --- RAG CHATBOT ADMIN ------------------------------------

from .models import KnowledgeDocument, DocumentChunk, ChatSession, ChatMessage, GuestUser

@admin.register(GuestUser)
class GuestUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'real_name', 'ip_address', 'created_at', 'last_active')
    search_fields = ('username', 'real_name', 'ip_address')

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'is_processed')
    readonly_fields = ('is_processed',)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.is_processed:
            from .rag_service import process_document, process_document_bytes

            # Process immediately so Vercel/serverless requests do not drop the job
            # before embeddings are written to the database.
            uploaded_file = form.files.get('file')
            if uploaded_file is not None:
                uploaded_file.seek(0)
                process_document_bytes(
                    document=obj,
                    raw_bytes=uploaded_file.read(),
                    source_name=getattr(uploaded_file, 'name', obj.file.name),
                )
            else:
                process_document(obj.id)
            obj.refresh_from_db(fields=['is_processed'])

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'chunk_preview')
    readonly_fields = ('embedding',)
    
    def chunk_preview(self, obj):
        if not obj.chunk_text: return "No Content"
        return obj.chunk_text[:50] + '...'

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'created_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at', 'message_preview')
    
    def message_preview(self, obj):
        if not obj.message: return "Empty"
        return obj.message[:50] + '...'
