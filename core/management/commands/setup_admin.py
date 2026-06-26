import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create an optional superuser and prepare database extensions when configured.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')

        if username and password:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username, email, password)
                self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))
            else:
                self.stdout.write(f"Admin user '{username}' already exists.")
        else:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD not set. Skipping admin creation.')

        if connection.vendor == 'postgresql':
            try:
                with connection.cursor() as cursor:
                    cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')
                self.stdout.write(self.style.SUCCESS('pgvector extension is ready.'))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'Could not prepare pgvector extension: {exc}'))
        else:
            self.stdout.write('Local non-Postgres database detected. Skipping pgvector extension setup.')