export type ProfileKey = "relationship" | "occasion" | "interests" | "budget";
export type GiftProfile = Record<ProfileKey, string>;
export type SearchResult = { title: string; url: string; content: string };
export type GiftSuggestion = { title: string; reason: string; recommended: boolean };
export type AgentState = "baseline" | "collect_profile" | "search_web" | "recommend" | "done" | "error";
export type ToolTrace = { tool: string; status: "success" | "skipped" | "error"; thought: string; action: string; observation: string };
export type AgentResult = {
  state: AgentState;
  profile: GiftProfile;
  product: string;
  reply: string;
  suggestions?: GiftSuggestion[];
  closing?: string;
  sources: SearchResult[];
  trace: ToolTrace[];
};

const emptyProfile: GiftProfile = { relationship: "", occasion: "", interests: "", budget: "" };
const marketplaceDomains = ["shopee.vn", "lazada.vn", "tiki.vn", "sendo.vn"];

function isMarketplaceUrl(url: string) {
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
    return marketplaceDomains.some((domain) => host === domain || host.endsWith(`.${domain}`));
  } catch {
    return false;
  }
}

function normalizeBudget(text: string) {
  const compact = text.toLowerCase().replace(/\s+/g, "");
  const million = compact.match(/(\d+(?:[.,]\d+)?)\s*(?:tr|triệu|trieu|m)\b/);
  if (million) return `${million[1].replace(",", ".")} triệu`;
  const thousand = compact.match(/(\d+(?:[.,]\d+)?)\s*(?:k|nghìn|nghin)\b/);
  if (thousand) return `${thousand[1].replace(",", ".")}k`;
  const plainVnd = compact.match(/\b(\d{5,9})\b/);
  if (plainVnd) return `${Number(plainVnd[1]).toLocaleString("vi-VN")}đ`;
  return "";
}

function regexNormalizeProfile(message: string, current: Partial<GiftProfile> = {}): GiftProfile {
  const next: GiftProfile = { ...emptyProfile, ...current };
  const lower = message.toLowerCase();

  if (!next.relationship) {
    if (/(bạn thân|bạn của mình)/.test(lower)) next.relationship = "Bạn thân";
    else if (/(người yêu|bạn trai|bạn gái)/.test(lower)) next.relationship = "Người yêu";
    else if (/(đồng nghiệp|sếp)/.test(lower)) next.relationship = "Đồng nghiệp";
    else if (/(mẹ|ba|bố|chị|anh|em)/.test(lower)) next.relationship = "Người thân";
  }
  if (!next.occasion) {
    if (/sinh nhật/.test(lower)) next.occasion = "Sinh nhật";
    else if (/kỷ niệm/.test(lower)) next.occasion = "Kỷ niệm";
    else if (/(cảm ơn|tri ân)/.test(lower)) next.occasion = "Cảm ơn";
  }
  if (!next.interests) {
    const interests = [
      [/(cà phê|coffee)/, "Cà phê"], [/(đọc sách|sách)/, "Đọc sách"],
      [/(game|chơi game)/, "Chơi game"], [/(skincare|chăm sóc da|làm đẹp)/, "Làm đẹp"],
      [/(nấu ăn|bếp)/, "Nấu ăn"], [/(du lịch|đi chơi)/, "Du lịch"],
      [/(xem phim|phim ảnh|rạp phim)/, "Xem phim"], [/(lười vận động|ở nhà|thư giãn)/, "Thư giãn tại nhà"],
      [/(ai|trí tuệ nhân tạo|công nghệ|tech)/, "AI và công nghệ"],
    ].filter(([pattern]) => (pattern as RegExp).test(lower)).map(([, value]) => value as string);
    if (interests.length) next.interests = interests.join(", ");
  }
  if (!next.budget) next.budget = normalizeBudget(message);
  return next;
}

type Normalization = { profile: GiftProfile; followup: string };

function cleanProfileValue(value: unknown) {
  return typeof value === "string" ? value.trim().slice(0, 120) : "";
}

