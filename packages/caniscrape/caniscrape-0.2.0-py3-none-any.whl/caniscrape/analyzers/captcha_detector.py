from __future__ import annotations

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
import random
from ..utils.captcha_solvers import get_solver, CaptchaSolverError

CAPTCHA_FINGERPRINTS = {
    "reCAPTCHA": [
        "google.com/recaptcha", "recaptcha/api.js", "g-recaptcha"
    ],
    "hCaptcha": [
        "hcaptcha.com", "hcaptcha-box", "h-captcha"
    ],
    "Cloudflare Turnstile": [
        "challenges.cloudflare.com/turnstile", "cf-turnstile"
    ]
}

def _scan_for_captcha_fingerprints(page: Page, network_requests: list[str]) -> str | None:
    """
    Scan the page's HTML and network requests for known CAPTCHA signatures.
    Returns the name of the detected CAPTCHA provider or None.
    """
    html_content = page.content().lower()
    all_evidence = network_requests + [html_content]

    for provider, patterns in CAPTCHA_FINGERPRINTS.items():
        for pattern in patterns:
            for evidence in all_evidence:
                if pattern in evidence:
                    return provider
    return None

def detect_captcha(url: str, service_name: str | None, api_key: str | None, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Analyzes a URL to detect the presence and type of CAPTCHA.
    """
    try:
        with sync_playwright() as p:
            launch_options = {'headless': True}
            if proxies:
                proxy_url = random.choice(proxies)
                launch_options['proxy'] = {'server': proxy_url}

            browser = p.chromium.launch(**launch_options)
            page = browser.new_page()

            captured_requests = []
            def capture_request(request):
                captured_requests.append(request.url.lower())
            page.on('request', capture_request)

            try:
                page.goto(url, wait_until='load', timeout=30000)
                page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass

            page.wait_for_timeout(2000)

            captcha_on_load = _scan_for_captcha_fingerprints(page, captured_requests)

            if captcha_on_load:
                if service_name and api_key:
                    try:
                        print(f"INFO: {captcha_on_load} detected. Attempting to solve...")
                        solver = get_solver(service_name=service_name, api_key=api_key)

                        sitekey_locator = page.locator('div[data-sitekey], iframe[data-sitekey], .g-recaptcha[data-sitekey], .h-captcha[data-sitekey]')
                        sitekey = sitekey_locator.get_attribute('data-sitekey') if sitekey_locator.count() > 0 else None

                        if not sitekey:
                            raise CaptchaSolverError('Could not find a sitekey on the page for reCAPTCHA or hCaptcha.')

                        token = None
                        if 'recaptcha' in captcha_on_load.lower():
                            token = solver.solve_recaptcha_v2(sitekey=sitekey, page_url=page.url)
                        elif 'hcaptcha' in captcha_on_load.lower():
                            token = solver.solve_hcaptcha(sitekey=sitekey, page_url=page.url)
                        else:
                            raise CaptchaSolverError(f'Solving for "{captcha_on_load}" is not yet supported.')
                        
                        browser.close()
                        return {'status': 'success', 'captcha_detected': True, 'captcha_type': captcha_on_load, 'trigger_condition': 'on page load', 'solve_status': 'solved', 'details': f'A {captcha_on_load} was detected and successfully solved by  the {service_name} service.'}
                    except (CaptchaSolverError, ValueError, ImportError) as e:
                        browser.close()
                        return {'status': 'success', 'captcha_detected': True, 'captcha_type': captcha_on_load, 'trigger_condition': 'on page load', 'solve_status': 'failed', 'details': f'A {captcha_on_load} was detected and but the solving attempt failed: {str(e)}'}
                else:
                    browser.close()
                    return {'status': 'success', 'captcha_detected': True, 'captcha_type': captcha_on_load, 'trigger_condition': 'on page load', 'solve_status': 'not attempted', 'details': f'A {captcha_on_load} was detected. Provide --captcha-service <your-captcha-service> --captcha-api-key <your-captchasolver-key> to attempt solving.'}
            
            captured_requests.clear()

            for _ in range(10):
                page.reload(wait_until='domcontentloaded')
            
            captcha_after_burst = _scan_for_captcha_fingerprints(page, captured_requests)
            browser.close()

            if captcha_after_burst:
                return {'status': 'success', 'captcha_detected': True, 'captcha_type': captcha_after_burst, 'trigger_condition': 'after burst of requests'}
            
            return {'status': 'success', 'captcha_detected': False}
    except PlaywrightTimeoutError:
        return {'status': 'error', 'message': 'Page load timed out.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}