import { NextResponse } from 'next/server';

const backendUrl = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:5000';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // Validate the data
    if (!data.name || !data.description || !data.latitude || !data.longitude) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Send the data to the backend
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to submit site to backend');
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error submitting site:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to submit site' },
      { status: 500 }
    );
  }
} 