async function normalizeProfile(message: string, current: Partial<GiftProfile> = {}): Promise<Normalization> {
  const fallback = regexNormalizeProfile(message, current);
  const key = process.env.GROQ_API_KEY;
  if (!key) return { profile: fallback, followup: "" };

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile", temperature: 0.65, max_completion_tokens: 180,
        messages: [
          { role: "system", content: "Bạn là bộ trích xuất hồ sơ quà tặng tiếng Việt. Hiểu cách nói tự nhiên, tiếng lóng và quan hệ không chuẩn như 'anh lab coach'. Không bịa ngân sách. 'không dịp gì cả', 'tặng vu vơ', 'bất ngờ' là occasion hợp lệ: 'Tặng bất ngờ'." },
          { role: "user", content: `Hồ sơ đã có: ${JSON.stringify(current)}. Tin nhắn mới: ${message}\nTrả về JSON thuần: {"relationship":"","occasion":"","interests":"","budget":"","followup":""}. Giữ thông tin đã có nếu tin nhắn không sửa. Chỉ điền điều người dùng nói hoặc có thể hiểu trực tiếp. Nếu còn thiếu, followup là một câu tiếng Việt ấm áp, đa dạng, có ghi nhận điều vừa biết và CHỈ hỏi một trường thiếu. Nếu đủ 4 trường, followup là chuỗi rỗng.` },
        ],
      }), cache: "no-store",
    });
    if (!response.ok) throw new Error();
    const data = (await response.json()) as { choices?: Array<{ message?: { content?: string } }> };
    const raw = data.choices?.[0]?.message?.content?.trim().replace(/^```json\s*|\s*```$/g, "");
    if (!raw) throw new Error();
    const parsed = JSON.parse(raw) as Partial<GiftProfile> & { followup?: unknown };
    const profile: GiftProfile = {
      relationship: cleanProfileValue(parsed.relationship) || fallback.relationship,
      occasion: cleanProfileValue(parsed.occasion) || fallback.occasion,
      interests: cleanProfileValue(parsed.interests) || fallback.interests,
      budget: cleanProfileValue(parsed.budget) || fallback.budget,
    };
    return { profile, followup: cleanProfileValue(parsed.followup) };
  } catch {
    return { profile: fallback, followup: "" };
  }
}

function nextQuestion(profile: GiftProfile) {
  if (!profile.relationship) return "Người nhận là ai với bạn để mình chọn món quà có độ thân mật vừa phải?";
  if (!profile.occasion) return `Tặng ${profile.relationship.toLowerCase()} thì mình sẽ ưu tiên món quà có cảm giác gần gũi. Bạn muốn tặng nhân dịp gì nhỉ?`;
  if (!profile.interests) return `Dịp ${profile.occasion.toLowerCase()} rất hợp để chọn món có câu chuyện riêng. Người ấy hay thích làm gì, hoặc có điều gì bạn muốn tránh không?`;
  return `Mình đã hình dung được hướng quà hợp với sở thích ${profile.interests.toLowerCase()}. Bạn dự tính chi khoảng bao nhiêu để mình chốt gợi ý vừa ý nhé?`;
}

async function selectProduct(profile: GiftProfile) {
  const key = process.env.GROQ_API_KEY;
  if (!key) throw new Error("Groq chưa được cấu hình");
  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile", temperature: 0.25, max_completion_tokens: 70,
      messages: [
        { role: "system", content: "Bạn chọn sản phẩm quà tặng cụ thể cho sàn thương mại điện tử Việt Nam." },
        { role: "user", content: `Chọn ĐÚNG MỘT sản phẩm cụ thể để tìm mua: tặng ${profile.relationship}, dịp ${profile.occasion}, thích ${profile.interests}, ngân sách ${profile.budget}. Chỉ trả về cụm từ tìm kiếm sản phẩm bằng tiếng Việt (tối đa 12 từ), không giải thích, không markdown.` },
      ],
    }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Groq product selection failed");
  const data = (await response.json()) as { choices?: Array<{ message?: { content?: string } }> };
  const product = data.choices?.[0]?.message?.content?.replace(/\s+/g, " ").trim().replace(/^[-•\d.\s]+/, "");
  if (!product || product.length > 140) throw new Error("Groq product selection missing content");
  return product;
}

async function searchWeb(profile: GiftProfile, product: string): Promise<SearchResult[]> {
  const key = process.env.TAVILY_API_KEY;
  if (!key) throw new Error("Tavily chưa được cấu hình");
  const query = `${product} giá ${profile.budget} mua online Việt Nam`;
  const response = await fetch("https://api.tavily.com/search", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ query, search_depth: "basic", max_results: 6, include_answer: false, include_domains: marketplaceDomains }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Tavily search failed");
  const data = (await response.json()) as { results?: Array<Partial<SearchResult>> };
  return (data.results ?? []).filter((item) => item.title && item.url && isMarketplaceUrl(item.url)).map((item) => ({
    title: item.title as string, url: item.url as string, content: item.content ?? "",
  }));
}

