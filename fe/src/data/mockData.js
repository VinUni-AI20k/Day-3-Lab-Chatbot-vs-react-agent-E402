/**
 * Mock data for the movie ticket booking agent
 * Based on PROJECT_PLAN.md specifications
 */

export const MOCK_MOVIES = [
  {
    film_name: "Avatar 3",
    genre: "Khoa học viễn tưởng",
    duration_min: 150,
    rating: "C13",
    synopsis: "Phần tiếp theo của bộ phim bom tấn Avatar, khám phá thêm những vùng đất mới trên hành tinh Pandora với những sinh vật kỳ bí và cuộc chiến bảo vệ hành tinh.",
    poster: "🎬",
    showtimes: [
      {
        cinema: "CGV Vincom Bà Triệu",
        date: "2026-07-28",
        time: "19:00",
        seats_available: 42,
        seat_map: {
          rows: ["A", "B", "C", "D", "E", "F", "G", "H"],
          cols_per_row: 12,
          zones: [
            { zone: "Thường - Gần màn hình", rows: ["A", "B", "C"], price: 60000, note: "Ngồi gần, phải ngước nhìn màn hình" },
            { zone: "VIP - Trung tâm", rows: ["D", "E", "F"], cols: "3-10", price: 95000, note: "Vị trí đẹp nhất, hình & âm thanh cân bằng" },
            { zone: "Thường - Cạnh loa", rows: ["D", "E", "F", "G"], cols: "1-2,11-12", price: 70000, note: "Gần loa surround hai bên, âm thanh to hơn" },
            { zone: "Sweetbox - Ghế đôi", rows: ["H"], price: 150000, note: "Ghế đôi liền kề, không tay vịn giữa, số lượng giới hạn" }
          ],
          booked_seats: ["D5", "D6", "E4", "E5", "E6", "F7", "F8", "H3", "H4", "A1", "A2", "B6"]
        }
      },
      {
        cinema: "CGV Vincom Bà Triệu",
        date: "2026-07-28",
        time: "21:30",
        seats_available: 68,
        seat_map: {
          rows: ["A", "B", "C", "D", "E", "F", "G", "H"],
          cols_per_row: 12,
          zones: [
            { zone: "Thường - Gần màn hình", rows: ["A", "B", "C"], price: 60000, note: "Ngồi gần, phải ngước nhìn màn hình" },
            { zone: "VIP - Trung tâm", rows: ["D", "E", "F"], cols: "3-10", price: 95000, note: "Vị trí đẹp nhất" },
            { zone: "Thường - Cạnh loa", rows: ["D", "E", "F", "G"], cols: "1-2,11-12", price: 70000, note: "Gần loa surround" },
            { zone: "Sweetbox - Ghế đôi", rows: ["H"], price: 150000, note: "Ghế đôi liền kề" }
          ],
          booked_seats: ["D5", "F3"]
        }
      },
      {
        cinema: "CGV Landmark 81",
        date: "2026-07-28",
        time: "20:15",
        seats_available: 0,
        seat_map: null
      }
    ]
  },
  {
    film_name: "Lật Mặt 8",
    genre: "Hành động, Hài",
    duration_min: 130,
    rating: "C16",
    synopsis: "Phần 8 của loạt phim bom tấn Việt Nam Lật Mặt với những tình huống hồi hộp, kịch tính xen lẫn hài hước.",
    poster: "🎭",
    showtimes: [
      {
        cinema: "CGV Vincom Bà Triệu",
        date: "2026-07-28",
        time: "17:30",
        seats_available: 55,
        seat_map: {
          rows: ["A", "B", "C", "D", "E", "F", "G", "H"],
          cols_per_row: 12,
          zones: [
            { zone: "Thường - Gần màn hình", rows: ["A", "B", "C"], price: 55000, note: "Gần màn hình" },
            { zone: "VIP - Trung tâm", rows: ["D", "E", "F"], cols: "3-10", price: 85000, note: "Vị trí đẹp nhất" },
            { zone: "Thường - Cạnh loa", rows: ["D", "E", "F", "G"], cols: "1-2,11-12", price: 65000, note: "Cạnh loa" },
            { zone: "Sweetbox - Ghế đôi", rows: ["H"], price: 140000, note: "Ghế đôi" }
          ],
          booked_seats: ["E5", "E6"]
        }
      }
    ]
  },
  {
    film_name: "Doraemon: Nobita và vùng đất lý tưởng trên bầu trời",
    genre: "Hoạt hình, Phiêu lưu",
    duration_min: 108,
    rating: "P",
    synopsis: "Nobita cùng Doraemon và nhóm bạn khám phá một vùng đất bí ẩn trên bầu trời với những cuộc phiêu lưu thú vị.",
    poster: "🐱",
    showtimes: [
      {
        cinema: "CGV Vincom Bà Triệu",
        date: "2026-07-28",
        time: "15:00",
        seats_available: 30,
        seat_map: {
          rows: ["A", "B", "C", "D", "E", "F"],
          cols_per_row: 10,
          zones: [
            { zone: "Thường - Gần màn hình", rows: ["A", "B"], price: 50000, note: "Gần màn hình" },
            { zone: "VIP - Trung tâm", rows: ["C", "D"], cols: "2-9", price: 75000, note: "Vị trí đẹp" },
            { zone: "Thường - Cạnh loa", rows: ["C", "D", "E"], cols: "1,10", price: 55000, note: "Cạnh loa" },
            { zone: "Sweetbox - Ghế đôi", rows: ["F"], price: 120000, note: "Ghế đôi" }
          ],
          booked_seats: ["C5", "C6", "D4"]
        }
      }
    ]
  },
  {
    film_name: "Transformers: Khởi Đầu",
    genre: "Hành động, Khoa học viễn tưởng",
    duration_min: 140,
    rating: "C13",
    synopsis: "Câu chuyện khởi đầu của cuộc chiến giữa Autobots và Decepticons trên Trái Đất.",
    poster: "🤖",
    showtimes: [
      {
        cinema: "CGV Landmark 81",
        date: "2026-07-28",
        time: "18:00",
        seats_available: 45,
        seat_map: {
          rows: ["A", "B", "C", "D", "E", "F", "G", "H"],
          cols_per_row: 14,
          zones: [
            { zone: "Thường - Gần màn hình", rows: ["A", "B", "C"], price: 65000, note: "Gần màn hình" },
            { zone: "VIP - Trung tâm", rows: ["D", "E", "F"], cols: "3-12", price: 100000, note: "Vị trí đẹp nhất" },
            { zone: "Thường - Cạnh loa", rows: ["D", "E", "F", "G"], cols: "1-2,13-14", price: 75000, note: "Cạnh loa" },
            { zone: "Sweetbox - Ghế đôi", rows: ["H"], price: 160000, note: "Ghế đôi" }
          ],
          booked_seats: ["D7", "D8", "E6", "E7"]
        }
      }
    ]
  }
];

