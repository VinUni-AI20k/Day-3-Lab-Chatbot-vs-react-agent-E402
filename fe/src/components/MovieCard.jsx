import './MovieCard.css';

/**
 * MovieCard - Displays a single movie with poster, genre, duration, and rating
 */
export default function MovieCard({ movie }) {
  return (
    <div className="movie-card">
      <div className="movie-poster">{movie.poster}</div>
      <h4>{movie.film_name}</h4>
      <p className="movie-genre">{movie.genre}</p>
      <div className="movie-meta">
        <span className="movie-duration">⏱ {movie.duration_min} phút</span>
        <span className="movie-rating">{movie.rating}</span>
      </div>
    </div>
  );
}
