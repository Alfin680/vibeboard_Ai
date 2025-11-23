// "use client";

// import { useRouter } from "next/navigation";
// import { useState } from "react";

// export default function DashboardPage() {
//     const router = useRouter();
// const [inputValue, setInputValue] = useState("");
// const handleTagClick = (tag: string) => {
//     if (inputValue.trim() === "") setInputValue(tag);
//     else setInputValue((prev) => prev + " " + tag);
//   };
//   return (
//     <div className="min-h-screen bg-white/60 backdrop-blur-[1px] text-black relative bg-[url('/grid.svg')] bg-[length:40px_40px] sm:bg-[length:50px_50px] bg-center">

//       {/* top left logo */}
//       <div className="absolute top-4 sm:top-6 left-4 sm:left-10 flex items-center gap-2 font-semibold scale-90 sm:scale-100">
//         <img
//           src="/logo.png"
//           className="h-6 w-6 sm:h-7 sm:w-7 object-contain"
//           alt="Vibeboard logo"
//         />
//         <span className="font-[Instrument_Serif] text-black text-xl sm:text-2xl">
//           Vibeboard
//         </span>
//       </div>

//       {/* top right button */}
//       <button
//         onClick={() => router.push("/vibeboard")}
//         className="
//           absolute top-4 sm:top-6 right-4 sm:right-10
//           w-[157px] h-[31px] sm:w-[157px] sm:h-[31px]
//           flex items-center justify-center
//           text-black text-[16px] sm:text-[16px] font-regular
//           rounded-tr-[10px] rounded-br-[10px] rounded-tl-[0px] rounded-bl-[10px]
//           bg-white
          
//           shadow-[inset_0_4px_4px_rgba(255,255,255,0.25)]
//           border-[1px] border-[#EFEFEF]
         
//           transition-transform duration-200 hover:scale-[1.05]
//         "
//       >
//         ❤️Your VibeBoard
//       </button>

//       {/* center title */}
//       <div className="flex flex-col items-center justify-center pt-28 sm:pt-32 px-4 text-center">
//         <h1 className="font-[Instrument_Serif] text-black font-normal text-[48px] sm:text-[78px] leading-none tracking-tight">
//           Vibeboard
//         </h1>

//         <p className="mt-4 sm:mt-6 text-[16px] sm:text-[20px] text-black/70 font-normal font-[var(--font-joan)] max-w-[90%] sm:max-w-none">
//           Find your visual direction instantly. Spend less time scrolling, more
//           time designing.
//         </p>
//       </div>

//       {/* big search box */}

//       <div
//         className="
//          mx-auto w-[92%] sm:w-full max-w-4xl
//     rounded-[22px] bg-white p-5 sm:p-7 mt-10

//     border-[7px] border-[#F7F7F7]

//     shadow-[0px_7px_28px_rgba(0,0,0,0.25)]
//         "
//       >
//         <input
//           type="text"
//           placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
//           value={inputValue}
//           onChange={(e) => setInputValue(e.target.value)}
//           className="w-full bg-transparent outline-none text-[15px] sm:text-[17px] text-black placeholder:text-gray-500"
//         />

//         {/* tags row */}
//         <div className="mt-6 flex items-center flex-wrap gap-3">
//           <span className="text-[13px] sm:text-[14px] text-black/60">
//             Popular Vibes:
//           </span>

//           {["SaaS", "Fintech", "Portfolio", "eCommerce", "AI Tool"].map(
//             (tag) => (
//               <button
//                 key={tag}
//                 onClick={() => handleTagClick(tag)}
//                 className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[13px] sm:text-[14px]"
//               >
//                 {tag}
//               </button>
//             )
//           )}

//           {/* Vibe Search button */}
//           <button
//             onClick={() => router.push("/signup")}
//             className="
//                w-[115px] h-[44px] sm:w-[136px] sm:h-[48px]
//               text-white text-[14px] sm:text-[15px] font-semibold
//               bg-gradient-to-b from-[#000000] to-[#484848]
//               border-[4px] border-[#1C1C1C]
//               rounded-tl-[0px] rounded-tr-[10px] rounded-br-[10px] rounded-bl-[10px]
//               shadow-[inset_0px_4px_4px_rgba(255,255,255,0.25)]
//               flex items-center justify-center ml-auto
//               transition-transform duration-200 hover:scale-[1.05]
//             "
//           >
//             Vibe Search
//           </button>
//         </div>
//       </div>

//       {/* CTA bottom */}
//       <div className="flex justify-center mt-8 mb-10 sm:mb-0 px-4">
//         <button className="text-xs sm:text-sm border border-black/15 bg-white px-4 py-1 rounded-tl-[10px] rounded-tr-[10px] rounded-bl-[2px] rounded-br-[2px] shadow hover:bg-black/5">
//           Creative Block? Click me ✨
//         </button>
//       </div>
//     </div>
//   );
// }
// app/dashboard/page.tsx


"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth, useClerk } from "@clerk/nextjs";

