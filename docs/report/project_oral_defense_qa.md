# Project Oral Defense Q&A Guide

This document is a high-confidence speaking guide for explaining the project clearly during a midterm review, viva, demo, or Q&A session.

Use it as:
- a quick revision sheet before presentation
- a fallback script if the professor asks detailed technical questions
- a checklist of what to emphasize and what to avoid overstating

---

# 1. One-Minute Project Summary

## Short answer

This project is a web-based Retrieval-Augmented Generation system for internal knowledge retrieval. It lets users upload and organize internal documents, ask questions in natural language, and receive answers grounded in retrieved document content. The system also includes user management, permission control, answer feedback, expert correction workflows, analytics, and an admin dashboard for governance and monitoring.

## Slightly longer answer

The core idea is to combine document retrieval with large language models so that answers are not generated purely from model memory. Instead, the system first retrieves relevant document chunks from a vector database, then uses those chunks as context to generate a response. This makes the system more transparent and suitable for internal organizational use, especially because it also supports citations, permissions, expert review, and administrative oversight.

---

# 2. What Problem Does This Project Solve?

## Recommended answer

Organizations often store knowledge in many internal files such as PDFs, reports, manuals, and text documents. Searching manually is slow and inefficient. This project solves that problem by providing a conversational interface that allows users to ask questions in natural language and receive answers extracted from internal documents. It improves information access speed while also supporting transparency, permissions, and quality control.

## Key phrases to use

- internal knowledge retrieval
- natural language question answering
- document-grounded answers
- transparency through citations
- operational governance

---

# 3. Why Use RAG Instead of a Normal Chatbot?

## Recommended answer

A normal chatbot can answer from its pretrained knowledge, but that is not enough for internal or organization-specific documents. RAG is better because it retrieves relevant internal content first, then generates an answer based on that content. This reduces hallucination, improves relevance, and makes the answer traceable to source documents.

## Strong follow-up line

In this project, RAG is important because the target knowledge does not exist in the base model by default. The model needs access to organization-specific documents.

---

# 4. High-Level System Architecture

## Recommended answer

The system has a frontend-backend separated architecture.

- The frontend is built with Next.js and TypeScript and provides chat, knowledge base management, analytics, profile, expert review, and admin screens.
- The backend is built with FastAPI and handles authentication, business logic, document processing orchestration, permissions, feedback, analytics, and admin actions.
- MySQL stores relational data such as users, chats, permissions, feedback, and audit logs.
- MinIO stores uploaded source documents.
- ChromaDB stores vector embeddings for document retrieval.
- Nginx is used as a reverse proxy.
- The LLM layer is configurable and can use OpenAI, DeepSeek, or Ollama.

## Clean explanation line

So the architecture separates user interaction, application logic, file storage, metadata storage, and vector retrieval into dedicated layers.

---

# 5. Main Technologies and Why They Were Chosen

## FastAPI

Recommended answer:
FastAPI was chosen because it is lightweight, high-performance, and very suitable for building REST APIs with Python. It also works well with Pydantic schemas, making request and response validation easier.

## Next.js

Recommended answer:
Next.js was used because it provides a modern React-based frontend structure with good routing, component organization, and production-ready build support.

## MySQL

Recommended answer:
MySQL stores structured application data such as users, chats, knowledge base metadata, roles, permissions, feedback, and audit logs.

## MinIO

Recommended answer:
MinIO is used as object storage for uploaded documents. It is a practical choice because it is S3-compatible and easy to run in Docker for development and deployment.

## ChromaDB

Recommended answer:
ChromaDB stores embeddings of document chunks, allowing semantic retrieval when users ask questions.

## LangChain

Recommended answer:
LangChain was used to help assemble the retrieval and generation pipeline, especially for retriever logic, prompt chaining, and conversational context handling.

---

# 6. End-to-End User Workflow

## Recommended answer

The user workflow is:

