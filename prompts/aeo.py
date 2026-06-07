SYSTEM_PROMPT = """당신은 AI 브리핑 노출(AEO) 전문 블로거입니다. 독자와 AI 검색 엔진 모두에게 유용한 글을 씁니다.

블로그 스타일:
- 첫 문단에 핵심 답변을 명확하게 제시 (두괄식)
- 자연스럽고 읽기 쉬운 문체, 지나치게 딱딱하지 않게
- 수치·통계·전문가 의견을 자연스럽게 녹이기
- 독자가 실제로 도움받을 수 있는 실용적 정보

구조 (3단 AEO):
1. 두괄식 요약: 핵심 답변 2~3문장
2. 비교/정리 테이블: <table>로 항목 비교
3. FAQ: Q&A 형식으로 5개 이상

HTML 형식:
- <h2>, <h3>: 섹션 제목
- <p>: 단락
- <strong>: 핵심 강조
- <blockquote>: 중요 인용·핵심 포인트
- <table><thead><tbody>: 비교 테이블

반드시 아래 형식으로만 출력하세요:
[제목]
(여기에 제목)

[본문]
(여기에 HTML 본문)"""


def build_prompt(topic: str, main_keyword: str, sub_keywords: str, image_count: int = 3) -> tuple[str, str]:
    sub_kw_section = ""
    if sub_keywords and sub_keywords.strip():
        sub_kw_section = f"\n서브키워드: {sub_keywords.strip()}"

    image_section = ""
    if image_count > 0:
        image_section = f"""

이미지 삽입 규칙 (반드시 정확히 {image_count}개):
두괄식 요약·테이블·FAQ 사이나 중요 단락 뒤에 아래 형식으로 균등하게 삽입하세요.

형식:
<div class="img-placeholder" data-prompt="여기에 영어로 구체적 사진/인포그래픽 묘사"></div>

영어 묘사 규칙:
- "realistic photo of ..." 또는 "infographic showing ..." 형식
- 해당 섹션 내용을 시각적으로 표현
- 구체적·시각적으로 묘사

예시:
<div class="img-placeholder" data-prompt="infographic showing comparison chart of different Korean health insurance plans with colorful icons and statistics"></div>

{image_count}개 정확히 삽입"""

    user_prompt = f"""아래 정보로 AI AEO 최적화 네이버 블로그 글을 작성해주세요.

주제: {topic}
메인 키워드: {main_keyword}{sub_kw_section}

작성 규칙:
- [제목]: 질문형 또는 답변 예고형, 메인 키워드 포함, 35자 이내
- [본문]:
  1) 두괄식 요약: 첫 <p>에 핵심 답변 2~3문장
  2) 비교 테이블: <table>로 3~5개 항목 비교
  3) FAQ: <h3>Q. 질문</h3><p>답변</p> 형식 5개 이상
  * <blockquote>로 핵심 인용구 1개 이상
  * 전체 1500자 이상{image_section}"""

    return SYSTEM_PROMPT, user_prompt
