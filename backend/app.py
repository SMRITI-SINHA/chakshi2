# backend/app.py
import asyncio
import base64
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="eCourts Chatbot API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis in production)
SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 30 minutes

# eCourts endpoints mapping
ECOURTS_ENDPOINTS = {
    'case_status': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=66b10a610467846e3db2e6975a62618871ab2063cdd3bfddffc39e209c256e7c',
    'cnr': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=home/index&app_token=fa23b5de9baffe7a33e6e6660618657f5fe17815915b76bf2fb119b31f0f9e8a',
    'court_orders': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=courtorder/index&app_token=ba399f32dca434c5d3844f1bbf1a3cc10893f2a89e6341134d88d49e0c786d48',
    'cause_list': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/index&app_token=db2fc03676d94555026470a0d4bb63f2bd62e754c559b0d90b5f54c0b3a5107c',
    'caveat': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=caveat_search/index&app_token=e132fafaac1274ecaa49b10213b05dfbe216bb32f66a123b10931f1c7d3fd714',
    'party_name': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=home/index&app_token=fa23b5de9baffe7a33e6e6660618657f5fe17815915b76bf2fb119b31f0f9e8a'
}


class SearchRequest(BaseModel):
    mode: str  # 'cnr', 'party_name', 'case_status', 'court_orders', 'cause_list', 'caveat'
    party_name: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    court_code: Optional[str] = None
    case_type: Optional[str] = None
    case_number: Optional[str] = None
    case_year: Optional[str] = None
    cnr_number: Optional[str] = None
    filing_number: Optional[str] = None


class CaptchaSubmit(BaseModel):
    session_id: str
    captcha_text: str


async def cleanup_old_sessions():
    """Remove sessions older than SESSION_TIMEOUT"""
    current_time = time.time()
    to_remove = []

    for session_id, session in SESSIONS.items():
        if current_time - session.get('created_at', 0) > SESSION_TIMEOUT:
            to_remove.append(session_id)
            # Clean up browser resources
            try:
                if 'context' in session:
                    await session['context'].close()
                if 'browser' in session:
                    await session['browser'].close()
                if 'pw' in session:
                    await session['pw'].stop()
            except Exception:
                pass

    for session_id in to_remove:
        del SESSIONS[session_id]


async def start_browser(headless: bool = True):
    """Initialize Playwright browser"""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=headless,
        args=['--disable-blink-features=AutomationControlled']
    )
    return pw, browser


async def wait_for_element(page: Page, selectors: list, timeout: int = 5000):
    """Try multiple selectors and return first found element"""
    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                return element, selector
        except Exception:
            continue
    return None, None


async def fill_party_name_form(page: Page, params: Dict[str, Any]):
    """Fill the party name search form"""
    print(f"[DEBUG] Filling party name form with params: {params}")

    # Wait for page to load
    await page.wait_for_load_state('networkidle', timeout=10000)

    # Try to click on "Party Name" radio button or tab
    party_name_selectors = [
        'input[value="party"]',
        'input[id*="party"]',
        'a:has-text("Party Name")',
        'label:has-text("Party Name")'
    ]

    for selector in party_name_selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                await element.click()
                await page.wait_for_timeout(500)
                break
        except Exception as e:
            print(f"[DEBUG] Could not click party name selector {selector}: {e}")

    # Fill party name
    if params.get('party_name'):
        party_input_selectors = [
            'input[name="party_name"]',
            'input[id="party_name"]',
            'input[placeholder*="Party Name"]',
            'input[placeholder*="party"]'
        ]

        for selector in party_input_selectors:
            try:
                await page.fill(selector, params['party_name'])
                print(f"[DEBUG] Filled party name using selector: {selector}")
                break
            except Exception as e:
                print(f"[DEBUG] Could not fill party name with {selector}: {e}")

    # Fill state if provided
    if params.get('state_code'):
        state_selectors = [
            'select[name="state_code"]',
            'select[id="state_code"]',
            'select[name="state"]'
        ]
        for selector in state_selectors:
            try:
                await page.select_option(selector, params['state_code'])
                print(f"[DEBUG] Selected state using selector: {selector}")
                await page.wait_for_timeout(1000)  # Wait for district dropdown to load
                break
            except Exception as e:
                print(f"[DEBUG] Could not select state with {selector}: {e}")

    # Fill district if provided
    if params.get('district_code'):
        district_selectors = [
            'select[name="district_code"]',
            'select[id="district_code"]',
            'select[name="district"]'
        ]
        for selector in district_selectors:
            try:
                await page.select_option(selector, params['district_code'])
                print(f"[DEBUG] Selected district using selector: {selector}")
                await page.wait_for_timeout(500)
                break
            except Exception as e:
                print(f"[DEBUG] Could not select district with {selector}: {e}")


