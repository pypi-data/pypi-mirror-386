from typing import Any, List, Literal

from beekeeper.core.embeddings import BaseEmbedding, Embedding
from pydantic.v1 import BaseModel, PrivateAttr


class HuggingFaceEmbedding(BaseModel, BaseEmbedding):
    """
    HuggingFace `sentence_transformers` embedding models.

    Attributes:
        model_name (str): Hugging Face model to be used. Defaults to `sentence-transformers/all-MiniLM-L6-v2`.
        device (str, optional): Device to run the model on. Supports `cpu` and `cuda`. Defaults to `cpu`.

    Example:
        ```python
        from beekeeper.embeddings.huggingface import HuggingFaceEmbedding

        embedding = HuggingFaceEmbedding()
        ```
    """

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: Literal["cpu", "cuda"] = "cpu"

    _client: Any = PrivateAttr()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        from sentence_transformers import SentenceTransformer

        self._client = SentenceTransformer(self.model_name, device=self.device)

    def embed_texts(self, texts: List[str]) -> List[Embedding]:
        """
        Compute embeddings for a list of texts.

        Args:
            texts (List[str]): A list of input strings for which to compute embeddings.
        """
        return self._client.encode(texts).tolist()