async function generateRecommendation(profile: GiftProfile, product: string, sources: SearchResult[]) {
  const key = process.env.GROQ_API_KEY;
  if (!key) throw new Error("Groq chưa được cấu hình");
  const sourceText = sources.map((source, index) => `[${index + 1}] ${source.title}\n${source.content.slice(0, 600)}\n${source.url}`).join("\n\n") || "Không có nguồn web.";
  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile", temperature: 0.5, max_completion_tokens: 500,
      messages: [
        { role: "system", content: "Bạn là Mèo Hồng, trợ lý chọn quà cẩn thận và không bịa thông tin mua hàng." },
        { role: "user", content: `Hồ sơ: ${profile.relationship}; ${profile.occasion}; thích ${profile.interests}; ngân sách ${profile.budget}.\nSản phẩm đích: ${product}.\n\nKết quả từ sàn thương mại điện tử:\n${sourceText}\n\nTrả về DUY NHẤT JSON hợp lệ, không Markdown, theo schema: {"intro":"một câu ngắn", "suggestions":[{"title":"tên sản phẩm cụ thể", "reason":"lý do + giá nếu nguồn có", "recommended":true}], "closing":"một câu nhắc kiểm tra link trước khi mua"}. Có ĐÚNG 1 suggestion và nó phải recommended=true. Chỉ chọn sản phẩm có trong nguồn; dùng [1], [2] trong reason để chỉ nguồn tương ứng. Không bịa giá, tồn kho, thương hiệu hoặc link. Nếu nguồn không có trang sản phẩm đáng tin, trả về suggestion.title là "Chưa xác minh được sản phẩm cụ thể".` },
      ],
    }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Groq recommendation failed");
  const data = (await response.json()) as { choices?: Array<{ message?: { content?: string } }> };
  const answer = data.choices?.[0]?.message?.content?.trim();
  if (!answer) throw new Error("Groq response missing content");
  const parsed = JSON.parse(answer.replace(/^```json\s*|\s*```$/g, "")) as {
    intro?: unknown; suggestions?: unknown; closing?: unknown;
  };
  if (typeof parsed.intro !== "string" || typeof parsed.closing !== "string" || !Array.isArray(parsed.suggestions)) {
    throw new Error("Groq response format invalid");
  }
  const suggestions = parsed.suggestions.slice(0, 1).flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const suggestion = item as { title?: unknown; reason?: unknown; recommended?: unknown };
    if (typeof suggestion.title !== "string" || typeof suggestion.reason !== "string") return [];
    return [{ title: suggestion.title, reason: suggestion.reason, recommended: suggestion.recommended === true }];
  });
  if (suggestions.length !== 1) throw new Error("Groq suggestion missing");
  suggestions[0].recommended = true;
  return { intro: parsed.intro, suggestions, closing: parsed.closing };
}

const tools = {
  normalize_profile: normalizeProfile,
  select_product: selectProduct,
  search_web: searchWeb,
  generate_recommendation: generateRecommendation,
};

export async function runBaselineChatbot(message: string, current: Partial<GiftProfile>): Promise<AgentResult> {
  const profile: GiftProfile = { ...emptyProfile, ...current };
  const trace: ToolTrace[] = [];
  const key = process.env.GROQ_API_KEY;
  if (!key) return { state: "error", profile, product: "", reply: "Chưa cấu hình Groq cho Baseline chatbot.", sources: [], trace };

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile", temperature: 0.7, max_completion_tokens: 300,
        messages: [
          { role: "system", content: "Bạn là chatbot tư vấn quà tặng thân thiện. Trả lời dựa trên kiến thức có sẵn; không tìm web, không gọi tool, không khẳng định giá hoặc tồn kho thực tế." },
          { role: "user", content: message },
        ],
      }), cache: "no-store",
    });
    if (!response.ok) throw new Error();
    const data = (await response.json()) as { choices?: Array<{ message?: { content?: string } }> };
    const reply = data.choices?.[0]?.message?.content?.trim();
    if (!reply) throw new Error();
    trace.push({ tool: "baseline_llm", status: "success", thought: "Câu hỏi được gửi thẳng cho chatbot, không cần dữ liệu thời gian thực.", action: "generate_text(message)", observation: "Đã tạo phản hồi từ kiến thức mô hình; không gọi tool." });
    return { state: "baseline", profile, product: "", reply, sources: [], trace };
  } catch {
    trace.push({ tool: "baseline_llm", status: "error", thought: "Câu hỏi được gửi thẳng cho chatbot.", action: "generate_text(message)", observation: "Không thể tạo phản hồi baseline." });
    return { state: "error", profile, product: "", reply: "Baseline chatbot chưa thể trả lời lúc này.", sources: [], trace };
  }
}

