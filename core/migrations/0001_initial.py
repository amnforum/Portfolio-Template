# Generated for the public starter schema.

from django.db import migrations, models
import django.db.models.deletion
import pgvector.django.vector
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('subject', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='GuestUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(help_text='Codename (ID) the guest chose.', max_length=100)),
                ('real_name', models.CharField(blank=True, help_text="The person's actual name.", max_length=100, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_active', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='KnowledgeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('file', models.FileField(help_text='Upload .txt or .pdf files', upload_to='knowledge_docs/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_processed', models.BooleanField(default=False, help_text='True if chunks and embeddings are generated')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('tagline', models.CharField(help_text="Short headline, e.g. 'Full Stack Developer'", max_length=200)),
                ('bio', models.TextField()),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='profile/')),
                ('resume_url', models.URLField(blank=True, null=True)),
                ('github', models.URLField(blank=True, null=True)),
                ('linkedin', models.URLField(blank=True, null=True)),
                ('twitter', models.URLField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('location', models.CharField(blank=True, max_length=100)),
                ('years_experience', models.PositiveIntegerField(default=0)),
            ],
            options={'verbose_name': 'Profile', 'verbose_name_plural': 'Profile'},
        ),
        migrations.CreateModel(
            name='ProjectCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={'verbose_name_plural': 'Project Categories'},
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('category', models.CharField(choices=[('Frontend', 'Frontend'), ('Backend', 'Backend'), ('Tools', 'Tools/DevOps'), ('Other', 'Other')], max_length=50)),
                ('icon_class', models.CharField(blank=True, help_text='e.g. devicon class or emoji', max_length=100)),
                ('image', models.ImageField(blank=True, help_text='Upload custom technology logo', null=True, upload_to='skills/')),
                ('url', models.URLField(blank=True, help_text='Official website or documentation link', null=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('short_description', models.CharField(max_length=300)),
                ('full_description', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, help_text='Main thumbnail image', null=True, upload_to='projects/')),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('live_url', models.URLField(blank=True, null=True)),
                ('github_url', models.URLField(blank=True, null=True)),
                ('tech_stack', models.CharField(blank=True, help_text='Comma-separated: Python, Django, React', max_length=500)),
                ('featured', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0, help_text='Lower = shown first')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.projectcategory')),
            ],
            options={'ordering': ['order', '-created_at']},
        ),
        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_text', models.TextField()),
                ('embedding', pgvector.django.vector.VectorField(dimensions=3072, help_text='Gemini native 3072-dimensional embedding')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='core.knowledgedocument')),
            ],
        ),
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('guest', models.ForeignKey(blank=True, help_text='The guest who generated this chat.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='core.guestuser')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectScreenshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='projects/gallery/')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screenshots', to='core.project')),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('human', 'Human'), ('ai', 'AI')], max_length=10)),
                ('message', models.TextField()),
                ('embedding', pgvector.django.vector.VectorField(blank=True, dimensions=3072, help_text='Gemini native 3072-dimensional embedding for human queries', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.chatsession')),
            ],
            options={'ordering': ['created_at']},
        ),
    ]