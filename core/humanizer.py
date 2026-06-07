import re
import random

# 1인칭 마커 — 문단 첫 문장 앞에 삽입 가능한 표현
_FIRST_PERSON_MARKERS = [
    "솔직히 말하면, ",
    "제 경험으로는, ",
    "실제로 해보니까, ",
    "제가 직접 써봤는데, ",
    "겪어보니 알게 된 건데, ",
    "이건 정말 중요한 포인트인데, ",
]

# 격식체 → 구어체 연결어 치환
_FORMAL_TO_COLLOQUIAL = [
    (r"따라서\b", "그래서"),
    (r"그러므로\b", "그러니까"),
    (r"또한\b", "그리고"),
    (r"그러나\b", "근데"),
    (r"하지만\b", "그런데"),
    (r"반면에\b", "반면"),
    (r"결론적으로\b", "정리하자면"),
    (r"이러한\b", "이런"),
    (r"해당\b", "이"),
]

# 문단 전환구 — <p> 태그 사이에 삽입
_TRANSITION_PHRASES = [
    "<p>사실 이 부분에서 많은 분들이 헷갈려하시더라고요.</p>",
    "<p>제가 처음 접했을 때도 비슷한 고민을 했었어요.</p>",
    "<p>이걸 알고 나면 생각보다 훨씬 쉬워집니다.</p>",
    "<p>실제로 주변에서도 자주 묻는 내용이에요.</p>",
]


def apply_persona(html_body: str) -> str:
    """
    HTML 본문에 인간화 페르소나를 적용한다.
    - 격식체 연결어 → 구어체
    - 일부 <p> 시작에 1인칭 마커 삽입
    - 문단 사이에 자연스러운 전환구 삽입
    """
    random.seed(42)

    # 1. 격식체 → 구어체
    for pattern, replacement in _FORMAL_TO_COLLOQUIAL:
        html_body = re.sub(pattern, replacement, html_body)

    # 2. <p> 태그 내 첫 문장에 1인칭 마커 삽입 (약 30% 확률)
    def _inject_marker(m: re.Match) -> str:
        if random.random() < 0.3:
            marker = random.choice(_FIRST_PERSON_MARKERS)
            inner = m.group(1)
            # 이미 마커로 시작하면 스킵
            if any(inner.startswith(mk.strip()) for mk in _FIRST_PERSON_MARKERS):
                return m.group(0)
            return f"<p>{marker}{inner}</p>"
        return m.group(0)

    html_body = re.sub(r"<p>((?!<).+?)</p>", _inject_marker, html_body, flags=re.DOTALL)

    # 3. </h2> 또는 </h3> 뒤에 전환구 삽입 (약 40% 확률)
    def _inject_transition(m: re.Match) -> str:
        if random.random() < 0.4:
            phrase = random.choice(_TRANSITION_PHRASES)
            return m.group(0) + "\n" + phrase
        return m.group(0)

    html_body = re.sub(r"</h[23]>", _inject_transition, html_body)

    return html_body
