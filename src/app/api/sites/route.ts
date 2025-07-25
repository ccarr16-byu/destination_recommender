import { NextResponse } from 'next/server';

const backendUrl = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}/all_sites` : 'http://localhost:5000/all_sites';

export async function GET() {
  try {
    const response = await fetch(backendUrl);
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.sites || !Array.isArray(data.sites)) {
      throw new Error('Invalid data format received from backend');
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching sites:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch sites' },
      { status: 500 }
    );
  }
} 