"""
🌐 FastAPI Server cho ReAct Agent đặt vé xem phim CGV
Wrap các tools từ tools.py, streaming ReAct loop qua SSE
"""

import json
import ast
import re
import os
import sys

# Đảm bảo import từ cùng thư mục src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from tools import (
    search_theater, search_movie, search_showtime,
    get_available_seats, book_seats, generate_ticket, load_movies
)
from prompts import REACT_SYSTEM_PROMPT, CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

app = FastAPI(title="CGV Movie Ticket Agent API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve poster images
assets_path = os.path.join(os.path.dirname(__file__), "..", "config", "assets", "posters")
if os.path.isdir(assets_path):
    app.mount("/assets/posters", StaticFiles(directory=assets_path), name="posters")


# ---- REST Endpoints ----

@app.get("/api/movies")
async def get_movies_api():
    """Return all movies from movies_cache.json"""
    return load_movies()


@app.get("/api/movies/{film_name}/showtimes")
async def get_showtimes_api(film_name: str, cinema: str = "", date: str = ""):
    """Return showtimes for a film"""
    return search_showtime.invoke({
        "movie_name": film_name,
        "cinema": cinema or "",
        "date": date or ""
    })


@app.get("/api/movies/{film_name}/seatmap")
async def get_seatmap_api(film_name: str, cinema: str = "", date: str = "", time: str = ""):
    """Return available seats for a specific showtime"""
    return get_available_seats.invoke({
        "movie_name": film_name,
        "cinema": cinema,
        "time": time
    })


class BookRequest(BaseModel):
    film_name: str
    cinema: str
    date: str
    time: str
    zone: str
    quantity: int


@app.post("/api/book")
async def book_endpoint(req: BookRequest):
    """Book seats directly"""
    return book_seats.invoke({
        "movie_name": req.film_name,
        "cinema": req.cinema,
        "time": req.time,
        "zone": req.zone,
        "quantity": req.quantity
    })


# ---- Tool Mapping ----

TOOLS_MAP = {
    "search_theater": search_theater,
    "search_movie": search_movie,
    "search_showtime": search_showtime,
    "get_available_seats": get_available_seats,
    "book_seats": book_seats,
    "generate_ticket": generate_ticket,
}

TOOL_KEYS = {
    "search_theater": ["location"],
    "search_movie": ["movie_name"],
    "search_showtime": ["movie_name", "cinema", "date"],
    "get_available_seats": ["movie_name", "cinema", "time"],
    "book_seats": ["movie_name", "cinema", "time", "zone", "quantity"],
    "generate_ticket": ["booking_id"],
}


def call_tool(action_name: str, args_list: list):
    """Execute a LangChain tool by name with positional arguments"""
    if action_name not in TOOLS_MAP:
        return f"LỖI: Công cụ '{action_name}' không tồn tại."

    tool_func = TOOLS_MAP[action_name]
    keys = TOOL_KEYS.get(action_name, [])

    kwargs = {}
    for i, val in enumerate(args_list):
        if i < len(keys):
            kwargs[keys[i]] = val

    try:
        return tool_func.invoke(kwargs)
    except Exception as e:
        return f"LỖI: {str(e)}"


def parse_llm_response(text: str):
    """Parse LLM output for Thought, Action, and Final Answer"""
    thought = ""
    action = None
    action_args = []
    final_answer = ""

    # Extract Thought
    thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)", text, re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()

    # Check Final Answer first (takes priority)
    final_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)
    if final_match:
        final_answer = final_match.group(1).strip()
        return thought, None, [], final_answer

    # Parse Action: tool_name["arg1", "arg2", ...]
    action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", text, re.DOTALL)
    if action_match:
        action = action_match.group(1).strip()
        args_str = action_match.group(2).strip()

        if args_str:
            try:
                action_args = ast.literal_eval(f"[{args_str}]")
            except Exception:
                # Fallback: split by comma and strip quotes
                action_args = [a.strip().strip("'\"") for a in args_str.split(',')]

    return thought, action, action_args, final_answer


# ---- Chat SSE Endpoint ----

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def sse_event(data: dict) -> str:
    """Format a dict as an SSE data event"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Main agent chat endpoint with SSE streaming.
    Implements the ReAct loop: Thought -> Action -> Observation -> repeat until Final Answer.
    """
    async def event_stream():
        provider = get_llm_provider()

        # Build conversation prompt from history
        prompt_parts = []
        for msg in req.history:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        prompt_parts.append(f"User: {req.message}")

        current_prompt = "\n".join(prompt_parts) + "\n"
        last_tool = None  # Track last tool for observation context

        for iteration in range(MAX_ITERATIONS):
            try:
                llm_response = provider.generate(current_prompt, system_prompt=REACT_SYSTEM_PROMPT)
            except Exception as e:
                yield sse_event({
                    "type": "final_answer",
                    "content": f"⚠️ Lỗi khi gọi LLM: {str(e)}"
                })
                break

            thought, action, args_list, final_answer = parse_llm_response(llm_response)

            # Emit thought
            if thought:
                yield sse_event({"type": "thought", "content": thought})

            # Final answer -> done
            if final_answer:
                yield sse_event({"type": "final_answer", "content": final_answer})
                break

            # Execute action
            if action:
                # Build readable action string
                args_display = ", ".join(
                    f'"{a}"' if isinstance(a, str) else str(a) for a in args_list
                )
                action_str = f'{action}[{args_display}]'

                yield sse_event({
                    "type": "action",
                    "content": action_str,
                    "tool": action
                })

                # Call the tool
                tool_result = call_tool(action, args_list)
                last_tool = action

                # Append to conversation for next iteration
                current_prompt += f"Thought: {thought}\nAction: {action_str}\nObservation: {json.dumps(tool_result, ensure_ascii=False) if not isinstance(tool_result, str) else tool_result}\n"

                # Emit observation with tool context
                obs_data = {
                    "type": "observation",
                    "content": json.dumps(tool_result, ensure_ascii=False) if not isinstance(tool_result, str) else str(tool_result),
                    "tool": action,
                    "toolResult": tool_result
                }

                # Attach context params for frontend mapping
                if action == "search_showtime" and len(args_list) > 0:
                    obs_data["filmName"] = args_list[0]
                    if len(args_list) > 1:
                        obs_data["cinema"] = args_list[1]
                elif action == "get_available_seats" and len(args_list) > 0:
                    obs_data["filmName"] = args_list[0]
                    if len(args_list) > 1:
                        obs_data["cinema"] = args_list[1]
                    if len(args_list) > 2:
                        obs_data["time"] = args_list[2]

                yield sse_event(obs_data)

                continue  # Next iteration

            # No action and no final answer -> treat raw response as final answer
            yield sse_event({
                "type": "final_answer",
                "content": llm_response.strip()
            })
            break
        else:
            # MAX_ITERATIONS exceeded
            yield sse_event({
                "type": "final_answer",
                "content": f"⚠️ Agent đã đạt giới hạn tối đa {MAX_ITERATIONS} bước suy luận. Vui lòng thử lại với câu hỏi cụ thể hơn."
            })

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
