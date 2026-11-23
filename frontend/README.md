# 🖥️ Learnify Frontend — Next.js 16 Client Application

The user-facing web portal for **Learnify**, built with Next.js 16 (App Router), React 19, Tailwind CSS, and Clerk Authentication.

---

## 🌟 Key Features

1. **Course & Topic Creation Studio**: Interactive topic generator (`/dashboard/generate-topic`) with difficulty adaptation (Beginner, Intermediate, Advanced).
2. **Real-Time Pipeline Progress Tracker**: Dynamic 7-stage checklist (`VideoGenerationProgress.tsx`) displaying live status:
   - Curriculum Research
   - Lesson Content Drafting
   - LLM-as-a-Judge Audit (Gemini)
   - Script Planning
   - Visual Scene Design
   - TTS Voiceover Sync
   - Remotion Video Render
3. **Multimedia Lesson Viewer**: Full markdown lesson reader, synchronized 1080p video player, and real-time AI verification badge.
4. **Interactive Quiz System**: Conceptual self-assessment multiple-choice questions with answer keys and pedagogical rationales.
5. **Slide-Out 24/7 AI Tutor Chatbot**: Context-grounded tutor powered by ChromaDB RAG and Groq.
6. **Authentication & User Management**: Secure authentication, login, and registration powered by Clerk.

---

## 📁 Key Routes & Pages

- `/` — Landing page with feature showcases and product hero.
- `/sign-in` & `/sign-up` — Clerk authentication flows.
- `/dashboard/generate-topic` — Single topic video and lesson generator.
- `/dashboard/generate-course` — Multi-chapter course generator.
- `/topics/[id]` — Individual lesson viewer with video player, markdown notes, quiz, and AI tutor.
- `/courses` — User course catalog with completion metrics.

---

## 🛠️ Development & Execution

```bash
# 1. Install dependencies
npm install

# 2. Run the Next.js development server
npm run dev
```

App runs at: **`http://localhost:3000`**

### Environment Configuration (`.env.local`)
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```
