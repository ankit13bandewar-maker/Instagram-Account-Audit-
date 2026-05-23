import { NextResponse } from 'next/server';

// Proxy handler for the FastAPI dashboard‑intelligence endpoint.
// The frontend calls `/api/dashboard-intelligence?profile_url=...` which
// forwards the request to the FastAPI server running on localhost:8000.
// This keeps the client side free of hard‑coded host/port values and
// avoids CORS issues.

export async function GET(request: Request) {
  const url = new URL(request.url);
  const profileUrl = url.searchParams.get('profile_url');

  if (!profileUrl) {
    return NextResponse.json({ error: 'Missing profile_url query parameter' }, { status: 400 });
  }

  try {
    const backendUrl = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
    console.log('Proxying to FastAPI URL:', backendUrl);
    // Perform a quick health check before making the main request
    try {
      const healthResp = await fetch(`${backendUrl}/health`, { method: 'GET' });
      if (!healthResp.ok) {
        throw new Error('Health check failed');
      }
    } catch (healthErr) {
      console.error('FastAPI health check failed:', healthErr);
      return NextResponse.json({ error: 'FastAPI backend is unreachable (health check failed)' }, { status: 502 });
    }
    const backendResponse = await fetch(
      `${backendUrl}/api/dashboard-intelligence?profile_url=${encodeURIComponent(profileUrl)}`
    );
    console.log('FastAPI responded with status', backendResponse.status);

    const data = await backendResponse.json();
    // Preserve the original status code (e.g., 200, 404, 500)
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (err) {
    console.error('Error proxying to FastAPI:', err);
    return NextResponse.json({ error: 'Failed to reach FastAPI backend' }, { status: 502 });
  }
}

export const runtime = 'nodejs'; // Use nodejs runtime for local backend calls
