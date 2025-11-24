
export async function saveSearch(userId: string, query: string) {
  try {
    const res = await fetch("http://localhost:8000/history/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, query }),
    });

    return res.json();
  } catch (err) {
    console.error("Error saving search:", err);
  }
}
