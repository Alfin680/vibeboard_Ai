"use client";

import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#f2f2f2] flex items-center justify-center px-4">
      <div
        className="
          bg-white 
          p-10 
          rounded-[18px]
          text-center 
          w-full max-w-[350px]
          shadow-[8px_8px_16px_rgba(0,0,0,0.15),_-8px_-8px_16px_rgba(255,255,255,0.9)]
        "
      >
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <img
            src="/signuplogo.png"
            className="h-10 w-10 object-contain"
            alt="Vibeboard logo"
          />
        </div>

        {/* Title */}
        <h2
          className="
            font-[Instrument_Serif] 
            font-[400]
            font-weight-400
            text-[24px] 
            leading-[100%] 
            tracking-[0.04em] 
            text-center 
            text-black 
            mb-12
          "
        >
          Welcome to Vibeboard
        </h2>

        {/* Google Button */}
        <button
          onClick={() => router.push("/dashboard")}
          className="
            w-full max-w-[290px] mx-auto px-4 py-3 rounded-xl
            flex items-center justify-center gap-3
            text-black 
            font-[Instrument_Serif] font-[500] text-[20px]

            bg-white
            border border-black

            shadow-[0px_1px_6px_rgba(0,0,0,0.15)]
            hover:shadow-[0px_2px_10px_rgba(0,0,0,0.2)]
            transition-all duration-200
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
