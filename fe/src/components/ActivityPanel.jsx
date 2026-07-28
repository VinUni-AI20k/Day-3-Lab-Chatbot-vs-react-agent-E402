import { useState, useEffect } from 'react';
import './ActivityPanel.css';
import MovieCard from './MovieCard';
import SeatMap from './SeatMap';
import { fetchMovies, getPosterUrl } from '../services/api';

/**
 * ActivityPanel - Right side panel showing visual representation of agent actions
 * Displays different views based on what the agent is currently doing
 */
export default function ActivityPanel({ currentActivity, agentSteps }) {
  const [allMovies, setAllMovies] = useState([]);

  // Load all movies on mount for the default view
  useEffect(() => {
    fetchMovies()
      .then(setAllMovies)
      .catch(() => setAllMovies([]));
  }, []);

  const renderContent = () => {
    if (!currentActivity) {
      return (
        <div className="activity-empty">
          <div className="empty-icon">🎬</div>
          <h3>Trợ Lý Đặt Vé CGV</h3>
          <p>
            Gửi tin nhắn cho agent để bắt đầu. Khu vực này sẽ hiển thị trực quan
            những gì agent đang thực hiện: tìm phim, xem suất chiếu, sơ đồ ghế,
            và xác nhận đặt vé.
          </p>
        </div>
      );
    }

    switch (currentActivity.type) {
      case 'movies':
        return renderMovies(currentActivity.data);
      case 'movie_detail':
        return renderMovieDetail(currentActivity.data);
      case 'theaters':
        return renderTheaters(currentActivity.data);
      case 'showtimes':
        return renderShowtimes(currentActivity.data);
      case 'available_seats':
        return renderAvailableSeats(currentActivity.data);
      case 'seatmap':
        return renderSeatMapView(currentActivity.data);
      case 'booking':
        return renderBooking(currentActivity.data);
      case 'ticket':
        return renderTicket(currentActivity.data);
      default:
        return null;
    }
  };

  // -- Movies grid --
  const renderMovies = (movies) => (
    <>
      <div className="activity-section-title">
        🔍 Kết quả tìm kiếm — {movies.length} phim đang chiếu
      </div>
      <div className="movies-grid">
        {movies.map(movie => (
          <MovieCard key={movie.film_name} movie={movie} />
        ))}
      </div>
    </>
  );

  // -- Single movie detail from search_movie --
  const renderMovieDetail = (movie) => (
    <div className="showtimes-container">
      <div className="showtime-film-header">
        <div className="film-poster-lg">
          {movie.poster ? (
            <img
              src={getPosterUrl(movie.poster)}
              alt={movie.film_name}
              style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'var(--radius-md)' }}
              onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
            />
          ) : null}
          <span style={{ display: movie.poster ? 'none' : 'flex' }}>🎬</span>
        </div>
        <div className="film-header-info">
          <h3>{movie.film_name}</h3>
          <p className="film-header-meta">
            {movie.genre} • {movie.duration} phút • {movie.rating}
          </p>
        </div>
      </div>
      {movie.synopsis && (
        <div style={{ padding: 'var(--spacing-md)', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginTop: 'var(--spacing-md)', fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
          <strong style={{ color: 'var(--text-primary)' }}>📝 Tóm tắt:</strong><br />
          {movie.synopsis}
        </div>
      )}
    </div>
  );

  // -- Theaters list from search_theater --
  const renderTheaters = (theaters) => (
    <>
      <div className="activity-section-title">🏢 Rạp CGV — {theaters.length} kết quả</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
        {theaters.map(name => (
          <div key={name} className="showtime-slot" style={{ textAlign: 'left', padding: 'var(--spacing-md)' }}>
            <div className="slot-time">🏢 {name}</div>
          </div>
        ))}
      </div>
    </>
  );

  // -- Showtimes from search_showtime --
  const renderShowtimes = ({ showtimes, filmName, cinema }) => (
    <div className="showtimes-container">
      {filmName && (
        <div className="showtime-film-header">
          <div className="film-poster-lg">🎬</div>
          <div className="film-header-info">
            <h3>{filmName}</h3>
            <p className="film-header-meta">{cinema || 'Tất cả rạp'}</p>
          </div>
        </div>
      )}
      <div className="activity-section-title">🕐 Suất chiếu</div>
      <div className="showtime-slots">
        {showtimes.map(st => (
          <div
            key={`${st.time}`}
            className={`showtime-slot ${st.seats_available === 0 ? 'showtime-slot--soldout' : ''}`}
          >
            <div className="slot-time">{st.time}</div>
            <div className={`slot-seats ${st.seats_available > 0 ? 'slot-seats--available' : 'slot-seats--soldout'}`}>
              {st.seats_available > 0
                ? `${st.seats_available} ghế trống`
                : 'Hết vé'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // -- Available seats from get_available_seats --
  const renderAvailableSeats = ({ seats, filmName, cinema, time }) => {
    // Find the full movie data to get the seat_map for visual rendering
    const movie = allMovies.find(m => filmName && m.film_name.toLowerCase().includes(filmName.toLowerCase()));
    const showtime = movie?.showtimes?.find(s =>
      (!cinema || s.cinema.toLowerCase().includes(cinema.toLowerCase())) &&
      (!time || s.time === time)
    );

    return (
      <div>
        <div className="showtime-film-header">
          <div className="film-poster-lg">💺</div>
          <div className="film-header-info">
            <h3>{filmName || 'Ghế trống'}</h3>
            <p className="film-header-meta">
              {cinema} • {time} • {seats.length} ghế trống
            </p>
          </div>
        </div>

        {showtime?.seat_map ? (
          <>
            <div className="activity-section-title">💺 Sơ đồ ghế</div>
            <SeatMap showtime={showtime} />
          </>
        ) : (
          <>
            <div className="activity-section-title">💺 Ghế trống ({seats.length})</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {seats.map(seat => (
                <span key={seat} style={{
                  display: 'inline-block',
                  padding: '4px 8px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-success)'
                }}>
                  {seat}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  // -- Seat map visual (from seatmap endpoint)
  const renderSeatMapView = ({ movie, showtime }) => (
    <div>
      <div className="showtime-film-header">
        <div className="film-poster-lg">{movie?.poster ? '🎬' : '💺'}</div>
        <div className="film-header-info">
          <h3>{movie?.film_name}</h3>
          <p className="film-header-meta">
            {showtime?.cinema} • {showtime?.time} • {showtime?.date}
          </p>
        </div>
      </div>
      <div className="activity-section-title">💺 Sơ đồ ghế</div>
      <SeatMap showtime={showtime} />
    </div>
  );

  // -- Booking result from book_seats --
  const renderBooking = (data) => (
    <div className="booking-confirm">
      <div className="booking-success-banner">
        <span className="success-icon">{data.status === 'SUCCESS' ? '🎉' : '❌'}</span>
        <h3>{data.status === 'SUCCESS' ? 'Đặt ghế thành công!' : 'Đặt ghế thất bại'}</h3>
        {data.status === 'SUCCESS' && (
          <span className="demo-badge">⚠️ DEMO - Không phải giao dịch thật</span>
        )}
      </div>

      {data.status === 'SUCCESS' ? (
        <>
          <div className="booking-details">
            <div className="booking-detail-row">
              <span className="detail-label">🎬 Phim</span>
              <span className="detail-value">{data.movie}</span>
            </div>
            <div className="booking-detail-row">
              <span className="detail-label">🏢 Rạp</span>
              <span className="detail-value">{data.cinema}</span>
            </div>
            <div className="booking-detail-row">
              <span className="detail-label">📅 Ngày</span>
              <span className="detail-value">{data.date}</span>
            </div>
            <div className="booking-detail-row">
              <span className="detail-label">⏰ Suất chiếu</span>
              <span className="detail-value">{data.time}</span>
            </div>
            <div className="booking-detail-row">
              <span className="detail-label">👤 Khách hàng</span>
              <span className="detail-value">{data.customer}</span>
            </div>
            <div className="booking-detail-row">
              <span className="detail-label">🪑 Ghế</span>
              <span className="detail-value detail-value--highlight">
                {Array.isArray(data.seats) ? data.seats.join(', ') : data.seats}
              </span>
            </div>
            <div className="booking-detail-row">
              <span className="detail-label">🔖 Mã đặt vé</span>
              <span className="detail-value detail-value--highlight">
                {data.booking_id}
              </span>
            </div>
          </div>
        </>
      ) : (
        <div style={{
          padding: 'var(--spacing-lg)',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          color: 'var(--color-error)',
          fontSize: 'var(--font-size-sm)'
        }}>
          {data.message || 'Có lỗi xảy ra khi đặt vé.'}
        </div>
      )}
    </div>
  );

  // -- Ticket from generate_ticket --
  const renderTicket = (data) => (
    <div className="booking-confirm">
      <div className="booking-success-banner" style={{
        background: 'linear-gradient(135deg, rgba(77, 166, 255, 0.1), rgba(77, 166, 255, 0.02))',
        borderColor: 'rgba(77, 166, 255, 0.2)'
      }}>
        <span className="success-icon">🎟️</span>
        <h3 style={{ color: 'var(--color-info)' }}>Vé điện tử đã sinh!</h3>
        <span className="demo-badge">⚠️ DEMO - Không có giá trị sử dụng thật</span>
      </div>

      <div className="booking-details">
        <div className="booking-detail-row">
          <span className="detail-label">🎟️ Mã vé</span>
          <span className="detail-value detail-value--highlight">{data.ticket_id}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🔖 Mã đặt vé</span>
          <span className="detail-value">{data.booking_id}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">👤 Khách hàng</span>
          <span className="detail-value">{data.customer}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🎬 Phim</span>
          <span className="detail-value">{data.movie}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🏢 Rạp</span>
          <span className="detail-value">{data.cinema}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">📅 Ngày</span>
          <span className="detail-value">{data.date}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">⏰ Giờ</span>
          <span className="detail-value">{data.time}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🪑 Ghế</span>
          <span className="detail-value detail-value--highlight">
            {Array.isArray(data.seats) ? data.seats.join(', ') : data.seats}
          </span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">📋 Trạng thái</span>
          <span className="detail-value" style={{ color: 'var(--color-success)' }}>
            {data.status || 'CONFIRMED'}
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="activity-panel">
      <div className="activity-header">
        <h2>
          📊 Hoạt động Agent
        </h2>
        {currentActivity && (
          <span className="activity-badge">
            {currentActivity.type === 'movies' && '🔍 Tìm phim'}
            {currentActivity.type === 'movie_detail' && '🎬 Chi tiết phim'}
            {currentActivity.type === 'theaters' && '🏢 Danh sách rạp'}
            {currentActivity.type === 'showtimes' && '🕐 Suất chiếu'}
            {currentActivity.type === 'available_seats' && '💺 Ghế trống'}
            {currentActivity.type === 'seatmap' && '💺 Sơ đồ ghế'}
            {currentActivity.type === 'booking' && '🎟️ Đặt vé'}
            {currentActivity.type === 'ticket' && '🎫 Vé điện tử'}
          </span>
        )}
      </div>
      <div className="activity-content">
        {renderContent()}
      </div>
    </div>
  );
}