async def fill_cnr_form(page: Page, params: Dict[str, Any]):
    """Fill the CNR search form"""
    print(f"[DEBUG] Filling CNR form with params: {params}")

    await page.wait_for_load_state('networkidle', timeout=10000)

    # Try to click on CNR radio button or tab
    cnr_tab_selectors = [
        'input[value="cnr"]',
        'input[id*="cnr"]',
        'a:has-text("CNR")',
        'label:has-text("CNR")'
    ]

    for selector in cnr_tab_selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                await element.click()
                await page.wait_for_timeout(500)
                break
        except Exception:
            pass

    # Fill CNR number
    if params.get('cnr_number'):
        cnr_input_selectors = [
            'input[name="cnr_number"]',
            'input[id="cnr_number"]',
            'input[name="cnrno"]',
            'input[placeholder*="CNR"]'
        ]

        for selector in cnr_input_selectors:
            try:
                await page.fill(selector, params['cnr_number'])
                print(f"[DEBUG] Filled CNR using selector: {selector}")
                break
            except Exception:
                pass


async def capture_captcha(page: Page):
    """Capture CAPTCHA image from the page"""
    print("[DEBUG] Attempting to capture CAPTCHA")

    # Wait a bit for CAPTCHA to load
    await page.wait_for_timeout(2000)

    # Try multiple CAPTCHA selectors
    captcha_selectors = [
        'img#captcha_image',
        'img#captchaimg',
        'img.captcha',
        'img[src*="captcha"]',
        'img[alt*="captcha" i]',
        'img[alt*="Captcha" i]',
        'img[id*="captcha" i]',
        'canvas#captcha'  # Some sites use canvas
    ]

    captcha_element = None
    successful_selector = None

    for selector in captcha_selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                # Check if element is visible
                is_visible = await element.is_visible()
                if is_visible:
                    captcha_element = element
                    successful_selector = selector
                    print(f"[DEBUG] Found CAPTCHA using selector: {selector}")
                    break
        except Exception as e:
            print(f"[DEBUG] Selector {selector} failed: {e}")

    if not captcha_element:
        print("[DEBUG] CAPTCHA element not found, taking full page screenshot")
        # Fallback: take a screenshot of the whole page
        screenshot_bytes = await page.screenshot(full_page=False)
        return base64.b64encode(screenshot_bytes).decode(), 'full_page'

    # Screenshot the CAPTCHA element
    try:
        captcha_bytes = await captcha_element.screenshot()
        b64_image = base64.b64encode(captcha_bytes).decode()
        print(f"[DEBUG] CAPTCHA captured successfully using {successful_selector}")
        return b64_image, successful_selector
    except Exception as e:
        print(f"[DEBUG] Error capturing CAPTCHA screenshot: {e}")
        # Fallback to full page screenshot
        screenshot_bytes = await page.screenshot(full_page=False)
        return base64.b64encode(screenshot_bytes).decode(), 'full_page'


async def submit_form_and_scrape(page: Page, captcha_text: str):
    """Submit form with CAPTCHA and scrape results"""
    print(f"[DEBUG] Submitting form with captcha: {captcha_text}")

    # Fill CAPTCHA input
    captcha_input_selectors = [
        'input[name="captcha"]',
        'input[id="captcha"]',
        'input[id*="captcha" i]',
        'input[placeholder*="Captcha" i]',
        'input[type="text"][name*="captcha" i]'
    ]

    filled = False
    for selector in captcha_input_selectors:
        try:
            await page.fill(selector, captcha_text)
            print(f"[DEBUG] Filled CAPTCHA using selector: {selector}")
            filled = True
            break
        except Exception as e:
            print(f"[DEBUG] Could not fill CAPTCHA with {selector}: {e}")

    if not filled:
        raise Exception("Could not find CAPTCHA input field")

    # Click submit button
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Search")',
        'button:has-text("Submit")',
        'input[value="Search"]',
        'input[value="Submit"]',
        'button.btn-primary',
        'button#submit'
    ]

    clicked = False
    for selector in submit_selectors:
        try:
            button = await page.query_selector(selector)
            if button:
                is_visible = await button.is_visible()
                if is_visible:
                    await button.click()
                    print(f"[DEBUG] Clicked submit button using selector: {selector}")
                    clicked = True
                    break
        except Exception as e:
            print(f"[DEBUG] Could not click submit with {selector}: {e}")

    if not clicked:
        # Try pressing Enter as fallback
        print("[DEBUG] Trying Enter key as fallback")
        await page.keyboard.press('Enter')

    # Wait for results
    try:
        await page.wait_for_load_state('networkidle', timeout=15000)
    except Exception:
        print("[DEBUG] Timeout waiting for networkidle, continuing anyway")
        await page.wait_for_timeout(3000)

    # Scrape results
    results = await scrape_results(page)
    return results


