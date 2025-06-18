import { NextResponse } from 'next/server';

// Get the backend URL based on the environment
const getBackendUrl = () => {
  // In development, use localhost
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:5000';
  }
  
  // In production, use the Vercel deployment URL
  const vercelUrl = process.env.VERCEL_URL;
  if (!vercelUrl) {
    throw new Error('VERCEL_URL environment variable is not set');
  }
  
  // Remove any existing protocol
  const cleanUrl = vercelUrl.replace(/^https?:\/\//, '');
  return `https://${cleanUrl}`;
};

const BACKEND_URL = getBackendUrl();

export async function GET() {
  try {
    console.log('Attempting to fetch from:', `${BACKEND_URL}/all_sites`);
    
    const response = await fetch(`${BACKEND_URL}/all_sites`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    const responseText = await response.text();
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    console.log('Response body:', responseText);
    
    if (!response.ok) {
      // Try to parse as JSON if possible
      let errorData;
      try {
        errorData = JSON.parse(responseText);
      } catch (e) {
        // If not JSON, use the raw text
        errorData = { error: 'Invalid response', details: responseText };
      }
      
      throw new Error(
        `Backend error: ${errorData.error}\nDetails: ${JSON.stringify(errorData.details, null, 2)}`
      );
    }

    // Try to parse the response as JSON
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      throw new Error(`Invalid JSON response: ${responseText.substring(0, 200)}...`);
    }
    
    if (!data.sites || !Array.isArray(data.sites)) {
      throw new Error('Invalid data format received from backend');
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching sites:', error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Failed to fetch sites',
        details: error instanceof Error ? error.stack : undefined
      },
      { status: 500 }
    );
  }
} 