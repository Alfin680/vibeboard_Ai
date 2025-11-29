"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { fetchSavedLikes, fetchLikedStatus, saveLike } from "@/lib/saveLike";

interface ResultItem {
  title: string;
  url: string;
  image: string;
  tags?: string;
  caption?: string;
}

export default function SavedVibeBoard() {
  const { userId, isSignedIn, isLoaded } = useAuth();
  const router = useRouter();

  const [savedItems, setSavedItems] = useState<ResultItem[]>([]);
  const [likedMap, setLikedMap] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  // ---------------- LOAD SAVED DESIGNS ----------------
  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push("/dashboard");
      return;
    }

    const load = async () => {
      if (!userId) return;

      setLoading(true);

      const savedUrls = await fetchSavedLikes(userId);

      if (savedUrls.length === 0) {
        setSavedItems([]);
        setLikedMap({});
        setLoading(false);
        return;
      }

      const res = await fetch("http://127.0.0.1:8000/api/designs/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(savedUrls),
      });

      const data = await res.json();
      setSavedItems(data.designs || []);

      const likes = await fetchLikedStatus(
        userId,
        data.designs.map((i: ResultItem) => i.url)
      );

      setLikedMap(likes);
      setLoading(false);
    };

    load();
  }, [userId, isLoaded, isSignedIn]);

  // ---------------- UNLIKE HANDLER ----------------
  const toggleUnlike = async (url: string) => {
    if (!userId) return;

    setSavedItems((prev) => prev.filter((i) => i.url !== url));
    setLikedMap((prev) => ({ ...prev, [url]: false }));

    await saveLike({
      user_id: userId,
      url,
      is_liked: false,
    });
  };

  // ---------------- UI ----------------

  if (loading)
    return (
      <div className="min-h-screen p-6 text-center text-xl text-[#222]">
        Loading your saved vibes...
      </div>
    );

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-black pb-24 flex flex-col items-center">

      {/* ---------------- HEADER ---------------- */}
      <div className="sticky top-0 bg-[#FAFAFA] w-full px-6 py-5 flex items-center justify-between border-b border-gray-300 z-20">
        <button
          onClick={() => router.push("/dashboard")}
          className="flex items-center gap-2 text-[#222] hover:opacity-70 transition"
        >
          <img src="/back.png" alt="Back" className="w-5 h-5 object-contain" />
          <span className="font-[Joan] text-lg  font-[24px]">Your Vibeboard</span>
        </button>
      

        

        <div>
      <button
          className="flex items-center gap-2 font-semibold text-black"
          onClick={() => router.push("/vibeboard")}
        >
          <img src="/logo.png" className="h-6 w-6" />
          <span className="font-[Instrument_Serif] text-lg">Vibeboard</span>
        </button>
      </div>
      </div>
      

      {/* ---------------- MAIN CONTAINER ---------------- */}
      <div
        className="
          bg-white 
          mt-10
          ml-0 mr-0
          border border-[#EAEAEA]
          shadow-[0px_4px_40px_rgba(0,0,0,0.08)]
          rounded-[24px]
          w-[95%] 
          max-w-[1200px]
          min-h-[800px]
          p-10
        "
      >
        {savedItems.length === 0 ? (
          <div className="text-center p-20 bg-white rounded-lg border border-gray-200 mt-10">
            <p className="text-xl font-semibold text-[#222]">
              You haven&apos;t saved any vibes yet!
            </p>
            <p className="mt-2 text-[#5C5B5B]">
              Go explore some creative inspiration.
            </p>
          </div>
        ) : (
          /* ----------- 3 CARDS PER ROW GRID ----------- */
          
          <div
            className="
              grid 
              grid-cols-1 
              sm:grid-cols-2 
              lg:grid-cols-3 
              gap-7 
              mt-8
            "
          >
            
            {savedItems.map((item) => (
              <div
                key={item.url}
                className="w-full h-[400px] rounded-[12px] bg-white shadow-lg border-[6px] border-[#F7F7F7] hover:shadow-xl transition overflow-hidden flex flex-col relative"
              >
                <div
                  className="relative group flex-shrink-0 px-2 pt-4"
                  style={{ height: "70%", maxHeight: "280px" }}
                >
                  <img
                    src={item.image || "/placeholder.png"}
                    className="w-full h-full object-cover rounded-t-[6px]"
                    alt={item.title}
                  />

                  <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="absolute inset-0 m-auto h-10 w-24 opacity-0
                      group-hover:opacity-100 bg-white shadow-[0_4px_4px_0_rgba(0,0,0,0.25)]
                      rounded-tl-[0px] rounded-tr-[8px] rounded-bl-[8px] rounded-br-[8px] text-sm font-[Joan]  text-black flex items-center justify-center
                      border border-white/30 transition-opacity duration-300"
                    >
                    <span>View</span>
                    <img src="/external-link.png" alt="View" className="w-4 h-4 ml-1" /> 
                    </a>

                  <button
                    onClick={() => toggleUnlike(item.url)}
                    className="absolute bottom-0 right-0 bg-white w-12 h-12 rounded-tl-[16px] flex items-center justify-center hover:scale-110 transition"
                  >
                    <img
                      src="/likedheart.png"
                      alt="Unlike"
                      className="w-6 h-6"
                    />
                  </button>
                </div>

                <div
                  className="px-2 pt-4 pb-4 text-sm leading-relaxed text-gray-700 border-t border-gray-200"
                  style={{ height: "30%" }}
                >
                  <p className="text-[18px] mb-1">
                    <img
                      src="/sparkle.png"
                      className="inline-block h-5 w-5 mr-1"
                    />
                    <span className="font-[Instrument_Sans] font-semibold">Vibe Explanation: </span>
                    <span className="font-[Instrument_Sans] font-medium text-[#5C5B5B]">
                      {item.caption || item.title}
                    </span>
                  </p>
                </div>
              </div>
            ))}
          </div>
          /* ----------- END GRID ----------- */
        )}
      </div>
    </div>
  );
}
