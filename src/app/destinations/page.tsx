"use client";

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface Site {
  name: string;
  description: string;
  photo_url: string;
  latitude: number;
  longitude: number;
}

export default function DestinationsPage() {
  const router = useRouter();
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSites = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/sites');
      if (!response.ok) {
        throw new Error('Failed to fetch sites');
      }
      const data = await response.json();
      if (data.sites && Array.isArray(data.sites)) {
        setSites(data.sites);
      } else {
        throw new Error('Invalid data format received');
      }
    } catch (error) {
      console.error('Error fetching sites:', error);
      setError(error instanceof Error ? error.message : 'Failed to load destinations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen p-8 bg-gradient-to-b from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950">
        <main className="max-w-6xl mx-auto">
          <div className="text-center text-emerald-800 dark:text-emerald-200">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
            Loading destinations...
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8 bg-gradient-to-b from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950">
        <main className="max-w-6xl mx-auto">
          <div className="text-center text-red-600 dark:text-red-400">
            {error}
          </div>
          <button
            onClick={fetchSites}
            className="mt-4 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-all shadow-sm hover:shadow-md hover:scale-105 active:scale-95"
          >
            Try Again
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 bg-gradient-to-b from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950">
      <main className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <button
            onClick={() => router.push('/')}
            className="inline-flex items-center text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-all group"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 transform group-hover:-translate-x-1 transition-transform" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to Home
          </button>
          <button
            onClick={fetchSites}
            className="inline-flex items-center text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-all group"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 transform group-hover:rotate-180 transition-transform duration-300" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
            Refresh
          </button>
        </div>

        <div className="mb-8">
          <h1 className="text-5xl font-bold text-emerald-800 dark:text-emerald-200 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-green-600 dark:from-emerald-400 dark:to-green-400">
            Destinations
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Explore our collection of favorite destinations!
          </p>
        </div>

        {sites.length === 0 ? (
          <div className="text-center text-gray-600 dark:text-gray-300">
            No destinations found
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {sites.map((site, index) => (
              <Link
                key={index}
                href={`/site/${encodeURIComponent(site.name)}?name=${encodeURIComponent(site.name)}&description=${encodeURIComponent(site.description)}&photoUrl=${encodeURIComponent(site.photo_url)}&latitude=${site.latitude}&longitude=${site.longitude}`}
                className="bg-white/80 dark:bg-black/80 backdrop-blur-sm rounded-xl overflow-hidden shadow-lg border border-emerald-200 dark:border-emerald-800 hover:shadow-xl transition-all transform hover:-translate-y-1"
              >
                {site.photo_url && (
                  <div className="relative w-full h-48">
                    <Image
                      src={site.photo_url}
                      alt={`${site.name} photo`}
                      fill
                      className="object-cover hover:scale-105 transition-transform duration-300"
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                  </div>
                )}
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-emerald-800 dark:text-emerald-200 mb-3 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                    {site.name}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-3">
                    {site.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
} 