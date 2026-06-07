import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
import anthropic
import json
import re

load_dotenv()

app = Flask(__name__, template_folder='../templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    topic = (data.get('topic') or '').strip()
    main_keyword = (data.get('main_keyword') or '').strip()
    sub_keywords = (data.get('sub_keywords') or '').strip()
    method = data.get('method', 'traditional')
    humanize = bool(data.get('humanize', False))

    if not topic or not main_keyword:
        return jsonify({'error': '주제와 메인 키워드를 입력해주세요.'}), 400

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY가 설정되지 않았습니다.'}), 500

    def stream():
        try:
            if method == 'traditional':
                from prompts.traditional_seo import build_prompt
            else:
                from prompts.aeo import build_prompt

            system_prompt, user_prompt = build_prompt(topic, main_keyword, sub_keywords)
            client = anthropic.Anthropic(api_key=api_key)

            full_text = ''
            with client.messages.stream(
                model='claude-sonnet-4-6',
                max_tokens=4096,
                system=system_prompt,
                messages=[{'role': 'user', 'content': user_prompt}],
            ) as s:
                for chunk in s.text_stream:
                    full_text += chunk
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"

            # 인간화 후처리
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
