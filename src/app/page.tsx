"use client";

import Image from "next/image";
import { useState } from "react";

interface Site {
  name: string;
  description: string;
  similarity: number;
  photo_url: string;
  latitude: number;
  longitude: number;
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [response, setResponse] = useState("");
  const [sites, setSites] = useState<Site[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: searchQuery }),
      });
      const data = await res.json();
      setResponse(data.message);
      setSites(data.sites || []);
    } catch (error) {
      console.error("Error:", error);
      setResponse("Error occurred while searching");
      setSites([]);
    }
  };

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)] bg-gradient-to-b from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950">
      <main className="flex flex-col gap-[32px] row-start-2 items-center w-full max-w-4xl">
        <h1 className="text-5xl font-bold text-emerald-800 dark:text-emerald-200 text-center sm:text-left bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-green-600 dark:from-emerald-400 dark:to-green-400">
          Destination Recommender
        </h1>

        <form onSubmit={handleSearch} className="w-full max-w-md">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="What do you want to see?"
              className="w-full px-4 py-3 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-white/80 dark:bg-black/80 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 dark:focus:ring-emerald-600 transition-all shadow-sm hover:shadow-md"
            />
            <button
              type="submit"
              className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-all shadow-sm hover:shadow-md hover:scale-105 active:scale-95"
            >
              Search
            </button>
          </div>
        </form>

        {sites.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
            {sites.map((site, index) => (
              <div 
                key={index}
                className="bg-white/80 dark:bg-black/80 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-emerald-200 dark:border-emerald-800 hover:shadow-xl transition-all transform hover:-translate-y-1"
              >
                {site.photo_url && (
                  <div className="relative w-full h-48 mb-4 rounded-lg overflow-hidden shadow-md">
                    <Image
                      src={site.photo_url}
                      alt={`${site.name} photo`}
                      fill
                      className="object-cover hover:scale-105 transition-transform duration-300"
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                  </div>
                )}
                <h2 className="text-xl font-semibold text-emerald-800 dark:text-emerald-200 mb-3">
                  {site.name}
                </h2>
                <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                  {site.description}
                </p>
                <div className="text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-full inline-block">
                  Match score: {Math.round(site.similarity * 100)}%
                </div>
                <a
                  href={`/site/${encodeURIComponent(site.name)}?name=${encodeURIComponent(site.name)}&description=${encodeURIComponent(site.description)}&photoUrl=${encodeURIComponent(site.photo_url)}&latitude=${site.latitude}&longitude=${site.longitude}`}
                  className="mt-3 inline-flex items-center text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors group"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 transform group-hover:translate-x-1 transition-transform" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  View Site
                </a>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <a
            className="rounded-full border border-solid border-emerald-600 dark:border-emerald-400 transition-all flex items-center justify-center bg-emerald-600 text-white gap-2 hover:bg-emerald-700 dark:hover:bg-emerald-500 font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto shadow-sm hover:shadow-md hover:scale-105 active:scale-95"
            href="/destinations"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
            Destinations
          </a>
          <a
            className="rounded-full border border-solid border-emerald-200 dark:border-emerald-800 transition-all flex items-center justify-center hover:bg-emerald-50 dark:hover:bg-emerald-900/50 font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto shadow-sm hover:shadow-md hover:scale-105 active:scale-95"
            href="/submit"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Submit a Destination
          </a>
        </div>
      </main>
    </div>
  );
}