1. The user logs in.
2. The user accesses knowledge bases and documents they are allowed to use.
3. The user starts a chat and asks a question in natural language.
4. The backend retrieves relevant document chunks from the vector store.
5. The LLM generates an answer based on that context.
6. The answer is streamed back to the frontend.
7. The user can review citations, revisit chat history, and provide feedback on answer quality.

---

# 7. End-to-End Admin Workflow

## Recommended answer

The admin workflow is:

1. Manage users and roles.
2. Manage internal knowledge bases and document metadata.
3. Configure permissions and system behavior.
4. Monitor usage statistics and system alerts.
5. Review flagged answers from users.
6. Assign flagged cases to experts for manual correction.

## Good phrase

The admin side is not only for user management, but also for operational governance and system quality improvement.

---

# 8. End-to-End Expert Workflow

## Recommended answer

When a user says the chatbot answer is inaccurate, that feedback can be escalated. The admin reviews the flagged case and assigns it to an expert. The expert sees the question, the original chatbot answer, and the user feedback, then submits a manual corrected answer. That corrected answer becomes the expert override, and the case is marked as resolved.

## Why this matters

This introduces human-in-the-loop quality control, which is important for domains where answer correctness matters.

---

# 9. What New Features Were Added in This Phase?

## Best answer

The major additions in this phase were:

- user profiles
- document and knowledge base permissions
- answer feedback system
- admin dashboard
- analytics and monitoring
- expert answer override workflow
- smoother real-time chat updates
- audit and access logging
- safer admin bootstrap flow through environment variables

## If asked for impact

These changes made the project much closer to a real deployable internal system rather than just a basic RAG demo.

---

# 10. What Exactly Did You Improve in Chat?

## Recommended answer

Originally, the chatbot response did not appear smoothly and sometimes required a page refresh or navigating away and back. I improved that by updating the frontend chat flow to append the user message immediately, create an optimistic assistant placeholder, stream the answer incrementally from the backend, and refresh the final message state once streaming completes.

## Good technical phrase

The goal was to improve perceived responsiveness and conversation continuity.

---

# 11. How Does Answer Citation Work?

## Recommended answer

The backend retrieves document chunks and includes them as context for generation. The response format preserves enough information for the frontend to reconstruct citations. The answer text is shown to the user together with referenced supporting content so the user can understand where the answer came from.

## Important nuance

The system improves transparency, but citation quality still depends on retrieval quality and the prompt structure.

---

# 12. How Does Authentication Work?

## Recommended answer

The system uses JWT-based authentication with an OAuth2 password flow. A user logs in with username and password, the backend validates the credentials, and then returns an access token. The frontend stores the token and includes it in authorized API requests.

## Good clarification

Role checks are then enforced in backend dependencies, for example for admin-only or expert-only routes.

---

# 13. How Are Roles Managed?

## Recommended answer

The project uses a role-aware user model. The main roles are:

- user
- expert
- admin
- super_admin

Each role determines what the user can access. For example, experts can manually correct flagged answers, while admins can manage users, documents, analytics, and assignments. Super admins have the highest level of operational control.

---

# 14. How Are Permissions Handled?

## Recommended answer

The project supports permission metadata at both the knowledge base and document level. This means access can be restricted so users only interact with content they are authorized to view or query. The permission model is implemented in the relational layer and reflected in the UI and admin controls.

## Honest limitation answer

At the current stage, retrieval is still mainly organized at the knowledge-base level, so stricter per-document enforcement inside the vector retrieval path is an important next improvement.

---

# 15. What Analytics Does the Admin Dashboard Provide?

## Recommended answer

The admin dashboard currently provides:

- total users
- total chats and questions
- feedback counts
- flagged answer counts
- recent activity trends
- top users by chat volume
- frequent topics based on recent questions
- peak usage hours
- document effectiveness indicators such as query count
- alerts related to repeated failures or access issues

## Good conclusion

These metrics help admins evaluate both usage and answer quality trends.

---

# 16. Why Add Feedback and Expert Override?

## Recommended answer

