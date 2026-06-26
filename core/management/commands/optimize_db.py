import uuid
from django.core.management.base import BaseCommand
from django.db import connection
from core.models import DocumentChunk, ChatMessage

class Command(BaseCommand):
    help = 'Optimizes PGVector performance by creating HNSW indices.'

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write(self.style.WARNING("Not using PostgreSQL. Skipping PGVector optimization."))
            return

        with connection.cursor() as cursor:
            self.stdout.write("Creating HNSW indices for high-performance vector search...")
            
            # Index for Document Chunks
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS doc_chunks_hnsw_idx ON core_documentchunk 
                    USING hnsw (embedding vector_cosine_ops);
                """)
                self.stdout.write(self.style.SUCCESS("Successfully created/verified HNSW index for DocumentChunk."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating DocumentChunk index: {e}"))

            # Index for Chat Messages
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS chat_msgs_hnsw_idx ON core_chatmessage 
                    USING hnsw (embedding vector_cosine_ops);
                """)
                self.stdout.write(self.style.SUCCESS("Successfully created/verified HNSW index for ChatMessage."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating ChatMessage index: {e}"))

        self.stdout.write(self.style.SUCCESS("Database optimization complete!"))
