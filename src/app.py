'''Ứng dụng tích hợp Chatbot Baseline và Cupid ReAct Agent.'''

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT
from providers import get_llm_provider
from tools import AVAILABLE_TOOLS

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_CASES_PATH = os.path.join(PROJECT_ROOT, 'config', 'test_cases.json')
PROFILES_PATH = os.path.join(PROJECT_ROOT, 'cupid_data', 'cupid_profiles.json')

MOCK_DATA_RULES = '''Bạn là Cupid Chatbot Baseline.
Dữ liệu MOCK_PROFILES trong yêu cầu là dữ liệu mô phỏng được phép sử dụng.
Chỉ dùng dữ liệu được cung cấp; không gọi tool, không bịa hồ sơ hoặc thuộc tính.
Nêu rõ kết quả chỉ mang tính minh họa, không phải kết luận khoa học.
Trả lời bằng tiếng Việt, ngắn gọn và lịch sự.'''


def _load_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_test_cases() -> list[dict[str, Any]]:
    tests = _load_json(TEST_CASES_PATH)
    if not isinstance(tests, list):
        raise ValueError('config/test_cases.json phải chứa một JSON array')
    return tests


def load_mock_profiles() -> list[dict[str, Any]]:
    profiles = _load_json(PROFILES_PATH)
    if not isinstance(profiles, list):
        raise ValueError('cupid_profiles.json phải chứa một JSON array')
    return profiles


def run_baseline_chatbot(user_query: str, provider) -> str:
    '''Chạy baseline có mock data trong context nhưng không gọi tool.'''
    grounded_query = user_query + '\n\nMOCK_PROFILES:\n' + json.dumps(
        load_mock_profiles(), ensure_ascii=False
    )
    return provider.generate(grounded_query, system_prompt=MOCK_DATA_RULES)


def _error(code: str, message: str) -> dict[str, Any]:
    return {'ok': False, 'error': {'code': code, 'message': message}}


def parse_react_response(response: str) -> dict[str, Any]:
    '''Parse đúng một Action hoặc Final Answer mà không dùng eval.'''
    if not isinstance(response, str) or not response.strip():
        return _error('INVALID_ACTION', 'Provider trả về nội dung rỗng')

    text = response.strip()
    if text.startswith('```') and text.endswith('```'):
        text = re.sub(r'^```(?:text)?\s*|\s*```$', '', text, flags=re.I)

    final_match = re.fullmatch(r'Final Answer\s*:\s*(.+)', text, re.I | re.S)
    if final_match:
        return {
            'ok': True,
            'type': 'final',
            'answer': final_match.group(1).strip(),
        }

    action_match = re.fullmatch(
        r'Action\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n'
        r'Action Input\s*:\s*(\{.*\})\s*',
        text,
        re.I | re.S,
    )
    if not action_match:
        return _error(
            'INVALID_ACTION',
            'Phản hồi phải chứa Action và Action Input, hoặc Final Answer',
        )

    try:
        action_input = json.loads(action_match.group(2))
    except json.JSONDecodeError:
        return _error('INVALID_ACTION', 'Action Input không phải JSON hợp lệ')
    if not isinstance(action_input, dict):
        return _error('INVALID_ACTION', 'Action Input phải là JSON object')

    return {
        'ok': True,
        'type': 'action',
        'action': action_match.group(1),
        'action_input': action_input,
    }


def execute_tool(action: str, action_input: dict[str, Any]) -> dict[str, Any]:
    '''Chỉ thực thi tool có trong registry và chuẩn hóa lỗi tích hợp.'''
    tool = AVAILABLE_TOOLS.get(action)
    if tool is None:
        return _error('UNKNOWN_TOOL', f'Tool không tồn tại: {action}')
    try:
        observation = tool(**action_input)
        if not isinstance(observation, dict) or 'ok' not in observation:
            return _error('TOOL_EXECUTION_ERROR', 'Tool trả về sai contract')
        return observation
    except TypeError:
        return _error('INVALID_TOOL_ARGUMENTS', 'Tham số gọi tool không hợp lệ')
    except Exception:
        return _error('TOOL_EXECUTION_ERROR', 'Không thể thực thi tool')


def _provider_error(response: str) -> bool:
    if not isinstance(response, str):
        return True
    prefix = response.lstrip().lower()
    return prefix.startswith('[') and (
        ' error]' in prefix or ' exception]' in prefix
    )


def _build_react_prompt(
    user_query: str,
    trace: list[dict[str, Any]],
) -> str:
    parts = [f'Yêu cầu ban đầu:\n{user_query}']
    if trace:
        parts.append('Lịch sử Action và Observation đã được hệ thống xác minh:')
        for item in trace:
            parts.extend(
                [
                    'Action: {}'.format(item['action']),
                    'Action Input: '
                    + json.dumps(item['action_input'], ensure_ascii=False),
                    'Observation: '
                    + json.dumps(item['observation'], ensure_ascii=False),
                ]
            )
    parts.append('Hãy trả về Action tiếp theo hoặc Final Answer đúng contract.')
    return '\n\n'.join(parts)


