"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const query = searchParams.get("query") || "";
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState(query);

  // Fetch results from backend
  useEffect(() => {
    if (!query) return;

    const fetchResults = async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/api/search?query=${encodeURIComponent(query)}`
        );
        const data = await res.json();
        setResults(data.results || []);
      } catch (e) {
        console.log("Error fetching results", e);
      }
      setLoading(false);
    };

    fetchResults();
  }, [query]);

  return (
    <div className="min-h-screen bg-[#f7f7f7] text-black px-4 pb-24">

      {/* ─── Top Bar ─────────────────────────────── */}
      <div className="flex items-center justify-between py-6 mb-6 
                      border-b border-black/5 bg-white rounded-b-2xl shadow-sm px-2">

        {/* Back + Query */}
        <div className="flex items-center gap-3 text-lg">
          <button className="text-gray-600 text-2xl" onClick={() => router.back()}>
            &lt;
          </button>

          <span className="font-medium text-black truncate max-w-[250px] sm:max-w-[400px]">
            {query}
          </span>
        </div>

        {/* Vibeboard Button */}
        <div
          className="flex items-center gap-2 font-semibold cursor-pointer"
          onClick={() => router.push("/dashboard")}
        >
          <img src="/logo.png" className="h-6 w-6" />
          <span className="font-[Instrument_Serif] text-lg">Vibeboard</span>
        </div>
      </div>


      {/* ─── Results Grid ─────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-7">

        {/* Loading Skeletons */}
        {loading &&
          [...Array(6)].map((_, i) => (
            <div key={i} className="animate-pulse rounded-2xl bg-gray-200 h-[270px]" />
          ))}

        {/* Render results */}
        {!loading &&
          results.map((item, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl shadow-sm border border-black/10 
                         hover:shadow-lg transition overflow-hidden relative"
            >
              {/* Image */}
              <div className="relative group">
                <img
                  src={item.image || "/placeholder.png"}
                  className="w-full h-[190px] object-cover rounded-t-2xl"
                />

                {/* Hover VIEW Button */}
                <button
                  className="absolute inset-0 m-auto h-9 w-20 opacity-0 group-hover:opacity-100 
                             transition bg-white/90 border rounded-lg text-xs shadow-md 
                             flex items-center justify-center backdrop-blur-sm"
                >
                  View 🔍
                </button>
              </div>

              {/* Caption */}
              <div className="p-4 text-sm leading-relaxed">
                <p className="font-semibold text-[15px]">
                  <span className="font-bold">✚ Vibe Explanation:</span>{" "}
                  {item.caption || item.title || "Creative Concept"}
                </p>
              </div>

              {/* Like button */}
              <button
                className="absolute right-4 bottom-4 text-gray-400 text-xl hover:text-red-500 transition"
              >
                ♥
              </button>
            </div>
          ))}
      </div>


      {/* ─── Floating Bottom Search Bar ─────────────────── */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full flex justify-center">
        <div className="flex items-center w-[90vw] sm:w-[420px] bg-white shadow-xl 
                        rounded-xl px-4 py-2 border relative">

          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="flex-1 bg-transparent outline-none text-[14px]"
            placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
          />

          {/* Search Button */}
          <button
            onClick={() =>
              router.push(`/results?query=${encodeURIComponent(inputValue)}`)
            }
            className="absolute right-3 bg-black text-white rounded-lg 
                       w-8 h-8 flex items-center justify-center text-lg"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
