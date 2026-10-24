# 🏛️ Wayhall Civic AI — Frontend Client

A responsive web interface for the **Wayhall Municipal Knowledge Assistant**, built with **React 19**, **Vite**, and **Tailwind CSS**.

---

## ✨ Features

- **Interactive Verified Citations**: Expandable citation cards with source PDF metadata, 1-indexed page badges, detected section headers, and exact text excerpts.
- **Strict Anti-Hallucination Disclaimers**: Highlights `Document Gap Notice` alerts whenever user queries exceed the municipal documents' scope.
- **Knowledge Base Inspector Modal**: Live viewer for inspecting indexed chunks across all three municipal document collections (`bylaws`, `permits`, `service_requests`).
- **Conversational Memory**: Session management with thread persistence in Supabase and browser `localStorage`.
- **Suggested Municipal Prompts**: Quick-start prompt chips for common municipal inquiries (noise by-laws, pothole reporting, building permits).
- **Resident Feedback Widget**: Built-in thumbs-up / thumbs-down rating and feedback reporting.

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The frontend will start at `http://localhost:5173`.

### 3. Backend Integration
The frontend connects to the FastAPI backend running at `http://localhost:8000`. Ensure the backend server is running before sending chat queries.

### 4. Build for Production
```bash
npm run build
npm run preview
```
