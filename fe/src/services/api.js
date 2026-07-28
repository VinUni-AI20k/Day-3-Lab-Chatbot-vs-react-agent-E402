/**
 * API service layer for connecting to the backend
 */

const API_BASE = 'http://localhost:8000';

/**
 * Fetch all movies from the backend
 */
export async function fetchMovies() {
  const res = await fetch(`${API_BASE}/api/movies`);
  if (!res.ok) throw new Error(`Failed to fetch movies: ${res.status}`);
  return res.json();
}

/**
 * Fetch showtimes for a specific film
 */
export async function fetchShowtimes(filmName, cinema = '', date = '') {
  const params = new URLSearchParams();
  if (cinema) params.set('cinema', cinema);
  if (date) params.set('date', date);
  const res = await fetch(`${API_BASE}/api/movies/${encodeURIComponent(filmName)}/showtimes?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch showtimes: ${res.status}`);
  return res.json();
}

/**
 * Fetch seat map for a specific showtime
 */
export async function fetchSeatMap(filmName, cinema, date, time) {
  const params = new URLSearchParams({ cinema, date, time });
  const res = await fetch(`${API_BASE}/api/movies/${encodeURIComponent(filmName)}/seatmap?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch seat map: ${res.status}`);
  return res.json();
}

/**
 * Send a chat message to the agent and receive streaming SSE responses
 * Returns an async generator yielding step objects
 */
export async function* streamChat(message, history = []) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history })
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from the buffer
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // SSE format: "data: {...json...}"
      if (trimmed.startsWith('data: ')) {
        const jsonStr = trimmed.slice(6);
        if (jsonStr === '[DONE]') return;
        try {
          const step = JSON.parse(jsonStr);
          yield step;
        } catch {
          // Skip malformed JSON lines
        }
      }
    }
  }

  // Process any remaining buffer
  if (buffer.trim()) {
    const trimmed = buffer.trim();
    if (trimmed.startsWith('data: ')) {
      const jsonStr = trimmed.slice(6);
      if (jsonStr !== '[DONE]') {
        try {
          yield JSON.parse(jsonStr);
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

/**
 * Book tickets directly via API
 */
export async function bookTickets(filmName, cinema, date, time, seats, customerName) {
  const res = await fetch(`${API_BASE}/api/book`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      film_name: filmName,
      cinema,
      date,
      time,
      seats,
      customer_name: customerName
    })
  });
  if (!res.ok) throw new Error(`Booking failed: ${res.status}`);
  return res.json();
}

/**
 * Get poster URL from backend
 */
export function getPosterUrl(posterPath) {
  if (!posterPath) return null;
  // poster_path is like "/assets/conan.webp", backend serves at /assets/posters/
  const filename = posterPath.split('/').pop();
  return `${API_BASE}/assets/posters/${filename}`;
}
