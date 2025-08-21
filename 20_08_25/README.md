# 📦 AI-Powered ITSM Assistant

This project implements an **AI-powered ITSM Assistant** to handle incidents during the warehouse packing workflow. The assistant integrates with a **MySQL database**, uses **LLM-based natural language interaction**, and provides a **React-based chat UI** for end users.

---

## 🚀 Features Implemented

### 🔹 Backend (FastAPI + Groq-hosted LLaMA)

1. **Packing Issue Handling**

   * Detects **packing-related issues** from user input.
   * Prompts for **Order ID or Container ID** if missing.
   * Fetches logs from `cms_logs` for the given ID.
   * Matches failure patterns from `known_failures` table.
   * Provides **only known workarounds** (never invents).
   * If workaround works → marks incident **Resolved**.
   * If no workaround → escalates to IT via **email alert**.

2. **Incident Summary Generation**

   * Added **`summary` intent** detection.
   * For incident summary requests:

     * Fetches incident details from `incident_logs`.
     * Queries `cms_logs` for last response related to the order/container.
     * Matches failure type & workaround from `known_failures`.
     * Generates a **natural language summary**:

       > “Order ORD1234 encountered a hazmat restriction error. The suggested workaround was to remove restricted items. The issue was confirmed resolved.”

3. **Intent Handling Logic**

   * Greeting / small talk handled naturally.
   * **Normal intent** used for packing failures.
   * **Summary intent** used for incident history/summary.
   * Context-aware: if user provides just **order/container ID**, the agent decides whether to:

     * Continue an **in-progress incident** flow.
     * Or fetch **incident summary** if explicitly asked.

4. **Database Integration**

   * **Tables used**:

     * `cms_logs` → stores CMS request/response.
     * `known_failures` → failure patterns + workarounds.
     * `incident_logs` → incident tracking (order/container ID, status, timestamps).

5. **Email Escalation**

   * Unknown issues get **auto-escalated to IT** via email.
   * Email content generated dynamically by the LLM.

---

### 🔹 Frontend (React Chat UI)

1. **Chat Assistant UI**

   * Floating chatbot bubble with attractive dark/light theme.
   * Sticky header with **dark mode toggle**.
   * Chat screen replicates ChatGPT-like layout:

     * User messages → right aligned.
     * Assistant messages → left aligned.
     * Animated typing dots + cascading bot response.
     * Smooth scrolling with wrapper to avoid flicker.

2. **Multi-Agent Entry Screen**

   * Users can start via **assist buttons** OR **pre-chat input**.
   * Pre-chat input:

     * User describes issue (e.g., “label not printing”).
     * LLM classifies intent and routes to correct agent (packing assist etc.).

3. **Chat Screen Enhancements**

   * Welcome banner with animation (disappears after first message).
   * Full-width responsive chat bubbles.
   * Rounded text input with translucent placeholder + send icon.
   * End Chat button → navigates back to home screen.

4. **Future-Proofing**

   * Currently **Packing Agent** connected to backend.
   * Other agents can be integrated via **FastAPI endpoints** on same host (`http://localhost:8000/agent_name`).

---

## ⚙️ Tech Stack

* **Backend**: FastAPI, Groq API (LLaMA), MySQL
* **Frontend**: React, CSS animations
* **Database**: MySQL (with tables: `cms_logs`, `known_failures`, `incident_logs`)
* **Email**: SMTP for IT escalation alerts

---

## 📂 Project Structure

```
AI_ITSM_ASSIST/
 ├── agent.py
 ├── llm_interface.py
 ├── incident_handler.py
 ├── db_interface.py
 ├── email_utils.py
 ├── main.py (FastAPI entrypoint)
 └── requirements.txt

chat_assist_ui/
 ├── src/
 │   ├── App.js
 │   ├── App.css
 │   ├── ChatScreen.jsx
 │   ├── ChatScreen.css
 │   ├── index.css
 │   └── index.js
 ├── public/
 │   └── index.html
 └── package.json
```

---

## 📝 Summary of Changes Done

* ✅ **Packing issue detection** → ID-based log matching + workarounds.
* ✅ **Summary intent** → incident summaries in natural language.
* ✅ **FastAPI backend** → `/chat` endpoint handling LLM + DB logic.
* ✅ **Incident logging** → `incident_logs` integration with status updates.
* ✅ **Email escalation** → for unknown issues.
* ✅ **Frontend redesign** → ChatGPT-style UI, multi-agent support, dark mode.
* ✅ **Pre-chat input** → routes users based on intent classification.
* ✅ **Consistent conversational flow** → greetings, clarifications, summaries.

---

## 🚧 Next Steps

* Integrate additional agents beyond packing (e.g., Shipping Assist, Inventory Assist).
* Add **user authentication & chat history persistence**.
* Enable **notifications** when IT updates incident via email response.
* Expand **failure pattern coverage** in `known_failures`.

