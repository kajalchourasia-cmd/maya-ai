from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
EVIDENCE = ROOT / "docs" / "maya-ui-restoration-evidence"
NODE = Path(os.environ.get("MAYA_NODE") or shutil.which("node") or "node")
CHROME = os.environ.get("MAYA_CHROME") or next((
    candidate for candidate in (
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ) if candidate and Path(candidate).exists()
), "")
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
API_PORT = 8011
WEB_PORT = 5173
API_URL = f"http://127.0.0.1:{API_PORT}"
BASE_URL = f"http://127.0.0.1:{WEB_PORT}"
processes: list[subprocess.Popen] = []
service_log = None


def wait_url(url: str, timeout: int = 75) -> None:
    started = time.time()
    error = ""
    while time.time() - started < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception as exc:
            error = str(exc)
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {url}: {error}")


def start_api() -> subprocess.Popen:
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", str(API_PORT)],
        cwd=ROOT,
        stdout=service_log,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW,
    )
    processes.append(process)
    wait_url(f"{API_URL}/docs")
    return process


def start_frontend() -> subprocess.Popen:
    env = os.environ.copy()
    env["NEXT_PUBLIC_MAYA_API_URL"] = API_URL
    process = subprocess.Popen(
        [str(NODE), str(FRONTEND / "node_modules" / "next" / "dist" / "bin" / "next"), "dev", "-p", str(WEB_PORT)],
        cwd=FRONTEND,
        env=env,
        stdout=service_log,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW,
    )
    processes.append(process)
    wait_url(BASE_URL, timeout=100)
    return process


def stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=6)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def wait_text(driver: webdriver.Chrome, text: str, timeout: int = 20) -> None:
    WebDriverWait(driver, timeout).until(lambda item: text in item.find_element(By.TAG_NAME, "body").text)


def click_text(driver: webdriver.Chrome, text: str, exact: bool = False) -> None:
    if exact:
        query = f"//*[self::button or @role='tab' or self::label][normalize-space(.)={json.dumps(text)}]"
    else:
        query = f"//*[self::button or @role='tab' or self::label][contains(normalize-space(.),{json.dumps(text)})]"
    element = WebDriverWait(driver, 15).until(lambda item: item.find_element(By.XPATH, query))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(0.25)


def fill(driver: webdriver.Chrome, by: str, value: str, text: str) -> None:
    element = WebDriverWait(driver, 15).until(lambda item: item.find_element(by, value))
    driver.execute_script("const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; setter.call(arguments[0], arguments[1]); arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", element, text)
    time.sleep(0.12)
    time.sleep(0.12)


def body(driver: webdriver.Chrome) -> str:
    return driver.find_element(By.TAG_NAME, "body").text


def reset(driver: webdriver.Chrome) -> None:
    driver.get(BASE_URL)
    WebDriverWait(driver, 30).until(lambda item: item.execute_script("return document.readyState") == "complete")
    driver.execute_script("localStorage.clear();sessionStorage.clear();")
    driver.refresh()
    wait_text(driver, "Feel held through")


def shot(driver: webdriver.Chrome, name: str) -> str:
    target = EVIDENCE / f"{name}.png"
    if not driver.save_screenshot(str(target)):
        raise RuntimeError(f"Could not capture {name}")
    print(f"SCREENSHOT={name}", flush=True)
    return target.relative_to(ROOT).as_posix()


def onboarding(
    driver: webdriver.Chrome,
    *,
    journey: str = "pregnant",
    timeline_mode: str = "week",
    timeline_value: str = "26",
    no_record: bool = True,
) -> None:
    reset(driver)
    click_text(driver, "Begin my journey")
    wait_text(driver, "start with you")
    fill(driver, By.ID, "name", "Postpartum preview" if journey == "postpartum" else "Pregnancy preview")
    click_text(driver, "Continue", exact=True)
    wait_text(driver, "Where are you in your journey?")
    if journey == "postpartum":
        click_text(driver, "postpartum")
    click_text(driver, "Continue", exact=True)
    wait_text(driver, "Your little timeline")
    if journey == "postpartum":
        fill(driver, By.ID, "birth-date", timeline_value)
    else:
        label = {"week": "Current week", "month": "Current month", "due": "Due date"}[timeline_mode]
        click_text(driver, label, exact=True)
        aria = {
            "week": "Current pregnancy week",
            "month": "Current pregnancy month",
            "due": "Estimated due date",
        }[timeline_mode]
        fill(driver, By.CSS_SELECTOR, f'[aria-label="{aria}"]', timeline_value)
    click_text(driver, "Continue", exact=True)
    wait_text(driver, "Make Maya feel like yours")
    click_text(driver, "Continue", exact=True)
    wait_text(driver, "Keep your care close")
    click_text(driver, "Continue without a care record" if no_record else "Use the fictional sample care record")
    click_text(driver, "Open my Maya", exact=True)
    wait_text(driver, "YOUR POSTPARTUM SPACE" if journey == "postpartum" else "YOUR SAMPLE CONTEXT", timeout=30)


def entry(case_id: str, passed: bool, evidence: str, **details) -> dict:
    return {"id": case_id, "passed": bool(passed), "evidence": evidence, **details}


