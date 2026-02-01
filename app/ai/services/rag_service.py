import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class RAGService:
    def __init__(self):
        # Local Qdrant (file-based)
        self.qdrant_path = os.getenv("QDRANT_PATH", "qdrant_data")
        self.collection_name = "seo_knowledge"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        try:
            self.client = QdrantClient(path=self.qdrant_path)
            self._init_collection()
        except Exception as e:
            print(f"Warning: Qdrant init failed: {e}")
            self.client = None
        
        # Only import OpenAI if key exists
        self.openai_client = None
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                print(f"Warning: OpenAI client init failed: {e}")

    def _init_collection(self):
        if not self.client:
            return
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection if it doesn't exist
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
            except Exception as e:
                print(f"Warning: Could not create collection: {e}")

    def retrieve_context(self, query: str, limit: int = 3) -> str:
        # Gracefully handle missing dependencies
        if not self.client or not self.openai_client:
            return "RAG not available (missing OpenAI API key or Qdrant)."
        
        try:
            # Generate embedding
            resp = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_vec = resp.data[0].embedding
            
            # Search Qdrant
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vec,
                limit=limit
            )
            
            if not hits:
                return "No relevant RAG context found."
            
            return "\n---\n".join([h.payload.get("text", "") for h in hits])
        except Exception as e:
            return f"RAG retrieval failed: {e}"

    def add_document(self, text: str, metadata: dict):
        if not self.client or not self.openai_client:
            return
        
        try:
            # Generate embedding
            resp = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            vector = resp.data[0].embedding
            
            # Upsert to Qdrant
            import uuid
            payload = metadata.copy() if metadata else {}
            payload["text"] = text
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload
            )
            self.client.upsert(collection_name=self.collection_name, points=[point])
        except Exception as e:
            print(f"Warning: Could not add document to RAG: {e}")

rag_service = RAGService()
