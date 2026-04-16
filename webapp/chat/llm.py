"""
LightRAG — naive vector search only.

Insertion: LLM completely mocked (returns empty), only embeddings stored.
Query:     Manual RAG — embed question, find chunks, answer with Ollama.
"""

import asyncio
import logging
import os

import requests as _requests
from django.conf import settings

logger = logging.getLogger(__name__)

_rag = None
_loop = None


async def _noop_llm(*args, **kwargs):
    return ""


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def _get_rag():
    global _rag
    if _rag is not None:
        return _rag

    try:
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc

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
            tasks = [loop.run_in_executor(None, _sync_embed_one, t) for t in texts]
            results = await asyncio.gather(*tasks)
            return np.array(results)

        os.makedirs(settings.LIGHTRAG_STORAGE_DIR, exist_ok=True)

        _rag = LightRAG(
            working_dir=settings.LIGHTRAG_STORAGE_DIR,
            llm_model_func=_noop_llm,
            llm_model_name=settings.LLM_MODEL,
            llm_model_max_async=1,
            entity_extract_max_gleaning=0,
            chunk_token_size=400,
            chunk_overlap_token_size=50,
            embedding_func=EmbeddingFunc(
                embedding_dim=768,
                max_token_size=512,
                func=_embed,
            ),
        )
        _get_loop().run_until_complete(_rag.initialize_storages())
        logger.info("LightRAG initialized (naive/noop, model=%s)", settings.LLM_MODEL)
    except Exception as e:
        logger.error("LightRAG init error: %s", e)
        _rag = None

    return _rag


def _embed_query(text: str) -> list:
    resp = _requests.post(
        f"{settings.OLLAMA_URL}/api/embeddings",
        json={"model": settings.EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def insert_text(text: str) -> None:
    rag = _get_rag()
    if rag is None:
        return
    _get_loop().run_until_complete(rag.ainsert(text))


def query(question: str, top_k: int = 5) -> str:
    rag = _get_rag()
    if rag is None:
        return "LightRAG başlatılamadı."

    try:
        # 1. Find top-k similar chunks from LightRAG's vector store
        results = _get_loop().run_until_complete(
            rag.chunks_vdb.query(question, top_k=top_k)
        )
        if not results:
            return "İlgili bilgi bulunamadı."

        context = "\n\n---\n\n".join(r.get("content", "") for r in results)

        # 3. Answer with Ollama
        prompt = (
            f"Aşağıdaki bilgileri kullanarak soruyu Türkçe olarak yanıtla.\n\n"
            f"Bilgiler:\n{context}\n\n"
            f"Soru: {question}\n\nYanıt:"
        )
        resp = _requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={"model": settings.LLM_MODEL, "prompt": prompt, "stream": False,
                  "options": {"num_ctx": 3000, "temperature": 0.5}},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "Yanıt alınamadı.")
    except Exception as e:
        logger.error("Query error: %s", e)
        return f"Sorgu hatası: {e}"
