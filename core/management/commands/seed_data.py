from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from core.models import Profile, Project, ProjectCategory, Skill


class Command(BaseCommand):
    help = 'Seed the database with safe demo portfolio content for local development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create a local demo admin user. Do not use this in production.',
        )

    def handle(self, *args, **options):
        if options['create_admin'] and not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'changeme-admin-password')
            self.stdout.write(self.style.WARNING('Created local demo admin: admin / changeme-admin-password'))

        profile, _ = Profile.objects.get_or_create(
            name='Portfolio Owner',
            defaults={
                'tagline': 'Full Stack Developer',
                'bio': (
                    'A short public bio goes here. Replace this sample profile with your own '
                    'background, focus areas, and preferred contact details from the Django admin.'
                ),
                'location': 'Remote',
                'years_experience': 1,
                'github': 'https://github.com/example',
                'linkedin': 'https://www.linkedin.com/in/example',
                'email': 'hello@example.com',
            },
        )
        self.stdout.write(self.style.SUCCESS(f'Profile ready: {profile.name}'))

        categories = [
            ('Web Apps', 'web-apps'),
            ('AI & Data', 'ai-data'),
            ('Open Source', 'open-source'),
        ]
        category_by_slug = {}
        for name, slug in categories:
            category, _ = ProjectCategory.objects.get_or_create(name=name, slug=slug)
            category_by_slug[slug] = category

        skills = [
            ('Python', 'Backend', 'fab fa-python text-blue-400'),
            ('Django', 'Backend', 'fas fa-server text-green-500'),
            ('JavaScript', 'Frontend', 'fab fa-js text-yellow-400'),
            ('Tailwind CSS', 'Frontend', 'fab fa-css3-alt text-blue-500'),
            ('Git', 'Tools', 'fab fa-git-alt text-orange-500'),
            ('SQL', 'Other', 'fas fa-database text-blue-300'),
        ]
        for name, category, icon_class in skills:
            Skill.objects.get_or_create(
                name=name,
                defaults={'category': category, 'icon_class': icon_class},
            )

        projects = [
            {
                'title': 'Portfolio Website',
                'short_description': 'A responsive Django portfolio with projects, skills, contact forms, and an optional AI assistant.',
                'full_description': 'Use this sample entry to document a real project, its goals, implementation details, and outcomes.',
                'category': category_by_slug['web-apps'],
                'tech_stack': 'Python, Django, Tailwind CSS, SQLite',
                'featured': True,
                'order': 1,
            },
            {
                'title': 'Knowledge Assistant',
                'short_description': 'An optional assistant that can answer questions from uploaded portfolio documents.',
                'full_description': 'Replace this sample with an AI, automation, or data project from your own work.',
                'category': category_by_slug['ai-data'],
                'tech_stack': 'Django, Groq, Gemini Embeddings, pgvector',
                'featured': True,
                'order': 2,
            },
            {
                'title': 'Open Source Starter',
                'short_description': 'A starter project entry for showcasing reusable packages, tools, or community work.',
                'full_description': 'Add repository links, live URLs, screenshots, and a short case study from the admin panel.',
                'category': category_by_slug['open-source'],
                'tech_stack': 'Python, Documentation, CI',
                'featured': False,
                'order': 3,
            },
        ]
        for data in projects:
            Project.objects.update_or_create(title=data['title'], defaults=data)

        self.stdout.write(self.style.SUCCESS('Safe demo portfolio content seeded.'))