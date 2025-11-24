"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

interface ResultItem {
  title: string;
  url: string;
  image: string;
  tags: string;
}

export default function VibeBoard() {
  const searchParams = useSearchParams();
  const query = searchParams.get("query");
  const [results, setResults] = useState<ResultItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchResults = async () => {
      if (!query) return;

      const res = await fetch(`http://127.0.0.1:8000/search?q=${encodeURIComponent(query)}&top_k=20`);
const data = await res.json();
setResults(data.results);
      setLoading(false);
    };

    fetchResults();
  }, [query]);

  if (loading) return <p className="text-black">Loading results...</p>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6 text-black">Results for: {query}</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {results.map((item, index) => (
          <a key={index} href={item.url} target="_blank" className="rounded-xl overflow-hidden border hover:scale-105 transition">
            <img src={item.image} alt={item.title} className="w-full h-48 object-cover" />
            <div className="p-3">
              <h2 className="font-semibold text-lg text-black">{item.title}</h2>
              <p className="text-sm opacity-70 text-black">{item.tags}</p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
