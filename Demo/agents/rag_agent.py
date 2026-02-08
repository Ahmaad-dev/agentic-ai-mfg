"""
RAGAgent - Wissensbasis-gestützte Antworten
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from azure.search.documents.models import VectorizedQuery
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """RAG Agent - Wissensbasis-gestützte Antworten"""
    
    def __init__(
        self,
        aoai_client,
        model_name: str,
        emb_model_name: str,
        search_client,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        routing_description: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 700,
        max_history_pairs: int = 2,
        top_k: int = 8,
        min_score: float = 0.5
    ):
        """
        Args:
            aoai_client: Azure OpenAI Client
            model_name: Deployment-Name des Chat-Modells
            emb_model_name: Deployment-Name des Embedding-Modells
            search_client: Azure Search Client
            system_prompt: Custom System-Prompt (None = default)
            description: Kurze Beschreibung (für Logging)
            routing_description: Routing-optimierte Beschreibung (für Orchestrator)
            temperature: LLM Temperature (default: 0.3 für Faktentreue)
            max_tokens: Max Output-Tokens (default: 700)
            max_history_pairs: Anzahl Message-Paare (default: 2 = 4 Messages)
            top_k: Anzahl Retrieval-Ergebnisse (default: 8)
            min_score: Minimaler Relevanz-Score (default: 0.5)
        """
        super().__init__(
            name="RAG",
            system_prompt=system_prompt,
            description=description,
            routing_description=routing_description,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_pairs=max_history_pairs
        )
        
        self.aoai_client = aoai_client
        self.model_name = model_name
        self.emb_model_name = emb_model_name
        self.search_client = search_client
        self.top_k = top_k
        self.min_score = min_score
    
    def _embed(self, text: str):
        """Erstellt Embedding für Text"""
        try:
            r = self.aoai_client.embeddings.create(
                model=self.emb_model_name,
                input=text
            )
            return r.data[0].embedding
        except Exception as e:
            logger.error(f"[{self.name} Agent] Embedding-Fehler: {e}")
            return None
    
    def _retrieve_context(self, query: str) -> Tuple[str, List[str], float, bool]:
        """Sucht relevante Dokumente"""
        try:
            qv = self._embed(query)
            if qv is None:
                return "", [], 0.0, False

            vector_query = VectorizedQuery(
                vector=qv,
                k_nearest_neighbors=self.top_k,
                fields="contentVector"
            )

            results = self.search_client.search(
                search_text="",
                vector_queries=[vector_query],
                select=["title", "source", "content", "page"]
            )

            chunks = []
            sources = []
            scores = []
            
            for r in results:
                score = r.get("@search.score", 0.0)
                scores.append(score)
                
                if score >= self.min_score:
                    title = r.get("title", "")
                    source = r.get("source", "")
                    content = r.get("content", "")
                    page = r.get("page")
                    
                    chunks.append(f"- {title} ({source}): {content}")
                    
                    if source:
                        source_ref = f"{source} (Seite {page})" if page else source
                        sources.append(source_ref)
            
            # Optional: Retrieval-Ergebnisse loggen
            import main
            if main.LOGGING_CONFIG.get("log_retrieval_results", False):
                retrieval_summary = f"Query: {query}\nGefunden: {len(chunks)} relevante Chunks (Score >= {self.min_score})\n"
                for i, (chunk, score) in enumerate(zip(chunks[:3], scores[:3]), 1):  # Nur Top 3
                    retrieval_summary += f"{i}. Score: {score:.3f} - {chunk[:100]}...\n"
                logger.info(f"[{self.name} Agent] RETRIEVAL RESULTS:\n{retrieval_summary}")
            
            max_score = max(scores) if scores else 0.0
            has_relevant_results = len(chunks) > 0
            
            if not has_relevant_results:
                logger.warning(
                    f"[{self.name} Agent] Keine Ergebnisse über Threshold {self.min_score} "
                    f"(Max-Score: {max_score:.3f}, TopK={self.top_k})"
                )
            else:
                logger.info(
                    f"[{self.name} Agent] Relevanz-Score: {max_score:.3f} "
                    f"({len(chunks)} Ergebnisse über {self.min_score})"
                )
            
            return "\n".join(chunks), sorted(set(sources)), max_score, has_relevant_results
            
        except Exception as e:
            logger.error(f"[{self.name} Agent] Suchfehler: {e}")
            return "", [], 0.0, False
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Führt RAG-basierte Antwort durch"""
        logger.info(f"[{self.name} Agent] Verarbeite Anfrage: {user_input[:100]}")
        
        # Retrieval durchführen
        doc_context, sources, relevance_score, has_relevant = self._retrieve_context(user_input)
        
        if not has_relevant:
            logger.info(
                f"[{self.name} Agent] Keine relevanten Dokumente gefunden "
                f"(Score: {relevance_score:.3f})"
            )
            return {
                "response": (
                    "Keine relevanten Dokumente gefunden. "
                    f"Maximaler Relevanz-Score: {relevance_score:.3f} (Schwellenwert: {self.min_score})"
                ),
                "metadata": {
                    "agent": self.name,
                    "sources": [],
                    "relevance_score": relevance_score,
                    "retrieval_success": False,
                    "raw_result": True,  # Signal für Orchestrator
                    "config": {
                        "top_k": self.top_k,
                        "min_score": self.min_score
                    }
                }
            }
        
        # Antwort mit Kontext generieren
        chat_history = self._get_chat_history(context)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *chat_history,
            {
                "role": "user",
                "content": (
                    f"KONTEXT AUS WISSENSBASIS:\n{doc_context}\n\n"
                    f"---\n\n"
                    f"FRAGE: {user_input}\n\n"
                    f"Beantworte die Frage basierend auf dem Kontext. Zitiere die relevanten Quellen."
                )
            }
        ]
        
        # Optional: LLM Request loggen
        import main
        if main.LOGGING_CONFIG.get("log_llm_requests", False):
            messages_str = json.dumps(messages, indent=2, ensure_ascii=False)
            logger.info(f"[{self.name} Agent] LLM REQUEST:\n{messages_str}")
        
        try:
            # LLM-Call Parameter vorbereiten
            call_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature
            }
            
            if self.max_tokens is not None:
                call_params["max_tokens"] = self.max_tokens
            
            response = self.aoai_client.chat.completions.create(**call_params)
            
            answer = response.choices[0].message.content
            
            # Optional: LLM Response loggen
            if main.LOGGING_CONFIG.get("log_llm_responses", False):
                logger.info(f"[{self.name} Agent] LLM RESPONSE:\n{answer}")
            
            logger.info(
                f"[{self.name} Agent] Antwort generiert mit {len(sources)} Quellen "
                f"(Temp={self.temperature}, History={len(chat_history)} msgs)"
            )
            
            return {
                "response": answer,  # Rohe LLM-Response
                "metadata": {
                    "agent": self.name,
                    "sources": sources,
                    "relevance_score": relevance_score,
                    "retrieval_success": True,
                    "raw_result": True,  # Signal für Orchestrator
                    "config": {
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "history_pairs": self.max_history_pairs,
                        "top_k": self.top_k,
                        "min_score": self.min_score
                    }
                }
            }
        except Exception as e:
            logger.error(f"[{self.name} Agent] Fehler: {e}")
            return {
                "response": f"Es gab einen Fehler bei der Verarbeitung: {str(e)}",
                "metadata": {"agent": self.name, "error": str(e)}
            }
