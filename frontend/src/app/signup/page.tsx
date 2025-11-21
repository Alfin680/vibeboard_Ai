"use client";

import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#f2f2f2] flex items-center justify-center">
      <div
        className="
          bg-[#ffffff]
          p-10 
          rounded-3xl 
          text-center 
          w-[380px]

          shadow-[8px_8px_16px_rgba(0,0,0,0.15),_-8px_-8px_16px_rgba(255,255,255,0.9)]
        "
      >
        {/* Icon */}
        <div className="text-4xl mb-6">📨</div>

        {/* Title */}
        <h2 className="text-xl font-serif mb-6">Welcome to Vibeboard</h2>

        {/* Google Button – Neumorphic */}
        <button
          onClick={() => alert("google auth later")}
          className="
            w-full px-4 py-3 rounded-xl
            flex items-center justify-center gap-3
            text-gray-700 font-medium

            bg-[#ffffff]
            shadow-[inset_4px_4px_8px_rgba(0,0,0,0.12),inset_-4px_-4px_8px_rgba(255,255,255,0.9)]
            border border-gray-200

            transition-all duration-200
            hover:shadow-[inset_2px_2px_6px_rgba(0,0,0,0.15),inset_-2px_-2px_6px_rgba(255,255,255,0.9)]
          "
        >
          <img
            src="https://www.gstatic.com/images/branding/product/1x/gsa_64dp.png"
            className="w-5 h-5"
          />
          Continue with Google
        </button>
      </div>
    </div>
  );
}
