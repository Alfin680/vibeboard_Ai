"use client";

import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#111] flex items-center justify-center">
      <div className="bg-white p-10 rounded-2xl shadow-xl w-[380px] text-center">
        <div className="text-4xl mb-6">📨</div>

        <h2 className="text-xl font-serif mb-6">Welcome to Vibeboard</h2>

        <button
          onClick={() => alert("google auth later")}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg flex items-center justify-center gap-2 hover:bg-gray-50"
        >
          <span>🔗</span> Continue with Google
        </button>
      </div>
    </div>
  );
}
