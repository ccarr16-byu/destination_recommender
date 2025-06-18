import { NextResponse } from 'next/server';

const BACKEND_URL = "https://" + process.env.VERCEL_URL || 'http://localhost:5000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/all_sites`);
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error('Backend error details:', errorData);
      throw new Error(
        `Backend error: ${errorData.error}\nDetails: ${JSON.stringify(errorData.details, null, 2)}`
      );
    }

    const data = await response.json();
    
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