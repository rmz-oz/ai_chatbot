"""
LightRAG integration with Ollama.

Retrieval modes:
  naive  — simple vector similarity (baseline)
  local  — entity-level graph context
  global — community-level graph context
  hybrid — local + global combined (recommended)
"""

import asyncio
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

_rag = None


def _get_rag():
    global _rag
    if _rag is not None:
        return _rag

    try:
        from lightrag import LightRAG
        from lightrag.llm.ollama import ollama_model_complete
        from lightrag.utils import EmbeddingFunc
        import requests as _requests

        ollama_url = settings.OLLAMA_URL

        def _sync_embed_one(text: str) -> list:
            resp = _requests.post(
                f"{ollama_url}/api/embeddings",
                json={"model": settings.EMBED_MODEL, "prompt": text},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["embedding"]

        async def _embed(texts):
            import numpy as np
            loop = asyncio.get_event_loop()
            results = []
            for text in texts:
                vec = await loop.run_in_executor(None, _sync_embed_one, text)
                results.append(vec)
            return np.array(results)

        os.makedirs(settings.LIGHTRAG_STORAGE_DIR, exist_ok=True)

        _rag = LightRAG(
            working_dir=settings.LIGHTRAG_STORAGE_DIR,
            llm_model_func=ollama_model_complete,
            llm_model_name=settings.LLM_MODEL,
            llm_model_kwargs={
                "host": ollama_url,
                "options": {"num_ctx": 4096, "temperature": 0.5},
            },
            embedding_func=EmbeddingFunc(
                embedding_dim=768,
                max_token_size=8192,
                func=_embed,
            ),
        )
        asyncio.run(_rag.initialize_storages())
        logger.info("LightRAG initialized (model=%s)", settings.LLM_MODEL)
    except Exception as e:
        logger.error("LightRAG init error: %s", e)
        _rag = None

    return _rag


def insert_text(text: str) -> None:
    rag = _get_rag()
    if rag is None:
        return
    asyncio.run(rag.ainsert(text))


def query(question: str, mode: str = "hybrid") -> str:
    rag = _get_rag()
    if rag is None:
        return "LightRAG başlatılamadı. Ollama servisini kontrol edin."
    try:
        from lightrag import QueryParam
        result = asyncio.run(rag.aquery(question, param=QueryParam(mode=mode)))
        return result or "Bilgi bulunamadı."
    except Exception as e:
        logger.error("LightRAG query error: %s", e)
        return f"Sorgu hatası: {e}"
