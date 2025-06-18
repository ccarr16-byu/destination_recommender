"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Loader } from '@googlemaps/js-api-loader';

interface MapClickEvent {
  latLng: {
    lat: () => number;
    lng: () => number;
  };
}

export default function SubmitPage() {
  const router = useRouter();
  const mapRef = useRef<HTMLDivElement>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submissionResult, setSubmissionResult] = useState<{
    original_description: string;
    enhanced_description: string;
  } | null>(null);
  const [loadingStep, setLoadingStep] = useState<string | null>(null);

  useEffect(() => {
    const initMap = async () => {
      const loader = new Loader({
        apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
        version: 'weekly',
        libraries: ['places']
      });

      try {
        const google = await loader.load();
        if (mapRef.current) {
          const initialMap = new google.maps.Map(mapRef.current, {
            center: { lat: 39.8283, lng: -98.5795 }, // Center of US
            zoom: 4,
            styles: [
              {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
              }
            ]
          });

          setMap(initialMap);

          // Add click listener to map
          initialMap.addListener("click", (e: MapClickEvent) => {
            const lat = e.latLng.lat();
            const lng = e.latLng.lng();
            
            setLatitude(lat);
            setLongitude(lng);

            // Remove previous marker if it exists
            if (markerRef.current) {
              markerRef.current.setMap(null);
            }

            // Create new marker
            const newMarker = new google.maps.Marker({
              position: { lat, lng },
              map: initialMap,
              animation: google.maps.Animation.DROP
            });
            markerRef.current = newMarker;
          });
        }
      } catch (error) {
        console.error('Error loading Google Maps:', error);
        setError('Failed to load map');
      }
    };

    initMap();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSubmissionResult(null);
    setLoadingStep("Enhancing description...");

    if (!latitude || !longitude) {
      setError('Please select a location on the map');
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await fetch('/api/submit-site', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          latitude,
          longitude,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit destination');
      }
      
      // Wait 2 seconds before redirecting
      setTimeout(() => {
        router.push('/destinations');
      }, 2000);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to submit destination');
    } finally {
      setIsSubmitting(false);
      setLoadingStep(null);
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gradient-to-b from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950">
      <main className="max-w-6xl mx-auto">
        <button
          onClick={() => router.push('/')}
          className="mb-8 inline-flex items-center text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Home
        </button>

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-emerald-800 dark:text-emerald-200 mb-4">
            Submit a New Destination
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Share a favorite place of yours with others!
          </p>
        </div>

        {isSubmitting ? (
          <div className="bg-white/80 dark:bg-black/80 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-emerald-200 dark:border-emerald-800 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
            <p className="text-emerald-800 dark:text-emerald-200">{loadingStep}</p>
          </div>
        ) : submissionResult ? (
          <div className="bg-white/80 dark:bg-black/80 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-emerald-200 dark:border-emerald-800">
            <div className="flex items-center justify-center mb-4">
              <svg className="h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-emerald-800 dark:text-emerald-200 mb-4 text-center">
              Successfully Added!
            </h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Original Description:</h3>
                <p className="text-gray-600 dark:text-gray-400">{submissionResult.original_description}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Enhanced Description:</h3>
                <p className="text-emerald-600 dark:text-emerald-400">{submissionResult.enhanced_description}</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-gray-500 dark:text-gray-400 text-center">
              Redirecting to destinations page...
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Site Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-white/80 dark:bg-black/80 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 dark:focus:ring-emerald-600 transition-all"
                  placeholder="Enter the name of the site"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description (max 30 words)
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  maxLength={200}
                  className="w-full px-4 py-2 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-white/80 dark:bg-black/80 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 dark:focus:ring-emerald-600 transition-all"
                  placeholder="Enter a brief description of the site"
                  rows={4}
                />
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {description.split(/\s+/).filter(Boolean).length}/30 words
                </p>
              </div>

              {latitude && longitude && (
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  Selected location: {latitude.toFixed(6)}, {longitude.toFixed(6)}
                </div>
              )}

              {error && (
                <div className="text-red-600 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Destination'}
              </button>
            </form>

            <div className="h-[400px] rounded-xl overflow-hidden shadow-lg">
              <div ref={mapRef} className="w-full h-full" />
            </div>
          </div>
        )}
      </main>
    </div>
  );
} 