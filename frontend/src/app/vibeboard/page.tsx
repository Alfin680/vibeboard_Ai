"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
// Assuming these are defined elsewhere in your project:
import { useAuth } from "@clerk/nextjs"; 
import { saveSearch } from "@/lib/saveSearch"; 

// --- INTERFACE (Kept unchanged) ---
interface ResultItem {
  title: string;
  url: string;
  image: string;
  tags: string;
  caption?: string; 
  _score?: number; 
}

export default function VibeBoard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const { userId, isSignedIn } = useAuth(); 
  const initialQuery = searchParams.get("query") || "";
  const [results, setResults] = useState<ResultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState(initialQuery); 

  // --- Data Fetching Logic (UNCHANGED) ---
  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true);
      if (!initialQuery) {
        setResults([]); 
        setLoading(false);
        return;
      }

      try {
        const res = await fetch(`http://127.0.0.1:8000/search?q=${encodeURIComponent(initialQuery)}&top_k=20`);
        const data = await res.json();
        setResults(data.results || []);
      } catch (e) {
        console.error("Error fetching search results:", e);
        setResults([]);
      }
      setLoading(false);
    };

    fetchResults();
  }, [initialQuery]); 

  // --- Handle Search (UNCHANGED) ---
  const handleSearch = async () => {
    if (!inputValue.trim()) return;

    if (isSignedIn && userId) {
      // await saveSearch(userId, inputValue); 
    }

    router.push(`/vibeboard?query=${encodeURIComponent(inputValue)}`);
  };

  const LoadingSkeleton = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-7 mt-6">
      {[...Array(6)].map((_, i) => ( 
        <div key={i} className="animate-pulse rounded-2xl bg-gray-700 h-[270px] shadow-sm" />
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-white font-sans relative pb-24">
      
      {/* ─── Top Bar (UI Maintained) ─────────────────────────────── */}
      <div className="sticky top-0 z-10 bg-[#FAFAFA] px-4 py-5 flex items-center justify-between border-b border-gray-300">
        <div className="flex items-center gap-3 text-lg">
          <button 
            className="text-[#222222] text-2xl hover:text-white transition-colors" 
            onClick={() => router.back()}
          >
            &lt;
          </button>
          <span className="font-[Joan] text-[#222222] sm:max-w-[450px]">
            {initialQuery}
          </span>
        </div>

        <button
          className="flex items-center gap-2 font-semibold text-black hover:text-white transition-colors"
          onClick={() => router.push("/dashboard")}
        >
          <img src="/logo.png" className="h-6 w-6" alt="Vibeboard Logo" />
          <span className="font-[Instrument_Serif] text-lg">Vibeboard</span>
        </button>
      </div>

      <div className="p-6">
        
        {/* ─── Results Grid ─────────────────────────────── */}
        {loading && <LoadingSkeleton />}

        {!loading && results.length > 0 && (
          <div className="flex flex-wrap gap-7 mt-6 justify-center"> 
            {results.map((item, i) => (
              <div
                key={i}
                // --- MAIN CARD CONTAINER (Dimensions Maintained) ---
                className="
                  w-[378px] h-[400px] 
                  rounded-[12px] 
                  bg-white shadow-lg 
                  border-[6px] border-[#F7F7F7] shadow-[inset_0_5.88_23.5px_rgba(0,0,0,0.25)]
                  hover:shadow-xl transition-all duration-200 overflow-hidden relative
                  flex flex-col text-black 
                "
              >
                
                {/* Image Container (NEW PADDING APPLIED) */}
                <div 
                  className="relative group flex-shrink-0 px-2 pt-4" // 8px left/right, 16px top padding
                  style={{ height: '70%', maxHeight: '280px' }}
                >
                  <img
                    src={item.image || "/placeholder.png"} 
                    // Image itself should take up all available space
                    className="w-full h-full object-cover object-center rounded-t-[6px]" 
                    alt={item.title || "UI Design"}
                  />

                  {/* Hover VIEW Button (UI Maintained) */}
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute inset-0 m-auto h-10 w-24 opacity-0 group-hover:opacity-100 
                               transition-opacity duration-300 bg-white/20 backdrop-blur-sm rounded-lg text-sm font-semibold text-white
                               flex items-center justify-center border border-white/30"
                  >
                    View ↗
                  </a>
                </div>

                {/* Caption / Vibe Explanation (NEW PADDING & SEPARATOR) */}
                <div 
                  className="px-2 pt-4 pb-4 text-sm leading-relaxed text-gray-700 border-t border-gray-200" // 8px left/right, 16px top/bottom padding + 1px separator
                  style={{ height: '30%' }}
                >
                  <p className="font-[Instrument-Sans] text-[#5C5B5B] text-[18px] mb-1">
                    <span className="font-bold text-[#222222]">✚ Vibe Explanation:</span>{" "}
                    {item.caption || item.title || "Creative Concept"}
                  </p>
                </div>

                {/* Like button (Heart) (UI Maintained) */}
                <button
                  className="absolute right-4 top-4 text-gray-400 text-xl hover:text-red-500 transition-colors duration-200"
                >
                  ♥
                </button>
              </div>
            ))}
          </div>
        )}

        {/* ─── No Results State ─────────────────────────────── */}
        {!loading && results.length === 0 && (
          <div className="text-center p-20 bg-[#2A2A2A] rounded-xl mt-10 shadow-lg border border-gray-700">
            <p className="text-xl font-semibold text-gray-300">
              No vibes found for "**{initialQuery}**".
            </p>
            <p className="text-gray-500 mt-2">Try a different description!</p>
          </div>
        )}
      </div>

      {/* ─── Floating Bottom Search Bar (UI Maintained) ─────────────────── */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full flex justify-center">
        <div className="flex items-center w-[90vw] sm:w-[420px] bg-[#2A2A2A] shadow-2xl 
                        rounded-xl px-2 py-4 border border-gray-700 relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
            className="flex-1 bg-transparent outline-none text-base text-white placeholder:text-gray-500"
            placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
          />

          <button
            onClick={handleSearch}
            className="absolute right-3 bg-white text-black rounded-lg 
                       w-8 h-8 flex items-center justify-center text-lg font-bold
                       hover:bg-gray-200 transition-colors"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}