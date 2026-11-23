import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Learnify — AI Course & Video Platform",
  description: "Autonomous AI-Powered Course Curriculum & Animated Video Lectures",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark bg-[#070b14]">
        <body className={`${inter.className} bg-[#070b14] text-slate-100 min-h-screen antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}