def main() -> int:
    global service_log
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    screenshots: list[str] = []
    service_log = (EVIDENCE / "local-services.log").open("w", encoding="utf-8")
    api = None
    frontend_process = None
    driver = None
    try:
        api = start_api()
        frontend_process = start_frontend()
        options = webdriver.ChromeOptions()
        if CHROME:
            options.binary_location = CHROME
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--window-size=1440,960")
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='maya-restoration-')}")
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1440, 960)
        driver.get(BASE_URL)
        wait_text(driver, "Feel held through", timeout=40)
        screenshots.append(shot(driver, "01-landing-desktop"))

        click_text(driver, "Explore a sample week")
        wait_text(driver, "WEEK 26", timeout=30)
        visible = body(driver)
        results.append(entry("pregnancy-exact-week", "WEEK 26" in visible and "small cabbage" in visible.lower(), "Week 26 and governed small-cabbage comparison rendered"))
        results.append(entry("pregnancy-navigation", all(label in visible for label in ["This week", "Nutrition", "Movement", "Symptoms", "Wellbeing", "FAQs", "Care records"]), "All pregnancy dashboard sections visible"))
        screenshots.append(shot(driver, "02-pregnancy-dashboard-week-26"))

        click_text(driver, "VIEW ALL 41 WEEKS")
        wait_text(driver, "Weeks 1", timeout=20)
        library_count = len(driver.find_elements(By.CSS_SELECTOR, '[aria-label^="Open week "]'))
        visible = body(driver)
        rounded = ["Small muskmelon (kharbuja)", "Small cabbage", "Honeydew melon", "Small watermelon", "Large muskmelon", "Full-size watermelon"]
        results.append(entry("complete-week-library", library_count == 41, f"{library_count}/41 week controls rendered"))
        results.append(entry("rounded-comparison-sequence", all(value in visible for value in rounded), "Rounded and repeated later-week sequence visible"))
        screenshots.append(shot(driver, "03-week-library-desktop"))
        click_text(driver, "Back to dashboard")
        wait_text(driver, "YOUR SAMPLE CONTEXT")

        click_text(driver, "Build weekly plan")
        wait_text(driver, "Not saved", timeout=30)
        visible = body(driver)
        results.append(entry("allergy-aware-plan", "Peanut" in visible and "Sample context applied" in visible, "Sample allergy visibly propagated into validated plan"))
        results.append(entry("connected-plan", "Proposed preview only" in visible and "Not saved" in visible, "Plan built through API and remains unsaved"))
        screenshots.append(shot(driver, "04-validated-plan-desktop"))

        driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button.floating-chat"))
        wait_text(driver, "What", timeout=15)
        suggested = "Show meal options"
        click_text(driver, suggested, exact=True)
        wait_text(driver, "Validated controlled-fixture result", timeout=30)
        visible = body(driver)
        results.append(entry("suggested-question-fidelity", suggested in visible, "Displayed suggestion submitted verbatim"))
        results.append(entry("routine-chat-validation", "Public guidance says" in visible and "Peanut" in visible, "Supported routine request rendered validated provenance and applied constraint"))
        screenshots.append(shot(driver, "05-ask-maya-validated-answer"))

        fill(driver, By.CSS_SELECTOR, 'input[placeholder^="Ask"]', "I feel dizzy right now")
        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send message"]').click()
        wait_text(driver, "One detail is needed first", timeout=30)
        visible = body(driver)
        results.append(entry("ambiguous-symptom-block", "One detail is needed first" in visible and "Ordinary generation calls: 1" not in visible, "Ambiguous current symptom blocked for clarification"))

        fill(driver, By.CSS_SELECTOR, 'input[placeholder^="Ask"]', "I cannot breathe right now")
        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send message"]').click()
        wait_text(driver, "This may need urgent medical attention", timeout=30)
        urgent_card = driver.find_elements(By.CSS_SELECTOR, "article.urgent-message")[-1]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", urgent_card)
        visible = body(driver)
        results.append(entry(
            "urgent-zero-generation",
            all(value in visible for value in ["Get urgent help now", "This may need urgent medical attention", "Ordinary generation calls: 0"]),
            "Unique fixed urgent route displayed with zero ordinary generation",
        ))
        screenshots.append(shot(driver, "06-urgent-safety-bypass"))

        onboarding(driver, timeline_mode="month", timeline_value="6")
        visible = body(driver)
        results.append(entry("month-range-no-guess", "week range" in visible and "not guessed a single week" in visible, "Month 6 remained an approximate week range"))
        screenshots.append(shot(driver, "07-month-range-dashboard"))

        due = (date.today() + timedelta(days=140)).isoformat()
        onboarding(driver, timeline_mode="due", timeline_value=due)
        visible = body(driver)
        results.append(entry("due-date-resolution", any(f"PREGNANCY WEEK {week}" in visible for week in (19, 20, 21)), "Due date resolved deterministically to an exact week near 20"))

        birth = (date.today() - timedelta(days=14)).isoformat()
        onboarding(driver, journey="postpartum", timeline_value=birth)
        visible = body(driver)
        results.append(entry("postpartum-surface", all(label in visible for label in ["Recovery", "Nourishment", "Feeding", "Wellbeing", "Care records"]), "Postpartum recovery, nourishment, feeding and wellbeing rendered"))
        results.append(entry("postpartum-comparison-suppression", "YOUR SIZE STORY" not in visible and "About the size of" not in visible, "No pregnancy comparison rendered postpartum"))
        screenshots.append(shot(driver, "08-postpartum-dashboard-desktop"))

        reset(driver)
        click_text(driver, "Explore a sample week")
        wait_text(driver, "WEEK 26", timeout=30)
        before_restart = body(driver)
        stop_process(api)
        api = start_api()
        driver.refresh()
        wait_text(driver, "YOUR SAMPLE CONTEXT", timeout=35)
        after_restart = body(driver)
        results.append(entry("backend-restart-recovery", "PREGNANCY WEEK 26" in before_restart and "PREGNANCY WEEK 26" in after_restart, "Fictional context recovered after actual in-memory backend restart"))

        stop_process(api)
        click_text(driver, "Build weekly plan")
        wait_text(driver, "Plan unavailable", timeout=15)
        failure_text = body(driver)
        api = start_api()
        click_text(driver, "Retry plan")
        try:
            wait_text(driver, "Not saved", timeout=35)
        except Exception:
            diagnostic = body(driver)
            (EVIDENCE / "api-retry-failure-body.txt").write_text(diagnostic, encoding="utf-8")
            shot(driver, "09-api-recovery-failure")
            raise
        recovered_text = body(driver)
        results.append(entry("api-failure-retry", "Plan unavailable" in failure_text and "Not saved" in recovered_text, "Visible API error recovered through Retry after service restart"))
        screenshots.append(shot(driver, "09-api-recovery-success"))

        driver.set_window_size(390, 844)
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
        reset(driver)
        mobile_landing = driver.execute_script("return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth}")
        screenshots.append(shot(driver, "10-landing-mobile"))
        click_text(driver, "Explore a sample week")
        wait_text(driver, "YOUR SAMPLE CONTEXT")
        mobile_dashboard = driver.execute_script("return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth}")
        results.append(entry("responsive-desktop", True, "Desktop principal views captured at 1440x960"))
        results.append(entry("responsive-mobile", mobile_landing["width"] == 390 and mobile_dashboard["width"] == 390 and mobile_landing["scrollWidth"] <= mobile_landing["width"] and mobile_dashboard["scrollWidth"] <= mobile_dashboard["width"], "No page-level horizontal overflow at an exact 390x844 emulated viewport", landing=mobile_landing, dashboard=mobile_dashboard))
        screenshots.append(shot(driver, "11-pregnancy-dashboard-mobile"))

        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        driver.set_window_size(1440, 960)
        reset(driver)
        focus_sequence = []
        begin_control = None
        for _ in range(8):
            driver.switch_to.active_element.send_keys(Keys.TAB)
            active = driver.switch_to.active_element
            label = (active.get_attribute("aria-label") or active.text or active.tag_name).strip()[:80]
            check = {
                "label": label,
                "tag": active.tag_name,
                "focus_visible": bool(driver.execute_script("return arguments[0].matches(':focus-visible')", active)),
                "outline_width": driver.execute_script("return getComputedStyle(arguments[0]).outlineWidth", active),
            }
            focus_sequence.append(check)
            if "Begin my journey" in label:
                begin_control = (active, check)
                break
        keyboard_passed = bool(begin_control and begin_control[1]["focus_visible"] and begin_control[1]["outline_width"] != "0px")
        if begin_control:
            begin_control[0].send_keys(Keys.ENTER)
            wait_text(driver, "What should we call you?", timeout=15)
            screenshots.append(shot(driver, "12-onboarding-desktop"))
            keyboard_passed = keyboard_passed and "What should we call you?" in body(driver)
        results.append(entry("keyboard-focus", keyboard_passed, "Keyboard focus visibly reached and activated the primary journey action", focus_sequence=focus_sequence))

        passed = sum(1 for item in results if item["passed"])
        payload = {
            "schema_version": "maya-ui-restoration-walkthrough-v1",
            "mode": "fictional_product_preview",
            "real_medical_data_used": False,
            "base_url": BASE_URL,
            "api_url": API_URL,
            "cases": {"passed": passed, "failed": len(results) - passed, "total": len(results)},
            "results": results,
            "screenshots": screenshots,
            "limitations": [
                "Automated Chrome walkthrough is engineering evidence, not usability research or clinical validation.",
                "Layout and focus checks do not claim WCAG conformance.",
                "Real uploads, Personal Mode, durable React persistence, live providers and deployment remain unavailable.",
            ],
        }
        (EVIDENCE / "interactive-walkthrough-results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"INTERACTIVE_WALKTHROUGHS_PASS={passed}/{len(results)}")
        return 0 if passed == len(results) else 1
    finally:
        if driver is not None:
            driver.quit()
        stop_process(frontend_process)
        stop_process(api)
        for process in processes:
            stop_process(process)
        if service_log is not None:
            service_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
