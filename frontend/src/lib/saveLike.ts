// /lib/saveLike.ts (Final Version)

import { supabase } from "@/lib/supabaseClient"; 

// --- Interface Definitions ---

interface LikeData {
  user_id: string;
  url: string;
  is_liked: boolean;
}

interface SupabaseUrlItem {
    url: string;
}

// --- CORE FUNCTIONS ---

/**
 * Inserts or deletes a like status in the database.
 * Deletes the row if is_liked is false (unliking).
 * Upserts (inserts/updates) the row if is_liked is true (liking).
 */
export async function saveLike(data: LikeData): Promise<boolean> {
  if (!data.user_id || !data.url) {
    console.error("Missing user_id or url for saving like.");
    return false;
  }

  // 1. Handle UNLIKE operation by DELETING the row
  if (!data.is_liked) {
    const { error } = await supabase
        .from("likes")
        .delete()
        .eq('user_id', data.user_id)
        .eq('url', data.url);

    if (error) {
        console.error("Supabase error deleting like:", error);
        return false;
    }
    return true; // Deletion successful
  }

  // 2. Handle LIKE operation by UPSERTING (insert/update)
  const { error } = await supabase
    .from("likes")
    .upsert({ 
      user_id: data.user_id, 
      url: data.url, 
      is_liked: data.is_liked,
    }, { 
      onConflict: 'user_id, url' 
    });
    
  if (error) {
    console.error("Supabase error saving like:", error);
    return false;
  }
  return true;
}

/**
 * Fetches all URLs liked by the current user.
 */
export async function fetchSavedLikes(userId: string): Promise<string[]> {
  if (!userId) return [];

  // Asserting the return type to ensure clean mapping
  const { data, error } = await supabase
    .from("likes")
    .select("url")
    .eq("user_id", userId)
    .eq("is_liked", true) as { data: SupabaseUrlItem[] | null, error: any };

  if (error || !data) {
    console.error("Supabase error fetching saved likes:", error);
    return [];
  }
  // Data is guaranteed to be SupabaseUrlItem[] thanks to the 'as' assertion
  return data.map(item => item.url); 
}

/**
 * Fetches the liked status for a batch of URLs for the current user.
 * Returns a map { url: true } for all liked items in the batch.
 */
export async function fetchLikedStatus(userId: string, urls: string[]): Promise<Record<string, boolean>> {
  if (!userId || urls.length === 0) return {};

  const { data, error } = await supabase
    .from("likes")
    .select("url")
    .eq("user_id", userId)
    .in("url", urls) // Check only the URLs currently visible on the page
    .eq("is_liked", true) as { data: SupabaseUrlItem[] | null, error: any };

  if (error || !data) {
    console.error("Supabase error fetching liked status:", error);
    return {};
  }
  
  // Convert the array of liked URLs into a map: { url: true }
  return data.reduce((acc, item) => {
    acc[item.url] = true;
    return acc;
  }, {} as Record<string, boolean>);
}