import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch(process.env.VERCEL_URL || 'http://localhost:5000');
    
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