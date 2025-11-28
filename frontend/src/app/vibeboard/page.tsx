// "use client";

// import { useSearchParams, useRouter } from "next/navigation";
// import { useEffect, useState } from "react";
// import { useAuth } from "@clerk/nextjs";

// // NOTE: Ensure your path to the saveLike file is correct (e.g., '@/lib/saveLike')
// // Assuming you have imported and configured these in your actual project:
// // import { saveLike, fetchLikedStatus } from "@/lib/saveLike"; 
// async function saveLikeToBackend(userId: string, item: any) {
//   await fetch("http://127.0.0.1:8000/api/likes/add", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({
//       user_id: userId,
//       title: item.title,
//       url: item.url,
//       image: item.image,
//       caption: item.caption,
//     }),
//   });
// }

// async function removeLikeFromBackend(userId: string, url: string) {
//   await fetch("http://127.0.0.1:8000/api/likes/remove", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({
//       user_id: userId,
//       url,
//     }),
//   });
// }

// interface ResultItem {
//   title: string;
//   url: string;
//   image: string;
//   tags?: string;
//   caption?: string;
//   _score?: number;
// }

// // Placeholder functions for database interaction
// // REPLACE THESE with the actual imported async functions from your /lib/saveLike.ts file
// const saveLike = async ({ url, is_liked, user_id }: any) => { console.log(`[DB] ${is_liked ? 'LIKING' : 'UNLIKING'} ${url} for ${user_id}`); return true; };
// const fetchLikedStatus = async (userId: string, urls: string[]): Promise<Record<string, boolean>> => { 
//     console.log(`[DB] Fetching liked status for ${urls.length} items for ${userId}`); 
//     return {}; // Returns an empty map for simplicity in this demo
// };


// export default function VibeBoard() {
//   const searchParams = useSearchParams();
//   const router = useRouter();
//   const { userId, isSignedIn } = useAuth();
//   const initialQuery = searchParams.get("query") || "";

//   const [results, setResults] = useState<ResultItem[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [inputValue, setInputValue] = useState(initialQuery);

//   // local liked state keyed by item url (string) -> boolean
//   const [likedMap, setLikedMap] = useState<Record<string, boolean>>({});

//   // --- Data & Status Fetching ---
//   useEffect(() => {
//     const fetchAllData = async () => {
//       setLoading(true);
//       if (!initialQuery) {
//         setResults([]);
//         setLoading(false);
//         return;
//       }
      
//       try {
//         // 1. Fetch Search Results
//         const res = await fetch(
//           `http://127.0.0.1:8000/search?q=${encodeURIComponent(initialQuery)}&top_k=20`
//         );
//         const data = await res.json();
//         const fetchedResults: ResultItem[] = data.results || [];
//         setResults(fetchedResults);

//         // 2. Fetch Initial Liked Status from Supabase
//         if (isSignedIn && userId && fetchedResults.length > 0) {
//           const urls = fetchedResults.map(r => r.url);
//           const initialLikes = await fetchLikedStatus(userId, urls);
//           setLikedMap(initialLikes);
//         }

//       } catch (e) {
//         console.error("Error fetching data:", e);
//         setResults([]);
//       }
//       setLoading(false);
//     };

//     fetchAllData();
//   }, [initialQuery, userId, isSignedIn]); // Fetch status when user signs in

//   // --- Handle Search (UNCHANGED) ---
//   const handleSearch = async () => {
//     if (!inputValue.trim()) return;
//     router.push(`/vibeboard?query=${encodeURIComponent(inputValue)}`);
//   };
  
//   // --- ASYNC LIKE TOGGLE (SUPABASE INTEGRATED) ---
//   const toggleLike = async (key: string, item: ResultItem) => {
//   const newState = !likedMap[key];

//   // immediate UI update
//   setLikedMap(prev => ({ ...prev, [key]: newState }));

//   if (!userId) return;

//   if (newState) {
//     await saveLikeToBackend(userId, item);
//   } else {
//     await removeLikeFromBackend(userId, key);
//   }
// };


//   const LoadingSkeleton = () => (
//     <div className="flex flex-wrap gap-7 mt-6 justify-center">
//       {[...Array(6)].map((_, i) => (
//         <div key={i} className="animate-pulse rounded-2xl bg-gray-700 w-full sm:w-[378px] h-[400px] shadow-sm" />
//       ))}
//     </div>
//   );

//   return (
//     <div className="min-h-screen bg-[#FAFAFA] text-white font-sans relative pb-24">
//       {/* ─── Top Bar ─────────────────────────────── */}
//       <div className="sticky top-0 z-10 bg-[#FAFAFA] px-4 py-5 flex items-center justify-between border-b border-gray-300">
//         <div className="flex items-center gap-3 text-lg">
//           <button className="text-[#222222] text-2xl hover:text-black transition-colors" onClick={() => router.back()}>
//             &lt;
//           </button>
//           <span className="font-[Joan] text-[#222222] sm:max-w-[450px]">{initialQuery}</span>
//         </div>

