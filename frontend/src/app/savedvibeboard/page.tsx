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

      // 1. Get URLs saved by the user
      const savedUrls = await fetchSavedLikes(userId);

      if (savedUrls.length === 0) {
        setSavedItems([]);
        setLikedMap({});
        setLoading(false);
        return;
      }

      // 2. Fetch full design info from backend
      const res = await fetch("http://127.0.0.1:8000/api/designs/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(savedUrls),
      });

      const data = await res.json();
      setSavedItems(data.designs || []);

      // 3. All fetched are liked initially
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

    // Optimistic remove
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
    <div className="min-h-screen bg-[#FAFAFA] text-black pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-[#FAFAFA] px-4 py-5 flex items-center justify-between border-b border-gray-300">
        <h1 className="text-2xl font-bold text-[#222]">❤️ Your Saved Vibes</h1>
        <button
          onClick={() => router.push("/dashboard")}
          className="text-blue-600 hover:underline text-lg"
        >
          ← Back to Search
        </button>
      </div>

      <div className="p-6">
        {savedItems.length === 0 ? (
          <div className="text-center p-20 bg-white shadow rounded-lg border border-gray-200 mt-10">
            <p className="text-xl font-semibold text-[#222]">
              You haven&apos;t saved any vibes yet!
            </p>
            <p className="mt-2 text-[#5C5B5B]">
              Go explore some creative inspiration.
            </p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-7 mt-6 justify-center">
            {savedItems.map((item) => (
              <div
                key={item.url}
                className="w-full sm:w-[378px] h-[400px] rounded-[12px] bg-white shadow-lg border-[6px] border-[#F7F7F7] hover:shadow-xl transition overflow-hidden flex flex-col relative"
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
                    className="absolute inset-0 m-auto h-10 w-24 opacity-0 group-hover:opacity-100 transition bg-white/20 backdrop-blur-sm rounded-lg text-sm font-semibold text-white flex items-center justify-center border border-white/30"
                  >
                    View ↗
                  </a>

                  {/* UNLIKE BUTTON */}
                  <button
                    onClick={() => toggleUnlike(item.url)}
                    className="absolute bottom-4 right-4 bg-white w-11 h-11 rounded-tl-[16px] shadow-md flex items-center justify-center hover:scale-110 transition"
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
                    <span className="font-semibold">Vibe Explanation: </span>
                    <span className="font-medium text-[#5C5B5B]">
                      {item.caption || item.title}
                    </span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
