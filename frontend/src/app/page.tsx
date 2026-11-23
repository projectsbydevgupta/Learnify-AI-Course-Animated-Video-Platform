import Link from "next/link";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function LandingPage() {
  const { userId } = await auth();

  if (userId) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center bg-slate-950 text-white">
      <h1 className="text-5xl font-extrabold mb-4 pb-2 bg-linear-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
        Learnify AI
      </h1>
      <p className="text-lg text-slate-400 max-w-xl mb-8">
        Autonomous AI-Powered Course Curriculum & 1080p Animated Video Lectures on Demand.
      </p>
      <div className="flex gap-4">
        <Link
          href="/sign-in"
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-semibold transition"
        >
          Sign In
        </Link>
        <Link
          href="/sign-up"
          className="px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg font-semibold transition"
        >
          Create Account
        </Link>
      </div>
    </main>
  );
}