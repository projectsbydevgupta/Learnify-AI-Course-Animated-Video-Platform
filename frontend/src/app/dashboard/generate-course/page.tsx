"use client";

import { useState, useEffect, useMemo } from "react";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface CurriculumLesson {
  code: string;
  title: string;
}

interface CurriculumChapter {
  chapter_number: number;
  title: string;
  clean_title: string;
  lessons: CurriculumLesson[];
}

interface CurriculumPart {
  id: string;
  title: string;
  total_chapters: number;
  total_lessons: number;
  chapters: CurriculumChapter[];
}

interface CurriculumSubject {
  id: string;
  name: string;
  title: string;
  icon: string;
  code: string;
  textbook: string;
  description: string;
  total_chapters: number;
  total_lessons: number;
  parts: CurriculumPart[];
}

interface CourseJobStatus {
  job_id: string;
  course_id: string;
  job_type: string;
  progress: number;
  status: string;
  current_lesson: string;
  completed_count: number;
  total_count: number;
  first_lesson_id?: string | null;
  first_lesson_title?: string | null;
  first_lesson_ready?: boolean;
  latest_completed_lesson_id?: string | null;
  error?: string | null;
}

export default function GenerateCoursePage() {
  const { user } = useUser();
  const router = useRouter();

  // Curriculum Index State
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>("dsa");
  const [selectedPartId, setSelectedPartId] = useState<string>("");
  const [selectedChapterNumber, setSelectedChapterNumber] = useState<number | null>(null);
  const [previewOpenPartId, setPreviewOpenPartId] = useState<string | null>(null);
  const [indexLoading, setIndexLoading] = useState(true);

  // Search / Custom Topic Mode State
  const [activeTab, setActiveTab] = useState<"index" | "search">("index");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMatch, setSearchMatch] = useState<any>(null);
  const [targetAudience, setTargetAudience] = useState("Computer Science Students & Developers");
  const [difficulty, setDifficulty] = useState("Adaptive");

  // Execution & Job State
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [courseId, setCourseId] = useState<string | null>(null);
  const [jobState, setJobState] = useState<CourseJobStatus | null>(null);
  const [autoRedirectCountdown, setAutoRedirectCountdown] = useState<number | null>(null);
  const [redirectCancelled, setRedirectCancelled] = useState(false);

  // Fetch Master Curriculum Index on mount
  useEffect(() => {
    const fetchIndex = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const res = await fetch(`${backendUrl}/api/curriculum/index`);
        if (res.ok) {
          const data = await res.json();
          const subs: CurriculumSubject[] = data.subjects || [];
          setSubjects(subs);
          if (subs.length > 0) {
            setSelectedSubjectId(subs[0].id);
            if (subs[0].parts.length > 0) {
              setSelectedPartId(subs[0].parts[0].id);
              setPreviewOpenPartId(subs[0].parts[0].id);
            }
          }
        }
      } catch (e) {
        console.error("Failed to load curriculum index:", e);
      } finally {
        setIndexLoading(false);
      }
    };
    fetchIndex();
  }, []);

  // Update selected part when subject changes
  const currentSubject = useMemo(() => {
    return subjects.find((s) => s.id === selectedSubjectId) || subjects[0] || null;
  }, [subjects, selectedSubjectId]);

  useEffect(() => {
    if (currentSubject && currentSubject.parts.length > 0) {
      // Default to first part of the newly selected subject
      const firstPart = currentSubject.parts[0];
      setSelectedPartId(firstPart.id);
      setPreviewOpenPartId(firstPart.id);
      if (firstPart.chapters.length > 0) {
        setSelectedChapterNumber(firstPart.chapters[0].chapter_number);
      }
    }
  }, [selectedSubjectId, currentSubject]);

  // Live search debounced matching
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchMatch(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const res = await fetch(`${backendUrl}/api/curriculum/match?q=${encodeURIComponent(searchQuery.trim())}`);
        if (res.ok) {
          const data = await res.json();
          setSearchMatch(data.match);
        }
      } catch (err) {
        console.error(err);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Progressive streaming countdown effect
  useEffect(() => {
    if (autoRedirectCountdown === null || redirectCancelled) return;
    if (autoRedirectCountdown <= 0) {
      if (jobState?.first_lesson_id && jobState?.course_id) {
        router.push(`/topics/${jobState.first_lesson_id}?course_id=${jobState.course_id}`);
      }
      return;
    }
    const timer = setTimeout(() => {
      setAutoRedirectCountdown((prev) => (prev !== null ? prev - 1 : null));
    }, 1000);
    return () => clearTimeout(timer);
  }, [autoRedirectCountdown, redirectCancelled, jobState, router]);

  const handleGenerateCourse = async (overridePayload?: any) => {
    setLoading(true);
    setStatusText("Initializing Master Curriculum Pipeline...");

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      
      let payload: any = {
        difficulty,
        target_audience: targetAudience,
        user_id: user?.id || "system_default_user"
      };

      if (overridePayload) {
        payload = { ...payload, ...overridePayload };
      } else if (activeTab === "index") {
        if (!selectedSubjectId) {
          throw new Error("Please select a valid subject from the index.");
        }
        if (selectedChapterNumber) {
          const ch = selectedPart?.chapters.find((c) => c.chapter_number === selectedChapterNumber);
          payload.subject_id = selectedSubjectId;
          payload.chapter_number = selectedChapterNumber;
          payload.topic = `${currentSubject?.name}: ${ch?.clean_title || "Chapter"}`;
        } else if (selectedPartId) {
          const part = currentSubject?.parts.find((p) => p.id === selectedPartId);
          payload.subject_id = selectedSubjectId;
          payload.part_id = selectedPartId;
          payload.topic = `${currentSubject?.name}: ${part?.title || "Module"}`;
        }
      } else {
        if (!searchQuery.trim()) {
          throw new Error("Please enter a course topic or search query.");
        }
        payload.topic = searchQuery.trim();
        if (searchMatch) {
          payload.subject_id = searchMatch.subject?.id;
          if (searchMatch.type === "part") {
            payload.part_id = searchMatch.part?.id;
          } else if (searchMatch.type === "chapter") {
            payload.chapter_number = searchMatch.chapter?.chapter_number;
          }
        }
      }

      const res = await fetch(`${backendUrl}/api/generate/course`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to initialize course generation.");
      }

      const data = await res.json();
      setJobId(data.job_id);
      setCourseId(data.course_id);

      // Start polling for course progress
      pollCourseProgress(data.job_id, data.course_id);
    } catch (err: unknown) {
      console.error(err);
      setStatusText(err instanceof Error ? err.message : "Error initiating course generation.");
      setLoading(false);
    }
  };

  const pollCourseProgress = (activeJobId: string, activeCourseId: string) => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${backendUrl}/api/jobs/${activeJobId}/status`);
        if (!res.ok) return;

        const data: CourseJobStatus = await res.json();
        setJobState(data);

        // Optimistic first module handoff: trigger countdown once lesson 1 is ready
        if (data.first_lesson_ready && data.first_lesson_id) {
          setAutoRedirectCountdown((prev) => (prev === null ? 5 : prev));
        }

        if (data.status === "COMPLETED" || data.status === "PARTIAL_FAILURE") {
          clearInterval(interval);
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 2500);
  };

  const selectedPart = useMemo(() => {
    return currentSubject?.parts.find((p) => p.id === selectedPartId) || null;
  }, [currentSubject, selectedPartId]);

  const selectedChapter = useMemo(() => {
    if (!selectedPart) return null;
    if (selectedChapterNumber) {
      const found = selectedPart.chapters.find((c) => c.chapter_number === selectedChapterNumber);
      if (found) return found;
    }
    return selectedPart.chapters[0] || null;
  }, [selectedPart, selectedChapterNumber]);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col items-center justify-start p-4 sm:p-8 relative overflow-hidden font-sans">
      {/* Background Ambient Glows */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-4xl w-full bg-slate-900/90 border border-slate-800 p-6 sm:p-10 rounded-3xl shadow-2xl backdrop-blur-2xl relative overflow-hidden my-4">
        <div className="absolute -top-24 -right-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="mb-8">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold mb-4 transition group"
          >
            <span className="group-hover:-translate-x-1 transition-transform">←</span> Back to Studio Dashboard
          </Link>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-2xl shadow-inner">
                🎓
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  Master Curriculum Course Generator
                </h1>
                <p className="text-xs text-slate-400 mt-1">
                  Textbook-Indexed Multi-Chapter Modules • Deterministic Pedagogy • Automated 1080p Video Pipelines
                </p>
              </div>
            </div>

            {/* Mode Switcher Tabs */}
            {!jobId && (
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 shrink-0 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setActiveTab("index")}
                  className={`px-3.5 py-1.5 rounded-lg transition ${
                    activeTab === "index"
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  📚 Master Index
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("search")}
                  className={`px-3.5 py-1.5 rounded-lg transition ${
                    activeTab === "search"
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🔍 Search / Custom
                </button>
              </div>
            )}
          </div>
        </div>

        {!jobId ? (
          <div className="space-y-6">
            {activeTab === "index" ? (
              /* TAB 1: MASTER CURRICULUM EXPLORER */
              <div className="space-y-6">
                {/* 1. Subject Selector Cards */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
                    1. Select Academic Pillar Subject
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {subjects.map((sub) => {
                      const isSelected = sub.id === selectedSubjectId;
                      return (
                        <button
                          key={sub.id}
                          type="button"
                          onClick={() => setSelectedSubjectId(sub.id)}
                          className={`p-3.5 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                            isSelected
                              ? "bg-gradient-to-br from-indigo-950/80 to-slate-900 border-indigo-500 shadow-lg shadow-indigo-950/40 ring-1 ring-indigo-500"
                              : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60"
                          }`}
                        >
                          <div>
                            <div className="flex items-center mb-2">
                              <span className="text-2xl">{sub.icon}</span>
                            </div>
                            <h3 className="font-bold text-sm text-white leading-tight mb-1">
                              {sub.name}
                            </h3>
                            <p className="text-[11px] text-slate-400 line-clamp-2">
                              {sub.description}
                            </p>
                          </div>

                          <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                            <span>{sub.total_chapters} Chapters</span>
                            <span className="font-semibold text-indigo-400">{sub.total_lessons} Lessons</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Subject Academic Benchmark Banner */}
                {currentSubject && (
                  <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2 text-slate-300">
                      <span className="text-base">📖</span>
                      <span>
                        <strong className="text-white">Academic Textbook Reference:</strong>{" "}
                        <span className="text-slate-400">{currentSubject.textbook}</span>
                      </span>
                    </div>
                    <span className="text-[11px] px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono font-medium shrink-0">
                      Standard Syllabus
                    </span>
                  </div>
                )}

                {/* 2. Select Module / Part from Textbook Index */}
                {currentSubject && (
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
                      2. Choose Module to Generate (Syllabus Structured Deterministically by Domain Content)
                    </label>

                    <div className="space-y-3">
                      {currentSubject.parts.map((part, idx) => {
                        const isSelected = part.id === selectedPartId;
                        const isPreviewOpen = previewOpenPartId === part.id;

                        return (
                          <div
                            key={part.id}
                            className={`rounded-2xl border transition-all ${
                              isSelected
                                ? "bg-slate-900 border-indigo-500/80 shadow-md ring-1 ring-indigo-500/50"
                                : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                            }`}
                          >
                            <div
                              onClick={() => {
                                setSelectedPartId(part.id);
                                setPreviewOpenPartId(part.id);
                              }}
                              className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer"
                            >
                              <div className="flex items-start gap-3">
                                <div
                                  className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5 ${
                                    isSelected
                                      ? "bg-indigo-600 text-white"
                                      : "bg-slate-800 text-slate-400"
                                  }`}
                                >
                                  {idx + 1}
                                </div>
                                <div>
                                  <h4 className="font-bold text-sm text-white">
                                    {part.title}
                                  </h4>
                                  <p className="text-xs text-slate-400 mt-0.5">
                                    {part.chapters.map((c) => c.clean_title).join(" • ")}
                                  </p>
                                </div>
                              </div>

                              <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
                                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-800 text-indigo-300 border border-slate-700">
                                  {part.total_chapters} {part.total_chapters === 1 ? "Chapter" : "Chapters"} • {part.total_lessons} Lessons
                                </span>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setPreviewOpenPartId(isPreviewOpen ? null : part.id);
                                  }}
                                  className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 rounded border border-slate-700/60 hover:bg-slate-800"
                                >
                                  {isPreviewOpen ? "Hide Outline ▲" : "View Outline ▼"}
                                </button>
                              </div>
                            </div>

                            {/* Detailed Chapter & Lesson Outline Accordion */}
                            {isPreviewOpen && (
                              <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-3 bg-slate-950/40 rounded-b-2xl animate-in fade-in duration-200">
                                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                                  <span className="flex items-center gap-1.5">
                                    <span>📜</span> Click Any Single Chapter to Generate (~4-5 Videos):
                                  </span>
                                  <span className="text-[10px] text-emerald-400 font-medium">
                                    ⚡ Recommended (Faster Generation)
                                  </span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                  {part.chapters.map((ch) => {
                                    const isChSelected = selectedChapterNumber === ch.chapter_number;
                                    return (
                                      <div
                                        key={ch.chapter_number}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setSelectedChapterNumber(ch.chapter_number);
                                        }}
                                        className={`p-3.5 rounded-xl border text-xs space-y-2.5 transition cursor-pointer flex flex-col justify-between ${
                                          isChSelected
                                            ? "bg-indigo-950/80 border-indigo-500 ring-2 ring-indigo-500/60 shadow-lg shadow-indigo-950/40"
                                            : "bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                                        }`}
                                      >
                                        <div>
                                          <div className="font-bold text-white flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                              <span
                                                className={`w-6 h-6 rounded-md flex items-center justify-center font-mono text-[10px] font-bold ${
                                                  isChSelected
                                                    ? "bg-indigo-500 text-white"
                                                    : "bg-slate-800 text-slate-400"
                                                }`}
                                              >
                                                {ch.chapter_number}
                                              </span>
                                              <span className="text-sm font-bold text-slate-100">
                                                {ch.clean_title}
                                              </span>
                                            </div>
                                            <span className="text-[10px] text-slate-400 font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800 shrink-0">
                                              {ch.lessons.length} lessons
                                            </span>
                                          </div>
                                          <ul className="space-y-1 text-slate-400 text-[11px] pl-1">
                                            {ch.lessons.map((ls) => (
                                              <li key={ls.code} className="flex items-start gap-1.5">
                                                <span className="text-indigo-400 font-mono text-[10px] shrink-0">
                                                  {ls.code}
                                                </span>
                                                <span className="line-clamp-1">{ls.title}</span>
                                              </li>
                                            ))}
                                          </ul>
                                        </div>

                                        {/* Direct 1-Click Single Chapter Generation Button */}
                                        <button
                                          type="button"
                                          disabled={loading}
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleGenerateCourse({
                                              topic: `${currentSubject?.name}: ${ch.clean_title}`,
                                              subject_id: currentSubject?.id,
                                              chapter_number: ch.chapter_number
                                            });
                                          }}
                                          className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-xs tracking-wide transition flex items-center justify-center gap-1.5 shadow cursor-pointer"
                                        >
                                          <span>⚡</span>
                                          <span>Generate Chapter {ch.chapter_number} ({ch.lessons.length} Videos) →</span>
                                        </button>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 3. Action Bar */}
                <div className="pt-2 space-y-2.5">
                  {selectedChapter ? (
                    <>
                      <button
                        type="button"
                        disabled={loading}
                        onClick={() =>
                          handleGenerateCourse({
                            topic: `${currentSubject?.name}: ${selectedChapter.clean_title}`,
                            subject_id: currentSubject?.id,
                            chapter_number: selectedChapter.chapter_number
                          })
                        }
                        className="w-full py-4 bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-600 hover:opacity-95 disabled:opacity-50 text-white rounded-2xl font-bold text-sm tracking-wide transition shadow-xl shadow-indigo-950/50 flex items-center justify-center gap-2 cursor-pointer"
                      >
                        {loading ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            <span>{statusText || "Structuring Syllabus..."}</span>
                          </>
                        ) : (
                          <>
                            <span>⚡</span>
                            <span>
                              Generate Chapter {selectedChapter.chapter_number}: {selectedChapter.clean_title}
                            </span>
                            <span className="text-xs bg-black/30 px-2.5 py-0.5 rounded-full font-normal">
                              {selectedChapter.lessons.length} Videos • Fast Generation
                            </span>
                          </>
                        )}
                      </button>

                      <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 px-1 gap-2">
                        <span>
                          🚀 <strong>Fast Mode:</strong> Generates strictly 1 chapter ({selectedChapter.lessons.length} videos). First video ready in ~1-2 mins!
                        </span>
                        {selectedPart && (
                          <button
                            type="button"
                            disabled={loading}
                            onClick={() =>
                              handleGenerateCourse({
                                topic: `${currentSubject?.name}: ${selectedPart.title.replace(/^PART\s+[A-Z]+\s*[■\-–:]*\s*/, '')}`,
                                subject_id: currentSubject?.id,
                                part_id: selectedPart.id
                              })
                            }
                            className="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium cursor-pointer shrink-0"
                          >
                            Or generate full module ({selectedPart.total_lessons} videos) →
                          </button>
                        )}
                      </div>
                    </>
                  ) : (
                    <button
                      type="button"
                      disabled={loading || !selectedPart}
                      onClick={() => handleGenerateCourse()}
                      className="w-full py-4 bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-600 hover:opacity-95 disabled:opacity-50 text-white rounded-2xl font-bold text-sm tracking-wide transition shadow-xl shadow-indigo-950/50 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      {loading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          <span>{statusText || "Structuring Syllabus..."}</span>
                        </>
                      ) : (
                        <>
                          <span>🚀</span>
                          <span>
                            Generate {selectedPart ? `${currentSubject?.name}: ${selectedPart.title.replace(/^PART\s+[A-Z]+\s*[■\-–:]*\s*/, '')}` : "Selected Module"}
                          </span>
                          <span className="text-xs bg-black/30 px-2 py-0.5 rounded-full font-normal">
                            {selectedPart?.total_chapters} Chapters • {selectedPart?.total_lessons} Lessons
                          </span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            ) : (
              /* TAB 2: SEARCH INDEX OR CUSTOM TOPIC */
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                    Search Master Index or Enter Any Custom Topic
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Linked Lists, B+ Tree Indexing, TCP Congestion Control, Backpropagation..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    disabled={loading}
                    className="w-full px-4 py-3.5 bg-slate-950/80 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                  />
                </div>

                {/* Live Index Match Detection Card */}
                {searchMatch && (
                  <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-500/60 shadow-lg relative overflow-hidden animate-in fade-in duration-300">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-emerald-400" />
                            Authoritative Textbook Match
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                            {searchMatch.subject?.name}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-white">
                          {searchMatch.matched_item?.clean_title || searchMatch.matched_item?.title}
                        </h3>
                        <p className="text-xs text-slate-300">
                          {searchMatch.type === "part" &&
                            `Module contains ${searchMatch.matched_item?.total_chapters || searchMatch.matched_item?.chapters?.length} chapters and ${searchMatch.matched_item?.total_lessons} lessons.`}
                          {searchMatch.type === "chapter" &&
                            `Textbook chapter contains ${searchMatch.matched_item?.lessons?.length} structured subtopics.`}
                          {searchMatch.type === "lesson" &&
                            `Detailed topic within ${searchMatch.chapter?.clean_title || "Chapter"}.`}
                        </p>
                      </div>

                      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 shrink-0">
                        {searchMatch.type === "chapter" && (
                          <>
                            <button
                              type="button"
                              onClick={() => handleGenerateCourse({
                                topic: searchMatch.chapter?.clean_title || searchQuery.trim(),
                                subject_id: searchMatch.subject?.id,
                                chapter_number: searchMatch.chapter?.chapter_number
                              })}
                              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold tracking-wide transition shadow cursor-pointer text-center"
                            >
                              Generate Just Chapter ({searchMatch.chapter?.lessons?.length || 5} Videos) →
                            </button>
                            {searchMatch.part && (
                              <button
                                type="button"
                                onClick={() => handleGenerateCourse({
                                  topic: `${searchMatch.subject?.name}: ${searchMatch.part?.title}`,
                                  subject_id: searchMatch.subject?.id,
                                  part_id: searchMatch.part?.id
                                })}
                                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium tracking-wide transition border border-slate-700 cursor-pointer text-center"
                              >
                                Full Module ({searchMatch.part?.total_lessons || 15} Videos) →
                              </button>
                            )}
                          </>
                        )}
                        {searchMatch.type !== "chapter" && (
                          <button
                            type="button"
                            onClick={() => handleGenerateCourse({
                              topic: searchQuery.trim(),
                              subject_id: searchMatch.subject?.id,
                              part_id: searchMatch.part?.id,
                              chapter_number: searchMatch.chapter?.chapter_number
                            })}
                            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold tracking-wide transition shadow cursor-pointer text-center"
                          >
                            Generate Textbook Module →
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {!searchMatch && searchQuery.trim().length > 3 && (
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-1.5">
                    <div className="flex items-center gap-2 text-indigo-300 font-semibold">
                      <span>🧠</span> Custom Academic Domain:
                    </div>
                    <p className="leading-relaxed">
                      This topic is not in the pre-indexed core textbook catalog. The Autonomous Course Planner Agent (Groq 120B) will analyze the domain depth and architect the exact optimal chapter and lesson structure automatically.
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                      Target Audience
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. CS Undergrads, Developers"
                      value={targetAudience}
                      onChange={(e) => setTargetAudience(e.target.value)}
                      disabled={loading}
                      className="w-full px-4 py-3 bg-slate-950/70 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                      Pedagogical Depth
                    </label>
                    <div className="w-full px-4 py-3 bg-slate-950/70 border border-slate-800 rounded-xl text-xs text-indigo-300 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
                        <span className="font-semibold">Auto-Adaptive</span>
                      </div>
                      <span className="text-[11px] text-slate-400">Dynamically generated per topic complexity</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={loading || !searchQuery.trim()}
                  onClick={() => handleGenerateCourse()}
                  className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-bold text-sm tracking-wide transition shadow-lg shadow-indigo-950/50 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>{statusText || "Designing Curriculum..."}</span>
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      <span>Generate Course for "{searchQuery.trim() || "Topic"}"</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        ) : (
          /* LIVE COURSE GENERATION PROGRESS VIEW */
          <div className="space-y-6">
            {/* Optimistic First-Module Progressive Handoff Banner */}
            {jobState?.first_lesson_ready && jobState?.first_lesson_id && (
              <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-950/90 via-teal-950/70 to-slate-900 border border-emerald-500/50 shadow-2xl relative overflow-hidden animate-in fade-in slide-in-from-top-2 duration-500">
                <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-2xl shrink-0 shadow-inner">
                    🎉
                  </div>
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                        First Module Ready to Learn!
                      </span>
                      <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono font-bold border border-emerald-500/30">
                        1080p Video + Notes Ready
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white leading-snug">
                      {jobState.first_lesson_title || "Lesson 1: Core Fundamentals"}
                    </h3>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      The first module is fully rendered and ready! You can start watching and learning right now while remaining lessons continue generating autonomously in the background.
                    </p>

                    {/* Progressive Handoff Navigation */}
                    <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                      <Link
                        href={`/topics/${jobState.first_lesson_id}?course_id=${jobState.course_id}`}
                        className="px-5 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-xs tracking-wide rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/50 transition transform hover:-translate-y-0.5 cursor-pointer"
                      >
                        <span>▶ Start Watching Lesson 1 Now</span>
                        {autoRedirectCountdown !== null && !redirectCancelled && (
                          <span className="bg-slate-950 text-emerald-300 px-1.5 py-0.5 rounded text-[10px] font-mono">
                            {autoRedirectCountdown}s
                          </span>
                        )}
                        <span>→</span>
                      </Link>

                      {autoRedirectCountdown !== null && !redirectCancelled && (
                        <button
                          type="button"
                          onClick={() => setRedirectCancelled(true)}
                          className="px-3.5 py-2 text-xs text-slate-400 hover:text-slate-200 border border-slate-700/80 rounded-xl transition cursor-pointer"
                        >
                          Cancel Auto-Redirect
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Background Course Pipeline Progress Card */}
            <div className="p-6 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                  Background Curriculum Engine
                </span>
                <span className="font-mono text-slate-400">
                  {jobState ? `${jobState.progress}%` : "Structuring..."}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-indigo-500 to-cyan-500 h-full transition-all duration-500 ease-out"
                  style={{ width: `${jobState?.progress || 10}%` }}
                />
              </div>

              <div className="flex items-center gap-2 text-sm text-slate-300">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                <span className="font-medium">
                  {jobState?.current_lesson || "Structuring curriculum chapters & lesson skeletons..."}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2 text-xs text-slate-400 border-t border-slate-800/80">
                <div>
                  Completed Lessons:{" "}
                  <span className="text-emerald-400 font-bold">
                    {jobState?.completed_count ?? 0} / {jobState?.total_count ?? "..."}
                  </span>
                </div>
                <div className="text-right">
                  Status:{" "}
                  <span className="text-indigo-300 font-semibold uppercase">
                    {jobState?.status || "QUEUED"}
                  </span>
                </div>
              </div>
            </div>

            {/* View Course Action */}
            {courseId && (
              <div className="space-y-3 pt-2">
                <button
                  onClick={() => router.push(`/courses/${courseId}`)}
                  className="w-full py-4 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-xl font-bold text-sm tracking-wide transition shadow-lg flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>📖</span>
                  <span>View Full Course Syllabus & Outline →</span>
                </button>
                <p className="text-xs text-center text-slate-500">
                  Subsequent lesson videos update automatically as the background engine finishes rendering each module.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
