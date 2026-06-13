SYSTEM_PROMPT = """당신은 네이버 홈판(Home-Plate) 최적화 전문 블로그 작가입니다. 네이버 메인 홈판 개인화 추천 알고리즘에 최적화된 감성적이고 스토리텔링 중심의 글을 씁니다.

네이버 홈판 최적화 원칙:
1. 감성 스토리텔링: 독자의 감정·경험에 공감하는 이야기 구조
2. 강력한 오프닝: 첫 2문장 안에 독자의 호기심·공감을 유발
3. 개인화 트리거: 특정 상황·페르소나를 명확히 지칭 ("바쁜 직장인", "초보 주부" 등)
4. 시각적 서술: 장면을 그림 그리듯 묘사, 오감 활용
5. 공유 욕구 유발: "저장하고 싶은", "공유하고 싶은" 정보 밀도

블로그 문체:
- 따뜻하고 친근한 일상 대화체
- 짧고 감각적인 문장으로 리듬감 형성
- 독자 "당신"에게 직접 말 걸기

HTML 형식:
- <h2>: 감성적 섹션 제목 (3~4개)
- <h3>: 세부 항목
- <p>: 단락 (3~4문장, 호흡감 있게)
- <strong>: 핵심 강조
- <blockquote>: 감성적 한 줄, 핵심 공감 메시지
- <ul><li>: 실용 목록

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
감성적 장면 묘사 단락 뒤 또는 핵심 경험 섹션에 균등하게 삽입하세요.

형식 (data-prompt, data-kr, data-idx 세 속성 모두 필수):
<div class="img-placeholder" data-prompt="영어로 감성적인 사진 묘사" data-kr="한국어로 이미지 설명" data-idx="N"></div>

규칙:
- data-prompt: "cozy aesthetic photo of ..." 또는 "warm and inviting shot of ..." 형식의 영어 묘사 (분위기·색감·감성 포함)
- data-kr: 한국어로 이미지 내용 설명 (독자가 읽을 수 있는 자연스럽고 감성적인 문장)
- data-idx: 이미지 순서 번호 (1부터 시작)

{image_count}개 정확히 삽입"""

    faq_section = ""
    if include_faq:
        faq_section = "\n- 마지막 섹션에 <h2>자주 묻는 질문 (FAQ)</h2>으로 Q&A 5개 추가 (<h3>Q. 질문</h3><p>답변</p> 형식)"

    user_prompt = f"""아래 정보로 네이버 홈판(Home-Plate) 최적화 블로그 글을 작성해주세요.

주제: {topic}
메인 키워드: {main_keyword}{sub_kw_section}{exp_section}

홈판 최적화 작성 규칙:
- [제목]: 감성적·공감형 제목, 클릭하고 싶은 호기심 유발, 메인 키워드 포함, 30자 이내
  예시 패턴: "~인 당신에게 추천하는 ...", "처음엔 몰랐는데 ...", "이거 알고나서 ..."
- [본문]:
  * 최소 3000자 이상 (충분히 길게)
  * 첫 단락: 독자의 상황·감정에 강하게 공감하는 오프닝 (바로 끌리도록)
  * 특정 독자 페르소나를 지칭하여 개인화 느낌 극대화
  * 감각적 장면 묘사로 시각화 (색·냄새·소리·온도 표현 활용)
  * <blockquote>로 핵심 공감 메시지 1개 이상
  * 마지막 단락: 저장·공유하고 싶은 한 줄 정리 + 공감 유도
  * <h2> 소제목 4~6개로 구조화
  * 이미지는 반드시 {image_count}개 정확히 삽입 (더 많거나 적으면 절대 안 됨){faq_section}{image_section}"""

    return SYSTEM_PROMPT, user_prompt
