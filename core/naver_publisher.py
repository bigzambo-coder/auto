import asyncio
import os
import json
from playwright.async_api import async_playwright, Page, BrowserContext

SESSION_FILE = os.getenv("SESSION_FILE", "naver_session.json")
NAVER_ID = os.getenv("NAVER_ID", "")
NAVER_PW = os.getenv("NAVER_PW", "")
NAVER_BLOG_ID = os.getenv("NAVER_BLOG_ID", "")
HEADLESS = os.getenv("HEADLESS_MODE", "false").lower() == "true"


async def publish_to_naver(title: str, body: str) -> str:
    """
    네이버 블로그에 글을 발행하고 완료된 포스트 URL을 반환한다.

    최초 실행 시: headless=False로 브라우저 열림 → 사용자가 직접 로그인 → 세션 저장
    이후 실행:   저장된 세션으로 자동 로그인 (headless=True)
    """
    async with async_playwright() as p:
        session_exists = os.path.exists(SESSION_FILE)
        headless = HEADLESS and session_exists

        browser = await p.chromium.launch(headless=headless)

        if session_exists:
            context = await browser.new_context(storage_state=SESSION_FILE)
        else:
            context = await browser.new_context()

        page = await context.new_page()

        # 로그인 상태 확인
        await page.goto("https://www.naver.com", wait_until="domcontentloaded")
        logged_in = await _check_login(page)

        if not logged_in:
            await _do_login(page, context)

        # 블로그 글쓰기 페이지 이동
        write_url = "https://blog.naver.com/PostWrite.nhn"
        if NAVER_BLOG_ID:
            write_url = f"https://blog.naver.com/{NAVER_BLOG_ID}/postwrite"

        await page.goto(write_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # SmartEditor 로드 대기 및 내용 입력
        await _fill_title(page, title)
        await _fill_body(page, body)

        # 발행
        published_url = await _publish(page)

        await context.storage_state(path=SESSION_FILE)
        await browser.close()
        return published_url


async def _check_login(page: Page) -> bool:
    try:
        # 로그인 상태면 마이페이지 링크 존재
        await page.wait_for_selector(
            "#account, .MyView-module__btn_my___HGsKr, [class*='gnb_my']",
            timeout=5000,
        )
        return True
    except Exception:
        return False


async def _do_login(page: Page, context: BrowserContext) -> None:
    """네이버 로그인. 자격증명이 있으면 자동, 없으면 사용자가 직접 입력."""
    await page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")

    if NAVER_ID and NAVER_PW:
        # 자동 로그인 시도
        await page.wait_for_selector("#id", timeout=10000)
        await page.fill("#id", NAVER_ID)
        await page.wait_for_timeout(500)
        await page.fill("#pw", NAVER_PW)
        await page.wait_for_timeout(500)
        await page.click(".btn_login")

        # CAPTCHA나 2단계 인증이 있을 수 있으므로 최대 60초 대기
        try:
            await page.wait_for_url("https://www.naver.com/**", timeout=60000)
        except Exception:
            # 수동 로그인 유도
            print("[안내] 자동 로그인에 실패했습니다. 브라우저에서 직접 로그인해주세요.")
            await _wait_for_manual_login(page)
    else:
        print("[안내] .env에 NAVER_ID/NAVER_PW가 설정되지 않았습니다. 브라우저에서 직접 로그인해주세요.")
        await _wait_for_manual_login(page)

    # 세션 저장
    await context.storage_state(path=SESSION_FILE)


async def _wait_for_manual_login(page: Page) -> None:
    """사용자가 로그인할 때까지 대기 (최대 3분)."""
    print("[대기] 네이버 로그인 완료 후 자동으로 진행됩니다...")
    await page.wait_for_url("https://www.naver.com/**", timeout=180000)


async def _fill_title(page: Page, title: str) -> None:
    """SmartEditor 제목 입력란에 제목 입력."""
    selectors = [
        ".se-title-input",
        "[placeholder='제목']",
        "input[class*='title']",
        ".tit_editor",
    ]
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            await page.click(sel)
            await page.keyboard.press("Control+a")
            await page.keyboard.type(title, delay=30)
            return
        except Exception:
            continue

    raise RuntimeError("제목 입력란을 찾을 수 없습니다. error.png를 확인하세요.")


async def _fill_body(page: Page, body: str) -> None:
    """SmartEditor ONE 본문 영역에 HTML 내용 입력."""
    # SmartEditor ONE은 iframe 내부에 contenteditable div를 가짐
    iframe_selectors = [
        "iframe[id*='se2_iframe']",
        "iframe[title*='에디터']",
        "iframe[title*='본문']",
        "iframe[class*='editor']",
        "#smart-editor-iframe",
    ]

    editor_frame = None
    for sel in iframe_selectors:
        try:
            await page.wait_for_selector(sel, timeout=15000)
            editor_frame = page.frame_locator(sel)
            break
        except Exception:
            continue

    if editor_frame is not None:
        # iframe 내부 contenteditable 찾기
        content_selectors = [
            ".se-content[contenteditable='true']",
            "[contenteditable='true']",
            ".se2_inputarea",
            "body[contenteditable='true']",
        ]
        for sel in content_selectors:
            try:
                editor_el = editor_frame.locator(sel).first
                await editor_el.wait_for(state="visible", timeout=10000)
                await editor_el.click()
                await page.keyboard.press("Control+a")
                await page.wait_for_timeout(300)

                # 클립보드로 HTML 붙여넣기
                await _paste_content(page, body)
                return
            except Exception:
                continue

    # iframe을 찾지 못한 경우 — 새 버전 SmartEditor 시도
    await _try_new_smarteditor(page, body)


async def _paste_content(page: Page, content: str) -> None:
    """클립보드를 통해 내용 붙여넣기."""
    try:
        # JavaScript로 클립보드에 텍스트 설정
        await page.evaluate(
            "text => navigator.clipboard.writeText(text)",
            content,
        )
        await page.keyboard.press("Control+v")
        await page.wait_for_timeout(1000)
    except Exception:
        # execCommand 폴백
        plain_text = _html_to_plain(content)
        await page.keyboard.type(plain_text, delay=10)


async def _try_new_smarteditor(page: Page, body: str) -> None:
    """새 버전 네이버 SmartEditor (SE3) 대응."""
    selectors = [
        ".se-main-container",
        ".se-placeholder",
        "[data-editor-version]",
    ]
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            await page.click(sel)
            await page.keyboard.press("Control+a")
            await page.wait_for_timeout(300)
            await _paste_content(page, body)
            return
        except Exception:
            continue

    # 마지막 수단: 스크린샷 찍고 오류 발생
    await page.screenshot(path="error.png")
    raise RuntimeError("본문 편집기를 찾을 수 없습니다. error.png를 확인하세요.")


async def _publish(page: Page) -> str:
    """발행 버튼 클릭 및 완료 URL 반환."""
    publish_selectors = [
        "button:has-text('발행')",
        ".btn_publish",
        "[class*='publish']",
        "button:has-text('등록')",
    ]

    for sel in publish_selectors:
        try:
            await page.wait_for_selector(sel, timeout=5000)
            await page.click(sel)
            break
        except Exception:
            continue
    else:
        await page.screenshot(path="error.png")
        raise RuntimeError("발행 버튼을 찾을 수 없습니다.")

    # 발행 모달 확인 버튼
    await page.wait_for_timeout(2000)
    modal_selectors = [
        "button:has-text('발행하기')",
        "button:has-text('확인')",
        ".btn_ok",
        "[class*='confirm']",
    ]
    for sel in modal_selectors:
        try:
            modal_btn = page.locator(sel).first
            if await modal_btn.is_visible():
                await modal_btn.click()
                break
        except Exception:
            continue

    # 발행 완료 페이지 대기
    try:
        await page.wait_for_url(
            "**/PostView*",
            timeout=30000,
        )
    except Exception:
        # URL 패턴이 다를 수 있으므로 현재 URL 반환
        pass

    return page.url


def _html_to_plain(html: str) -> str:
    """HTML 태그를 제거하여 plain text 반환 (폴백용)."""
    import re
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return text
