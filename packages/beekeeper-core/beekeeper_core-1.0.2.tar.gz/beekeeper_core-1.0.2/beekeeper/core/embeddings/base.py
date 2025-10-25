from abc import ABC, abstractmethod
from enum import Enum
from typing import List

import numpy as np
from beekeeper.core.document import Document
from beekeeper.core.schema import TransformerComponent
from beekeeper.core.utils.pairwise import cosine_similarity
from deprecated import deprecated

Embedding = List[float]


class SimilarityMode(str, Enum):
    """Modes for similarity."""

    COSINE = "cosine"
    DOT_PRODUCT = "dot_product"
    EUCLIDEAN = "euclidean"


def similarity(
    embedding1: Embedding,
    embedding2: Embedding,
    mode: SimilarityMode = SimilarityMode.COSINE,
):
    """Get embedding similarity."""
    if mode == SimilarityMode.EUCLIDEAN:
        return -float(np.linalg.norm(np.array(embedding1) - np.array(embedding2)))

    elif mode == SimilarityMode.DOT_PRODUCT:
        return np.dot(embedding1, embedding2)

    else:
        return cosine_similarity(embedding1, embedding2)


class BaseEmbedding(TransformerComponent, ABC):
    """Abstract base class defining the interface for embedding models."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseEmbedding"

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[Embedding]:
        """Embed a list of text strings."""

    def embed_text(self, query: str) -> Embedding:
        """Embed a single text string."""
        return self.embed_texts([query])[0]

    def embed_documents(self, documents: List[Document]) -> List[Document]:
        """Embed a list of documents and set them in the 'embedding' attribute."""
        texts = [document.get_content() for document in documents]
        embeddings = self.embed_texts(texts)

        for document, embedding in zip(documents, embeddings):
            document.embedding = embedding

        return documents

    @deprecated(
        reason="'get_text_embedding()' is deprecated and will be removed in a future version. Use 'embed_text' instead.",
        version="1.0.2",
        action="always",
    )
    def get_text_embedding(self, query: str) -> Embedding:
        return self.embed_text(query)

    @deprecated(
        reason="'get_texts_embedding()' is deprecated and will be removed in a future version. Use 'embed_texts' instead.",
        version="1.0.2",
        action="always",
    )
    def get_texts_embedding(self, texts: List[str]) -> List[Embedding]:
        return self.embed_texts(texts)

    @deprecated(
        reason="'get_documents_embedding()' is deprecated and will be removed in a future version. Use 'embed_documents' instead.",
        version="1.0.2",
        action="always",
    )
    def get_documents_embedding(self, documents: List[Document]) -> List[Document]:
        return self.embed_documents(documents)

    @staticmethod
    def similarity(
        embedding1: Embedding,
        embedding2: Embedding,
        mode: SimilarityMode = SimilarityMode.COSINE,
    ):
        """Get embedding similarity."""
        return similarity(embedding1, embedding2, mode)

    def __call__(self, documents: List[Document]) -> List[Document]:
        return self.get_documents_embedding(documents)
