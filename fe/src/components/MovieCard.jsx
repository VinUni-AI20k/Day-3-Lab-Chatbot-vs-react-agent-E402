import { useState } from 'react';
import { getPosterUrl } from '../services/api';
import './MovieCard.css';

/**
 * MovieCard - Displays a single movie with poster image, genre, duration, and rating
 */
export default function MovieCard({ movie }) {
  const [imgError, setImgError] = useState(false);
  const posterUrl = getPosterUrl(movie.poster_path || movie.poster);

  return (
    <div className="movie-card">
      <div className="movie-poster">
        {posterUrl && !imgError ? (
          <img
            src={posterUrl}
            alt={movie.film_name}
            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'var(--radius-sm)' }}
            onError={() => setImgError(true)}
            loading="lazy"
          />
        ) : (
          <span>{movie.poster || '🎬'}</span>
        )}
      </div>
      <h4>{movie.film_name}</h4>
      <p className="movie-genre">{movie.genre}</p>
      <div className="movie-meta">
        <span className="movie-duration">⏱ {movie.duration_min || movie.duration} phút</span>
        <span className="movie-rating">{movie.rating}</span>
      </div>
    </div>
  );
}