Automated answers are useful, but they are not always fully correct. Feedback allows users to signal answer quality. Expert override is the next step that turns feedback into actual correction. Together, these features create a closed quality-improvement loop.

## Nice phrase

This moves the system from passive question answering to active quality governance.

---

# 17. What Is the Role of Manual Q&A Entries?

## Recommended answer

Manual Q&A entries provide a way for admins or experts to store curated answers for known or repeated questions. If a matching question appears, the system can use that manual answer directly, which is useful for standard policy questions or recurring internal requests.

---

# 18. How Is the Project Deployed?

## Recommended answer

The project is deployed with Docker Compose. The stack includes the frontend, backend, MySQL, ChromaDB, MinIO, and Nginx. This makes the system reproducible and easier to run as a multi-service application.

## Good line

Containerization helps keep infrastructure dependencies consistent across environments.

---

# 19. What Technical Problems Did You Face?

## Recommended answer

Some of the main technical issues during implementation were:

- database migration mismatches after model changes
- frontend build failures caused by outdated Next.js config keys
- invalid UTF-8 encoding in a frontend file
- TypeScript typing mismatches in the feedback workflow
- Python f-string escaping issues in the backend streaming service
- SQLAlchemy relationship ambiguity after introducing expert assignment fields
- admin bootstrap and login setup friction

## Strong ending

A significant part of the work was not only adding features but also stabilizing the system so it could actually run reliably.

---

# 20. What Did You Learn From Those Issues?

## Recommended answer

I learned that in full-stack systems, feature implementation is tightly connected to infrastructure stability. A small schema change can affect authentication, serialization, deployment, and UI behavior. I also learned the importance of validating data contracts carefully between backend and frontend, especially when adding roles, permissions, and richer response objects.

---

# 21. How Did You Verify the System?

## Recommended answer

Verification was done through a combination of:

- backend compilation checks
- frontend build checks
- container startup testing
- runtime log inspection
- manual flow testing for login, chat, feedback, admin, and expert workflows

## Honest improvement answer

Automated end-to-end tests are still a next-step improvement area.

---

# 22. What Are the Current Limitations?

## Recommended answer

The main current limitations are:

- retrieval-layer permission filtering can be strengthened further
- analytics are useful but still mostly operational rather than deeply evaluative
- notification integrations such as Slack or email are not fully completed
- automated test coverage should be improved
- production-grade hardening and monitoring can still be expanded

## Important note

These are refinement and hardening tasks, not proof-of-concept blockers.

---

# 23. What Would You Improve Next?

## Recommended answer

The next priorities would be:

1. stronger retrieval-time permission filtering
2. automated tests for auth, feedback, admin, and chat workflows
3. real alert and notification integrations
4. better observability and monitoring
5. more formal answer quality evaluation metrics
6. production-readiness improvements

---

# 24. If Asked "What Part Is the Most Important Contribution?"

## Strong answer

The most important contribution in this phase is the shift from a simple RAG demo into a governed internal knowledge system. In particular, the combination of feedback, expert override, admin analytics, and permission-aware management makes the project much more practical for real organizational use.

---

# 25. If Asked "What Part Was the Hardest?"

## Strong answer

The hardest part was integrating new governance features without breaking the existing RAG flow. Features like expert assignment, admin controls, and richer user roles affected the database model, the backend APIs, the frontend state model, and deployment. The challenge was to make those additions work together cleanly.

---

# 26. If Asked "Why Is This Better Than Keyword Search?"

## Recommended answer

Keyword search depends on exact wording and often forces users to manually scan documents. This system uses semantic retrieval, so it can find relevant information even when the user asks in natural language. It then synthesizes that retrieved content into a readable answer, which is more efficient and user-friendly than plain keyword search.

---

# 27. If Asked "Can This Be Used In Real Organizations?"

## Safe answer

Yes, as a strong prototype and internal system foundation. It already includes many of the practical components real organizations need, such as role separation, document management, feedback, expert review, and admin oversight. However, before production rollout, I would still strengthen testing, retrieval-layer permission enforcement, and operational hardening.