export async function runGiftAgent(message: string, current: Partial<GiftProfile>): Promise<AgentResult> {
  const trace: ToolTrace[] = [];
  const normalization = await tools.normalize_profile(message, current);
  const profile = normalization.profile;
  trace.push({ tool: "normalize_profile", status: "success", thought: "Cần hiểu tự nhiên thông tin người dùng vừa cung cấp.", action: "normalize_profile(message, current_profile)", observation: `Đã nhận ${Object.values(profile).filter(Boolean).length}/4 trường hồ sơ.` });

  if (!Object.values(profile).every(Boolean)) {
    trace.push(
      { tool: "select_product", status: "skipped", thought: "Hồ sơ chưa đủ để chọn sản phẩm chính xác.", action: "skip select_product", observation: "Chờ thêm thông tin từ người dùng." },
      { tool: "search_web", status: "skipped", thought: "Chưa có tiêu chí tìm kiếm đầy đủ.", action: "skip search_web", observation: "Không gọi Tavily." },
      { tool: "generate_recommendation", status: "skipped", thought: "Chưa đủ dữ kiện để chốt quà.", action: "skip generate_recommendation", observation: "Hỏi một trường còn thiếu." },
    );
    return { state: "collect_profile", profile, product: "", reply: normalization.followup || nextQuestion(profile), sources: [], trace };
  }

  let product = `quà ${profile.interests} ${profile.budget}`;
  try {
    product = await tools.select_product(profile);
    trace.push({ tool: "select_product", status: "success", thought: "Hồ sơ đã đủ, cần chọn một sản phẩm đích để tìm chính xác.", action: "select_product(profile)", observation: `Sản phẩm đích: ${product}.` });
  } catch {
    trace.push({ tool: "select_product", status: "error", thought: "Cần một sản phẩm đích trước khi tìm sàn TMĐT.", action: "select_product(profile)", observation: "Không chọn được; dùng cụm từ fallback từ sở thích và ngân sách." });
  }

  let sources: SearchResult[] = [];
  try {
    sources = await tools.search_web(profile, product);
    trace.push({ tool: "search_web", status: "success", thought: "Cần kiểm tra các trang bán hàng thực tế.", action: "search_web(product, marketplaces)", observation: `Tìm thấy ${sources.length} kết quả hợp lệ từ sàn TMĐT.` });
  } catch {
    trace.push({ tool: "search_web", status: "error", thought: "Cần kiểm tra các trang bán hàng thực tế.", action: "search_web(product, marketplaces)", observation: "Tavily không phản hồi; tiếp tục tạo câu trả lời thận trọng." });
  }

  try {
    const recommendation = await tools.generate_recommendation(profile, product, sources);
    trace.push({ tool: "generate_recommendation", status: "success", thought: "Đã có hồ sơ và nguồn để chốt khuyến nghị.", action: "generate_recommendation(profile, product, sources)", observation: "Đã tạo khuyến nghị sản phẩm và dẫn nguồn." });
    return { state: "done", profile, product, reply: recommendation.intro, suggestions: recommendation.suggestions, closing: recommendation.closing, sources, trace };
  } catch {
    trace.push({ tool: "generate_recommendation", status: "error", thought: "Đã có hồ sơ để tạo khuyến nghị.", action: "generate_recommendation(profile, product, sources)", observation: "Không tạo được câu trả lời cuối; trả về thông báo lỗi an toàn." });
    return { state: "error", profile, product, reply: "Mình đã có đủ thông tin nhưng chưa thể tạo khuyến nghị ngay lúc này. Bạn thử lại sau ít phút nhé.", sources, trace };
  }
}