/**
 * Simulate agent responses with ReAct pattern
 * Each scenario maps user intent to a sequence of agent steps
 */
export const AGENT_SCENARIOS = {
  // Default greeting
  greeting: {
    steps: [
      {
        type: "final_answer",
        content: "Xin chào! 👋 Tôi là trợ lý đặt vé xem phim CGV. Tôi có thể giúp bạn:\n\n🎬 Tìm phim đang chiếu\n🕐 Tra cứu suất chiếu\n💺 Kiểm tra ghế trống\n🎟️ Đặt vé xem phim\n\nBạn muốn xem phim gì hôm nay?"
      }
    ],
    activityType: null
  },

  // Search movies
  search_movies: {
    steps: [
      {
        type: "thought",
        content: "Người dùng muốn biết phim đang chiếu. Tôi cần gọi tool search_now_showing_films để tra cứu."
      },
      {
        type: "action",
        content: "search_now_showing_films[]",
        tool: "search_now_showing_films"
      },
      {
        type: "observation",
        content: "Tìm thấy 4 phim đang chiếu: Avatar 3 (Khoa học viễn tưởng), Lật Mặt 8 (Hành động, Hài), Doraemon: Nobita và vùng đất lý tưởng trên bầu trời (Hoạt hình), Transformers: Khởi Đầu (Hành động, Khoa học viễn tưởng)"
      },
      {
        type: "final_answer",
        content: "🎬 Hiện tại CGV đang chiếu các phim sau:\n\n1. **Avatar 3** - Khoa học viễn tưởng (150 phút) - C13\n2. **Lật Mặt 8** - Hành động, Hài (130 phút) - C16\n3. **Doraemon: Nobita và vùng đất lý tưởng** - Hoạt hình (108 phút) - P\n4. **Transformers: Khởi Đầu** - Hành động, KHVT (140 phút) - C13\n\nBạn muốn xem phim nào? Tôi sẽ tra cứu suất chiếu cho bạn! 🍿"
      }
    ],
    activityType: "movies"
  },

  // Get showtimes for Avatar 3
  showtimes_avatar: {
    steps: [
      {
        type: "thought",
        content: "Người dùng hỏi suất chiếu phim Avatar 3. Tôi cần gọi get_showtimes để tra cứu lịch chiếu."
      },
      {
        type: "action",
        content: 'get_showtimes["Avatar 3"]',
        tool: "get_showtimes"
      },
      {
        type: "observation",
        content: "Avatar 3 có 3 suất chiếu hôm nay:\n- CGV Vincom Bà Triệu: 19:00 (42 ghế trống), 21:30 (68 ghế trống)\n- CGV Landmark 81: 20:15 (HẾT VÉ)"
      },
      {
        type: "final_answer",
        content: "📅 Suất chiếu **Avatar 3** hôm nay (28/07):\n\n🏢 **CGV Vincom Bà Triệu**\n  • ⏰ 19:00 - Còn 42 ghế trống ✅\n  • ⏰ 21:30 - Còn 68 ghế trống ✅\n\n🏢 **CGV Landmark 81**\n  • ⏰ 20:15 - ❌ HẾT VÉ\n\nBạn muốn đặt vé suất nào? Tôi sẽ kiểm tra sơ đồ ghế cho bạn! 💺"
      }
    ],
    activityType: "showtimes",
    filmName: "Avatar 3"
  },

  // Check seats and book
  book_ticket: {
    steps: [
      {
        type: "thought",
        content: "Người dùng muốn đặt 2 vé VIP suất 19:00 phim Avatar 3 tại CGV Vincom Bà Triệu. Tôi cần kiểm tra sơ đồ ghế trước."
      },
      {
        type: "action",
        content: 'get_seat_map["Avatar 3", "CGV Vincom Bà Triệu", "19:00"]',
        tool: "get_seat_map"
      },
      {
        type: "observation",
        content: "Sơ đồ ghế suất 19:00:\n- Thường - Gần màn hình (A-C): 60,000đ - 34 ghế trống\n- VIP - Trung tâm (D-F, cột 3-10): 95,000đ - 18 ghế trống\n- Thường - Cạnh loa (D-G, cột 1-2,11-12): 70,000đ - 14 ghế trống\n- Sweetbox - Ghế đôi (H): 150,000đ - 4 ghế trống"
      },
      {
        type: "thought",
        content: "Zone VIP - Trung tâm còn 18 ghế trống, đủ cho 2 vé. Tôi sẽ tiến hành đặt vé."
      },
      {
        type: "action",
        content: 'book_ticket["Avatar 3", "CGV Vincom Bà Triệu", "19:00", "VIP - Trung tâm", 2]',
        tool: "book_ticket"
      },
      {
        type: "observation",
        content: '✅ [DEMO] Đặt thành công 2 vé "VIP - Trung tâm" (D3, D4) phim "Avatar 3" suất 19:00 tại CGV Vincom Bà Triệu. Tổng tiền: 190,000đ. Mã đặt vé: BK20260728-190500.'
      },
      {
        type: "final_answer",
        content: "🎉 **Đặt vé thành công!** [DEMO]\n\n🎬 Phim: **Avatar 3**\n🏢 Rạp: CGV Vincom Bà Triệu\n⏰ Suất: 19:00 - 28/07/2026\n💺 Ghế: **D3, D4** (VIP - Trung tâm)\n💰 Tổng tiền: **190,000đ**\n🔖 Mã đặt vé: **BK20260728-190500**\n\n⚠️ *Đây là đặt vé mô phỏng (demo), không phải giao dịch thật.*\n\nChúc bạn xem phim vui vẻ! 🍿"
      }
    ],
    activityType: "booking",
    filmName: "Avatar 3",
    cinema: "CGV Vincom Bà Triệu",
    time: "19:00",
    zone: "VIP - Trung tâm",
    seats: ["D3", "D4"],
    bookingId: "BK20260728-190500",
    totalPrice: 190000
  },

  // Check seat map
  seat_map: {
    steps: [
      {
        type: "thought",
        content: "Người dùng muốn xem sơ đồ ghế. Tôi cần gọi get_seat_map để lấy thông tin chi tiết."
      },
      {
        type: "action",
        content: 'get_seat_map["Avatar 3", "CGV Vincom Bà Triệu", "19:00"]',
        tool: "get_seat_map"
      },
      {
        type: "observation",
        content: "Sơ đồ ghế suất 19:00 Avatar 3 tại CGV Vincom Bà Triệu:\n8 hàng (A-H), 12 cột mỗi hàng.\nGhế đã đặt: D5, D6, E4, E5, E6, F7, F8, H3, H4, A1, A2, B6"
      },
      {
        type: "final_answer",
        content: "💺 **Sơ đồ ghế** - Avatar 3 | CGV Vincom Bà Triệu | 19:00\n\nTôi đã hiển thị sơ đồ ghế bên phải màn hình. Bạn có thể thấy:\n\n🟢 **Thường - Gần màn hình** (A-C): 60,000đ/vé\n🟡 **VIP - Trung tâm** (D-F): 95,000đ/vé\n🔵 **Thường - Cạnh loa** (cạnh): 70,000đ/vé\n💜 **Sweetbox - Ghế đôi** (H): 150,000đ/vé\n\nBạn muốn đặt vé loại ghế nào?"
      }
    ],
    activityType: "seatmap",
    filmName: "Avatar 3",
    cinema: "CGV Vincom Bà Triệu",
    time: "19:00"
  },

  // Fallback
  fallback: {
    steps: [
      {
        type: "final_answer",
        content: "Tôi hiểu bạn đang hỏi nhưng tôi cần thêm thông tin. Tôi có thể giúp bạn:\n\n🎬 **Tìm phim**: \"phim gì đang chiếu?\"\n🕐 **Suất chiếu**: \"Avatar 3 chiếu lúc mấy giờ?\"\n💺 **Kiểm tra ghế**: \"còn ghế VIP không?\"\n🎟️ **Đặt vé**: \"đặt 2 vé VIP suất 19h\"\n\nBạn muốn tôi giúp gì?"
      }
    ],
    activityType: null
  }
};

/**
 * Simple keyword matching to determine which scenario to trigger
 */
export function matchScenario(message) {
  const lower = message.toLowerCase();

  if (lower.match(/xin chào|hello|hi|chào|hey/)) {
    return "greeting";
  }

  if (lower.match(/đặt.*vé|book|đặt giúp|đặt.*ghế/)) {
    return "book_ticket";
  }

  if (lower.match(/sơ đồ|ghế.*trống|seat|chỗ ngồi|còn ghế/)) {
    return "seat_map";
  }

  if (lower.match(/suất chiếu|lịch chiếu|mấy giờ|giờ chiếu|showtime|chiếu lúc/)) {
    return "showtimes_avatar";
  }

  if (lower.match(/phim.*đang chiếu|phim gì|danh sách phim|film|có phim|xem phim gì/)) {
    return "search_movies";
  }

  return "fallback";
}