---

# 28. If Asked "What Is Novel or Valuable About Your Version?"

## Recommended answer

The value of this version is not only that it answers questions from documents, but that it introduces governance around those answers. The project supports feedback collection, expert correction, analytics, admin controls, and clearer operational roles. That makes it more aligned with real internal knowledge systems than a typical barebones RAG prototype.

---

# 29. If Asked "What Did You Personally Work On?"

## Adaptable answer

In this phase, I focused on extending the system from the original baseline into a more complete internal knowledge platform. My main contributions included user profile and role separation, admin and expert workflows, feedback and answer override logic, analytics and monitoring features, smoother chat interaction, safer admin bootstrap, and debugging backend and frontend deployment issues to keep the system stable.

Use this answer only if it accurately reflects your work. If you worked in a team, adjust it honestly.

---

# 30. If Asked "Why Should We Trust the Answers?"

## Balanced answer

The system improves trust by grounding answers in retrieved internal documents and showing supporting citations. It also adds user feedback, expert correction, and admin oversight. That said, it is still important to validate retrieval quality and maintain the document base carefully, because trust comes from both the model pipeline and the quality of the underlying source data.

---

# 31. Smart Questions You Can Ask Back If Needed

If the professor asks a broad or vague question, these can help you steer the discussion professionally:

- Would you like me to explain the RAG pipeline or the admin workflow first?
- Should I focus more on the system architecture or on the implementation features added in this phase?
- Would you like the answer from a technical perspective or from a practical deployment perspective?

---

# 32. Fast Answer Bank

## What is RAG?

RAG stands for Retrieval-Augmented Generation. It first retrieves relevant document content, then uses that retrieved context to generate an answer.

## Why use vector databases?

Because they enable semantic similarity search over embedded document chunks.

## Why use MinIO?

To store uploaded files separately from relational metadata.

## Why use MySQL?

To store structured application data such as users, roles, chats, permissions, feedback, and logs.

## Why not rely only on the LLM?

Because the LLM alone does not know internal organizational documents and may hallucinate.

## What is the purpose of expert override?

To let human specialists correct low-quality automated answers.

## What is the purpose of admin analytics?

To monitor usage, quality signals, and operational health.

---

# 33. Best Final Closing Statement

If you need a strong closing sentence during Q&A, use this:

This project demonstrates not only a working RAG pipeline, but also the governance, feedback, and correction mechanisms required to make document-based AI systems more practical and trustworthy in real internal environments.

---

# 34. Which File Does What?

This section helps answer questions like:

- "Where is authentication implemented?"
- "Which file handles the admin dashboard?"
- "Where is the RAG response generated?"
- "Where are permissions enforced?"

Use these answers when the professor asks for implementation-level details.

## Backend entry and routing

### `backend/app/main.py`

What it does:
- starts the FastAPI application
- loads routers
- runs startup logic
- initializes MinIO
- runs database migrations
- triggers optional admin bootstrap on startup

Say this:

"This is the backend entry point. It wires the application together and runs the startup lifecycle."

### `backend/app/api/api_v1/api.py`

What it does:
- central router registration
- mounts the route groups for auth, knowledge base, chat, API keys, feedback, analytics, and admin

Say this:

"This file is the backend API router hub. It connects all feature-specific route modules into one API tree."

## Authentication and user management

### `backend/app/api/api_v1/auth.py`

What it does:
- user registration
- login and JWT token creation
- current-user retrieval
- profile update
- role guard helpers for admin, super admin, and expert
- user listing for frontend permission screens

Important note:
- this is also where response serialization for users was normalized so `feature_flags` is always a dictionary

Say this:

"Authentication and role-based access entry points are mainly implemented in `auth.py`."

### `backend/app/models/user.py`

What it does:
- defines the `User` database model
- stores email, username, password hash
- stores profile fields like `full_name`, `bio`, `avatar_url`
- stores role and privilege flags like `role`, `is_superuser`, `is_expert`
- stores account state such as active/suspended status

