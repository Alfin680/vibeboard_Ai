"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get("query") || "";

  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch results from your backend
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
    <div className="min-h-screen bg-[#f7f7f7] text-black px-4 pb-20 relative">

      {/* ─── Top Bar ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between py-6 mb-6 border-b bg-white px-2 rounded-b-xl shadow-sm">
        <div className="flex items-center gap-3 text-lg">
          <span className="text-gray-600">&lt;</span>
          <span className="font-medium text-black">{query}</span>
        </div>

        <div className="flex items-center gap-2 font-semibold cursor-pointer"
             onClick={() => router.push("/dashboard")}>
          <img src="/logo.png" className="h-6 w-6" />
          <span className="font-[Instrument_Serif] text-lg">Vibeboard</span>
        </div>
      </div>


      {/* ─── Results Grid ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">

        {loading && (
          <>
            {[...Array(6)].map((_, i) => (
              <div key={i} className="animate-pulse h-[280px] bg-gray-200 rounded-xl" />
            ))}
          </>
        )}

        {!loading &&
          results.map((item, i) => (
            <div
              key={i}
              className="bg-white rounded-xl shadow-md border hover:shadow-lg transition relative overflow-hidden"
            >
              {/* Image */}
              <div className="relative group">
                <img
                  src={item.image || "/placeholder.png"}
                  className="w-full h-44 object-cover rounded-t-xl"
                />

                {/* Hover action */}
                <button
                  className="absolute inset-0 m-auto h-9 w-20 opacity-0 group-hover:opacity-100 transition 
                             bg-white border rounded-lg text-xs shadow-md flex items-center justify-center gap-1"
                >
                  View 🔍
                </button>
              </div>

              {/* Text block */}
              <div className="p-4 text-sm leading-relaxed">
                <p className="font-semibold text-[15px]">
                  <span className="font-bold">✚ Vibe Explanation:</span>{" "}
                  {item.caption || item.title || "Creative Concept"}
                </p>
              </div>

              {/* Like button */}
              <button className="absolute right-4 bottom-4 text-gray-400 text-xl hover:text-red-500 transition">
                ♥
              </button>
            </div>
          ))}
      </div>


      {/* ─── Floating Bottom Search Bar ───────────────────────────── */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2">
        <div className="flex items-center w-[90vw] sm:w-[420px] bg-white shadow-lg rounded-xl px-4 py-2 border relative">

          <input
            type="text"
            className="flex-1 bg-transparent outline-none text-[14px]"
            placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
          />

          {/* Search button */}
          <button
            onClick={() => router.push(`/results?query=${query}`)}
            className="absolute right-3 bg-black text-white rounded-lg w-8 h-8 flex items-center justify-center text-lg"
          >
            ↑
          </button>
        </div>
      </div>

    </div>
  );
}