//         <button
//           className="flex items-center gap-2 font-semibold text-black hover:text-black transition-colors"
//           onClick={() => router.push("/dashboard")}
//         >
//           <img src="/logo.png" className="h-6 w-6" alt="Vibeboard Logo" />
//           <span className="font-[Instrument_Serif] text-lg">Vibeboard</span>
//         </button>
//       </div>

//       <div className="p-6">
//         {loading && <LoadingSkeleton />}

//         {!loading && results.length > 0 && (
//           // ─── Results Grid (Vertical Scrolling / Wrapping) ────────────────
//           <div className="flex flex-wrap gap-7 mt-6 justify-center">
//             {results.map((item, i) => {
//               const key = item.url || `idx-${i}`;
//               const liked = !!likedMap[key];

//               return (
//                 <div
//                   key={key}
//                   // --- MAIN CARD CONTAINER (Fixed Dimensions & White Background) ---
//                   className="
//                     w-full sm:w-[378px] h-[400px] 
//                     rounded-[12px] 
//                     bg-white shadow-lg 
//                     border-[6px] border-[#F7F7F7] 
//                     hover:shadow-xl transition-all duration-200 overflow-hidden relative
//                     flex flex-col text-black
//                   "
//                 >
//                   {/* Image container (fixed height percentage + inner padding) */}
//                   <div className="relative group flex-shrink-0 px-2 pt-4" style={{ height: "70%", maxHeight: "280px" }}>
//                     <img
//                       src={item.image || "/placeholder.png"}
//                       className="w-full h-full object-cover object-center rounded-t-[6px]"
//                       alt={item.title || "UI Design"}
//                     />

//                     {/* View overlay (appears on hover) */}
//                     <a
//                       href={item.url}
//                       target="_blank"
//                       rel="noopener noreferrer"
//                       className="absolute inset-0 m-auto h-10 w-24 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-white/20 backdrop-blur-sm rounded-lg text-sm font-semibold text-white flex items-center justify-center border border-white/30"
//                     >
//                       View ↗
//                     </a>

//                     {/* 💖 Heart button (White background, Top-Left Rounding) 💖 */}
//                     <button
//                       onClick={(e) => {
//                         e.stopPropagation();
//                         e.preventDefault();
//                         toggleLike(key, item); // CALLS ASYNC FUNCTION
//                       }}
//                       className={`
//                         absolute bottom-0 right-1 
//                         w-12 h-12 flex items-center justify-center
//                         transition-transform duration-200 hover:scale-110 
                        
//                         // --- White Background and Top-Left Rounding ---
//                         bg-white 
//                         rounded-tl-[16px] 
                        
//                       `}
//                       aria-pressed={liked}
//                       title={liked ? "Unlike" : "Like"}
//                     >
//                       {/* Use images for heart icon */}
//                       {liked ? (
//                         <img src="/likedheart.png" alt="Liked" className="w-8 h-8 object-contain" />
//                       ) : (
//                         <img src="/grayheart.png" alt="Like" className="w-8 h-8 object-contain" />
//                       )}
//                     </button>
//                   </div>

//                   {/* Caption area (fixed height percentage + inner padding) */}
//                   <div className="px-2 pt-4 pb-4 text-sm leading-relaxed text-gray-700 border-t border-gray-200" style={{ height: "30%" }}>
//                     <p className="font-[Instrument-Sans] text-[18px] mb-1">
//                       {/* SPARKLE IMAGE */}
//                       <img src="/sparkle.png" alt="Sparkle" className="inline-block h-5 w-5 mr-1 align-text-bottom" /> 
                      
//                       {/* 1. Vibe Explanation Label (SEMI-BOLD 600) */}
//                       <span className="font-semibold text-[#222222]">Vibe Explanation:</span>{" "}
                      
//                       {/* 2. Creative Concept Value (MEDIUM 500) */}
//                       <span className="font-medium text-[#5C5B5B]">
//                         {item.caption || item.title || "Creative Concept"}
//                       </span>
//                     </p>
//                   </div>
//                 </div>
//               );
//             })}
//           </div>
//         )}

//         {/* ─── No Results State ─────────────────────────────── */}
//         {!loading && results.length === 0 && (
//           <div className="text-center p-20 bg-[#2A2A2A] rounded-xl mt-10 shadow-lg border border-gray-700">
//             <p className="text-xl font-semibold text-gray-300">No vibes found for "<strong>{initialQuery}</strong>".</p>
//             <p className="text-gray-500 mt-2">Try a different description!</p>
//           </div>
//         )}
//       </div>

