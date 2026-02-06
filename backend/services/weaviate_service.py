"""
Weaviate service for vector storage and RAG operations with chunking support.
Migrated from LocalRAG Python scripts (1-create-collection.py, 3-semantic_search.py, 4-generative_search.py).
"""
import weaviate
import weaviate.classes as wvc
import weaviate.classes.config as wc
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from typing import List, Dict, Optional
import json
import requests

from config import settings


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks to handle long documents.

    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If this isn't the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence boundary (., !, ?) in the last 100 chars
            for sep in ['. ', '! ', '? ', '\n\n', '\n']:
                last_sep = text[end-100:end].rfind(sep)
                if last_sep != -1:
                    end = end - 100 + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, with overlap
        start = end - overlap if end < len(text) else end

    return chunks


class WeaviateService:
    """Service for interacting with Weaviate vector database."""

    def __init__(self):
        """Initialize Weaviate client with configuration."""
        self.client = None
        self.collection_name = "Note"
        self._connect()

    def _connect(self):
        """Establish connection to Weaviate with retry logic."""
        import time
        max_retries = 10
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                # For docker networking (weaviate:8080)
                self.client = weaviate.connect_to_local(
                    host="weaviate",
                    port=8080,
                    auth_credentials=Auth.api_key(settings.weaviate_api_key),
                    additional_config=AdditionalConfig(
                        timeout=Timeout(
                            init=settings.weaviate_timeout_init,
                            query=settings.weaviate_timeout_query,
                            insert=settings.weaviate_timeout_insert
                        )
                    )
                )
                print(f"✓ Connected to Weaviate successfully")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Weaviate not ready (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Failed to connect to Weaviate after {max_retries} attempts: {e}")
                    print("   Make sure Weaviate container is running and healthy")
                    raise

    def ensure_collection(self) -> bool:
        """
        Create Note collection if it doesn't exist.
        Based on 1-create-collection.py logic, adapted for notes with chunking support.

        Returns:
            bool: True if collection exists or was created successfully
        """
        try:
            # Check if collection already exists
            try:
                self.client.collections.get(self.collection_name)
                print(f"Collection '{self.collection_name}' already exists")
                return True
            except:
                pass

            # Create Note collection with chunking support
            self.client.collections.create(
                name=self.collection_name,
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(
                    api_endpoint=settings.ollama_url,
                    model=settings.ollama_embedding_model,
                ),
                generative_config=wvc.config.Configure.Generative.ollama(
                    api_endpoint=settings.ollama_url,
                    model=settings.ollama_generation_model,
                ),
                properties=[
                    wc.Property(
                        name="note_id",
                        data_type=wc.DataType.TEXT,
                        skip_vectorization=True,
                    ),
                    wc.Property(
                        name="title",
                        data_type=wc.DataType.TEXT,
                    ),
                    wc.Property(
                        name="content",
                        data_type=wc.DataType.TEXT,
                    ),
                    wc.Property(
                        name="chunk_index",
                        data_type=wc.DataType.INT,
                        skip_vectorization=True,
                    ),
                    wc.Property(
                        name="total_chunks",
                        data_type=wc.DataType.INT,
                        skip_vectorization=True,
                    ),
                    wc.Property(
                        name="tags",
                        data_type=wc.DataType.TEXT,
                    ),
                    wc.Property(
                        name="created_at",
                        data_type=wc.DataType.TEXT,
                        skip_vectorization=True,
                    ),
                    wc.Property(
                        name="updated_at",
                        data_type=wc.DataType.TEXT,
                        skip_vectorization=True,
                    ),
                ],
            )
            print(f"Created collection '{self.collection_name}' with chunking support")
            return True
        except Exception as e:
            print(f"Error ensuring collection: {e}")
            return False

    def index_note(
        self,
        note_id: str,
        title: str,
        content: str,
        tags: List[str],
        created_at: str,
        updated_at: str
    ) -> Optional[str]:
        """
        Add or update note in vector database with automatic chunking.
        Long documents are split into chunks to fit within embedding model context limits.

        Args:
            note_id: Unique note identifier
            title: Note title
            content: Markdown content
            tags: List of tags
            created_at: Creation timestamp
            updated_at: Update timestamp

        Returns:
            str: Weaviate UUID of first chunk if successful, None otherwise
        """
        try:
            note_collection = self.client.collections.get(self.collection_name)

            # First, delete any existing chunks for this note
            self.delete_note(note_id)

            # Split content into chunks
            content_chunks = chunk_text(content)
            total_chunks = len(content_chunks)

            first_uuid = None
            for i, chunk in enumerate(content_chunks):
                properties = {
                    "note_id": note_id,
                    "title": title,
                    "content": chunk,
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "tags": ", ".join(tags) if tags else "",
                    "created_at": created_at,
                    "updated_at": updated_at,
                }

                # Insert chunk
                weaviate_uuid = note_collection.data.insert(properties)
                if i == 0:
                    first_uuid = str(weaviate_uuid)

            print(f"Indexed note {note_id} as {total_chunks} chunk(s)")
            return first_uuid
        except Exception as e:
            print(f"Error indexing note {note_id}: {e}")
            return None

    def delete_note(self, note_id: str) -> bool:
        """
        Remove all chunks of a note from vector database.

        Args:
            note_id: Note identifier to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            note_collection = self.client.collections.get(self.collection_name)

            # Use delete_many with filter instead of fetching all objects first
            # This is more efficient and avoids pagination limits
            result = note_collection.data.delete_many(
                where=wvc.query.Filter.by_property("note_id").equal(note_id)
            )

            deleted_count = result.successful if hasattr(result, 'successful') else 0

            if deleted_count > 0:
                print(f"Deleted {deleted_count} chunk(s) for note: {note_id}")
                return True
            else:
                print(f"No chunks found to delete for note: {note_id}")
                return False
        except Exception as e:
            print(f"Error deleting note {note_id}: {e}")
            return False

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        tag_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search notes using semantic similarity with chunk deduplication.
        Retrieves chunks and groups them by note_id to return complete notes.

        Args:
            query: Search query string
            limit: Maximum number of notes to return (not chunks)
            tag_filter: Optional list of tags to filter by

        Returns:
            List of matching notes with relevance scores
        """
        try:
            note_collection = self.client.collections.get(self.collection_name)

            # Build filters if tag_filter provided
            filters = None
            if tag_filter:
                tag_conditions = [
                    wvc.query.Filter.by_property("tags").contains_any(tag)
                    for tag in tag_filter
                ]
                if len(tag_conditions) == 1:
                    filters = tag_conditions[0]
                else:
                    filters = wvc.query.Filter.any_of(tag_conditions)

            # Retrieve more chunks than needed to ensure we get enough unique notes
            response = note_collection.query.near_text(
                query=query,
                limit=limit * 3,  # Get 3x chunks to account for multi-chunk notes
                filters=filters,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            # Deduplicate and aggregate by note_id
            notes_dict = {}
            for obj in response.objects:
                note_id = obj.properties.get("note_id")
                if note_id not in notes_dict:
                    # Use the first chunk's data (usually most relevant)
                    notes_dict[note_id] = {
                        "note_id": note_id,
                        "title": obj.properties.get("title", ""),
                        "content": obj.properties.get("content", ""),
                        "tags": obj.properties.get("tags", "").split(", ") if obj.properties.get("tags") else [],
                        "created_at": obj.properties.get("created_at", ""),
                        "updated_at": obj.properties.get("updated_at", ""),
                        "relevance_score": 1 - obj.metadata.distance if obj.metadata.distance else 0.0,
                        "chunk_index": obj.properties.get("chunk_index", 0)
                    }

            # Sort by relevance and return top results
            results = sorted(notes_dict.values(), key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

    def search_within_note(
        self,
        note_id: str,
        query: str,
        window_chunks: int = 2
    ) -> Optional[Dict]:
        """
        Search within a specific note and return a context window around the best match.

        Args:
            note_id: The note to search within
            query: Search query
            window_chunks: Number of chunks to include before and after the best match

        Returns:
            Dict with combined context text and metadata, or None if note not found
        """
        try:
            print(f"\n🔍 [SEARCH_WITHIN_NOTE] note_id={note_id}, query='{query}'")
            note_collection = self.client.collections.get(self.collection_name)

            # Search within this specific note
            response = note_collection.query.near_text(
                query=query,
                limit=50,  # Get all chunks for this note
                filters=wvc.query.Filter.by_property("note_id").equal(note_id),
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            if not response.objects:
                print(f"❌ [SEARCH_WITHIN_NOTE] No chunks found for note_id={note_id}")
                return None

            print(f"✓ [SEARCH_WITHIN_NOTE] Found {len(response.objects)} chunks")

            # Find the best matching chunk
            best_match = response.objects[0]
            best_chunk_index = best_match.properties.get("chunk_index", 0)
            total_chunks = best_match.properties.get("total_chunks", 1)
            title = best_match.properties.get("title", "")

            print(f"📍 [SEARCH_WITHIN_NOTE] Best match: chunk {best_chunk_index}/{total_chunks}, title='{title}'")
            print(f"   Distance: {best_match.metadata.distance if hasattr(best_match.metadata, 'distance') else 'N/A'}")
            print(f"   Content preview: {best_match.properties.get('content', '')[:100]}...")

            # Calculate window range
            start_index = max(0, best_chunk_index - window_chunks)
            end_index = min(total_chunks - 1, best_chunk_index + window_chunks)
            print(f"📊 [SEARCH_WITHIN_NOTE] Context window: chunks {start_index}-{end_index}")

            # Fetch all chunks in the window range
            all_chunks = note_collection.query.fetch_objects(
                filters=wvc.query.Filter.by_property("note_id").equal(note_id),
                limit=total_chunks
            )

            # Sort by chunk_index and extract the window
            sorted_chunks = sorted(
                all_chunks.objects,
                key=lambda x: x.properties.get("chunk_index", 0)
            )

            window_chunks_list = [
                chunk for chunk in sorted_chunks
                if start_index <= chunk.properties.get("chunk_index", 0) <= end_index
            ]

            # Combine chunks into context
            context_text = "\n\n".join([
                chunk.properties.get("content", "")
                for chunk in window_chunks_list
            ])

            return {
                "context": context_text,
                "title": title,
                "chunk_range": f"{start_index}-{end_index}",
                "total_chunks": total_chunks,
                "best_chunk_index": best_chunk_index
            }

        except Exception as e:
            print(f"Error searching within note {note_id}: {e}")
            return None

    def generative_search(
        self,
        query: str,
        limit: int = 5,
        tag_filter: Optional[List[str]] = None,
        additional_context: Optional[str] = None
    ) -> Dict:
        """
        Generate response using RAG with distance filtering and deduplication.

        New approach:
        1. Retrieve chunks with distance scores
        2. Filter by distance threshold
        3. Deduplicate by note_id (keep best chunk per note)
        4. Generate response using filtered chunks

        Args:
            query: User's question
            limit: Maximum number of unique notes to use as context
            tag_filter: Optional list of tags to filter by
            additional_context: Additional context to include without vectorization

        Returns:
            Dict with AI response and context notes
        """
        try:
            note_collection = self.client.collections.get(self.collection_name)

            # Build filters if tag_filter provided
            filters = None
            if tag_filter:
                tag_conditions = [
                    wvc.query.Filter.by_property("tags").contains_any(tag)
                    for tag in tag_filter
                ]
                if len(tag_conditions) == 1:
                    filters = tag_conditions[0]
                else:
                    filters = wvc.query.Filter.any_of(tag_conditions)

            print(f"\n🤖 [GENERATIVE_SEARCH] query='{query}', limit={limit}")

            # Step 1: Retrieve chunks with distance scores
            query_response = note_collection.query.near_text(
                query=query,
                limit=limit * 4,  # Over-retrieve to have options after filtering
                filters=filters,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            if not query_response.objects:
                return {
                    "response": "No relevant notes found to answer your question.",
                    "context_notes": []
                }

            # Step 2: Filter by distance threshold and log all chunks
            DISTANCE_THRESHOLD = 0.5  # Lower distance = better match (0.0 = perfect, 2.0 = opposite)
            print(f"📏 [GENERATIVE_SEARCH] Distance threshold: {DISTANCE_THRESHOLD}")
            print(f"📚 [GENERATIVE_SEARCH] Retrieved {len(query_response.objects)} chunks before filtering:")

            filtered_chunks = []
            for i, obj in enumerate(query_response.objects):
                distance = obj.metadata.distance if hasattr(obj.metadata, 'distance') else None
                note_id = obj.properties.get("note_id")
                title = obj.properties.get("title", "")
                chunk_idx = obj.properties.get("chunk_index", 0)

                relevance_emoji = "✓" if (distance is not None and distance < DISTANCE_THRESHOLD) else "✗"
                distance_str = f"{distance:.4f}" if distance is not None else "N/A"
                print(f"   {relevance_emoji} [{i+1}] distance={distance_str}, note_id={note_id[:8]}, title='{title}', chunk={chunk_idx}")

                if distance is not None and distance < DISTANCE_THRESHOLD:
                    filtered_chunks.append((obj, distance))

            print(f"✓ [GENERATIVE_SEARCH] {len(filtered_chunks)} chunks passed distance threshold")

            # If no chunks pass threshold, keep top 3 best matches
            if not filtered_chunks:
                print(f"⚠️  [GENERATIVE_SEARCH] No chunks passed threshold, keeping top 3 best matches")
                filtered_chunks = [
                    (obj, obj.metadata.distance if hasattr(obj.metadata, 'distance') else 1.0)
                    for obj in query_response.objects[:3]
                ]

            # Step 3: Deduplicate by note_id (keep best chunk per note)
            note_best_chunks = {}
            for obj, distance in filtered_chunks:
                note_id = obj.properties.get("note_id")

                if note_id not in note_best_chunks or distance < note_best_chunks[note_id][1]:
                    note_best_chunks[note_id] = (obj, distance)

            deduplicated_chunks = list(note_best_chunks.values())
            print(f"🎯 [GENERATIVE_SEARCH] {len(deduplicated_chunks)} unique notes after deduplication")

            # Sort by distance and limit to requested number
            deduplicated_chunks.sort(key=lambda x: x[1])  # Sort by distance (lower = better)
            final_chunks = deduplicated_chunks[:limit]

            print(f"📊 [GENERATIVE_SEARCH] Using {len(final_chunks)} chunks for generation:")
            for i, (obj, distance) in enumerate(final_chunks):
                note_id = obj.properties.get("note_id")
                title = obj.properties.get("title", "")
                chunk_idx = obj.properties.get("chunk_index", 0)
                print(f"   [{i+1}] distance={distance:.4f}, note_id={note_id[:8]}, title='{title}', chunk={chunk_idx}")

            # Step 4: Build context from filtered chunks
            additional_context_section = ""
            if additional_context:
                print(f"📝 [GENERATIVE_SEARCH] Additional context: {len(additional_context)} chars")
                additional_context_section = f"""

IMPORTANT - Additional Context Provided:
---
{additional_context}
---

Please focus on the additional context above to answer the question."""

            context_excerpts = []
            for obj, _ in final_chunks:
                title = obj.properties.get("title", "")
                content = obj.properties.get("content", "")
                chunk_idx = obj.properties.get("chunk_index", 0)
                total_chunks = obj.properties.get("total_chunks", 1)

                context_excerpts.append(f"""---
**From: {title}** (chunk {chunk_idx}/{total_chunks})
{content}
---""")

            context_text = "\n".join(context_excerpts)

            # Step 5: Build prompt and call Ollama directly
            full_prompt = f"""You are a helpful AI assistant. The user has asked the following question:

"{query}"{additional_context_section}

Below are relevant excerpts from the user's notes that may help answer this question:

{context_text}

Based on the excerpts above{" and the additional context" if additional_context else ""}, provide a helpful and accurate answer to the user's question.
- If the excerpts contain relevant information, reference it specifically.
- If the excerpts don't contain enough information to fully answer, say so.
- Be concise but thorough."""

            # Call Ollama API directly
            ollama_response = requests.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_generation_model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=120
            )

            if ollama_response.status_code == 200:
                generated_text = ollama_response.json().get("response", "")
                print(f"✓ [GENERATIVE_SEARCH] Generated response: {len(generated_text)} chars")
            else:
                print(f"❌ [GENERATIVE_SEARCH] Ollama error: {ollama_response.status_code}")
                generated_text = "I encountered an error while generating a response."

            # Step 6: Build context notes for response
            context_notes = []
            for obj, _ in final_chunks:
                note_id = obj.properties.get("note_id")
                title = obj.properties.get("title", "")
                content = obj.properties.get("content", "")

                context_notes.append({
                    "note_id": note_id,
                    "title": title,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                })

            return {
                "response": generated_text if generated_text else "I couldn't generate a response based on your notes.",
                "context_notes": context_notes
            }

        except Exception as e:
            print(f"❌ [GENERATIVE_SEARCH] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "response": f"Error generating response: {str(e)}",
                "context_notes": []
            }

    def is_ready(self) -> bool:
        """Check if Weaviate is ready and responsive."""
        try:
            return self.client.is_ready()
        except Exception as e:
            print(f"Weaviate not ready: {e}")
            return False

    def close(self):
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            print("Weaviate connection closed")


# Global instance (initialized in main.py lifespan)
weaviate_service = None


def get_weaviate_service() -> WeaviateService:
    """Dependency injection for Weaviate service."""
    global weaviate_service
    if weaviate_service is None:
        weaviate_service = WeaviateService()
    return weaviate_service
