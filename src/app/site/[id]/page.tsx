"use client";

import { useSearchParams, useRouter } from 'next/navigation';
import Image from 'next/image';

export default function SitePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const name = searchParams.get('name');
  const description = searchParams.get('description');
  const photoUrl = searchParams.get('photoUrl');
  const latitude = searchParams.get('latitude');
  const longitude = searchParams.get('longitude');

  return (
    <div className="min-h-screen p-8 bg-gradient-to-b from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950">
      <main className="max-w-6xl mx-auto">
        <button
          onClick={() => router.back()}
          className="mb-8 inline-flex items-center text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Previous Page
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left column - Site info and photo */}
          <div className="space-y-6">
            <h1 className="text-4xl font-bold text-emerald-800 dark:text-emerald-200">
              {name}
            </h1>
            
            {photoUrl && (
              <div className="relative w-full h-96 rounded-xl overflow-hidden">
                <Image
                  src={photoUrl}
                  alt={`${name} photo`}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, 50vw"
                />
              </div>
            )}
            
            <p className="text-gray-600 dark:text-gray-300 text-lg">
              {description}
            </p>
          </div>

          {/* Right column - Map */}
          <div className="h-[600px] rounded-xl overflow-hidden shadow-lg">
            <iframe
              width="100%"
              height="100%"
              style={{ border: 0 }}
              loading="lazy"
              allowFullScreen
              referrerPolicy="no-referrer-when-downgrade"
              src={`https://www.google.com/maps/embed/v1/place?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&q=${latitude},${longitude}&zoom=15`}
            />
          </div>
        </div>
      </main>
    </div>
  );
} 