//       {/* ─── Floating bottom search ─────────────────────────────── */}
//       <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full flex justify-center">
//         <div className="flex items-center w-[90vw] sm:w-[420px] bg-[#2A2A2A] shadow-2xl rounded-xl px-2 py-4 border border-gray-700 relative">
//           <input
//             type="text"
//             value={inputValue}
//             onChange={(e) => setInputValue(e.target.value)}
//             onKeyPress={(e) => {
//               if (e.key === "Enter") handleSearch();
//             }}
//             className="flex-1 bg-transparent outline-none text-base text-white placeholder:text-gray-500"
//             placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
//           />

//           <button
//             onClick={handleSearch}
//             className="absolute right-3 bg-white text-black rounded-lg w-8 h-8 flex items-center justify-center text-lg font-bold hover:bg-gray-200 transition-colors"
//           >
//             ↑
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// }

"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

// -------------------- TYPES --------------------
interface ResultItem {
  title: string;
  url: string;
  image: string;
  caption?: string;
  _score?: number;
}

// -------------------- SKELETON COMPONENT (top-level) --------------------
function LoadingSkeleton() {
  return (
    <div className="flex flex-wrap gap-7 mt-6 justify-center">
      {[...Array(6)].map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-2xl bg-gray-700 w-full sm:w-[378px] h-[400px] shadow-sm"
        />
      ))}
    </div>
  );
}

// -------------------- BACKEND LIKE API --------------------
async function saveLikeToBackend(userId: string, item: ResultItem) {
  await fetch("http://127.0.0.1:8000/api/likes/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      title: item.title,
      url: item.url,
      image: item.image,
      caption: item.caption,
    }),
  });
}

async function removeLikeFromBackend(userId: string, url: string) {
  await fetch("http://127.0.0.1:8000/api/likes/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, url }),
  });
}

// -------------------- FETCH LIKED STATUS --------------------
// returns a map { url: true } for liked ones
async function fetchLikedStatus(
  userId: string,
  urls: string[]
): Promise<Record<string, boolean>> {
  // backend should return something like { "<url>": true, ... }
  const res = await fetch("http://127.0.0.1:8000/api/likes/status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, urls }),
  });

  if (!res.ok) return {};
  try {
    const json = await res.json();
    if (typeof json === "object" && json !== null) return json as Record<string, boolean>;
    return {};
  } catch {
    return {};
  }
}

