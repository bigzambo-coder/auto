SYSTEM_PROMPT = """당신은 네이버 인기 블로거입니다. 독자가 끝까지 읽고 싶은, 자연스럽고 진정성 있는 블로그 글을 씁니다.

블로그 글쓰기 원칙:
1. 도입부: 독자가 공감할 상황·경험으로 시작. "혹시 이런 경험 있으신가요?", "솔직히 말하면..." 처럼 자연스럽게
2. 본론: 소제목마다 직접 경험한 것처럼 구체적으로 서술. 수치·날짜·가격·장소명 포함
3. 문체: "저는", "제가", "사실", "솔직히" 등 1인칭 구어체. 딱딱한 나열 금지
4. 소제목: 흥미를 끄는 표현 ("이게 진짜 달랐던 이유", "처음엔 몰랐는데..." 등)
5. 마무리: 핵심 한 줄 정리 + 댓글·공감 유도 문장

HTML 형식:
- <h2>: 섹션 제목 (3~4개)
- <h3>: 세부 항목
- <p>: 단락 (자연스러운 호흡, 2~5문장)
- <strong>: 핵심 강조
- <ul><li>: 목록 정보

C-Rank/D.I.A.+ 최적화: 메인 키워드를 제목·첫 단락·마지막 단락에 자연스럽게 배치

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

    exp_section = ""
    if user_experience and user_experience.strip():
        exp_section = f"\n\n사용자 실제 경험 (반드시 본문에 자연스럽게 녹여주세요):\n{user_experience.strip()}"

    faq_section = ""
    if include_faq:
        faq_section = "\n  * 마지막 섹션에 <h2>자주 묻는 질문 (FAQ)</h2>으로 Q&A 5개 추가 (<h3>Q. 질문</h3><p>답변</p> 형식)"

    image_section = ""
    if image_count > 0:
        image_section = f"""

이미지 삽입 규칙 (반드시 정확히 {image_count}개):
각 <h2> 소제목 바로 아래 또는 핵심 단락 뒤에 아래 형식으로 삽입하세요.
이미지는 본문 전체에 균등하게 배치하고, 해당 섹션 내용을 시각적으로 표현해야 합니다.

형식:
<div class="img-placeholder" data-prompt="여기에 영어로 구체적 사진 묘사"></div>

영어 묘사 규칙:
- "realistic photo of ..." 또는 "close-up of ..." 형식
- 주제·섹션과 직접 관련된 장면, 색상·분위기·배경 포함
- 구체적이고 생생하게

예시:
<div class="img-placeholder" data-prompt="realistic photo of a steaming bowl of Korean budae jjigae with spam, sausages and ramen noodles in rich red broth, rustic wooden table setting"></div>

{image_count}개 정확히 삽입 (많거나 적으면 안 됨)"""

    user_prompt = f"""아래 정보로 네이버 블로그 글을 작성해주세요.

주제: {topic}
메인 키워드: {main_keyword}{sub_kw_section}{exp_section}

작성 규칙:
- [제목]: 메인 키워드 포함, 클릭하고 싶은 제목, 30자 이내
- [본문]:
  * 최소 1500자
  * 1인칭 블로그 문체 (경험담 형식)
  * <h2> 소제목 3~4개
  * 첫 단락에 메인 키워드 자연 포함
  * 마지막 단락에서 독자에게 말 걸기{faq_section}{image_section}"""

    return SYSTEM_PROMPT, user_prompt