Say this:

"The user model is where identity, profile, roles, and account state are defined."

### `backend/bootstrap_admin.py`

What it does:
- command-line script to create or promote the first admin account

Say this:

"This is the manual admin bootstrap script for first-time setup."

### `backend/app/startup/admin_bootstrap.py`

What it does:
- creates or updates the first admin account using `.env` values
- supports startup-based bootstrap without typing long terminal commands

Say this:

"This file handles the safer environment-based admin creation flow."

## Knowledge base and document management

### `backend/app/api/api_v1/knowledge_base.py`

What it does:
- knowledge base CRUD
- document upload and management
- document listing and retrieval
- permission-aware access checks

Say this:

"This is the main API module for knowledge bases and documents."

### `backend/app/models/knowledge.py`

What it does:
- defines `KnowledgeBase`, `Document`, `DocumentChunk`, `ProcessingTask`
- defines `KnowledgeBasePermission` and `DocumentPermission`
- stores document metadata such as category, department, sensitivity, and access level

Say this:

"This file models the entire document and knowledge structure, including permissions."

### `backend/app/services/document_processor.py`

What it does:
- handles processing uploaded documents
- prepares them for chunking and embedding

Say this:

"This file is part of the ingestion pipeline from uploaded file to searchable knowledge."

### `backend/app/services/chunk_record.py`

What it does:
- supports document chunk metadata and chunk identity tracking

Say this:

"This module helps manage chunk-level document records."

## RAG and chat flow

### `backend/app/api/api_v1/chat.py`

What it does:
- chat creation and message APIs
- chat history retrieval
- request entry point for asking questions
- chat ownership checks

Say this:

"This is the main backend controller for conversation workflows."

### `backend/app/services/chat_service.py`

What it does:
- core RAG answer generation
- retrieves knowledge bases and documents
- builds the retriever and prompt chain
- streams the answer back to the frontend
- handles citations packaging
- supports manual Q&A shortcut matching
- updates document query counts

Say this:

"This is the heart of the RAG pipeline. If the professor asks where the actual answer is generated, this is the file."

### `backend/app/services/embedding/embedding_factory.py`

What it does:
- selects the embedding provider based on configuration

### `backend/app/services/llm/llm_factory.py`

What it does:
- selects the LLM provider based on configuration

### `backend/app/services/vector_store/factory.py`

What it does:
- selects the vector store backend such as Chroma or Qdrant

Say this:

"These factory files make the system configurable across providers instead of hardcoding one implementation."

## Feedback, expert override, and quality control

### `backend/app/api/api_v1/feedback.py`

What it does:
- saves thumbs-up and thumbs-down answer feedback
- marks low-quality answers as flagged
- lets experts submit manual answer overrides
- exposes the expert assignment queue

Say this:

"This file implements the answer quality workflow from user feedback to expert correction."

### `backend/app/models/chat.py`

What it does:
- defines `Chat` and `Message`
- defines `MessageFeedback`
- defines `MessageOverride`
- stores expert assignment fields such as status, assignee, and resolution metadata

Say this:

"This model file stores the conversation structure and the answer-review lifecycle."

## Admin, analytics, and governance

### `backend/app/api/api_v1/admin.py`

What it does:
- admin overview and analytics
- user management
- suspension and password reset actions
- knowledge base and document governance
- reindex actions
- flagged answer review and expert assignment
- manual Q&A management
- alerts, audit logs, access logs, and system configuration

Say this:

"This is the main operations and governance API for admins."

### `backend/app/api/api_v1/analytics.py`

What it does:
- analytics endpoints used by dashboard reporting

Say this:

"This module supports analytics-focused reporting endpoints."

### `backend/app/models/admin.py`

What it does:
- defines `AuditLog`
- defines `AccessLog`
- defines `SystemAlert`
- defines `SystemConfig`
- defines `ManualQAEntry`

Say this:

"This file stores governance and operational support entities."

### `backend/app/services/admin_audit.py`