// ================================================================
//                      MAIN COMPONENT
// ================================================================
export default function VibeBoard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { userId, isSignedIn } = useAuth();

  const initialQuery = searchParams.get("query") || "";
  const [results, setResults] = useState<ResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [inputValue, setInputValue] = useState("");


  // map[url] = true/false
  const [likedMap, setLikedMap] = useState<Record<string, boolean>>({});

  // -------------------- FETCH SEARCH + LIKED STATUS --------------------
  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      setLoading(true);

      if (!initialQuery) {
        setResults([]);
        setLoading(false);
        return;
      }

      try {
        const res = await fetch(
          `http://127.0.0.1:8000/search?q=${encodeURIComponent(initialQuery)}&top_k=20`
        );
        const data = await res.json();
        const fetched: ResultItem[] = Array.isArray(data.results) ? data.results : [];
        if (cancelled) return;
        setResults(fetched);

        if (isSignedIn && userId && fetched.length > 0) {
          const urls = fetched.map((r: ResultItem) => r.url);
          const status = await fetchLikedStatus(userId, urls);
          if (!cancelled) setLikedMap(status);
        }
      } catch (err) {
        console.error("Error fetching data:", err);
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [initialQuery, isSignedIn, userId]);

  // -------------------- SEARCH HANDLER --------------------
  const handleSearch = () => {
    if (!inputValue.trim()) return;
    router.push(`/vibeboard?query=${encodeURIComponent(inputValue)}`);
  };

  // -------------------- LIKE / UNLIKE TOGGLE --------------------
  const toggleLike = async (url: string, item: ResultItem) => {
    const newState = !likedMap[url];
    // optimistic UI update
    setLikedMap(prev => ({ ...prev, [url]: newState }));

    if (!userId) return;

    try {
      if (newState) {
        await saveLikeToBackend(userId, item);
      } else {
        await removeLikeFromBackend(userId, url);
      }
    } catch (err) {
      console.error("Error toggling like:", err);
      // rollback on failure
      setLikedMap(prev => ({ ...prev, [url]: !newState }));
    }
  };

  // ================================================================
  //                              UI
  // ================================================================
  return (
    <div className="min-h-screen bg-[#FAFAFA] text-white font-sans relative pb-24">
      {/* Top Bar */}
      <div className="sticky top-0 z-10 bg-[#FAFAFA] px-4 py-5 flex items-center justify-between border-b border-gray-300">
        <div className="flex items-center gap-3 text-lg">
          <button
            className="text-[#222222] text-2xl hover:text-black transition-colors"
            onClick={() => router.back()}
          >
            <img src="/back.png" alt="Back" className="w-5 h-5 object-contain" />
          
          </button>
          <span className="font-[Joan] text-[#222222]">{initialQuery}</span>
        </div>

        <button
          className="flex items-center gap-2 font-semibold text-black"
          onClick={() => router.push("/savedvibeboard")}
        >
          <img src="/logo.png" className="h-6 w-6" />
          <span className="font-[Instrument_Serif] text-lg">Vibeboard</span>
        </button>
      </div>

      <div className="p-6">
        {loading && <LoadingSkeleton />}

        {!loading && results.length > 0 && (
          <div className="flex flex-wrap gap-7 mt-6 justify-center">
            {results.map((item, i) => {
              const url = item.url;
              const liked = !!likedMap[url];

              return (
                <div
                  key={url ?? `idx-${i}`}
                  className="
                    w-full sm:w-[378px] h-[400px]
                    rounded-[12px] bg-white shadow-lg
                    border-[6px] border-[#F7F7F7]
                    hover:shadow-xl transition-all duration-200
                    overflow-hidden flex flex-col text-black
                  "
                >
                  {/* IMAGE */}
                  <div className="relative group px-2 pt-4" style={{ height: "70%", maxHeight: "280px" }}>
                    <img
                      src={item.image || "/placeholder.png"}
                      className="w-full h-full object-cover rounded-t-[6px]"
                    />

                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="absolute inset-0 m-auto h-10 w-24 opacity-0
                      group-hover:opacity-100 bg-white/20 backdrop-blur-sm
                      rounded-lg text-sm font-semibold text-white flex items-center justify-center
                      border border-white/30 transition-opacity duration-300"
                    >
                      View ↗
                    </a>

                    {/* HEART */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        toggleLike(item.url, item);
                      }}
                      className="absolute bottom-0 right-1 w-12 h-12 bg-white rounded-tl-[16px]
                      flex items-center justify-center hover:scale-110 transition-transform"
                      aria-pressed={liked}
                      title={liked ? "Unlike" : "Like"}
                    >
                      <img
                        src={liked ? "/likedheart.png" : "/grayheart.png"}
                        className="w-8 h-8"
                        alt={liked ? "Liked" : "Like"}
                      />
                    </button>
                  </div>

                  {/* CAPTION */}
                  <div className="px-2 pt-4 pb-4 text-sm text-gray-700 border-t border-gray-200" style={{ height: "30%" }}>
                    <p className="font-[Instrument-Sans] text-[18px]">
                      <img
                        src="/sparkle.png"
                        className="inline-block h-5 w-5 mr-1"
                        alt=""
                      />
                      <span className="font-semibold text-[#222]">Vibe Explanation: </span>
                      <span className="font-medium text-[#5C5B5B]">
                        {item.caption || item.title || "Creative Concept"}
                      </span>
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!loading && results.length === 0 && (
          <div className="text-center p-20 bg-[#2A2A2A] rounded-xl mt-10 shadow-lg border border-gray-700">
            <p className="text-xl text-gray-300">
              No vibes found for &quot;<strong>{initialQuery}</strong>&quot;.
            </p>
            <p className="text-gray-500 mt-2">Try something else!</p>
          </div>
        )}
      </div>

      {/* Floating bottom search - EXACT DASHBOARD STYLE */}
<div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full flex justify-center z-50">

  <div
    className="
      relative
      mx-auto 
      w-[92%] max-w-4xl
      bg-white 
      rounded-[22px]
      p-5
      border-[7px] border-[#F7F7F7]
      shadow-[0px_7px_28px_rgba(0,0,0,0.25)]
      flex items-center
    "
  >

    {/* Input inside white box */}
    <input
      type="text"
       placeholder="Describe your vibe (e.g., calm fintech dashboard, bold landing page)"
      value={inputValue}
      onChange={(e) => setInputValue(e.target.value)}
      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
     
      className="
        flex-1
        bg-transparent
        outline-none
        text-[16px]
        text-black
        placeholder:text-gray-500
      "
    />

    {/* RIGHT BLACK ARROW BUTTON */}
    <button
      onClick={handleSearch}
      className="
        absolute 
        right-5 
        top-1/2 
        -translate-y-1/2
        w-[48px] h-[48px]
        bg-gradient-to-b from-[#000000] to-[#484848]
        border-[4px] border-[#1C1C1C]
        rounded-[10px]
        shadow-[inset_0px_4px_4px_rgba(255,255,255,0.25)]
        flex items-center justify-center
        text-white text-xl
        hover:scale-105 transition-transform
      "
    >
      <img src="/arrow-down.png" alt="Search" className="w-6 h-6 object-contain" />
    </button>

  </div>
</div>

    </div>
  );
}
