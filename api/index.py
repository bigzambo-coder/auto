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
    '/v1beta/models/gemini-2.5-flash:streamGenerateContent'
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
    image_count  = max(0, min(7, int(data.get('image_count', 3))))
    include_faq  = bool(data.get('include_faq', False))

    if not topic or not main_keyword:
        return jsonify({'error': '주제와 메인 키워드를 입력해주세요.'}), 400

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'GEMINI_API_KEY가 설정되지 않았습니다.'}), 500

    user_experience = (data.get('user_experience') or '').strip()

    def stream():
        try:
            if method == 'rcon':
                from prompts.rcon import build_prompt
            elif method == 'aeo':
                from prompts.aeo import build_prompt
            elif method == 'insight_edge':
                from prompts.insight_edge import build_prompt
            elif method == 'home_plate':
                from prompts.home_plate import build_prompt
            else:
                from prompts.traditional_seo import build_prompt

            import inspect
            sig = inspect.signature(build_prompt)
            kwargs = {}
            if 'include_faq' in sig.parameters:
                kwargs['include_faq'] = include_faq
            if 'user_experience' in sig.parameters:
                kwargs['user_experience'] = user_experience
            system_prompt, user_prompt = build_prompt(topic, main_keyword, sub_keywords, image_count, **kwargs)

            payload = {
                'systemInstruction': {'parts': [{'text': system_prompt}]},
                'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
                'generationConfig': {'maxOutputTokens': 16384},
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

                resp.encoding = 'utf-8'
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


_GEMINI_SIMPLE_URL = (
    'https://generativelanguage.googleapis.com'
    '/v1beta/models/gemini-2.5-flash:generateContent'
)

def _gemini_call(prompt_text, max_tokens=512):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None, 'GEMINI_API_KEY 없음'
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt_text}]}],
        'generationConfig': {'maxOutputTokens': max_tokens},
    }
    resp = http_req.post(_GEMINI_SIMPLE_URL, params={'key': api_key}, json=payload, timeout=25)
    resp.encoding = 'utf-8'
    if not resp.ok:
        return None, resp.text[:300]
    data = resp.json()
    text = data['candidates'][0]['content']['parts'][0]['text']
    return text, None


@app.route('/suggest_experience', methods=['POST'])
def suggest_experience():
    data = request.get_json()
    topic        = (data.get('topic') or '').strip()
    main_keyword = (data.get('main_keyword') or '').strip()
    prompt = f"""주제 '{topic}', 키워드 '{main_keyword}'로 네이버 블로그를 작성하려 합니다.
블로거가 실제 경험했을 법한 구체적이고 생생한 개인 경험담을 아래 조건에 맞게 작성해주세요.

조건:
- 8~10문장, 자연스럽게 이어지는 완성된 글로 출력 (중간에 절대 끊지 말 것)
- 1인칭 구어체 ("저는", "제가", "솔직히", "사실", "처음엔" 포함)
- 처음 접한 계기·상황 (날짜·장소·상황 구체적으로)
- 사용/경험 과정에서 느낀 점 (구체적 에피소드, 감정, 놀랐던 순간)
- 주변 반응이나 비교 경험 (가족·친구·동료 등)
- 결과적 만족·아쉬운 점 (솔직하게, 단점도 포함)
- 독자가 공감하고 몰입할 수 있는 생생한 묘사
- 설명 없이 경험담 본문만 출력 (제목·소제목 없이 자연스럽게 이어지는 글)
- 마크다운 서식(**볼드**, *이탤릭*, # 제목 등) 절대 사용 금지 — 순수 텍스트만 출력"""
    text, err = _gemini_call(prompt, 1200)
    if err:
        return jsonify({'error': err}), 500
    return jsonify({'experience': text})


@app.route('/analyze', methods=['POST'])
def analyze():
    data   = request.get_json()
    title  = (data.get('title') or '').strip()
    body   = (data.get('body') or '').strip()
    method = data.get('method', 'traditional')
    humanize = bool(data.get('humanize', False))

    method_names = {
        'traditional': 'C-Rank/D.I.A.+',
        'rcon': 'RCON',
        'aeo': 'AEO',
        'insight_edge': '인사이트 엣지',
        'home_plate': '네이버 홈판',
    }
    mn = method_names.get(method, 'C-Rank/D.I.A.+')

    humanize_inst = '③ humanize: 인간화 페르소나 적용 분석 (2~3문장)' if humanize else '③ humanize: null'

    humanize_field = '"humanize": "인간화 페르소나 적용 분석 2~3문장"' if humanize else '"humanize": null'

    prompt = f"""다음 네이버 블로그 글을 {mn} SEO 관점에서 분석하세요.

제목: {title}
본문 (일부): {body[:1200]}

아래 JSON 형식으로만 출력하세요. 백틱(```)이나 다른 텍스트 없이 JSON만:
{{
  "c_rank": "C-Rank & D.I.A. 관점에서 이 글의 신뢰도·전문성·경험치 평가 (2~3문장)",
  "content_quality": "콘텐츠 구조·가독성·정보 밀도 평가 (2~3문장)",
  "user_satisfaction": "사용자 체류 시간·공감·재방문 유도 요소 평가 (2~3문장)",
  {humanize_field}
}}"""

    text, err = _gemini_call(prompt, 2500)
    if err:
        return jsonify({'error': err}), 500

    # 마크다운 코드블록 및 불필요한 래핑 제거
    text = re.sub(r'```[a-zA-Z]*', '', text)
    text = re.sub(r'```', '', text).strip()
    json_match = re.search(r'\{[\s\S]+\}', text)
    if not json_match:
        return jsonify({'error': f'분석 파싱 실패 (응답: {text[:200]})'}), 500
    try:
        result = json.loads(json_match.group())
        return jsonify(result)
    except json.JSONDecodeError as e:
        raw = json_match.group()
        return jsonify({'error': f'JSON 파싱 오류: {str(e)} | 원문: {raw[:200]}'}), 500


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