async def scrape_results(page: Page):
    """Scrape case details from result page"""
    print("[DEBUG] Scraping results")

    results = {
        'raw_text': [],
        'tables': [],
        'cases': []
    }

    try:
        # Check for error messages
        error_selectors = [
            '.error',
            '.alert-danger',
            'div:has-text("No records found")',
            'div:has-text("Invalid captcha")',
            'span.error'
        ]

        for selector in error_selectors:
            try:
                error_elem = await page.query_selector(selector)
                if error_elem:
                    error_text = await error_elem.inner_text()
                    if error_text and len(error_text.strip()) > 0:
                        results['error'] = error_text.strip()
                        print(f"[DEBUG] Found error message: {error_text}")
                        return results
            except Exception:
                pass

        # Try to find result tables
        tables = await page.query_selector_all('table')
        print(f"[DEBUG] Found {len(tables)} tables")

        for idx, table in enumerate(tables):
            try:
                table_html = await table.inner_html()
                rows = await table.query_selector_all('tr')

                table_data = []
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    row_data = []
                    for cell in cells:
                        text = await cell.inner_text()
                        row_data.append(text.strip())
                    if row_data:
                        table_data.append(row_data)

                if table_data:
                    results['tables'].append({
                        'index': idx,
                        'data': table_data
                    })
            except Exception as e:
                print(f"[DEBUG] Error parsing table {idx}: {e}")

        # Get main content area text
        content_selectors = [
            '#content',
            '.content',
            '#main',
            '.main-content',
            'body'
        ]

        for selector in content_selectors:
            try:
                content = await page.query_selector(selector)
                if content:
                    text = await content.inner_text()
                    if text:
                        results['raw_text'].append(text[:5000])  # Limit length
                        break
            except Exception:
                pass

        # Try to extract structured case information
        case_info = {}

        # Common field patterns
        field_patterns = {
            'cnr': ['CNR', 'Case Number', 'CNR Number'],
            'case_number': ['Case No', 'Case Number', 'Suit No'],
            'filing_number': ['Filing No', 'Filing Number'],
            'parties': ['Petitioner', 'Respondent', 'Plaintiff', 'Defendant'],
            'status': ['Case Status', 'Status'],
            'next_hearing': ['Next Hearing', 'Next Date', 'Hearing Date'],
            'judge': ['Judge', 'Court', 'Coram']
        }

        page_text = await page.content()

        for field, patterns in field_patterns.items():
            for pattern in patterns:
                if pattern.lower() in page_text.lower():
                    case_info[field] = f"Found: {pattern}"

        if case_info:
            results['cases'].append(case_info)

        print(f"[DEBUG] Scraped results: {len(results['tables'])} tables, {len(results['raw_text'])} text blocks")

    except Exception as e:
        results['error'] = f"Error scraping results: {str(e)}"
        print(f"[DEBUG] Error in scrape_results: {e}")

    return results


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("[INFO] eCourts Chatbot API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("[INFO] Cleaning up sessions...")
    for session_id in list(SESSIONS.keys()):
        try:
            session = SESSIONS[session_id]
            if 'context' in session:
                await session['context'].close()
            if 'browser' in session:
                await session['browser'].close()
            if 'pw' in session:
                await session['pw'].stop()
        except Exception:
            pass


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "running",
        "version": "1.0.0",
        "message": "eCourts Chatbot API"
    }