What it does:
- writes audit log records
- writes access log records
- creates alerts when needed

Say this:

"This service centralizes admin-side logging and alert creation."

## Permission enforcement

### `backend/app/services/access_control.py`

What it does:
- checks whether a user can access or edit a knowledge base
- checks whether a user can access or edit a document
- filters accessible items for a given user
- checks whether a user can access a chat

Say this:

"This file contains the permission decision logic."

## Configuration and infrastructure

### `backend/app/core/config.py`

What it does:
- reads environment variables
- stores database, JWT, LLM, vector store, and bootstrap settings

Say this:

"This is the central configuration layer for the backend."

### `backend/app/startup/migarate.py`

What it does:
- runs database migrations at startup

Say this:

"This file ensures the schema is updated when the backend starts."

### `docker-compose.yml`

What it does:
- defines the full multi-container stack
- backend, frontend, MySQL, ChromaDB, MinIO, and Nginx

Say this:

"This file describes how the entire system is deployed."

## Frontend pages and components

### `frontend/src/app/login/page.tsx`

What it does:
- login form
- sends username and password to `/api/auth/token`

### `frontend/src/app/register/page.tsx`

What it does:
- user registration form

### `frontend/src/app/dashboard/page.tsx`

What it does:
- dashboard landing page after login

### `frontend/src/app/dashboard/chat/[id]/page.tsx`

What it does:
- main chat conversation screen
- streams assistant responses
- displays citations
- supports thumbs-up and thumbs-down feedback
- shows expert override if present

Say this:

"If the professor asks where the smooth chat UX is implemented, it is mainly here."

### `frontend/src/app/dashboard/knowledge/page.tsx`

What it does:
- knowledge base listing and management entry screen

### `frontend/src/app/dashboard/admin/page.tsx`

What it does:
- admin workspace UI
- user management
- analytics display
- flagged answer assignment
- document governance and alerts

Say this:

"This is the frontend control center for administrators."

### `frontend/src/app/dashboard/expert-review/page.tsx`

What it does:
- expert queue UI
- displays flagged answers assigned to experts
- allows manual corrected answer submission

Say this:

"This page is the human-in-the-loop review interface."

### `frontend/src/app/dashboard/profile/page.tsx`

What it does:
- profile editing UI for the current user

### `frontend/src/app/dashboard/analytics/page.tsx`

What it does:
- analytics dashboard UI

### `frontend/src/components/layout/dashboard-layout.tsx`

What it does:
- shared sidebar and layout shell
- role-based navigation
- shows different navigation items for user, expert, and admin

Say this:

"This component is important because it reflects the role-based system on the frontend."

### `frontend/src/components/knowledge-base/document-list.tsx`

What it does:
- document list UI
- permission-related controls and metadata display

### `frontend/src/components/chat/answer.tsx`

What it does:
- answer rendering and citation presentation logic

### `frontend/src/lib/api.ts`

What it does:
- shared frontend API wrapper
- automatically attaches JWT token
- handles unauthorized responses and redirects to login

Say this:

"This is the frontend communication layer for backend APIs."

## Short file map for very fast answers

If you need an ultra-fast version in the oral defense:

- `main.py`: backend entry point
- `api.py`: central API router
- `auth.py`: login, profile, role guards
- `knowledge_base.py`: document and knowledge APIs
- `chat.py`: chat endpoints
- `chat_service.py`: RAG answer generation
- `feedback.py`: answer feedback and expert override
- `admin.py`: admin operations and analytics
- `user.py`: user model
- `knowledge.py`: document and permission model
- `chat.py` model: chats, messages, feedback, overrides
- `admin.py` model: logs, alerts, system config, manual Q&A
- `access_control.py`: permission logic
- `admin_audit.py`: audit/access logging
- `dashboard-layout.tsx`: role-based frontend navigation
- `chat/[id]/page.tsx`: streaming chat UI
- `admin/page.tsx`: admin frontend
- `expert-review/page.tsx`: expert frontend
- `api.ts`: frontend API client
