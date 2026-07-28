import './ActivityPanel.css';
import MovieCard from './MovieCard';
import SeatMap from './SeatMap';

/**
 * ActivityPanel - Right side panel showing visual representation of agent actions
 * Displays different views based on what the agent is currently doing
 */
export default function ActivityPanel({ currentActivity, agentSteps }) {
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
      case 'showtimes':
        return renderShowtimes(currentActivity.data);
      case 'seatmap':
        return renderSeatMap(currentActivity.data);
      case 'booking':
        return renderBooking(currentActivity.data);
      default:
        return null;
    }
  };

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

  const renderShowtimes = (movie) => {
    if (!movie) return null;

    // Group showtimes by cinema
    const cinemas = {};
    for (const st of movie.showtimes) {
      if (!cinemas[st.cinema]) cinemas[st.cinema] = [];
      cinemas[st.cinema].push(st);
    }

    return (
      <div className="showtimes-container">
        <div className="showtime-film-header">
          <div className="film-poster-lg">{movie.poster}</div>
          <div className="film-header-info">
            <h3>{movie.film_name}</h3>
            <p className="film-header-meta">
              {movie.genre} • {movie.duration_min} phút • {movie.rating}
            </p>
          </div>
        </div>

        <div className="activity-section-title">🕐 Suất chiếu hôm nay</div>

        {Object.entries(cinemas).map(([cinema, showtimes]) => (
          <div key={cinema} className="showtime-cinema">
            <div className="cinema-name">🏢 {cinema}</div>
            <div className="showtime-slots">
              {showtimes.map(st => (
                <div
                  key={`${cinema}-${st.time}`}
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
        ))}
      </div>
    );
  };

  const renderSeatMap = ({ movie, showtime }) => (
    <div>
      <div className="showtime-film-header">
        <div className="film-poster-lg">{movie?.poster}</div>
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

  const renderBooking = (data) => (
    <div className="booking-confirm">
      <div className="booking-success-banner">
        <span className="success-icon">🎉</span>
        <h3>Đặt vé thành công!</h3>
        <span className="demo-badge">⚠️ DEMO - Không phải giao dịch thật</span>
      </div>

      <div className="booking-details">
        <div className="booking-detail-row">
          <span className="detail-label">🎬 Phim</span>
          <span className="detail-value">{data.filmName}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🏢 Rạp</span>
          <span className="detail-value">{data.cinema}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">⏰ Suất chiếu</span>
          <span className="detail-value">{data.time}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">💺 Loại ghế</span>
          <span className="detail-value">{data.zone}</span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🪑 Ghế</span>
          <span className="detail-value detail-value--highlight">
            {data.seats?.join(', ')}
          </span>
        </div>
        <div className="booking-detail-row">
          <span className="detail-label">🔖 Mã đặt vé</span>
          <span className="detail-value detail-value--highlight">{data.bookingId}</span>
        </div>
      </div>

      <div className="booking-total">
        <span className="total-label">💰 Tổng tiền</span>
        <span className="total-amount">
          {data.totalPrice?.toLocaleString('vi-VN')}đ
        </span>
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
            {currentActivity.type === 'showtimes' && '🕐 Suất chiếu'}
            {currentActivity.type === 'seatmap' && '💺 Sơ đồ ghế'}
            {currentActivity.type === 'booking' && '🎟️ Đặt vé'}
          </span>
        )}
      </div>
      <div className="activity-content">
        {renderContent()}
      </div>
    </div>
  );
}
