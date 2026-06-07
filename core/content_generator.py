import os
import re
import anthropic
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def _parse_response(text: str) -> dict:
    """Claude 응답에서 [제목]과 [본문] 파싱."""
    title = ""
    body = ""

    title_match = re.search(r"\[제목\]\s*\n(.+?)(?=\n\[본문\]|\Z)", text, re.DOTALL)
    body_match = re.search(r"\[본문\]\s*\n(.+)", text, re.DOTALL)

    if title_match:
        title = title_match.group(1).strip()
    if body_match:
        body = body_match.group(1).strip()

    # 파싱 실패 시 전체 텍스트로 폴백
    if not title:
        lines = text.strip().split("\n")
        title = lines[0].strip()
    if not body:
        body = text.strip()

    return {"title": title, "body": body}


def generate_content(
    topic: str,
    main_keyword: str,
    sub_keywords: str,
    method: str,
    humanize: bool,
) -> dict:
    """
    Claude API로 블로그 콘텐츠 생성.

    Args:
        topic: 블로그 주제
        main_keyword: 메인 키워드
        sub_keywords: 서브키워드 (쉼표 구분, 선택)
        method: "traditional" | "aeo"
        humanize: True면 인간화 페르소나 후처리 적용

    Returns:
        {"title": str, "body": str}
    """
    if method == "traditional":
        from prompts.traditional_seo import build_prompt
    else:
        from prompts.aeo import build_prompt

    system_prompt, user_prompt = build_prompt(topic, main_keyword, sub_keywords)

    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text
    result = _parse_response(raw_text)

    if humanize:
        from core.humanizer import apply_persona
        result["body"] = apply_persona(result["body"])

    return result
