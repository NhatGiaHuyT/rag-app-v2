import json
import base64
from datetime import datetime
from typing import List, AsyncGenerator
import requests
from sqlalchemy.orm import Session
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document as LangchainDocument
from app.core.config import settings
from app.models.chat import Message
from app.models.knowledge import KnowledgeBase, Document, DocumentChunk
from app.models.admin import ManualQAEntry, SystemConfig
from langchain.globals import set_verbose, set_debug
from app.services.vector_store import VectorStoreFactory
from app.services.embedding.embedding_factory import EmbeddingsFactory
from app.services.llm.llm_factory import LLMFactory
from app.services.runtime_config import get_runtime_model_settings

set_verbose(True)
set_debug(True)


def _score_chunk(query: str, page_content: str) -> int:
    terms = [term for term in query.lower().split() if len(term) >= 2]
    text = page_content.lower()
    return sum(text.count(term) for term in terms)


def _retrieve_chunks_from_db(
    db: Session,
    query: str,
    knowledge_base_ids: List[int],
    limit: int = 4,
) -> List[LangchainDocument]:
    chunk_rows = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.kb_id.in_(knowledge_base_ids))
        .all()
    )
    ranked: list[tuple[int, DocumentChunk]] = []
    for row in chunk_rows:
        metadata = dict(row.chunk_metadata or {})
        page_content = metadata.get("page_content", "")
        if not page_content.strip():
            continue
        ranked.append((_score_chunk(query, page_content), row))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = [row for score, row in ranked if score > 0][:limit]
    if not selected:
        selected = [row for _, row in ranked[:limit]]

    documents: List[LangchainDocument] = []
    for row in selected:
        metadata = dict(row.chunk_metadata or {})
        page_content = metadata.pop("page_content", "")
        if not page_content.strip():
            continue
        documents.append(
            LangchainDocument(
                page_content=page_content,
                metadata=metadata,
            )
        )
    return documents


def _generate_ollama_answer(
    db: Session,
    query: str,
    context_docs: List[LangchainDocument],
) -> str:
    runtime_settings = get_runtime_model_settings(db)
    base_url = runtime_settings.get("ollama_api_base", settings.OLLAMA_API_BASE).rstrip("/")
    model = runtime_settings.get("chat_model") or settings.OLLAMA_MODEL

    context_lines = []
    for index, doc in enumerate(context_docs, start=1):
        excerpt = doc.page_content.strip().replace("\r", "\n")
        if len(excerpt) > 900:
            excerpt = excerpt[:900] + "..."
        context_lines.append(f"[{index}] {excerpt}")

    prompt = (
        "You are a helpful RAG assistant. Answer the user's question only from the provided context. "
        "If the context is insufficient, say what information is missing. "
        "Cite the supporting context using [citation:x]. Keep the answer concise.\n\n"
        f"Question:\n{query}\n\n"
        "Context:\n"
        + "\n\n".join(context_lines)
    )

    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    return (payload.get("response") or "").strip()


def _build_excerpt_fallback(context_docs: List[LangchainDocument]) -> str:
    excerpts = []
    for index, doc in enumerate(context_docs[:3], start=1):
        excerpt = " ".join(doc.page_content.strip().split())
        if len(excerpt) > 240:
            excerpt = excerpt[:240] + "..."
        excerpts.append(f"{index}. {excerpt}")
    joined = "\n".join(excerpts) if excerpts else "No relevant excerpts were found."
    return (
        "The local Ollama chat model is currently unavailable on this machine, so I can't generate a full answer right now. "
        "Here are the most relevant excerpts from the knowledge base:\n"
        f"{joined}"
    )

