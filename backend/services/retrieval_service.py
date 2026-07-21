"""
Retrieval Service for SynkAI.
Orchestrates Retrieval-Augmented Generation (RAG) by fetching context chunks from VectorService and querying Ollama.
"""

from typing import List, Dict, Any, Optional
from backend.services.vector_service import VectorService
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

RAG_SYSTEM_PROMPT = """You are SynkAI, an intelligent meeting assistant.
Answer the user's question accurately based ONLY on the provided meeting context snippets below.

Rules:
1. If the provided context contains enough information, give a direct, concise, and helpful answer.
2. Highlight specific details, names, owners, deadlines, or decisions mentioned in the context.
3. If the context does not contain the answer, state clearly: "Based on the provided meeting transcript context, I could not find information regarding your question."
4. Do not make up facts or extrapolate beyond the provided text.

Context Snippets:
{context}
"""


class RetrievalService:
    """
    RAG service combining vector similarity retrieval with LLM answer synthesis.
    """

    def __init__(self, vector_service: Optional[VectorService] = None, ollama_service: Optional[OllamaService] = None):
        self.vector_service = vector_service or VectorService()
        self.ollama_service = ollama_service or OllamaService()

    def answer_question(
        self,
        question: str,
        filename: Optional[str] = None,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Retrieves relevant context chunks and generates an AI answer for the question.

        Args:
            question (str): User question.
            filename (Optional[str]): Target transcript filename to query against.
            top_k (int): Number of context chunks to retrieve.

        Returns:
            Dict[str, Any]: Object containing 'answer', 'sources', and 'model_used'.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        logger.info(f"RAG query received: '{question}' (filename filter: '{filename}')...")

        # Step 1: Similarity Search in Vector Store
        sources = self.vector_service.similarity_search(
            query_text=question,
            filename=filename,
            top_k=top_k
        )

        if not sources:
            logger.warning("No matching context chunks found in vector database.")
            return {
                "answer": "No relevant meeting transcript context was found to answer your question.",
                "sources": [],
                "model_used": self.ollama_service.model
            }

        # Step 2: Construct Context String
        context_parts = []
        clean_sources = []

        for idx, src in enumerate(sources, 1):
            chunk_num = src.get("chunk_number", idx)
            fname = src.get("filename", "transcript")
            text = src.get("text", "")

            context_parts.append(f"[Snippet #{idx} | Source: {fname} (Chunk #{chunk_num})]\n{text}")
            clean_sources.append({
                "filename": fname,
                "chunk_number": chunk_num,
                "text": text
            })

        formatted_context = "\n\n".join(context_parts)

        # Step 3: Prompt Synthesizing LLM (qwen3)
        system_instructions = RAG_SYSTEM_PROMPT.format(context=formatted_context)
        prompt = f"User Question: {question}\n\nProvide your answer below:"

        logger.info(f"Synthesizing RAG answer with Ollama ({self.ollama_service.model})...")
        answer = self.ollama_service.generate(
            prompt=prompt,
            system_prompt=system_instructions,
            json_format=False
        )

        logger.info("RAG response generated successfully.")

        return {
            "answer": answer,
            "sources": clean_sources,
            "model_used": self.ollama_service.model
        }
