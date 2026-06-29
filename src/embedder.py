from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

class Embedder:
    def __init__(self, model_name=MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts, batch_size=256, show_progress=True):
        """Embed a list of texts. Returns numpy array of shape (len(texts), dim)."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

    def embed_single(self, text):
        """Embed a single text."""
        return self.embed([text], show_progress=False)[0]

# Global instance (lazy loaded)
_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder