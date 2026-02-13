# core/retrieval.py
import os
from typing import Tuple, Dict, Callable

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_core.structured_query import (
    StructuredQuery, Operation, Comparison, Comparator, Operator, Visitor
)

from domain.config import (
    VECTOR_DB_PATH, EMBEDDING_MODEL, RERANKER_MODEL, 
    LLM_MODEL, ANTHROPIC_API_KEY
)
from domain.prompts import SYSTEM_PROMPT
from domain.metadata_schema import METADATA_FIELD_INFO

# --- Custom Translator for FAISS (which expects a Callable filter) ---
class FunctionalTranslator(Visitor):
    """Translate structure queries to a callable filter function for FAISS."""
    allowed_operators = [Operator.AND, Operator.OR]
    allowed_comparators = [
        Comparator.EQ,
        Comparator.NE,
        Comparator.GT,
        Comparator.GTE,
        Comparator.LT,
        Comparator.LTE,
    ]

    def _compare(self, value, comparator, target):
        try:
            if comparator == Comparator.EQ: return value == target
            if comparator == Comparator.NE: return value != target
            if comparator == Comparator.GT: return value > target
            if comparator == Comparator.GTE: return value >= target
            if comparator == Comparator.LT: return value < target
            if comparator == Comparator.LTE: return value <= target
        except TypeError:
            # Handle mixed types (e.g. string vs float) gracefully
            return False
        return False

    def visit_operation(self, operation: Operation) -> Callable:
        args = [arg.accept(self) for arg in operation.arguments]
        def _filter(metadata: Dict) -> bool:
            results = [f(metadata) for f in args]
            if operation.operator == Operator.AND:
                return all(results)
            elif operation.operator == Operator.OR:
                return any(results)
            return False
        return _filter

    def visit_comparison(self, comparison: Comparison) -> Callable:
        def _filter(metadata: Dict) -> bool:
            val = metadata.get(comparison.attribute)
            if val is None: return False
            return self._compare(val, comparison.comparator, comparison.value)
        return _filter

    def visit_structured_query(
        self, structured_query: StructuredQuery
    ) -> Tuple[str, dict]:
        if structured_query.filter is None:
            kwargs = {}
        else:
            kwargs = {"filter": structured_query.filter.accept(self)}
        return structured_query.query, kwargs

def get_rag_chain():
    if not os.path.exists(VECTOR_DB_PATH):
        raise FileNotFoundError(f"Vector store not found at {VECTOR_DB_PATH}.")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)

    # Setup LLM
    llm = ChatAnthropic(
        model_name=LLM_MODEL,
        temperature=0,
        api_key=ANTHROPIC_API_KEY
    )

    # --- SELF-QUERY RETRIEVER ---
    document_content_description = "DCPR 2034 Regulations for Mumbai"
    
    self_query_retriever = SelfQueryRetriever.from_llm(
        llm,
        vectorstore,
        document_content_description,
        METADATA_FIELD_INFO,
        structured_query_translator=FunctionalTranslator(), # Use our custom translator
        verbose=True
    )
    
    # --- HYBRID PIPELINE (Self-Query + Reranker) ---
    reranker_model = HuggingFaceCrossEncoder(model_name=RERANKER_MODEL)
    compressor = CrossEncoderReranker(model=reranker_model, top_n=7)
    
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, 
        base_retriever=self_query_retriever
    )

    # --- HISTORY AWARE RETRIEVER ---
    
    # Contextualize question prompt
    # Rephrases the latest user question using the chat history to make it a standalone question
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    history_aware_retriever = create_history_aware_retriever(
        llm, compression_retriever, contextualize_q_prompt
    )

    # --- QA CHAIN ---
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Create Chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain
