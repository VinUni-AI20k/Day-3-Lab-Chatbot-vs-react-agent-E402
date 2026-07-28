type TavilyResult = { title?: string; url?: string; content?: string };

const MAX_QUERY_LENGTH = 300;

export async function POST(request: Request) {
  let body: { query?: unknown };
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Request body phải là JSON hợp lệ." }, { status: 400 });
  }

  const query = typeof body.query === "string" ? body.query.trim() : "";
  if (!query || query.length > MAX_QUERY_LENGTH) {
    return Response.json({ error: `Query phải có từ 1 đến ${MAX_QUERY_LENGTH} ký tự.` }, { status: 400 });
  }

  const apiKey = process.env.TAVILY_API_KEY;
  if (!apiKey) {
    return Response.json({ error: "Chưa cấu hình TAVILY_API_KEY trên server." }, { status: 503 });
  }

  try {
    const searchResponse = await fetch("https://api.tavily.com/search", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ query, search_depth: "basic", max_results: 4, include_answer: false }),
      cache: "no-store",
    });

    if (!searchResponse.ok) {
      console.error("Tavily search failed", searchResponse.status);
      return Response.json({ error: "Không thể tìm kiếm web lúc này. Vui lòng thử lại." }, { status: 502 });
    }

    const data = (await searchResponse.json()) as { results?: TavilyResult[] };
    const results = (data.results ?? []).filter((result) => result.title && result.url).map((result) => ({
      title: result.title as string,
      url: result.url as string,
      content: result.content ?? "",
    }));
    return Response.json({ results });
  } catch (error) {
    console.error("Web search request failed", error);
    return Response.json({ error: "Không thể kết nối dịch vụ tìm kiếm. Vui lòng thử lại." }, { status: 502 });
  }
}