export default function DashboardPage() {
  const router = useRouter();
  const { isSignedIn } = useAuth();
  const { signOut } = useClerk();
  const [inputValue, setInputValue] = useState("");

  const handleTagClick = (tag: string) => {
    setInputValue(prev => (prev.trim() ? `${prev} ${tag}` : tag));
  };

  const handleSignOut = () => {
    signOut({ redirectUrl: "/dashboard" });
  };

  const samplePrompts = [
  "Minimalist fintech dashboard with soft gradients",
  "Luxury eCommerce landing page with serif typography",
  "Vibrant portfolio site with animated transitions",
  "Dark-mode SaaS interface with neon accents",
  "Calm wellness app UI with pastel colors"
];

const typeEffect = (text: string, i = 0) => {
  if (i <= text.length) {
    setInputValue(text.slice(0, i));
    setTimeout(() => typeEffect(text, i + 1), 40); // adjust typing speed: lower = faster
  }
};

const handleCreativeBlock = () => {
  const random = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
  typeEffect(random);
};


  return (
    <div className="min-h-screen bg-white/60 backdrop-blur-[1px] text-black relative bg-[url('/grid.svg')] bg-[length:40px_40px] sm:bg-[length:50px_50px] bg-center">
      
      {/* Logo = signout easter egg */}
      <button
        onClick={() => (isSignedIn ? handleSignOut() : null)}
        className="absolute top-4 sm:top-6 left-4 sm:left-10 flex items-center gap-2 font-semibold scale-90 sm:scale-100"
      >
        <img
          src="/logo.png"
          className="h-6 w-6 sm:h-7 sm:w-7 object-contain"
          alt="Vibeboard logo"
        />
        <span className="font-[Instrument_Serif] text-black text-xl sm:text-2xl">
          Vibeboard
        </span>
      </button>

      {/* Top right button */}
      {isSignedIn ? (
        <button
          onClick={() => router.push("/vibeboard")}
          className="absolute top-4 sm:top-6 right-4 sm:right-10 w-[157px] h-[31px] flex items-center justify-center text-black text-[16px] bg-white rounded-[10px] border border-[#EFEFEF] shadow hover:scale-[1.05] transition"
        >
          ❤️ Your VibeBoard
        </button>
      ) : (
        <button
          onClick={() => router.push("/signup")}
          className="absolute top-4 sm:top-6 right-4 sm:right-10 w-[115px] h-[42px] text-white bg-gradient-to-b from-[#484848] to-[#6C6C6C] rounded-[10px] border-[4px] border-[#535353] shadow hover:scale-[1.05] transition"
        >
          Start for free
        </button>
      )}

      {/* center title */}
      <div className="flex flex-col items-center justify-center pt-28 sm:pt-32 px-4 text-center">
        <h1 className="font-[Instrument_Serif] text-black font-normal text-[48px] sm:text-[78px] leading-none">
          Vibeboard
        </h1>

        <p className="mt-4 sm:mt-6 text-[16px] sm:text-[20px] text-black/70 font-normal max-w-[90%] sm:max-w-none">
          Find your visual direction instantly. Spend less time scrolling, more time designing.
        </p>
      </div>

      {/* search bar */}
      <div className="mx-auto w-[92%] max-w-4xl rounded-[22px] bg-white p-7 mt-10 border-[7px] border-[#F7F7F7] shadow-[0px_7px_28px_rgba(0,0,0,0.25)]">
        <input
          type="text"
          placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="w-full bg-transparent outline-none text-[17px] text-black placeholder:text-gray-500"
        />

        <div className="mt-6 flex items-center flex-wrap gap-3">
          <span className="text-[14px] text-black/60">Popular Vibes:</span>

          {["SaaS", "Fintech", "Portfolio", "eCommerce", "AI Tool"].map(tag => (
            <button
              key={tag}
              onClick={() => handleTagClick(tag)}
              className="px-3 py-[5px] rounded-md border border-black/10 bg-white text-[14px]"
            >
              {tag}
            </button>
          ))}

          <button
            onClick={() =>
              router.push(
                isSignedIn
                  ? `/vibeboard?query=${encodeURIComponent(inputValue)}`
                  : "/signup"
              )
            }
            className="w-[115px] h-[44px] sm:w-[136px] sm:h-[48px]
              text-white text-[14px] sm:text-[15px] font-semibold
              bg-gradient-to-b from-[#000000] to-[#484848]
              border-[4px] border-[#1C1C1C]
              rounded-tl-[0px] rounded-tr-[10px] rounded-br-[10px] rounded-bl-[10px]
              shadow-[inset_0px_4px_4px_rgba(255,255,255,0.25)]
              flex items-center justify-center ml-auto
              transition-transform duration-200 hover:scale-[1.05]"
          >
            Vibe Search
          </button>
        </div>
      </div>

      <div className="flex justify-center mt-8 mb-10 px-4">
        <button className="text-xs sm:text-sm border border-black/15 bg-white px-4 py-1 rounded-tl-[10px] rounded-tr-[10px] rounded-bl-[2px] rounded-br-[2px] shadow hover:bg-black/5" 
        onClick={handleCreativeBlock}>
          Creative Block? Click me ✨
        </button>
      </div>
    </div>
  );
}

