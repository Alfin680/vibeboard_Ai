import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()  # make sure .env is loaded

def get_pinecone_index():
    """Initialize and return the Pinecone index."""
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "vibeboard-index"

    # Create the index if it doesn't exist
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"🪶 Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # matches text-embedding-3-small
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print("✅ Index created successfully!")

    # Connect to the index
    index = pc.Index(index_name)
    return index
