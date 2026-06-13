SYSTEM_PROMPT = """당신은 인사이트 엣지(Insight Edge) 전략 블로그 작가입니다. 실시간 트렌드와 데이터 기반으로 독자가 미처 몰랐던 선제적 정보를 제공합니다.

인사이트 엣지 원칙:
1. 시의성: 지금 이 순간 독자가 가장 궁금해하는 정보를 먼저 제시
2. 데이터 우위: 수치·통계·비교 분석으로 정보 우위 선점
3. 예측·전망: 단순 현황 설명을 넘어 향후 방향 제시
4. 비교 분석: 선택지·옵션을 명확히 비교하여 의사결정 도움

블로그 문체:
- 명확하고 직관적인 문체, 핵심부터 전달
- "~입니다"보다 "~예요", "~거든요" 등 자연스러운 어미 활용
- 독자의 고민을 대신 해결해 주는 어조

HTML 형식:
- <h2>: 섹션 제목 (3~4개)
- <h3>: 세부 비교 항목
- <p>: 단락
- <strong>: 핵심 수치·결론
- <blockquote>: 핵심 인사이트 한 줄 요약
- <ul><li>: 비교/목록
- <table>: 옵션 비교 테이블 (선택)

반드시 아래 형식으로만 출력하세요:
[제목]
(여기에 제목)

[본문]
(여기에 HTML 본문)

[해시태그]
#태그1 #태그2 ... (메인키워드 포함 9~12개, 공백으로 구분)"""


def build_prompt(topic: str, main_keyword: str, sub_keywords: str, image_count: int = 3, include_faq: bool = False, user_experience: str = '') -> tuple[str, str]:
    sub_kw_section = ""
    if sub_keywords and sub_keywords.strip():
        sub_kw_section = f"\n서브키워드: {sub_keywords.strip()}"

    exp_section = f"\n\n사용자 실제 경험 (반드시 본문에 자연스럽게 녹여주세요):\n{user_experience.strip()}" if user_experience and user_experience.strip() else ""

    image_section = ""
    if image_count > 0:
        image_section = f"""

이미지 삽입 규칙 (반드시 정확히 {image_count}개):
핵심 데이터 단락 뒤 또는 비교 테이블 앞뒤에 균등하게 삽입하세요.

형식 (data-prompt, data-kr, data-idx 세 속성 모두 필수):
<div class="img-placeholder" data-prompt="영어로 구체적 사진/인포그래픽 묘사" data-kr="한국어로 이미지 설명" data-idx="N"></div>

규칙:
- data-prompt: "realistic photo of ..." 또는 "data visualization of ..." 형식의 영어 묘사
- data-kr: 한국어로 이미지 내용 설명 (독자가 읽을 수 있는 자연스러운 문장)
- data-idx: 이미지 순서 번호 (1부터 시작)

{image_count}개 정확히 삽입"""

    faq_section = ""
    if include_faq:
        faq_section = "\n- 마지막 섹션에 <h2>자주 묻는 질문 (FAQ)</h2>으로 Q&A 5개 추가 (<h3>Q. 질문</h3><p>답변</p> 형식)"

    user_prompt = f"""아래 정보로 인사이트 엣지 전략의 네이버 블로그 글을 작성해주세요.

주제: {topic}
메인 키워드: {main_keyword}{sub_kw_section}{exp_section}

인사이트 엣지 작성 규칙:
- [제목]: "2025 최신", "몰랐던", "비교 분석" 등 시의성·정보 우위 표현 활용, 메인 키워드 포함, 35자 이내
- [본문]:
  * 텍스트 본문 최소 4000자 이상 (이미지 placeholder 태그는 글자 수에 포함하지 말 것 — 이미지 장수와 무관하게 텍스트 분량 동일)
  * 첫 단락: 독자가 바로 행동하거나 판단할 수 있는 핵심 인사이트 제시
  * 데이터·수치·최신 트렌드 반영 (구체적 수치 최소 5개 이상)
  * 비교 분석 섹션 포함 (옵션 A vs B, 또는 장단점 비교)
  * 향후 전망 또는 독자 행동 제언으로 마무리
  * <blockquote>로 핵심 인사이트 1줄 요약 1개 이상
  * <h2> 소제목 4~6개로 구조화, 각 섹션마다 300자 이상 충분한 텍스트 작성
  * 이미지는 반드시 {image_count}개 정확히 삽입 (더 많거나 적으면 절대 안 됨){faq_section}{image_section}"""

    return SYSTEM_PROMPT, user_prompt
