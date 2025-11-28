"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
// NOTE: Ensure your path to the saveLike file is correct (e.g., '../../lib/saveLike')
import { fetchSavedLikes, saveLike, fetchLikedStatus } from '@/lib/saveLike'; 

// Use the same interface for results as VibeBoard
interface ResultItem {
    title: string;
    url: string;
    image: string;
    tags?: string;
    caption?: string;
    _score?: number;
}

export default function SavedVibeBoard() {
    const { userId, isSignedIn, isLoaded } = useAuth();
    const router = useRouter();
    
    const [savedItems, setSavedItems] = useState<ResultItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [likedMap, setLikedMap] = useState<Record<string, boolean>>({});

    // --- Data Fetching Effect ---
    useEffect(() => {
        // 1. Authentication Check
        if (isLoaded && !isSignedIn) {
            router.push('/dashboard'); 
            return;
        }

        const loadSavedItems = async () => {
            if (!userId) return;
            setLoading(true);
            setError(null);

            try {
                // 2. Fetch all URLs the user has liked from Supabase
                const savedUrls = await fetchSavedLikes(userId);

                if (savedUrls.length > 0) {
                    // 3. Fetch detailed item data from custom backend API
                    // NOTE: You must implement the POST /api/designs/batch endpoint in FastAPI
                    const res = await fetch(`http://127.0.0.1:8000/api/designs/batch`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ urls: savedUrls }),
                    });
                    
                    if (!res.ok) throw new Error("Failed to fetch design details from API.");
                    
                    const data = await res.json();
                    const fetchedItems: ResultItem[] = data.designs || [];
                    setSavedItems(fetchedItems);

                    // 4. Initialize likedMap (all fetched items are initially liked)
                    const initialLikes = await fetchLikedStatus(userId, fetchedItems.map(i => i.url));
                    setLikedMap(initialLikes);

                } else {
                    setSavedItems([]);
                    setLikedMap({});
                }
            } catch (err) {
                console.error("Error loading saved items:", err);
                setError("Could not load saved designs. Please check the backend API.");
            } finally {
                setLoading(false);
            }
        };

        if (userId) {
            loadSavedItems();
        }
    }, [userId, isLoaded, isSignedIn, router]);

    // --- Unlike Handler ---
    const toggleUnlike = async (key: string, item: ResultItem) => {
        if (!userId) return;

        // Since this is the saved page, we only handle UNLIKE (newState = false)
        const newState = false; 
        
        // Optimistic local update: remove from map, then filter from results list
        setLikedMap((prev) => ({ ...prev, [key]: newState }));
        setSavedItems((prev) => prev.filter(i => i.url !== key));

        // Database interaction (saveLike handles the DELETE operation)
        const success = await saveLike({
            user_id: userId,
            url: key,
            is_liked: newState,
        });
        
        // Revert if the API call failed (less critical here as the user expects it to disappear)
        if (!success) {
            console.error("Failed to delete like state from database.");
            // Optional: Re-insert the item into the list if the unlike failed
        }
    };


    // --- UI Components ---
    const LoadingSpinner = () => (
        <div className="text-center p-20 text-xl text-[#222222]">
            Loading your saved vibes...
        </div>
    );


    if (loading) return <div className="min-h-screen p-6 bg-[#FAFAFA]">{LoadingSpinner()}</div>;
    if (error) return <div className="min-h-screen p-6 text-xl text-red-600 bg-[#FAFAFA]">{error}</div>;

    
    return (
        <div className="min-h-screen bg-[#FAFAFA] text-black font-sans relative pb-24">
            
            {/* ─── Top Header ─────────────────────────────── */}
            <div className="sticky top-0 z-10 bg-[#FAFAFA] px-4 py-5 flex items-center justify-between border-b border-gray-300">
                <h1 className="text-2xl font-bold text-[#222222]">❤️ Your Saved Vibes</h1>
                <button 
                    onClick={() => router.push('/dashboard')} 
                    className="text-blue-600 hover:underline font-medium text-lg"
                >
                    ← Back to Search
                </button>
            </div>

            <div className="p-6">
                
                {savedItems.length === 0 ? (
                    <div className="text-center p-20 bg-white shadow rounded-lg border border-gray-200 mt-10">
                        <p className="text-xl font-semibold text-[#222222]">You haven't saved any vibes yet!</p>
                        <p className="mt-2 text-[#5C5B5B]">Go find some inspiration on the dashboard.</p>
                    </div>
                ) : (
                    // ─── Results Grid (Vertical Scrolling / Wrapping) ────────────────
                    <div className="flex flex-wrap gap-7 mt-6 justify-center">
                        {savedItems.map((item, i) => {
                            const key = item.url;
                            const liked = !!likedMap[key]; // Should always be true here

                            return (
                                <div
                                    key={key}
                                    className="
                                        w-full sm:w-[378px] h-[400px] 
                                        rounded-[12px] 
                                        bg-white shadow-lg 
                                        border-[6px] border-[#F7F7F7] 
                                        hover:shadow-xl transition-all duration-200 overflow-hidden relative
                                        flex flex-col text-black
                                    "
                                >
                                    {/* Image container */}
                                    <div className="relative group flex-shrink-0 px-2 pt-4" style={{ height: "70%", maxHeight: "280px" }}>
                                        <img
                                            src={item.image || "/placeholder.png"}
                                            className="w-full h-full object-cover object-center rounded-t-[6px]"
                                            alt={item.title || "UI Design"}
                                        />

                                        {/* View overlay (appears on hover) */}
                                        <a
                                            href={item.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="absolute inset-0 m-auto h-10 w-24 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-white/20 backdrop-blur-sm rounded-lg text-sm font-semibold text-white flex items-center justify-center border border-white/30"
                                        >
                                            View ↗
                                        </a>

                                        {/* 💖 Unlike Button 💖 (Always red and active on this page) */}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                e.preventDefault();
                                                toggleUnlike(key, item); // Calls the unlike function
                                            }}
                                            className="
                                                absolute bottom-4 right-4 
                                                w-11 h-11 flex items-center justify-center
                                                transition-transform duration-200 hover:scale-110 
                                                bg-white rounded-tl-[16px] shadow-md
                                            "
                                            title="Unlike and Remove"
                                        >
                                            {/* Use the liked heart image for visual consistency */}
                                            <img src="/likedheart.png" alt="Liked" className="w-6 h-6 object-contain" />
                                        </button>
                                    </div>

                                    {/* Caption area */}
                                    <div className="px-2 pt-4 pb-4 text-sm leading-relaxed text-gray-700 border-t border-gray-200" style={{ height: "30%" }}>
                                        <p className="font-[Instrument-Sans] text-[18px] mb-1">
                                            {/* SPARKLE IMAGE */}
                                            <img src="/sparkle.png" alt="Sparkle" className="inline-block h-5 w-5 mr-1 align-text-bottom" /> 
                                            
                                            {/* 1. Vibe Explanation Label (SEMI-BOLD 600) */}
                                            <span className="font-semibold text-[#222222]">Vibe Explanation:</span>{" "}
                                            
                                            {/* 2. Creative Concept Value (MEDIUM 500) */}
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
            </div>
        </div>
    );
}