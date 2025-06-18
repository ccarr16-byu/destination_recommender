import { NextResponse } from 'next/server';

// In development, use localhost, in production use the same origin
const getBackendUrl = () => {
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:5000';
  }
  return ''; // Empty string means same origin
};

const BACKEND_URL = getBackendUrl();

export async function GET() {
  try {
    const url = `${BACKEND_URL}/api/all_sites`;
    console.log('Environment:', process.env.NODE_ENV);
    console.log('Backend URL:', BACKEND_URL);
    console.log('Attempting to fetch from:', url);
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      cache: 'no-store' // Disable caching
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