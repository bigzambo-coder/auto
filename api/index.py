import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
import requests as http_req
import json
import re
import asyncio

if sys.platform == 'win32' and hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore[attr-defined]

load_dotenv()

app = Flask(__name__, template_folder='../templates')

_GEMINI_URL = (
    'https://generativelanguage.googleapis.com'
    '/v1beta/models/gemini-2.0-flash:streamGenerateContent'
)


@app.route('/')
def index():
    api_key_set = bool(os.getenv('GEMINI_API_KEY'))
    return render_template('index.html', api_key_set=api_key_set)


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    topic        = (data.get('topic') or '').strip()
    main_keyword = (data.get('main_keyword') or '').strip()
    sub_keywords = (data.get('sub_keywords') or '').strip()
    method       = data.get('method', 'traditional')
    humanize     = bool(data.get('humanize', False))

    if not topic or not main_keyword:
        return jsonify({'error': '주제와 메인 키워드를 입력해주세요.'}), 400

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'GEMINI_API_KEY가 설정되지 않았습니다.'}), 500

    def stream():
        try:
            if method == 'traditional':
                from prompts.traditional_seo import build_prompt
            else:
                from prompts.aeo import build_prompt

            system_prompt, user_prompt = build_prompt(topic, main_keyword, sub_keywords)

            payload = {
                'systemInstruction': {'parts': [{'text': system_prompt}]},
                'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
                'generationConfig': {'maxOutputTokens': 4096},
            }

            full_text = ''
            with http_req.post(
                _GEMINI_URL,
                params={'key': api_key, 'alt': 'sse'},
                json=payload,
                stream=True,
                timeout=55,
            ) as resp:
                if not resp.ok:
                    err = resp.text[:600]
                    yield f"data: {json.dumps({'error': f'{resp.status_code}: {err}'}, ensure_ascii=False)}\n\n"
                    return

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith('data:'):
                        continue
                    raw = line[5:].strip()
                    if raw == '[DONE]':
                        break
                    try:
                        chunk = json.loads(raw)
                        text = (
                            chunk.get('candidates', [{}])[0]
                                 .get('content', {})
                                 .get('parts', [{}])[0]
                                 .get('text', '')
                        )
                        if text:
                            full_text += text
                            yield f"data: {json.dumps({'chunk': text}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        pass

            if humanize:
                from core.humanizer import apply_persona
                body_match = re.search(r'\[본문\]\s*\n(.+)', full_text, re.DOTALL)
                if body_match:
                    humanized = apply_persona(body_match.group(1).strip())
                    yield f"data: {json.dumps({'humanized_body': humanized}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        stream(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@app.route('/publish', methods=['POST'])
def publish():
    try:
        from core.naver_publisher import publish_to_naver
    except ImportError:
        return jsonify({'error': 'Playwright가 설치되지 않았습니다. 로컬 환경에서만 발행 가능합니다.'}), 501

    data = request.get_json()
    title = (data.get('title') or '').strip()
    body  = (data.get('body') or '').strip()

    if not title or not body:
        return jsonify({'error': '제목과 본문이 없습니다.'}), 400

    try:
        url = asyncio.run(publish_to_naver(title, body))
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
