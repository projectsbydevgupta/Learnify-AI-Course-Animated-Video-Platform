"use client";

import { useState, useEffect } from "react";
import { UserButton, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface GeneratedLesson {
  id: string;
  title: string;
  topic: string;
  difficulty: string;
  status: string;
  created_at: string | null;
  has_video: boolean;
  video_url: string | null;
  quiz_count: number;
  read_time: string;
  summary: string;
}

interface GeneratedCourse {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  created_at: string | null;
  chapters_count: number;
  total_lessons: number;
  completed_lessons: number;
  failed_lessons: number;
  progress_percent: number;
}

export default function DashboardPage() {
  const { user } = useUser();
  const router = useRouter();
  const [quickTopic, setQuickTopic] = useState("");

  const [lessons, setLessons] = useState<GeneratedLesson[]>([]);
  const [loadingLessons, setLoadingLessons] = useState(true);
  const [courses, setCourses] = useState<GeneratedCourse[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [searchFilter, setSearchFilter] = useState("");
  const [showAll, setShowAll] = useState(false);

  const handleQuickSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickTopic.trim()) return;
    router.push(`/dashboard/generate-topic?topic=${encodeURIComponent(quickTopic.trim())}`);
  };

  const handleDeleteLesson = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm("Are you sure you want to delete this lesson?")) return;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${backendUrl}/api/topics/${id}`, { method: "DELETE" });
      if (res.ok) {
        setLessons((prev) => prev.filter((l) => l.id !== id));
      }
    } catch (err) {
      console.error("Error deleting lesson:", err);
    }
  };

  const handleDeleteCourse = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm("Are you sure you want to delete this course and its curriculum?")) return;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${backendUrl}/api/courses/${id}`, { method: "DELETE" });
      if (res.ok) {
        setCourses((prev) => prev.filter((c) => c.id !== id));
      }
    } catch (err) {
      console.error("Error deleting course:", err);
    }
  };

  useEffect(() => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    fetch(`${backendUrl}/api/topics`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch topics");
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setLessons(data);
        }
      })
      .catch((err) => {
        console.error("Error loading generated topics:", err);
      })
      .finally(() => {
        setLoadingLessons(false);
      });

    fetch(`${backendUrl}/api/courses`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch courses");
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setCourses(data);
        }
      })
      .catch((err) => {
        console.error("Error loading courses:", err);
      })
      .finally(() => {
        setLoadingCourses(false);
      });
  }, []);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Recently";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "Recently";
    }
  };

  const filteredLessons = lessons.filter((l) =>
    l.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
    l.topic.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-40 px-6 sm:px-10 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
            <span className="text-white font-black text-lg">L</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide">
              Learnify
            </h1>
            <p className="text-[11px] text-cyan-400 font-mono tracking-wider uppercase">
              Autonomous Course & Video Studio
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>ChromaDB RAG Active</span>
          </div>
          <UserButton />
        </div>
      </header>

      {/* Main Dashboard Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 sm:p-10 space-y-12">
        {/* Welcome Hero with Integrated Quick-Generator */}
        <section className="relative rounded-3xl bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-indigo-950/40 border border-slate-800/80 p-8 sm:p-12 shadow-2xl overflow-hidden backdrop-blur-2xl">
          <div className="absolute -top-32 -right-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-32 -left-32 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 space-y-6 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold tracking-wide uppercase">
              ⚡ Multi-Agent Educational Engine
            </div>

            <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
              Master Any Concept with <br />
              <span className="bg-gradient-to-r from-cyan-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                Animated Videos & AI Tutoring
              </span>
            </h2>

            <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
              Welcome back{user?.firstName ? `, ${user.firstName}` : ""}! Enter any computer science, AI, or math topic.
              Our agentic pipeline retrieves verified knowledge, drafts intuitive analogies, scripts narration, and renders a 1080p educational video on demand.
            </p>

            {/* Quick Generator Input Bar */}
            <form onSubmit={handleQuickSubmit} className="pt-2 flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="e.g. Binary Search Trees, Gradient Descent, Graph Traversals, Transformer Attention..."
                  value={quickTopic}
                  onChange={(e) => setQuickTopic(e.target.value)}
                  className="w-full px-5 py-4 bg-slate-950/90 border border-slate-700/80 rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-sm sm:text-base shadow-inner transition"
                />
              </div>

              <button
                type="submit"
                disabled={!quickTopic.trim()}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 disabled:opacity-50 text-white rounded-2xl font-bold text-sm sm:text-base transition shadow-lg shadow-purple-950/40 cursor-pointer whitespace-nowrap flex items-center justify-center gap-2"
              >
                <span>🚀</span>
                <span>Generate Lesson</span>
              </button>
            </form>
          </div>

          {/* Metric Stats Badges */}
          <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-8 border-t border-slate-800/60">
            <div className="p-3">
              <span className="text-2xl font-black text-cyan-400">1080p</span>
              <p className="text-xs text-slate-400 mt-1">Full HD Video Engine</p>
            </div>
            <div className="p-3">
              <span className="text-2xl font-black text-emerald-400">RAG + Chroma</span>
              <p className="text-xs text-slate-400 mt-1">Verified Citations</p>
            </div>
            <div className="p-3">
              <span className="text-2xl font-black text-indigo-400">8-Scene</span>
              <p className="text-xs text-slate-400 mt-1">Visual Blueprints</p>
            </div>
            <div className="p-3">
              <span className="text-2xl font-black text-amber-400">Adaptive</span>
              <p className="text-xs text-slate-400 mt-1">Interactive Quizzes</p>
            </div>
          </div>
        </section>

        {/* Primary Generator Modes */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Mode 1: Single Topic Generator */}
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800/80 hover:border-cyan-500/50 transition-all duration-300 shadow-xl relative overflow-hidden group">
            <div className="flex justify-between items-start mb-6">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-3xl shadow-inner">
                💡
              </div>
              <span className="text-xs font-semibold px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 rounded-full uppercase tracking-wider">
                Core Pipeline
              </span>
            </div>

            <h3 className="text-2xl font-bold text-white group-hover:text-cyan-300 transition-colors">
              Single Topic Generator
            </h3>
            <p className="text-sm text-slate-400 mt-2 mb-6 leading-relaxed">
              Generate a comprehensive topic course with real-world analogies, step-by-step logic breakdowns, 1080p Remotion animations, natural voiceover, and an interactive self-assessment quiz.
            </p>

            <Link
              href="/dashboard/generate-topic"
              className="inline-flex items-center justify-center w-full py-4 bg-cyan-600 hover:bg-cyan-500 text-white rounded-2xl font-bold transition shadow-lg shadow-cyan-950/50"
            >
              Start Topic Generator →
            </Link>
          </div>

          {/* Mode 2: Full Course Generator */}
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/50 transition-all duration-300 shadow-xl relative overflow-hidden group">
            <div className="flex justify-between items-start mb-6">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-3xl shadow-inner">
                🎓
              </div>
              <span className="text-xs font-semibold px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-full uppercase tracking-wider">
                Full Curriculum
              </span>
            </div>

            <h3 className="text-2xl font-bold text-white group-hover:text-indigo-300 transition-colors">
              Full Course Generator
            </h3>
            <p className="text-sm text-slate-400 mt-2 mb-6 leading-relaxed">
              Generate a multi-chapter structured curriculum (Course → Chapters → Lessons) utilizing the exact same lesson-generation pipeline for every module with unified student tracking.
            </p>

            <Link
              href="/dashboard/generate-course"
              className="inline-flex items-center justify-center w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-bold transition shadow-lg shadow-indigo-950/50"
            >
              Start Course Generator →
            </Link>
          </div>
        </section>

        {/* Live Generated Full Courses (Curriculums) Section */}
        {courses.length > 0 && (
          <section className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-2xl font-bold text-white flex items-center gap-2.5">
                  <span>🎓</span> Your Generated Courses (Curriculums)
                </h3>
                <p className="text-sm text-slate-400 mt-1">
                  Multi-chapter courses with synchronized Remotion animated videos and assessment quizzes.
                </p>
              </div>

              <Link
                href="/dashboard/generate-course"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
              >
                + Create New Course
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {courses.map((course) => (
                <div
                  key={course.id}
                  className="p-7 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/50 transition-all duration-300 shadow-xl flex flex-col justify-between space-y-4 group"
                >
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 font-semibold uppercase tracking-wider">
                        🎓 Course Curriculum
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-slate-500">
                          {course.chapters_count} Chapters • {course.total_lessons} Lessons
                        </span>
                        <button
                          onClick={(e) => handleDeleteCourse(course.id, e)}
                          title="Delete this course"
                          className="p-1 text-slate-500 hover:text-rose-400 rounded-md hover:bg-slate-800/80 transition cursor-pointer text-xs"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>

                    <h4 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors">
                      {course.title}
                    </h4>

                    {course.description && (
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {course.description}
                      </p>
                    )}

                    {/* Progress Bar */}
                    <div className="space-y-2 pt-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">Curriculum Progress</span>
                        <span className="font-mono font-bold text-emerald-400">
                          {course.completed_lessons} / {course.total_lessons} Ready ({course.progress_percent}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-emerald-500 h-full transition-all duration-500"
                          style={{ width: `${course.progress_percent}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between gap-4">
                    <Link
                      href={`/courses/${course.id}`}
                      className="w-full inline-flex items-center justify-center py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition shadow"
                    >
                      Explore Course Syllabus & Lessons →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Live Generated Lessons Library from Database */}
        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-2xl font-bold text-white flex items-center gap-2.5">
                <span>📚</span> Your Generated Lessons Library
              </h3>
              <p className="text-sm text-slate-400 mt-1">
                Access your real generated animated videos, verified notes, and quiz records from PostgreSQL.
              </p>
            </div>

            {/* Search Filter */}
            <div className="w-full sm:w-72">
              <input
                type="text"
                placeholder="Search generated lessons..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>
          </div>

          {loadingLessons ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-4 animate-pulse"
                >
                  <div className="flex justify-between items-center">
                    <div className="w-20 h-5 bg-slate-800 rounded-full" />
                    <div className="w-16 h-4 bg-slate-800 rounded" />
                  </div>
                  <div className="w-3/4 h-6 bg-slate-800 rounded" />
                  <div className="w-full h-12 bg-slate-800/60 rounded" />
                  <div className="w-full h-10 bg-slate-800 rounded-xl mt-4" />
                </div>
              ))}
            </div>
          ) : filteredLessons.length === 0 ? (
            <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-800/80 space-y-4">
              <span className="text-4xl">📖</span>
              <h4 className="text-lg font-bold text-white">No Generated Lessons Found</h4>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                {searchFilter ? "No lessons match your search." : "You haven't generated any lessons yet. Use the generator above to create your first lesson with 1080p animated video!"}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {(showAll ? filteredLessons : filteredLessons.slice(0, 6)).map((item) => (
                  <div
                    key={item.id}
                    className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 transition-all duration-300 shadow-xl flex flex-col justify-between space-y-4 group hover:shadow-cyan-950/20 relative"
                  >
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full border bg-cyan-500/10 border-cyan-500/30 text-cyan-300">
                          🎓 Topic Lecture
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 font-mono">
                            {formatDate(item.created_at)}
                          </span>
                          <button
                            onClick={(e) => handleDeleteLesson(item.id, e)}
                            title="Delete this lesson"
                            className="p-1 text-slate-500 hover:text-rose-400 rounded-md hover:bg-slate-800/80 transition cursor-pointer text-xs"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>

                      <h4 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-2">
                        {item.title.replace(/\s*\((Advanced|Intermediate|Beginner)\s*Guide\)/gi, "")}
                      </h4>

                      {item.summary && (
                        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                          {item.summary}...
                        </p>
                      )}

                      <div className="flex flex-wrap gap-2 pt-1 text-xs">
                        {item.has_video ? (
                          <span className="px-2.5 py-1 rounded-md bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 font-medium flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            🎬 1080p Video Ready
                          </span>
                        ) : (
                          <span className="px-2.5 py-1 rounded-md bg-slate-800/80 text-slate-400 border border-slate-700">
                            📝 Notes Ready
                          </span>
                        )}

                        {item.quiz_count > 0 && (
                          <span className="px-2.5 py-1 rounded-md bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 font-medium">
                            📝 {item.quiz_count} Questions
                          </span>
                        )}

                        <span className="px-2.5 py-1 rounded-md bg-slate-800/60 text-slate-400 border border-slate-700/60">
                          ⏱️ {item.read_time}
                        </span>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-slate-800/80">
                      <Link
                        href={`/topics/${item.id}`}
                        className="w-full inline-flex items-center justify-center py-2.5 px-4 bg-slate-800 hover:bg-cyan-600 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition duration-200 shadow"
                      >
                        View Lesson & Video →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>

              {filteredLessons.length > 6 && (
                <div className="text-center pt-2">
                  <button
                    onClick={() => setShowAll(!showAll)}
                    className="px-6 py-2.5 bg-slate-800/90 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-300 rounded-xl transition cursor-pointer"
                  >
                    {showAll ? "Show Latest 6 Only" : `View All ${filteredLessons.length} Saved Lessons`}
                  </button>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}