import { useMemo } from 'react';
import './SeatMap.css';

/**
 * Determine which zone a seat belongs to based on the seat_map zones config
 */
function getSeatZone(row, col, zones) {
  for (const zone of zones) {
    if (!zone.rows.includes(row)) continue;

    // If zone has cols restriction, parse it
    if (zone.cols) {
      const validCols = new Set();
      for (const part of zone.cols.split(',')) {
        if (part.includes('-')) {
          const [start, end] = part.split('-').map(Number);
          for (let c = start; c <= end; c++) validCols.add(c);
        } else {
          validCols.add(Number(part));
        }
      }
      if (validCols.has(col)) return zone;
    } else {
      return zone;
    }
  }
  return null;
}

/**
 * Map zone name to a CSS class suffix
 */
function zoneClass(zoneName) {
  if (!zoneName) return 'standard';
  if (zoneName.includes('VIP')) return 'vip';
  if (zoneName.includes('Cạnh loa')) return 'speaker';
  if (zoneName.includes('Sweetbox')) return 'sweetbox';
  return 'standard';
}

/**
 * SeatMap - Visual cinema seat map with color-coded zones
 */
export default function SeatMap({ showtime }) {
  const seatMap = showtime?.seat_map;

  const grid = useMemo(() => {
    if (!seatMap) return [];

    const { rows, cols_per_row, zones, booked_seats } = seatMap;
    const bookedSet = new Set(booked_seats || []);

    return rows.map(row => {
      const cols = [];
      // Sweetbox rows have paired seats
      const isSweetbox = zones.some(z => z.zone.includes('Sweetbox') && z.rows.includes(row));

      if (isSweetbox) {
        for (let c = 1; c <= cols_per_row; c += 2) {
          const seatId1 = `${row}${c}`;
          const seatId2 = `${row}${c + 1}`;
          const isBooked = bookedSet.has(seatId1) || bookedSet.has(seatId2);
          cols.push({
            id: `${seatId1}-${seatId2}`,
            label: `${c}-${c + 1}`,
            isBooked,
            zone: 'sweetbox',
            isSweetbox: true
          });
        }
      } else {
        for (let c = 1; c <= cols_per_row; c++) {
          const seatId = `${row}${c}`;
          const zone = getSeatZone(row, c, zones);
          cols.push({
            id: seatId,
            label: c,
            isBooked: bookedSet.has(seatId),
            zone: zone ? zoneClass(zone.zone) : 'standard',
            isSweetbox: false
          });
        }
      }

      return { row, cols };
    });
  }, [seatMap]);

  if (!seatMap) {
    return (
      <div className="seat-map-container">
        <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
          Không có sơ đồ ghế cho suất chiếu này.
        </p>
      </div>
    );
  }

  return (
    <div className="seat-map-container">
      {/* Screen */}
      <div className="seat-map-screen">
        <div className="screen-visual" />
        <p className="screen-label">Màn hình</p>
      </div>

      {/* Seat Grid */}
      <div className="seat-grid">
        {grid.map(({ row, cols }) => (
          <div key={row} className="seat-row">
            <span className="row-label">{row}</span>
            {cols.map(seat => (
              <div
                key={seat.id}
                className={`seat ${
                  seat.isBooked
                    ? 'seat--booked'
                    : seat.isSweetbox
                      ? 'seat--available-sweetbox'
                      : `seat--available-${seat.zone}`
                }`}
                title={seat.isBooked ? `${seat.id} (Đã đặt)` : seat.id}
              >
                {seat.isBooked ? '×' : seat.label}
              </div>
            ))}
            <span className="row-label">{row}</span>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="zone-legend">
        {seatMap.zones.map(zone => (
          <div key={zone.zone} className="zone-item">
            <div className={`zone-color zone-color--${zoneClass(zone.zone)}`} />
            <div className="zone-info">
              <div className="zone-name">{zone.zone}</div>
              <div className="zone-price">{zone.price.toLocaleString('vi-VN')}đ</div>
            </div>
          </div>
        ))}
        <div className="zone-item">
          <div className="zone-color zone-color--booked" />
          <div className="zone-info">
            <div className="zone-name">Đã đặt</div>
            <div className="zone-price">Không khả dụng</div>
          </div>
        </div>
      </div>
    </div>
  );
}