async def generate_response(
    query: str,
    messages: dict,
    knowledge_base_ids: List[int],
    chat_id: int,
    db: Session
) -> AsyncGenerator[str, None]:
    try:
        manual_entry = (
            db.query(ManualQAEntry)
            .filter(ManualQAEntry.is_active.is_(True))
            .filter(ManualQAEntry.question.ilike(f"%{query}%"))
            .order_by(ManualQAEntry.updated_at.desc())
            .first()
        )

        # Create user message
        user_message = Message(
            content=query,
            role="user",
            chat_id=chat_id
        )
        db.add(user_message)
        db.commit()
        
        # Create bot message placeholder
        bot_message = Message(
            content="",
            role="assistant",
            chat_id=chat_id
        )
        db.add(bot_message)
        db.commit()

        if manual_entry:
            bot_message.content = manual_entry.answer
            db.add(bot_message)
            db.commit()
            yield f"0:{json.dumps(manual_entry.answer)}\n"
            yield 'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
            return
        
        # Get knowledge bases and their documents
        knowledge_bases = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.id.in_(knowledge_base_ids))
            .all()
        )

        runtime_settings = get_runtime_model_settings(db)
        chat_provider = (runtime_settings.get("chat_provider") or settings.CHAT_PROVIDER).lower()

        if chat_provider == "ollama":
            context_docs = _retrieve_chunks_from_db(db, query, knowledge_base_ids)
            if not context_docs:
                error_msg = (
                    "I couldn't find any stored knowledge chunks for this chat yet. "
                    "Please upload and process documents for the selected knowledge base first."
                )
                yield f"0:{json.dumps(error_msg)}\n"
                yield 'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
                bot_message.content = error_msg
                db.commit()
                return

            serializable_context = [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in context_docs
            ]
            escaped_context = json.dumps({"context": serializable_context})
            base64_context = base64.b64encode(escaped_context.encode()).decode()
            separator = "__LLM_RESPONSE__"
            yield f'0:"{base64_context}{separator}"\n'

            try:
                answer_chunk = _generate_ollama_answer(db, query, context_docs)
                if not answer_chunk:
                    answer_chunk = (
                        "I couldn't generate an answer from the current knowledge base contents. "
                        "Please try rephrasing the question."
                    )
            except Exception:
                answer_chunk = _build_excerpt_fallback(context_docs)
            full_response = base64_context + separator + answer_chunk
            yield f"0:{json.dumps(answer_chunk)}\n"

            touched_document_ids = {
                int(doc.metadata["document_id"])
                for doc in context_docs
                if doc.metadata.get("document_id")
            }
            if touched_document_ids:
                for document in db.query(Document).filter(Document.id.in_(list(touched_document_ids))).all():
                    document.query_count = (document.query_count or 0) + 1
                    document.last_queried_at = datetime.utcnow()
                    db.add(document)

            bot_message.content = full_response
            db.commit()
            yield 'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
            return
        
        # Initialize embeddings
        embeddings = EmbeddingsFactory.create(db=db)
        
        # Create a vector store for each knowledge base
        vector_stores = []
        for kb in knowledge_bases:
            documents = db.query(Document).filter(Document.knowledge_base_id == kb.id).all()
            if documents:
                # Use the factory to create the appropriate vector store
                vector_store = VectorStoreFactory.create(
                    store_type=settings.VECTOR_STORE_TYPE,  # 'chroma' or other supported types
                    collection_name=f"kb_{kb.id}",
                    embedding_function=embeddings,
                )
                collection_count = vector_store._store._collection.count()
                print(f"Collection {f'kb_{kb.id}'} count:", collection_count)
                if collection_count > 0:
                    vector_stores.append(vector_store)
        
        if not vector_stores:
            error_msg = (
                "I couldn't find any indexed knowledge for this chat yet. "
                "Please upload and process documents for the selected knowledge base first."
            )
            yield f"0:{json.dumps(error_msg)}\n"
            yield 'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
            bot_message.content = error_msg
            db.commit()
            return
        
        # Use first vector store for now
        retriever = vector_stores[0].as_retriever()
        
        # Initialize the language model
        # We assemble and emit our own response chunks, so non-streaming LLM calls are
        # more reliable here than provider-level streaming.
        llm = LLMFactory.create(db=db, streaming=False)
        
        # Create contextualize question prompt
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, just "
            "reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        
        # Create history aware retriever
        history_aware_retriever = create_history_aware_retriever(
            llm, 
            retriever,
            contextualize_q_prompt
        )

        # Create QA prompt
        qa_system_prompt = (
            "You are given a user question, and please write clean, concise and accurate answer to the question. "
            "You will be given a set of related contexts to the question, which are numbered sequentially starting from 1. "
            "Each context has an implicit reference number based on its position in the array (first context is 1, second is 2, etc.). "
            "Please use these contexts and cite them using the format [citation:x] at the end of each sentence where applicable. "
            "Your answer must be correct, accurate and written by an expert using an unbiased and professional tone. "
            "Please limit to 1024 tokens. Do not give any information that is not related to the question, and do not repeat. "
            "Say 'information is missing on' followed by the related topic, if the given context do not provide sufficient information. "
            "If a sentence draws from multiple contexts, please list all applicable citations, like [citation:1][citation:2]. "
            "Other than code and specific names and citations, your answer must be written in the same language as the question. "
            "Be concise.\n\nContext: {context}\n\n"
            "Remember: Cite contexts by their position number (1 for first context, 2 for second, etc.) and don't blindly "
            "repeat the contexts verbatim."
        )
        response_settings = (
            db.query(SystemConfig).filter(SystemConfig.key == "response_settings").first()
        )
        max_answer_length = 1024
        if response_settings and response_settings.value:
            max_answer_length = int(response_settings.value.get("max_answer_length", 1024))
        qa_system_prompt += f" Keep the answer within about {max_answer_length} characters when possible."
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])

        # 修改 create_stuff_documents_chain 来自定义 context 格式
        document_prompt = PromptTemplate.from_template("\n\n- {page_content}\n\n")

        # Create QA chain
        question_answer_chain = create_stuff_documents_chain(
            llm,
            qa_prompt,
            document_variable_name="context",
            document_prompt=document_prompt
        )

        # Create retrieval chain
        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain,
        )

        # Generate response
        chat_history = []
        for message in messages["messages"]:
            if message["role"] == "user":
                chat_history.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                # if include __LLM_RESPONSE__, only use the last part
                if "__LLM_RESPONSE__" in message["content"]:
                    message["content"] = message["content"].split("__LLM_RESPONSE__")[-1]
                chat_history.append(AIMessage(content=message["content"]))

        full_response = ""
        touched_document_ids = set()
        result = await rag_chain.ainvoke({
            "input": query,
            "chat_history": chat_history
        })

        serializable_context = []
        for context in result.get("context", []):
            document_id = context.metadata.get("document_id")
            if document_id:
                touched_document_ids.add(int(document_id))
            serializable_doc = {
                "page_content": context.page_content.replace('"', '\\"'),
                "metadata": context.metadata,
            }
            serializable_context.append(serializable_doc)

        if serializable_context:
            escaped_context = json.dumps({
                "context": serializable_context
            })
            base64_context = base64.b64encode(escaped_context.encode()).decode()
            separator = "__LLM_RESPONSE__"
            yield f'0:"{base64_context}{separator}"\n'
            full_response += base64_context + separator

        answer_chunk = result.get("answer", "")
        if not answer_chunk or not answer_chunk.strip():
            answer_chunk = (
                "I couldn't generate an answer from the current knowledge base contents. "
                "Please verify the documents were indexed successfully and try again."
            )
        full_response += answer_chunk
        yield f"0:{json.dumps(answer_chunk)}\n"

        if touched_document_ids:
            for document in db.query(Document).filter(Document.id.in_(list(touched_document_ids))).all():
                document.query_count = (document.query_count or 0) + 1
                document.last_queried_at = datetime.utcnow()
                db.add(document)
            
        # Update bot message content
        bot_message.content = full_response
        db.commit()
        yield 'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
            
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        yield '3:{text}\n'.format(text=error_message)
        yield 'd:{"finishReason":"error","usage":{"promptTokens":0,"completionTokens":0}}\n'
        
        # Update bot message with error
        if 'bot_message' in locals():
            bot_message.content = error_message
            db.commit()
    finally:
        db.close()
