import { supabase } from "@/lib/supabaseClient";

interface LikeData {
  user_id: string;
  url: string;
  is_liked: boolean;
}

// -----------------------------
// SAVE OR REMOVE LIKE
// -----------------------------
export async function saveLike(data: LikeData): Promise<boolean> {
  if (!data.user_id || !data.url) return false;

  // UNLIKE → DELETE THE ROW
  if (!data.is_liked) {
    const { error } = await supabase
      .from("likes")
      .delete()
      .eq("user_id", data.user_id)
      .eq("url", data.url);

    if (error) {
      console.error("Supabase error deleting like:", error);
      return false;
    }

    return true;
  }

  // LIKE → INSERT IF NOT EXISTS
  const { error } = await supabase
    .from("likes")
    .upsert(
      {
        user_id: data.user_id,
        url: data.url,
      },
      { onConflict: "user_id, url" }
    );

  if (error) {
    console.error("Supabase error saving like:", error);
    return false;
  }

  return true;
}

// -----------------------------
// FETCH ALL SAVED URLS
// -----------------------------
export async function fetchSavedLikes(userId: string): Promise<string[]> {
  if (!userId) return [];

  const { data, error } = await supabase
    .from("likes")
    .select("url")
    .eq("user_id", userId);

  if (error || !data) {
    console.error("Supabase error fetching saved likes:", error);
    return [];
  }

  return data.map((row) => row.url);
}

// -----------------------------
// FETCH LIKE STATUS FOR A LIST OF URLS
// -----------------------------
export async function fetchLikedStatus(
  userId: string,
  urls: string[]
): Promise<Record<string, boolean>> {
  if (!userId || urls.length === 0) return {};

  const { data, error } = await supabase
    .from("likes")
    .select("url")
    .eq("user_id", userId)
    .in("url", urls);

  if (error || !data) {
    console.error("Supabase error fetching liked status:", error);
    return {};
  }

  const map: Record<string, boolean> = {};
  for (const row of data) {
    map[row.url] = true;
  }

  return map;
}
