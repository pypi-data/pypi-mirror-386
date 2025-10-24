import { NextResponse } from 'next/server';

export async function POST() {
  const botStartUrl =
    process.env.BOT_START_URL || 'http://localhost:7860/start';

  if (!process.env.BOT_START_URL) {
    console.warn(
      'BOT_START_URL not configured, using default: http://localhost:7860/start'
    );
  }

  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (process.env.BOT_START_PUBLIC_API_KEY) {
      headers.Authorization = `Bearer ${process.env.BOT_START_PUBLIC_API_KEY}`;
    }

    const response = await fetch(botStartUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        createDailyRoom: true,
        dailyRoomProperties: { start_video_off: true },
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to connect to Pipecat: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to process connection request: ${error}` },
      { status: 500 }
    );
  }
}
