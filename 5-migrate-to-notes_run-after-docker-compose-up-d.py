"""
Migration script: Convert from Book collection to Note collection.
Run this script once to migrate from the LocalRAG book demo to the HexaNote notebook app.

Credits:
- Original LocalRAG Book demo by https://github.com/itsajchan/LocalRAG/tree/main

"""
import weaviate
import weaviate.classes as wvc
import weaviate.classes.config as wc
from weaviate.classes.init import Auth

# Configuration (same as existing LocalRAG scripts)
WEAVIATE_API_KEY = "user-a-key"
WEAVIATE_URL = "http://localhost:8080"
OLLAMA_URL = "http://ollama:11434"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
GENERATION_MODEL = "llama3.2:1b"


def main():
    print("Starting migration from Book to Note collection...")

    # Connect to Weaviate
    client = weaviate.connect_to_local(
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY)
    )

    try:
        # Check connection
        if not client.is_ready():
            print("❌ Weaviate is not ready. Make sure docker compose is running.")
            return

        print("✓ Connected to Weaviate")

        # Delete Book collection if it exists
        try:
            client.collections.delete("Book")
            print("✓ Deleted existing 'Book' collection")
        except Exception as e:
            print(f"  (Book collection doesn't exist or already deleted)")

        # Delete Note collection if it exists (to recreate with new config)
        try:
            client.collections.delete("Note")
            print("✓ Deleted existing 'Note' collection")
        except Exception as e:
            print(f"  (Note collection doesn't exist or already deleted)")

        # Create Note collection
        print("Creating 'Note' collection...")
        client.collections.create(
            name="Note",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(
                api_endpoint=OLLAMA_URL,
                model=EMBEDDING_MODEL,
            ),
            generative_config=wvc.config.Configure.Generative.ollama(
                api_endpoint=OLLAMA_URL,
                model=GENERATION_MODEL,
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
        print("✓ Created 'Note' collection")

        # Verify collection
        note_collection = client.collections.get("Note")
        config = note_collection.config.get()
        print(f"✓ Note collection verified: {config.name}")
        print(f"  Properties: {[p.name for p in config.properties]}")

        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend: cd LocalRAG && docker compose up -d")
        print("2. Test the API: curl http://localhost:8001/api/v1/health")
        print("3. View API docs: http://localhost:8001/docs")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    main()
