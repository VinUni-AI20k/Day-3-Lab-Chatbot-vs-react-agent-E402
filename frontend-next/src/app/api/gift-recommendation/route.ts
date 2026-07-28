type GiftProfile = { relationship?: unknown; occasion?: unknown; interests?: unknown; budget?: unknown };
type SearchSource = { title?: unknown; url?: unknown; content?: unknown };

function isText(value: unknown) {
  return typeof value === "string" && value.trim().length > 0;
}

export async function POST(request: Request) {
  let body: { profile?: GiftProfile; sources?: SearchSource[] };
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Request body phải là JSON hợp lệ." }, { status: 400 });
  }

  const profile = body.profile ?? {};
  if (![profile.relationship, profile.occasion, profile.interests, profile.budget].every(isText)) {
    return Response.json({ error: "Cần đủ thông tin người nhận, dịp, sở thích và ngân sách." }, { status: 400 });
  }

  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    return Response.json({ error: "Chưa cấu hình GROQ_API_KEY trên server." }, { status: 503 });
  }

  const sources = (body.sources ?? []).slice(0, 4).map((source, index) => ({
    number: index + 1,
    title: typeof source.title === "string" ? source.title : "Nguồn tham khảo",
    url: typeof source.url === "string" ? source.url : "",
    content: typeof source.content === "string" ? source.content.slice(0, 700) : "",
  }));

  const prompt = `Hồ sơ người nhận quà:
- Mối quan hệ: ${profile.relationship}
- Dịp: ${profile.occasion}
- Sở thích: ${profile.interests}
- Ngân sách: ${profile.budget}

Nguồn web đã tìm được:
${sources.map((source) => `[${source.number}] ${source.title}\n${source.content}\n${source.url}`).join("\n\n") || "Không có nguồn cụ thể."}

Hãy trả lời bằng tiếng Việt thân thiện, ngắn gọn. Đưa ra đúng 3 gợi ý quà, mỗi gợi ý gồm tên món quà, khoảng giá nếu suy luận được và một lý do gắn với hồ sơ. Xếp hạng 1 món 'Nên chọn nhất'. Chỉ dùng nguồn để tham khảo, không khẳng định giá/còn hàng nếu nguồn không nói rõ. Kết thúc bằng một câu nhắc người dùng kiểm tra link trước khi mua. Không dùng Markdown table.`;

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile",
        temperature: 0.5,
        max_completion_tokens: 500,
        messages: [
          { role: "system", content: "Bạn là Mèo Hồng, trợ lý chọn quà cẩn thận và không bịa thông tin mua hàng." },
          { role: "user", content: prompt },
        ],
      }),
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Groq request failed");

    const data = (await response.json()) as { choices?: Array<{ message?: { content?: string } }> };
    const answer = data.choices?.[0]?.message?.content?.trim();
    if (!answer) throw new Error("Missing Groq answer");
    return Response.json({ answer });
  } catch {
    return Response.json({ error: "Chưa thể tạo khuyến nghị lúc này. Vui lòng thử lại." }, { status: 502 });
  }
}
