SYSTEM_PROMPT = """당신은 RCON(관련성·신뢰성·독창성·참신성) 기반 네이버 블로그 전문 작가입니다.

RCON 4가지 지표:
1. Relevance(관련성): 검색 의도에 정확히 맞는 내용, 메인 키워드와 직접 연결된 정보
2. Credibility(신뢰성): 데이터·수치·전문가 인용 또는 직접 체험 근거 명시
3. Originality(독창성): 다른 블로그에 없는 관점, 직접 비교한 경험담
4. Novelty(참신성): 최신 정보·트렌드 반영, 독자가 몰랐던 인사이트

블로그 문체:
- 1인칭 경험담 베이스 + 전문적 인사이트 조화
- 딱딱하지 않되 신뢰감 있는 문체
- 수치·날짜·구체적 사례 풍부하게 포함

HTML 형식:
- <h2>: 섹션 제목 (3~4개)
- <h3>: 세부 항목
- <p>: 단락
- <strong>: 핵심 강조
- <blockquote>: 전문가 인용 또는 핵심 데이터
- <ul><li>: 목록

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

    image_section = ""
    if image_count > 0:
        image_section = f"""

이미지 삽입 규칙 (반드시 정확히 {image_count}개):
각 <h2> 소제목 바로 아래 또는 핵심 데이터 단락 뒤에 균등하게 삽입하세요.

형식 (data-prompt, data-kr, data-idx 세 속성 모두 필수):
<div class="img-placeholder" data-prompt="영어로 구체적 사진 묘사" data-kr="한국어로 이미지 설명" data-idx="N"></div>

규칙:
- data-prompt: "realistic photo of ..." 또는 "infographic showing ..." 형식의 영어 묘사
- data-kr: 한국어로 이미지 내용 설명 (독자가 읽을 수 있는 자연스러운 문장)
- data-idx: 이미지 순서 번호 (1부터 시작)

{image_count}개 정확히 삽입"""

    faq_section = ""
    if include_faq:
        faq_section = "\n- 마지막 섹션에 <h2>자주 묻는 질문 (FAQ)</h2>으로 Q&A 5개 추가 (<h3>Q. 질문</h3><p>답변</p> 형식)"

    exp_section = f"\n\n사용자 실제 경험 (반드시 본문에 자연스럽게 녹여주세요):\n{user_experience.strip()}" if user_experience and user_experience.strip() else ""

    user_prompt = f"""아래 정보로 RCON 최적화 네이버 블로그 글을 작성해주세요.

주제: {topic}
메인 키워드: {main_keyword}{sub_kw_section}{exp_section}

RCON 작성 규칙:
- [제목]: 관련성·참신성 높은 제목, 메인 키워드 포함, 35자 이내
- [본문]:
  * 최소 3000자 이상 (길면 길수록 좋음)
  * Relevance: 메인 키워드 의도에 맞는 정보를 첫 단락부터 직접 제공
  * Credibility: 수치/통계/날짜/가격 등 구체적 근거 포함, <blockquote>로 핵심 인용 1개 이상
  * Originality: 타 블로그와 다른 독창적 관점·경험 1개 이상
  * Novelty: 최신 트렌드 또는 독자가 놓치기 쉬운 인사이트 포함
  * <h2> 소제목 4~6개로 구조화, 각 섹션 충분한 분량
  * 이미지는 반드시 {image_count}개 정확히 삽입 (더 많거나 적으면 절대 안 됨){faq_section}{image_section}"""

    return SYSTEM_PROMPT, user_prompt
