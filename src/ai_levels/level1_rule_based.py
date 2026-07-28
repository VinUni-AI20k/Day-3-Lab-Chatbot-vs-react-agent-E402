import re

class Level1RuleBasedCupid:
    def __init__(self):
        # Tập luật bắt từ khóa và phản hồi tương ứng
        self.rules = [
            (r"chào|hi|hello", "Chào bạn! Tôi là Cupid Level 1. Bạn đang tìm kiếm lời khuyên tình yêu hay muốn tìm đối tượng hẹn hò?"),
            (r"sở thích|thích", "Sở thích chung là cầu nối tuyệt vời! Bạn có thể chia sẻ các sở thích như: đọc sách, du lịch, xem phim, cà phê..."),
            (r"tuổi|bao nhiêu tuổi", "Độ tuổi lý tưởng mà bạn muốn Cupid tìm kiếm cho bạn là khoảng bao nhiêu?"),
            (r"hẹn hò|địa điểm", "Một buổi hẹn hò hoàn hảo nên bắt đầu ở một không gian nhẹ nhàng như quán cà phê yên tĩnh hoặc triển lãm nghệ thuật!"),
            (r"thất tình|buồn", "Cupid rất tiếc khi nghe điều đó. Đừng buồn, cánh cửa này đóng lại sẽ có cánh cửa khác mở ra!")
        ]

    def respond(self, user_input: str) -> str:
        user_input_lower = user_input.lower()
        
        for pattern, response in self.rules:
            if re.search(pattern, user_input_lower):
                return f"[Cupid Level 1]: {response}"
        
        return (
            "[Cupid Level 1]: Xin lỗi, tôi chưa hiểu ý bạn. Do là phiên bản dựa trên luật (Rule-based), "
            "tôi chỉ có thể trả lời các từ khóa như: 'chào', 'sở thích', 'độ tuổi', 'hẹn hò', 'thất tình'."
        )