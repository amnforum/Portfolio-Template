from django.core.management.base import BaseCommand
from core.models import DocumentChunk, ChatMessage
from core.rag_service import get_embedding
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Finds and repairs zero-vector embeddings in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reindex-all',
            action='store_true',
            help='Rebuild all chunk and human-message embeddings, not just zero vectors.',
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting Matrix Embedding Repair...")
        reindex_all = options['reindex_all']
        
        # 1. Repair Document Chunks
        chunks = DocumentChunk.objects.all()
        repaired_chunks = 0
        
        for chunk in chunks:
            needs_refresh = reindex_all or (chunk.embedding and all(v == 0 for v in chunk.embedding))
            if needs_refresh:
                self.stdout.write(f"Repairing Chunk {chunk.id}...")
                new_vec = get_embedding(chunk.chunk_text, task_type='RETRIEVAL_DOCUMENT')
                if any(v != 0 for v in new_vec):
                    chunk.embedding = new_vec
                    chunk.save(update_fields=['embedding'])
                    repaired_chunks += 1
                else:
                    self.stdout.write(self.style.WARNING(f"Failed to repair Chunk {chunk.id} - API still returning zeros."))

        # 2. Repair Chat Messages (Human role only, as AI role doesn't need embeddings usually)
        msg_query = ChatMessage.objects.filter(role='human')
        repaired_msgs = 0
        
        for msg in msg_query:
            needs_refresh = reindex_all or (msg.embedding and all(v == 0 for v in msg.embedding))
            if needs_refresh:
                self.stdout.write(f"Repairing Message {msg.id}...")
                new_vec = get_embedding(msg.message, task_type='RETRIEVAL_QUERY')
                if any(v != 0 for v in new_vec):
                    msg.embedding = new_vec
                    msg.save(update_fields=['embedding'])
                    repaired_msgs += 1

        self.stdout.write(self.style.SUCCESS(
            f"Repair Complete! Repaired {repaired_chunks} chunks and {repaired_msgs} messages."
        ))
