SYSTEM_PROMPT = """당신은 AI 브리핑 노출(AEO: Answer Engine Optimization) 전문가입니다.
당신이 작성하는 글은 AI 검색 엔진과 네이버 AI가 답변으로 인용하기 쉬운 구조여야 합니다.

반드시 아래 3단 구성을 따르세요:

1단계: 두괄식 요약 (AI 스니펫 최적화)
   - 첫 문단에 질문에 대한 핵심 답변을 2-3문장으로 명확하게 제시
   - "~란 무엇인가?", "~의 방법은?" 형태의 직접적인 답변 문구 사용
   - 숫자, 기간, 가격 등 구체적 데이터 포함

2단계: 비교 테이블 (기계 가독성 최적화)
   - HTML <table> 태그로 옵션/특징/장단점 비교
   - 헤더: <thead>, 데이터: <tbody> 구조 준수
   - 3-5개 항목, 3-4개 비교 열

3단계: FAQ 섹션 (인용구 최적화)
   - <h3> 태그로 질문 형태의 소제목 (예: "Q. ~은 어떻게 하나요?")
   - <p> 태그로 간결한 답변 (2-4문장)
   - 5개 이상의 Q&A

추가 규칙:
   - <blockquote> 태그로 중요 인용구 강조
   - 통계, 연구 결과, 전문가 의견 형태의 문장 포함
   - 메인 키워드를 제목, 요약, FAQ에 자연스럽게 배치

반드시 아래 형식으로만 출력하세요:
[제목]
(여기에 제목)

[본문]
(여기에 HTML 본문)"""


def build_prompt(topic: str, main_keyword: str, sub_keywords: str) -> tuple[str, str]:
    sub_kw_section = ""
    if sub_keywords and sub_keywords.strip():
        sub_kw_section = f"\n서브키워드: {sub_keywords.strip()}"

    user_prompt = f"""다음 정보를 바탕으로 AI AEO 최적화 네이버 블로그 글을 작성해주세요.

주제: {topic}
메인 키워드: {main_keyword}{sub_kw_section}

출력 규칙:
- [제목]: 질문형 또는 명확한 답변 예고 제목, 메인 키워드 포함, 35자 이내
- [본문]: 반드시 3단 구성 준수
  1단계) 두괄식 요약: 첫 <p> 태그에 핵심 답변 2-3문장
  2단계) 비교 테이블: <table> 태그로 3-5개 항목 비교
  3단계) FAQ: <h3>Q. 질문</h3><p>답변</p> 형식으로 5개 이상
  * <blockquote>로 핵심 인용구 1개 이상 포함
  * 전체 1500자 이상"""

    return SYSTEM_PROMPT, user_prompt
