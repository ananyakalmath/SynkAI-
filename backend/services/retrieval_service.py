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

Rules:
- Answer ONLY using retrieved context.
- Do not hallucinate.
- If the answer is unavailable respond exactly: "I couldn't find that information in this meeting transcript."
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
        document_id: str,
        question: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieves relevant context chunks and generates an AI answer for the question.

        Args:
            document_id (str): Document ID to query.
            question (str): User question.
            top_k (int): Number of context chunks to retrieve.

        Returns:
            Dict[str, Any]: Object containing 'answer', 'sources', and 'model_used'.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")
        if not document_id or not document_id.strip():
            raise ValueError("Document ID cannot be empty.")

        logger.info(f"RAG query received: '{question}' (document_id: '{document_id}')...")

        # Step 1: Similarity Search in Vector Store (Top-5 chunks)
        sources = self.vector_service.similarity_search(
            query_text=question,
            document_id=document_id,
            top_k=top_k
        )

        if not sources:
            logger.warning(f"No matching context chunks found in vector database for document '{document_id}'.")
            return {
                "answer": "I couldn't find that information in this meeting transcript.",
                "sources": [],
                "model_used": self.ollama_service.model
            }

        # Step 2: Construct Context String
        context_parts = []
        clean_sources = []

        for idx, src in enumerate(sources, 1):
            chunk_num = src.get("chunk_number", idx)
            fname = src.get("filename", "transcript")
            text = src.get("chunk_text", "")

            context_parts.append(f"[Snippet #{idx} | Source: {fname} (Chunk #{chunk_num})]\n{text}")
            clean_sources.append({
                "filename": fname,
                "chunk_number": chunk_num
            })

        formatted_context = "\n\n".join(context_parts)

        # Step 3: Prompt Synthesizing LLM (qwen3)
        prompt = f"""Context:
{formatted_context}

Question:
{question}"""

        logger.info(f"Synthesizing RAG answer with Ollama ({self.ollama_service.model})...")
        answer = self.ollama_service.generate(
            prompt=prompt,
            system_prompt=RAG_SYSTEM_PROMPT,
            json_format=False,
            label="rag_chat"
        )

        logger.info("RAG response generated successfully.")

        # Post-process response to handle potential LLM phrasing deviations
        cleaned_answer = answer.strip()
        # If the response indicates failure/unavailability but didn't match the phrase exactly
        unavail_indicators = [
            "could not find", "couldn't find", "not found", "no information",
            "not mentioned", "not discussed", "not contain", "does not contain",
            "no mention", "not mention"
        ]
        if any(ind in cleaned_answer.lower() for ind in unavail_indicators) and len(cleaned_answer) < 150:
            cleaned_answer = "I couldn't find that information in this meeting transcript."


        return {
            "answer": cleaned_answer,
            "sources": clean_sources,
            "model_used": self.ollama_service.model
        }

