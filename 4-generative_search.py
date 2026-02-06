import weaviate
from weaviate.classes.init import AdditionalConfig, Timeout, Auth

weaviate_api_key = "user-a-key"
client = weaviate.connect_to_local(
    auth_credentials=Auth.api_key(weaviate_api_key),
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=600, insert=120)  # Increased for LLM generation
    )
)

print(client.is_connected())

book_collection = client.collections.get(name="Book")

# Generative Search

user_input = input("What query do you have for book recommendations? ")

response = book_collection.generate.near_text(
    query=user_input,
    limit=3,
    single_prompt="Here's the description of a book called {title}: {description}. Use the information available to you. Give a brief explanation as to why this book might be interesting to read to someone who originally prompted: " + user_input + "? Don't produce a list of reasons, just simplify it into a simple sentence or two."
)


print(f"Here are the recommended books for you based on your interest in {user_input}:")
for book in response.objects:
    print(f"Book Title: {book.properties['title']}")
    print(f"Book Description: {book.properties['description']}")
    print(book.generative.text)

    print('---\n\n\n')

client.close()