@app.post("/start-search")
async def start_search(request: SearchRequest):
    """Initialize a new search session"""
    try:
        # Clean up old sessions
        await cleanup_old_sessions()

        # Generate session ID
        session_id = base64.urlsafe_b64encode(os.urandom(12)).decode().rstrip('=')

        # Store initial session data
        SESSIONS[session_id] = {
            'status': 'starting',
            'created_at': time.time(),
            'params': request.dict()
        }

        print(f"[INFO] Starting new search session: {session_id}")
        print(f"[INFO] Search parameters: {request.dict()}")

        # Start the search in background
        asyncio.create_task(run_search(session_id, request.dict()))

        return {
            'session_id': session_id,
            'status': 'started',
            'message': 'Search initiated successfully'
        }

    except Exception as e:
        print(f"[ERROR] Error starting search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_search(session_id: str, params: Dict[str, Any]):
    """Execute the search and capture CAPTCHA"""
    pw = None
    browser = None

    try:
        SESSIONS[session_id]['status'] = 'running'
        print(f"[INFO] Running search for session {session_id}")

        # Determine which endpoint to use
        mode = params.get('mode', 'party_name')
        url = ECOURTS_ENDPOINTS.get(mode, ECOURTS_ENDPOINTS['party_name'])

        print(f"[INFO] Using endpoint: {url}")

        # Start browser
        headless = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
        pw, browser = await start_browser(headless=headless)

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # Navigate to the URL
        print(f"[INFO] Navigating to {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)

        # Fill the form based on mode
        if mode == 'cnr':
            await fill_cnr_form(page, params)
        else:
            await fill_party_name_form(page, params)

        # Capture CAPTCHA
        captcha_b64, selector_used = await capture_captcha(page)

        if not captcha_b64:
            SESSIONS[session_id]['status'] = 'error'
            SESSIONS[session_id]['error'] = 'Could not capture CAPTCHA image'
            return

        # Update session with CAPTCHA and browser objects
        SESSIONS[session_id].update({
            'status': 'awaiting_captcha',
            'captcha_b64': captcha_b64,
            'captcha_selector': selector_used,
            'page': page,
            'context': context,
            'browser': browser,
            'pw': pw
        })

        print(f"[INFO] CAPTCHA captured for session {session_id}, awaiting user input")

    except Exception as e:
        print(f"[ERROR] Error in run_search for session {session_id}: {e}")
        SESSIONS[session_id]['status'] = 'error'
        SESSIONS[session_id]['error'] = str(e)

        # Cleanup on error
        try:
            if browser:
                await browser.close()
            if pw:
                await pw.stop()
        except Exception:
            pass


@app.get("/captcha/{session_id}")
async def get_captcha(session_id: str):
    """Get CAPTCHA image for a session"""
    session = SESSIONS.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = session.get('status')

    if status == 'error':
        return {
            'status': 'error',
            'error': session.get('error', 'Unknown error')
        }

    if status != 'awaiting_captcha':
        return {
            'status': status,
            'message': f'Session is in {status} state'
        }

    return {
        'status': 'awaiting_captcha',
        'captcha_b64': session.get('captcha_b64'),
        'selector_used': session.get('captcha_selector')
    }


@app.post("/submit-captcha")
async def submit_captcha(body: CaptchaSubmit):
    """Submit CAPTCHA and get results"""
    session = SESSIONS.get(body.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get('status') != 'awaiting_captcha':
        raise HTTPException(
            status_code=400,
            detail=f"Session is not awaiting CAPTCHA. Current status: {session.get('status')}"
        )

    try:
        print(f"[INFO] Processing CAPTCHA submission for session {body.session_id}")

        page = session['page']

        # Submit form and scrape results
        results = await submit_form_and_scrape(page, body.captcha_text)

        # Update session
        session['status'] = 'completed'
        session['results'] = results
        session['completed_at'] = time.time()

        # Cleanup browser resources
        try:
            await session['context'].close()
            await session['browser'].close()
            await session['pw'].stop()
        except Exception as e:
            print(f"[WARN] Error cleaning up browser: {e}")

        print(f"[INFO] Search completed for session {body.session_id}")

        return {
            'status': 'completed',
            'results': results
        }

    except Exception as e:
        print(f"[ERROR] Error submitting CAPTCHA for session {body.session_id}: {e}")
        session['status'] = 'error'
        session['error'] = str(e)

        return {
            'status': 'error',
            'error': str(e)
        }


@app.get("/results/{session_id}")
async def get_results(session_id: str):
    """Get results for a completed session"""
    session = SESSIONS.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        'status': session.get('status'),
        'results': session.get('results'),
        'error': session.get('error')
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and cleanup resources"""
    session = SESSIONS.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Cleanup browser resources
        if 'context' in session:
            await session['context'].close()
        if 'browser' in session:
            await session['browser'].close()
        if 'pw' in session:
            await session['pw'].stop()
    except Exception:
        pass

    del SESSIONS[session_id]

    return {'status': 'deleted', 'session_id': session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True
    )