def _collect_structured_output(
    result: dict[str, Any],
    action: str,
    observation: dict[str, Any],
) -> None:
    if not observation.get('ok'):
        return
    data = observation.get('data', {})
    if action == 'find_candidate_matches':
        result['matches'] = data.get('matches', [])
    elif action == 'calculate_compatibility':
        result['compatibility'] = data
    elif action == 'suggest_first_message':
        result['opener'] = data
    elif action == 'get_user_profile':
        result['profile'] = data


def run_react_agent(
    user_query: str,
    provider,
    user_id: str | None = None,
) -> dict[str, Any]:
    '''Chạy ReAct loop có registry, trace và giới hạn số Action.'''
    result: dict[str, Any] = {
        'status': 'running',
        'answer': '',
        'profile': None,
        'matches': [],
        'compatibility': None,
        'opener': None,
        'trace': [],
        'error': None,
    }

    while True:
        response = provider.generate(
            _build_react_prompt(user_query, result['trace']),
            system_prompt=REACT_SYSTEM_PROMPT,
        )
        if _provider_error(response):
            result['status'] = 'error'
            result['error'] = {
                'code': 'PROVIDER_ERROR',
                'message': 'Không thể nhận phản hồi hợp lệ từ LLM provider',
            }
            result['answer'] = result['error']['message']
            return result

        parsed = parse_react_response(response)
        if not parsed.get('ok'):
            result['status'] = 'error'
            result['error'] = parsed['error']
            result['answer'] = parsed['error']['message']
            return result

        if parsed['type'] == 'final':
            result['status'] = 'success'
            result['answer'] = parsed['answer']
            return result

        if len(result['trace']) >= MAX_ITERATIONS:
            result['status'] = 'error'
            result['error'] = {
                'code': 'MAX_ITERATIONS',
                'message': f'Đã đạt giới hạn {MAX_ITERATIONS} lần gọi tool',
            }
            result['answer'] = 'Agent đã dừng an toàn vì đạt giới hạn số bước.'
            return result

        action_input = dict(parsed['action_input'])
        if user_id and 'user_id' not in action_input:
            action_input['user_id'] = user_id
        observation = execute_tool(parsed['action'], action_input)
        trace_item = {
            'iteration': len(result['trace']) + 1,
            'action': parsed['action'],
            'action_input': action_input,
            'observation': observation,
        }
        result['trace'].append(trace_item)
        _collect_structured_output(result, parsed['action'], observation)


def print_baseline_result(test: dict[str, Any], answer: str) -> None:
    print('\n💬 [BASELINE — TEST {}] {}'.format(test['id'], test['question']))
    print(f'🤖 {answer}')


def print_react_result(test: dict[str, Any], result: dict[str, Any]) -> None:
    print('\n🤖 [REACT — TEST {}] {}'.format(test['id'], test['question']))
    for item in result['trace']:
        print('\n🔄 Bước {}'.format(item['iteration']))
        print('🛠️ Action: {}'.format(item['action']))
        print(
            '📥 Action Input: '
            + json.dumps(item['action_input'], ensure_ascii=False)
        )
        print(
            '👁️ Observation: '
            + json.dumps(item['observation'], ensure_ascii=False)
        )
    print('\n🏁 Final Answer: {}'.format(result['answer']))
    if result['error']:
        print('⚠️ Error: ' + json.dumps(result['error'], ensure_ascii=False))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Cupid Chatbot và ReAct Agent')
    parser.add_argument(
        '--mode',
        choices=('baseline', 'react', 'all'),
        default='react',
    )
    parser.add_argument('--test', type=int, choices=range(1, 6), default=4)
    parser.add_argument(
        '--provider',
        choices=('mock', 'openai', 'gemini', 'anthropic', 'openrouter'),
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    provider = get_llm_provider(args.provider)
    tests = {item['id']: item for item in load_test_cases()}
    test = tests[args.test]
    model_name = getattr(provider, 'model_name', 'Offline Mock Mode')

    print('=' * 60)
    print('💘 CUPID AGENT — CHATBOT BASELINE VS REACT AGENT')
    print('=' * 60)
    print(
        f'🔌 Provider: {provider.__class__.__name__} | Model: {model_name}'
    )

    if args.mode in ('baseline', 'all'):
        print_baseline_result(test, run_baseline_chatbot(test['question'], provider))
    if args.mode in ('react', 'all'):
        print_react_result(test, run_react_agent(test['question'], provider))
