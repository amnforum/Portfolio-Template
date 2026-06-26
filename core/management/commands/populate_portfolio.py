from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Deprecated alias for seed_data. Kept for older deploy scripts without personal data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('populate_portfolio is deprecated; running seed_data instead.'))
        call_command('seed_data')