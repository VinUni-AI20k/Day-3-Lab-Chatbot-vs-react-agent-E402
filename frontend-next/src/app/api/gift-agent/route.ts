import { runBaselineChatbot, runGiftAgent, type GiftProfile } from "@/lib/gift-agent";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { message?: unknown; profile?: Partial<GiftProfile>; mode?: unknown };
    const message = typeof body.message === "string" ? body.message.trim() : "";
    if (!message || message.length > 1_000) return Response.json({ error: "Tin nhắn không hợp lệ." }, { status: 400 });
    return Response.json(body.mode === "baseline" ? await runBaselineChatbot(message, body.profile ?? {}) : await runGiftAgent(message, body.profile ?? {}));
  } catch {
    return Response.json({ error: "Không thể xử lý yêu cầu chọn quà." }, { status: 500 });
  }
}
