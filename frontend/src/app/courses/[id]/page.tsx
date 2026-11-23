"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface LessonItem {
  id: string;
  title: string;
  topic: string;
  status: string;
  has_video: boolean;
  video_url: string | null;
  quiz_count: number;
  verification_score: number | null;
}

interface ChapterItem {
  id: string;
  title: string;
  order_index: number;
  lessons: LessonItem[];
}

interface CourseDetail {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  created_at: string | null;
  total_lessons: number;
  completed_lessons: number;
  progress_percent: number;
  chapters: ChapterItem[];
}

export default function CourseViewerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const courseId = resolvedParams.id;
  const router = useRouter();

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [retryingLessonId, setRetryingLessonId] = useState<string | null>(null);

  const fetchCourse = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/courses/${courseId}`);
      if (!res.ok) throw new Error("Course not found");
      const data: CourseDetail = await res.json();
      setCourse(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourse();
    // Poll course state every 4s while any lesson is still processing or pending
    const interval = setInterval(() => {
      fetchCourse();
    }, 4000);
    return () => clearInterval(interval);
  }, [courseId]);

  const handleRetryLesson = async (lessonId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setRetryingLessonId(lessonId);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      await fetch(`${backendUrl}/api/courses/${courseId}/retry-lesson/${lessonId}`, {
        method: "POST"
      });
      await fetchCourse();
    } catch (err) {
      console.error(err);
    } finally {
      setRetryingLessonId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070b14] text-white flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Loading Course Syllabus...</p>
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen bg-[#070b14] text-white flex flex-col items-center justify-center p-6 text-center">
        <h2 className="text-2xl font-bold mb-2">Course Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">The requested course could not be retrieved from PostgreSQL.</p>
        <Link
          href="/dashboard"
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold transition"
        >
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 p-4 sm:p-8 relative font-sans">
      {/* Background Ambient Glows */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-5xl mx-auto space-y-8 relative z-10">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition group"
          >
            <span className="group-hover:-translate-x-1 transition-transform">←</span>
            Back to Studio Dashboard
          </Link>
          <span className="text-xs font-mono text-slate-500">
            Course ID: {course.id}
          </span>
        </div>

        {/* Hero Header Card */}
        <div className="p-8 sm:p-10 rounded-3xl bg-slate-900/70 border border-slate-800/90 shadow-2xl backdrop-blur-2xl space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
              🎓 Full Course Curriculum
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              {course.chapters.length} Chapters • {course.total_lessons} Lessons
            </span>
          </div>

          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              {course.title}
            </h1>
            {course.description && (
              <p className="text-sm text-slate-400 mt-3 leading-relaxed max-w-3xl">
                {course.description}
              </p>
            )}
          </div>

          {/* Progress Overview Bar */}
          <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300">
                Course Completion Status
              </span>
              <span className="font-mono font-bold text-emerald-400">
                {course.completed_lessons} / {course.total_lessons} Lessons Ready ({course.progress_percent}%)
              </span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-indigo-500 via-cyan-500 to-emerald-500 h-full transition-all duration-700 ease-out"
                style={{ width: `${course.progress_percent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Chapters & Lessons Syllabus Tree */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📑</span> Course Syllabus & Modular Breakdown
          </h2>

          <div className="space-y-6">
            {course.chapters.map((ch, chIdx) => (
              <div
                key={ch.id}
                className="rounded-3xl bg-slate-900/50 border border-slate-800/80 overflow-hidden shadow-xl"
              >
                {/* Chapter Banner */}
                <div className="px-6 py-4 bg-slate-900/90 border-b border-slate-800/80 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 text-xs font-bold flex items-center justify-center font-mono">
                      {ch.order_index}
                    </span>
                    <h3 className="text-base font-bold text-white">
                      {ch.title}
                    </h3>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    {ch.lessons.length} {ch.lessons.length === 1 ? "Lesson" : "Lessons"}
                  </span>
                </div>

                {/* Lessons List in Chapter */}
                <div className="divide-y divide-slate-800/60 p-2 sm:p-4">
                  {ch.lessons.map((ls, lsIdx) => {
                    const isCompleted = ls.status === "completed";
                    const isProcessing = ls.status === "processing";
                    const isFailed = ls.status === "failed";

                    return (
                      <div
                        key={ls.id}
                        className="p-4 rounded-2xl hover:bg-slate-800/40 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
                      >
                        <div className="space-y-1.5 flex-1">
                          <div className="flex items-center gap-2.5">
                            <span className="text-xs text-slate-500 font-mono">
                              {ch.order_index}.{lsIdx + 1}
                            </span>
                            <h4 className="text-sm sm:text-base font-semibold text-white group-hover:text-cyan-300 transition-colors">
                              {ls.title}
                            </h4>
                          </div>

                          {/* Metadata Pills */}
                          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                            {isCompleted ? (
                              <span className="px-2.5 py-0.5 rounded-full bg-emerald-950/70 text-emerald-300 border border-emerald-800/60 font-medium flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                Completed
                              </span>
                            ) : isProcessing ? (
                              <span className="px-2.5 py-0.5 rounded-full bg-amber-950/70 text-amber-300 border border-amber-800/60 font-medium flex items-center gap-1.5 animate-pulse">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                                Generating Video & Notes...
                              </span>
                            ) : isFailed ? (
                              <span className="px-2.5 py-0.5 rounded-full bg-rose-950/70 text-rose-300 border border-rose-800/60 font-medium">
                                ⚠️ Requires Retry
                              </span>
                            ) : (
                              <span className="px-2.5 py-0.5 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700">
                                ⏳ Queued in Worker
                              </span>
                            )}

                            {ls.has_video && (
                              <span className="px-2 py-0.5 rounded-md bg-cyan-950/50 text-cyan-300 border border-cyan-800/50">
                                🎬 1080p Video Ready
                              </span>
                            )}

                            {ls.quiz_count > 0 && (
                              <span className="px-2 py-0.5 rounded-md bg-indigo-950/50 text-indigo-300 border border-indigo-800/50">
                                📝 {ls.quiz_count} Questions
                              </span>
                            )}

                            {ls.verification_score !== null && (
                              <span className="px-2 py-0.5 rounded-md bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
                                🛡️ {ls.verification_score}% Academic Score
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 shrink-0">
                          {isCompleted ? (
                            <Link
                              href={`/topics/${ls.id}?course_id=${courseId}`}
                              className="px-4 py-2 bg-indigo-600 hover:bg-cyan-600 text-white rounded-xl text-xs font-bold transition shadow"
                            >
                              Open Lesson & Video →
                            </Link>
                          ) : isFailed ? (
                            <button
                              onClick={(e) => handleRetryLesson(ls.id, e)}
                              disabled={retryingLessonId === ls.id}
                              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition cursor-pointer"
                            >
                              {retryingLessonId === ls.id ? "Retrying..." : "🔄 Retry Lesson"}
                            </button>
                          ) : (
                            <span className="text-xs text-slate-500 font-mono italic px-3 py-1.5">
                              Rendering in background...
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

