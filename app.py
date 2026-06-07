import asyncio
import os
import sys

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Windows asyncio 이벤트 루프 호환성 설정
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

st.set_page_config(
    page_title="네이버 블로그 자동 발행기",
    page_icon="✍️",
    layout="wide",
)

st.title("📝 네이버 블로그 자동 발행기")
st.caption("SEO 최적화된 블로그 글을 자동으로 생성하고 네이버에 발행합니다.")

st.divider()

# ─── 입력 영역 ────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    seo_method = st.radio(
        "SEO 방식 선택",
        options=["기존방식 (C-Rank/D.I.A.+)", "AI AEO"],
        help=(
            "기존방식: 진정성·전문성 최우선, 네이버 C-Rank/D.I.A.+ 알고리즘 대응\n\n"
            "AI AEO: 두괄식 요약→비교 테이블→FAQ 구조, AI 인식률 극대화"
        ),
    )
    humanize = st.checkbox(
        "인간화 페르소나 적용 (AI 탐지 우회)",
        help="구어체, 1인칭 마커, 자연스러운 전환구를 추가해 사람이 쓴 글처럼 만듭니다.",
    )

with col_right:
    topic = st.text_input(
        "주제",
        placeholder="예: 강남 맛집 추천",
        help="블로그 글의 주제를 입력하세요.",
    )
    main_keyword = st.text_input(
        "메인 키워드",
        placeholder="예: 강남 파스타 맛집",
        help="검색 최적화할 핵심 키워드를 입력하세요.",
    )
    sub_keywords = st.text_input(
        "서브키워드 (선택, 쉼표로 구분)",
        placeholder="예: 강남역 이탈리안, 강남 데이트 코스",
        help="추가로 노출되길 원하는 서브 키워드를 입력하세요.",
    )

st.divider()

# ─── 액션 버튼 ───────────────────────────────────────────────
btn_col1, btn_col2, _ = st.columns([1, 1, 2])

with btn_col1:
    generate_btn = st.button(
        "콘텐츠 생성",
        type="primary",
        disabled=not (topic and main_keyword),
        use_container_width=True,
    )

with btn_col2:
    publish_btn = st.button(
        "네이버 블로그 발행",
        type="secondary",
        disabled="generated_title" not in st.session_state,
        use_container_width=True,
    )

# 필수 항목 안내
if not topic or not main_keyword:
    st.info("주제와 메인 키워드를 입력하면 '콘텐츠 생성' 버튼이 활성화됩니다.")

# ─── 콘텐츠 생성 ─────────────────────────────────────────────
if generate_btn:
    method = "traditional" if "기존방식" in seo_method else "aeo"

    with st.spinner("Claude API로 콘텐츠를 생성하는 중입니다..."):
        try:
            from core.content_generator import generate_content

            result = generate_content(topic, main_keyword, sub_keywords, method, humanize)
            st.session_state["generated_title"] = result["title"]
            st.session_state["generated_body"] = result["body"]
            st.success("콘텐츠가 생성되었습니다. 아래에서 확인 후 발행하세요.")
        except Exception as e:
            st.error(f"콘텐츠 생성 실패: {e}")

# ─── 미리보기 ─────────────────────────────────────────────────
if "generated_title" in st.session_state:
    st.subheader("생성된 콘텐츠 미리보기")

    new_title = st.text_input(
        "제목 (수정 가능)",
        value=st.session_state["generated_title"],
        key="editable_title",
    )
    new_body = st.text_area(
        "본문 (수정 가능)",
        value=st.session_state["generated_body"],
        height=400,
        key="editable_body",
    )

    # 수정된 내용 세션에 반영
    st.session_state["generated_title"] = new_title
    st.session_state["generated_body"] = new_body

# ─── 네이버 발행 ──────────────────────────────────────────────
if publish_btn:
    title_to_publish = st.session_state.get("generated_title", "")
    body_to_publish = st.session_state.get("generated_body", "")

    if not title_to_publish or not body_to_publish:
        st.error("발행할 콘텐츠가 없습니다. 먼저 콘텐츠를 생성해주세요.")
    else:
        with st.status("네이버 블로그에 발행 중...", expanded=True) as status:
            st.write("브라우저를 시작합니다...")
            try:
                from core.naver_publisher import publish_to_naver

                session_file = os.getenv("SESSION_FILE", "naver_session.json")
                if not os.path.exists(session_file):
                    st.write(
                        "🔐 **첫 실행입니다.** 브라우저가 열리면 네이버에 로그인해주세요. "
                        "로그인이 완료되면 자동으로 진행됩니다."
                    )

                st.write("글을 작성하고 발행합니다...")
                published_url = asyncio.run(
                    publish_to_naver(title_to_publish, body_to_publish)
                )

                status.update(label="발행 완료!", state="complete", expanded=False)
                st.success(f"발행 완료! 포스트 URL: {published_url}")

            except Exception as e:
                status.update(label="발행 실패", state="error")
                st.error(f"발행 중 오류가 발생했습니다: {e}")
                if os.path.exists("error.png"):
                    st.image("error.png", caption="오류 발생 시점 스크린샷")
