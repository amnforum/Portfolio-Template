import os
from django.db import connection
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_project.settings')
django.setup()

def enable_vector():
    with connection.cursor() as cursor:
        print("Attempting to enable pgvector extension...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print("Successfully enabled pgvector!")
        except Exception as e:
            print(f"Error: {e}")
            print("You may need to run 'CREATE EXTENSION IF NOT EXISTS vector;' manualy as a superuser (postgres).")

if __name__ == "__main__":
    enable_vector()
