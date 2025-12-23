# Library imports

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pathlib import Path
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import date
from datetime import timedelta
from selenium.common import (
    NoSuchElementException,
    NoAlertPresentException,
    NoSuchFrameException,
)
from selenium.webdriver.common.alert import Alert
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import re
import os
import glob
import shutil
import base64
import pyautogui
from dotenv import load_dotenv
import pyodbc
import pyautogui
import time

# Helpers


def _try_find_click_print(driver, timeout=4):
    for by, sel in PRINT_LOCATORS:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, sel))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

            # Focus the iframe by clicking on its body
            iframe_body = driver.find_element(By.TAG_NAME, "body")
            iframe_body.click()

            try:
                # el.click()
                print("Print button clicked._try_find_click_print funtion")

                # input("checking 1")
                actions = ActionChains(driver)
                actions.key_down(Keys.CONTROL).send_keys("p").key_up(
                    Keys.CONTROL
                ).perform()

                time.sleep(2)  # wait for print dialog

                # Press TAB twice
                actions = ActionChains(driver)
                actions.send_keys(Keys.TAB).send_keys(Keys.TAB).perform()

                time.sleep(1)

                # Press ENTER
                actions = ActionChains(driver)
                actions.send_keys(Keys.ENTER).perform()

                time.sleep(6)

            except Exception:
                driver.execute_script("arguments[0].click();", el)
            return True
        except TimeoutException:
            continue
    return False


def _dfs_frames_for_print(driver, max_depth=2, timeout=6, depth=0):
    """Depth-first search within current context to find/click Print button across nested iframes."""
    if _try_find_click_print(driver, timeout=2):
        return True

    if depth >= max_depth:
        return False

    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for idx, fr in enumerate(frames):
        try:
            WebDriverWait(driver, timeout).until(
                EC.frame_to_be_available_and_switch_to_it(fr)
            )
            if _dfs_frames_for_print(
                driver, max_depth=max_depth, timeout=timeout, depth=depth + 1
            ):
                return True
        except (TimeoutException, NoSuchFrameException, StaleElementReferenceException):
            pass
        finally:
            # go back up one level before trying the next sibling frame
            try:
                driver.switch_to.parent_frame()
            except Exception:
                driver.switch_to.default_content()
    return False


def click_print_from_iframe3(driver):
    """Switch to iframe #3 (index 2). If Print isn't there, search nested iframes."""
    attempts = 1
    switch_timeout = 2
    for attempt in range(1, attempts + 1):
        try:
            driver.switch_to.default_content()
            all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if len(all_iframes) < 3:
                raise TimeoutException(
                    f"Found only {len(all_iframes)} iframes; iframe #3 not available."
                )

            # Get a fresh reference each attempt (avoid stale)
            fr = driver.find_elements(By.TAG_NAME, "iframe")[1]
            fr_id = fr.get_attribute("id")
            fr_src = fr.get_attribute("src")
            print(
                f"[INFO] Attempt {attempt}: switching to iframe 2 id={fr_id}, src starts='{(fr_src or '')[:80]}'"
            )

            WebDriverWait(driver, switch_timeout).until(
                EC.frame_to_be_available_and_switch_to_it(fr)
            )

            # 1) try directly in iframe #3
            if _try_find_click_print(driver, timeout=6):
                print("[OK] Print clicked in iframe #3.")
                driver.switch_to.default_content()
                return True

            # 2) search nested iframes inside #3 (PDF viewer often nests another iframe)
            if _dfs_frames_for_print(driver, max_depth=2, timeout=6):
                print("[OK] Print clicked in a nested iframe under iframe #3.")
                driver.switch_to.default_content()
                return True

        except (
            TimeoutException,
            NoSuchFrameException,
            StaleElementReferenceException,
        ) as e:
            print(f"[WARN] Switch/click attempt {attempt} failed: {e}")
            time.sleep(0.8)
        finally:
            driver.switch_to.default_content()

    print("[ERROR] Could not click Print via iframe #3 (and nested).")
    return False


def wait_invisibility_of_selectors(selectors, timeout=15):
    for css in selectors:
        try:
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, css))
            )
        except TimeoutException:
            pass


def js_click(el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)


def find_in_any_frame(locator, timeout=18):
    end = time.time() + timeout
    last_err = None
    while time.time() < end:
        try:
            driver.switch_to.default_content()
            el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(locator))
            return el
        except Exception as e:
            last_err = e
        frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
        for fr in frames:
            try:
                driver.switch_to.default_content()
                WebDriverWait(driver, 2).until(
                    EC.frame_to_be_available_and_switch_to_it(fr)
                )
                el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(locator))
                return el
            except Exception:
                continue
        time.sleep(0.3)
    driver.switch_to.default_content()
    raise TimeoutException(f"Not found in any frame: {locator} (last: {last_err})")


def click_retry_in_any_frame(
    locator, attempts=6, base_timeout=5, pause=0.4, wait_stale=False
):
    last_err = None
    for i in range(attempts):
        try:
            driver.switch_to.default_content()
            el = find_in_any_frame(locator, timeout=base_timeout + i * 2)
            js_click(el)
            if wait_stale:
                try:
                    WebDriverWait(driver, 2 + i).until(EC.staleness_of(el))
                except TimeoutException:
                    pass
            return True
        except (StaleElementReferenceException, WebDriverException) as e:
            last_err = e
            time.sleep(pause)
            continue
        except Exception as e:
            last_err = e
            time.sleep(pause)
    raise last_err


def wait_viewer_ready(timeout=20):
    driver.switch_to.default_content()
    time.sleep(0.6)
    wait_invisibility_of_selectors(
        [
            ".modal-backdrop.fade.in",
            ".blockUI.blockOverlay",
            ".loading-indicator",
            ".spinner",
            ".busy-indicator",
        ],
        timeout=timeout,
    )
    end = time.time() + timeout
    while time.time() < end:
        try:
            driver.switch_to.default_content()
            if driver.find_elements(
                By.CSS_SELECTOR,
                "canvas.pdfViewer, .pdfViewer, .viewerToolbar, .k-pdfviewer",
            ):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return True


def close_patient_hub_safely():
    driver.switch_to.default_content()
    wait_invisibility_of_selectors(
        [
            ".modal-backdrop.fade.in",
            ".blockUI.blockOverlay",
            ".loading-indicator",
            ".spinner",
        ],
        timeout=5,
    )
    try:
        close_btn = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.ID, "patient-hubBtn1"))
        )
        driver.execute_script(
            "arguments[0].style.position='relative';arguments[0].style.zIndex='999999';",
            close_btn,
        )
        js_click(close_btn)
        try:
            WebDriverWait(driver, 8).until(
                EC.invisibility_of_element_located((By.ID, "patient_hub"))
            )
        except Exception:
            pass
    except Exception:
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.6)
        except Exception:
            pass


def wait_and_rename_pdf(account_number, save_path, processed_path, timeout=20):
    """Original behavior for Progress Notes: {account_number}_{n}.pdf"""
    start_time = time.time()
    pdf_path = None
    while time.time() - start_time < timeout:
        pdfs = glob.glob(os.path.join(save_path, "*.pdf"))
        if pdfs:
            pdf_path = max(pdfs, key=os.path.getctime)
            break
        time.sleep(1)
    if not pdf_path:
        print(f"[WARN] PDF not generated for {account_number}")
        return
    os.makedirs(processed_path, exist_ok=True)
    counter = 1
    while True:
        filename = f"{account_number}_{counter}.pdf"
        final_path = os.path.join(processed_path, filename)
        if not os.path.exists(final_path):
            break
        counter += 1
    try:
        shutil.move(pdf_path, final_path)
        print(f"[OK] PDF saved as: {final_path}")
    except Exception as e:
        print(f"[ERROR] Error renaming/moving file: {e}")


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "document"


def wait_and_rename_pdf_with_basename(
    base_name,
    search_term,
    account_number,
    save_path,
    processed_path,
    timeout=90,
    start_time=None,
):
    """New naming for Patient Docs: {base_name}_{account_number}_{n}.pdf"""
    if start_time is None:
        start_time = time.time()
    base = slugify(base_name)
    deadline = time.time() + timeout
    pdf_path = None
    while time.time() < deadline:
        pdfs = glob.glob(os.path.join(save_path, "*.pdf"))
        pdfs = [p for p in pdfs if os.path.getctime(p) >= start_time - 0.5]
        if pdfs:
            pdf_path = max(pdfs, key=os.path.getctime)
            break
        time.sleep(1)
    if not pdf_path:
        print(f"[WARN] PDF not found after print for {account_number} (base={base})")
        return
    os.makedirs(processed_path, exist_ok=True)
    counter = 1
    while True:
        filename = f"{base}_{search_term}_{account_number}_{counter}.pdf"
        final_path = os.path.join(processed_path, filename)
        if not os.path.exists(final_path):
            break
        counter += 1
    try:
        shutil.move(pdf_path, final_path)
        print(f"[OK] PDF saved as: {final_path}")
    except Exception as e:
        print(f"[ERROR] Error renaming/moving file: {e}")


def inject_resume_button(text="Click here AFTER you finish Print → Print"):
    js = r"""
    (function(){
      try {
        if (window.__resumeDiv) return;
        const d = document.createElement('div');
        d.id='__resumeDiv';
        d.style.position='fixed';
        d.style.zIndex='2147483647';
        d.style.top='12px';
        d.style.right='12px';
        d.style.padding='10px 14px';
        d.style.background='#0b5';
        d.style.color='#fff';
        d.style.font='14px sans-serif';
        d.style.borderRadius='8px';
        d.style.boxShadow='0 2px 8px rgba(0,0,0,.25)';
        d.style.cursor='pointer';
        d.textContent = arguments[0];
        d.addEventListener('click', function(){
          try {
            document.body.dataset.resumeAutomationClicked = '1';
            d.textContent = 'Resuming...';
            d.style.background = '#777';
          } catch(e){}
        });
        document.body.appendChild(d);
        window.__resumeDiv = d;
      } catch(e) {}
    })();"""
    try:
        driver.switch_to.default_content()
        driver.execute_script(js, text)
    except Exception:
        pass


def msvcrt_available():
    try:
        import msvcrt  # noqa

        return True
    except Exception:
        return False


def wait_for_resume_click_or_console(timeout=5):
    """
    Wait until the injected Resume button is clicked *or* user presses Enter in console.
    Non-blocking – polls the page, optionally listens for Enter on Windows console.
    """
    end = time.time() + timeout
    print(
        "[WAIT] Finish Print → Print, then click the green 'Resume' button in the page OR press Enter in this console."
    )
    while time.time() < end:
        try:
            clicked = driver.execute_script(
                "return document.body && document.body.dataset && document.body.dataset.resumeAutomationClicked === '1';"
            )
            if clicked:
                try:
                    driver.execute_script(
                        """
                        try {
                           delete document.body.dataset.resumeAutomationClicked;
                           const d = document.getElementById('__resumeDiv'); if (d) d.remove();
                        } catch(e){}
                    """
                    )
                except Exception:
                    pass
                return True
        except Exception:
            pass

        # Optional: Windows console Enter key
        if msvcrt_available():
            import msvcrt

            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    try:
                        driver.execute_script(
                            "const d=document.getElementById('__resumeDiv'); if(d) d.remove();"
                        )
                    except Exception:
                        pass
                    return True
        time.sleep(0.4)
    return False


def switch_into_viewer_iframe(driver, timeout=15):
    """
    Switch into the dynamic viewer iframe (id changes like 'e375', 'd7a4', 'df29').
    Heuristics:
      1) iframe[title='webviewer']
      2) iframe[src*='ReaderControl.jsp']
      3) fallback: try each iframe and look for the print button
    Returns True if switched successfully, else False.
    """
    driver.switch_to.default_content()

    # 1) Prefer stable attributes
    candidates = driver.find_elements(
        By.CSS_SELECTOR, "iframe[title='webviewer'], iframe[src*='ReaderControl.jsp']"
    )
    if not candidates:
        candidates = driver.find_elements(By.TAG_NAME, "iframe")

    for fr in candidates:
        try:
            WebDriverWait(driver, timeout).until(
                EC.frame_to_be_available_and_switch_to_it(fr)
            )
            # Check if print button exists in this frame
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//span[@id='printButton' or (@title='Print' and contains(@class,'print'))]",
                        )
                    )
                )
                return True  # found the correct frame
            except TimeoutException:
                driver.switch_to.default_content()
                continue
        except TimeoutException:
            driver.switch_to.default_content()
            continue

    return False


def _try_click_current_context(driver, locators, timeout=3):
    for by, sel in locators:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, sel))
            )
            try:
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)
            return True
        except TimeoutException:
            continue
    return False


def _dfs_click_anywhere(driver, locators, timeout_per_level=3, max_depth=3, depth=0):
    # try in the current context
    if _try_click_current_context(driver, locators, timeout=timeout_per_level):
        return True

    if depth >= max_depth:
        return False

    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for fr in frames:
        try:
            WebDriverWait(driver, timeout_per_level).until(
                EC.frame_to_be_available_and_switch_to_it(fr)
            )
            if _dfs_click_anywhere(
                driver, locators, timeout_per_level, max_depth, depth + 1
            ):
                return True
        except (TimeoutException, NoSuchFrameException, StaleElementReferenceException):
            pass
        finally:
            try:
                driver.switch_to.parent_frame()
            except Exception:
                driver.switch_to.default_content()
    return False


def _switch_to_new_window_if_opened(driver, base_handles, wait_seconds=3):
    end = time.time() + wait_seconds
    while time.time() < end:
        handles = driver.window_handles
        if len(handles) > len(base_handles):
            # switch to the newest window
            new_handle = [h for h in handles if h not in base_handles][-1]
            driver.switch_to.window(new_handle)
            return True
        time.sleep(0.2)
    return False


def handle_print_popups_anywhere(driver):
    """
    Assumes you already clicked the Print button in the viewer.
    Handles:
      1) Optional 'Skip Adding Patient Identifiers'
      2) 'Print' (id=printStartButton)
      3) Optional 'Done'
    Searches main doc, all iframes (nested up to depth 3), and a new window if one opened.
    """
    # remember current window to switch back later
    base_handles = driver.window_handles[:]
    driver.switch_to.default_content()

    # If clicking Print opened a new window, switch to it
    _switch_to_new_window_if_opened(driver, base_handles, wait_seconds=4)

    # 1) Skip (optional)
    try:
        if _dfs_click_anywhere(driver, SKIP_LOCATORS, timeout_per_level=3, max_depth=3):
            print("[OK] Clicked 'Skip Adding Patient Identifiers'.")
        else:
            print("[INFO] Skip popup not present.")
    finally:
        driver.switch_to.default_content()

    # 2) Print start (required)
    if _dfs_click_anywhere(
        driver, PRINT_START_LOCATORS, timeout_per_level=4, max_depth=3
    ):
        print("[OK] Clicked 'Print' in popup.")
    else:
        raise TimeoutException(
            "Could not find 'Print' (printStartButton) in any context."
        )

    driver.switch_to.default_content()

    # 3) Done (optional)
    if _dfs_click_anywhere(driver, DONE_LOCATORS, timeout_per_level=3, max_depth=3):
        print("[OK] Clicked 'Done'.")
    else:
        print("[INFO] 'Done' not shown; continuing.")

    # go back to original window if we switched
    if driver.window_handles and base_handles[0] in driver.window_handles:
        try:
            driver.switch_to.window(base_handles[0])
        except Exception:
            pass
    driver.switch_to.default_content()


def click_any_image(image_paths, confidence=0.6, timeout=8, check_interval=0.5):
    """
    Try multiple images and click the first one that appears.

    :param image_paths: list of image file paths
    :param confidence: 0–1, how strict the match should be (requires OpenCV)
    :param timeout: total seconds to keep trying
    :param check_interval: seconds between checks
    :return: (True, image_path) if clicked, else (False, None)
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        for img in image_paths:
            print(f"Checking for {img} ...")
            location = pyautogui.locateCenterOnScreen(img, confidence=confidence)

            if location:
                print(f"Found {img} at {location} → clicking")
                pyautogui.moveTo(location.x, location.y, duration=0.3)
                pyautogui.click()
                return True, img

        time.sleep(check_interval)

    print("No matching popup image found within timeout.")
    return False, None


def click_if_exists(image_path, confidence=0.9, wait_time=3):
    """
    Check if the image exists on screen.
    If yes → click it.
    If no → continue without errors.
    """

    time.sleep(wait_time)

    location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)

    if location:
        print(f"{image_path} found → clicking...")
        pyautogui.moveTo(location.x, location.y, duration=0.3)
        pyautogui.click()
        return True
    else:
        print(f"{image_path} not found → skipping.")
        return False


def process_doc_type(
    search_term: str, folder_text: str, default_base: str, account_number: str
):
    """
    In Patient Docs modal:
      - types `search_term` into Quick Search
      - clicks folder with `folder_text`
      - clicks the first document under that folder (if present)
      - you click Print → Print (we pause)
      - we rename PDF as {documentname}_{account_number}_{n}.pdf
    """
    print(f"[STEP] Processing '{folder_text}'")

    # 1) Type into Quick Search
    search_ip = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "patientdocsIpt1"))
    )
    try:
        cb = driver.find_element(
            By.XPATH,
            "//input[@id='patientdocsIpt1']/preceding::input[@type='checkbox'][1]",
        )
        if cb.is_displayed() and cb.is_enabled():
            driver.execute_script("arguments[0].click();", cb)
    except Exception:
        pass
    search_ip.clear()
    search_ip.send_keys(search_term)
    search_ip.send_keys(Keys.ENTER)
    time.sleep(1)
    print(f"[OK] Searched for '{search_term}'.")

    # 2) Click the folder
    folder_locator = (
        By.XPATH,
        f"//a[@context-menu='menuOptions'][.//li[contains(normalize-space(), '{folder_text}')]]",
    )
    try:
        # click_retry_in_any_frame(folder_locator, attempts=6)
        print(f"[OK] '{folder_text}' folder clicked (expanded).")
    except Exception as e:
        print(f"[WARN] Could not click folder '{folder_text}': {e}")
        return  # nothing to do

    # 3) First document under this folder
    list_ul_locator = (
        By.XPATH,
        f"//a[@context-menu='menuOptions'][.//li[contains(normalize-space(), '{folder_text}')]]"
        "/following-sibling::ul[contains(@class,'final-dox')]",
    )
    try:
        WebDriverWait(driver, 8).until(EC.presence_of_element_located(list_ul_locator))
    except TimeoutException:
        print(f"[INFO] No list area rendered for '{folder_text}'. Skipping.")
        return

    first_doc_specific = (
        By.XPATH,
        f"{list_ul_locator[1]}//a[@id='patientdocsTreeLink1']",
    )
    first_doc_any = (
        By.XPATH,
        f"{list_ul_locator[1]}//a[starts-with(@id,'patientdocsTreeLink')]",
    )

    base_name = default_base
    try:
        candidates = driver.find_elements(*first_doc_specific)
        if not candidates:
            candidates = driver.find_elements(*first_doc_any)
        if not candidates:
            print(f"[INFO] No documents under '{folder_text}'. Skipping.")
            return

        first_link = candidates[0]
        try:
            label_el = first_link.find_element(By.XPATH, "./ul/li")
            label_text = label_el.text.strip()
            if label_text:
                base_name = slugify(label_text)[:60]
                print(f"[INFO] Using item label for base_name: {base_name}")
        except Exception:
            print("[INFO] Could not extract document label; using default base name.")
    except Exception as e:
        print(f"[INFO] Could not inspect first document label: {e}")

    try:
        try:
            click_retry_in_any_frame(first_doc_specific, attempts=4)
        except Exception:
            click_retry_in_any_frame(first_doc_any, attempts=6)
        print(f"[OK] First document clicked for '{folder_text}'.")
    except Exception as e:
        print(f"[WARN] Could not click first document for '{folder_text}': {e}")
        return

    # 4) Let viewer load and hand off to you for Print -> Print
    wait_viewer_ready(timeout=5)

    before_windows = set(driver.window_handles)
    print_trigger_time = time.time()

    try:
        # Debug info
        current_frame = driver.execute_script("return self.name")
        print("Current frame name:", current_frame)

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print("Total iframes on page:", len(iframes))

        viewer_iframe = iframes[2]
        print("Using iframe 3 -> id:", viewer_iframe.get_attribute("id"))

        for idx, iframe in enumerate(iframes, start=1):
            print(
                f"Iframe {idx}: id={iframe.get_attribute('id')} name={iframe.get_attribute('name')} src={iframe.get_attribute('src')}"
            )

        success = click_print_from_iframe3(driver=driver)
        if not success:
            print("Print button not found/clickable.")
        else:
            print("[OK] Print button clicked via iframe #3 method.")

        driver.switch_to.default_content()

    except Exception as e:
        print(f"[WARN] Could not complete Print flow for '{folder_text}': {e}")
    finally:
        # Always return to main document
        driver.switch_to.default_content()

    # Handle print-preview window (if any)
    time.sleep(1.0)
    after_windows = set(driver.window_handles)
    new_windows = list(after_windows - before_windows)
    if new_windows:
        preview_handle = new_windows[0]
        try:
            driver.switch_to.window(preview_handle)
            time.sleep(3)  # allow kiosk print to write file
            driver.close()
            driver.switch_to.window(list(before_windows)[0])
            print("[OK] Closed print preview window.")
        except Exception as e:
            print(f"[INFO] Could not close preview window (continuing): {e}")
    else:
        time.sleep(3)

    # 5) Rename saved PDF
    wait_and_rename_pdf_with_basename(
        base_name,
        search_term,
        account_number,
        save_path,
        processed_path,
        timeout=90,
        start_time=print_trigger_time,
    )
    print(f"[OK] Saved '{folder_text}' PDF.\n")


def GetAccount_FromExcel():
    ############ Load Accounts from Excel ############
    excel_path = r"C:\\code\\potomac\\accounts.xlsx"  # <-- put your file path here
    df_accounts = pd.read_excel(excel_path)

    if "Account_no" in df_accounts.columns:
        ACCOUNTS = [str(x).strip() for x in df_accounts["Account_no"] if pd.notna(x)]
    else:
        ACCOUNTS = [str(x).strip() for x in df_accounts.iloc[:, 0] if pd.notna(x)]

    print(f"Loaded {len(ACCOUNTS)} account(s) from Excel.")


def load_accounts_from_sql(
    practice_id: int = 2113, lookback_days: int = 4
) -> list[str]:
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )

    sql = """
    SELECT DISTINCT a.account
    FROM tbl_order a
    INNER JOIN tbl_patient_insurance b
        ON a.[Patient Insurance Map ID] = b.ID
    INNER JOIN tbl_insurance c
        ON c.[Insurance ID] = b.[Insurance ID]
    INNER JOIN tbl_order_procedure d
        ON d.[Order ID] = a.[Order ID]
    LEFT JOIN tbl_order_documents e
        ON e.[Order ID] = a.[Order ID]
    WHERE CAST(a.[Creation Date] AS date) >= DATEADD(day, -?, CAST(GETDATE() AS date))
      AND a.[Practice ID] = ?
      AND e.[document id] IS NULL
    """

    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(sql, conn, params=[lookback_days, practice_id])

    # Clean + normalize
    accounts = df["account"].dropna().astype(str).str.strip().tolist()

    # Optional: dedupe while preserving order
    seen = set()
    accounts = [x for x in accounts if not (x in seen or seen.add(x))]

    print(f"Loaded {len(accounts)} account(s) from SQL Server.")
    return accounts


def wait_and_rename_pdf(account_number, save_path, processed_path, timeout=60):
    """
    Waits for Chrome's downloaded PDF in save_path (e.g., 'download.pdf', 'download (1).pdf'),
    then moves it to processed_path with the name:
        progress_notes_<account_number>_<counter>.pdf
    where counter auto-increments if a file already exists.
    """
    os.makedirs(processed_path, exist_ok=True)

    start = time.time()
    pdf_path = None
    last_size = -1

    # Wait for a new PDF to appear
    while time.time() - start < timeout:
        # ignore temp Chrome files
        candidates = [
            p
            for p in glob.glob(os.path.join(save_path, "*.pdf"))
            if not p.endswith(".crdownload")
        ]
        if candidates:
            # newest by ctime
            pdf_path = max(candidates, key=os.path.getctime)
            # ensure it has stopped growing (not being written)
            size = os.path.getsize(pdf_path)
            if size == last_size:
                break
            last_size = size
        time.sleep(1)

    if not pdf_path:
        print(f"PDF not generated for {account_number}")
        return

    # Build final name with auto-increment
    counter = 1
    while True:
        filename = f"progress_notes_{account_number}_{counter}.pdf"
        final_path = os.path.join(processed_path, filename)
        if not os.path.exists(final_path):
            break
        counter += 1

    try:
        shutil.move(pdf_path, final_path)
        print(f"PDF saved as: {final_path}")
    except Exception as e:
        print(f"Error renaming/moving file: {e}")


def click_if_present_by_id(id_value, wait_seconds=8):
    # 1) Try default content
    driver.switch_to.default_content()
    try:
        el = WebDriverWait(driver, wait_seconds).until(
            EC.element_to_be_clickable((By.ID, id_value))
        )
        try:
            el.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", el)
        return True
    except TimeoutException:
        pass

    # 2) Try frames
    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for f in frames:
        driver.switch_to.default_content()
        driver.switch_to.frame(f)
        try:
            el = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.ID, id_value))
            )
            try:
                el.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", el)
            return True
        except TimeoutException:
            continue

    driver.switch_to.default_content()
    return False


def close_patient_hub_if_exists(driver, timeout=3):
    try:
        close_btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "patient-hubBtn1"))
        )

        # Scroll into view (handles resolution / hidden cases)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", close_btn
        )

        # JS click bypasses overlay / z-index issues
        driver.execute_script("arguments[0].click();", close_btn)

        print("Patient hub modal closed.")
    except TimeoutException:
        print("Patient hub close button not found. Continuing.")


def close_modal_if_exists(driver, timeout=3):
    try:
        close_btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "savePrompt-tplBtn1"))
        )

        # Scroll into view (handles small screens)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", close_btn
        )

        # JS click bypasses overlay / hidden issues
        driver.execute_script("arguments[0].click();", close_btn)

        print("Modal close button clicked.")
    except TimeoutException:
        print("Close button not found. Continuing.")


def click_duplicate_patient_if_exists(driver, timeout=3):
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "DuplicatePatientWarningBtn3"))
        )
        driver.execute_script("arguments[0].click();", btn)
        print("Duplicate patient popup clicked via JS.")
    except TimeoutException:
        pass


def handle_other_popups_if_exists(driver):
    try:
        # 1️⃣ Bootbox / modal OK button (your new case)
        ok_buttons = driver.find_elements(
            By.CSS_SELECTOR, "button[data-bb-handler='cancel']"
        )
        if ok_buttons:
            driver.execute_script("arguments[0].click();", ok_buttons[0])
            print("Bootbox OK popup clicked.")
            return

        # 2️⃣ Generic OK / Yes / Continue buttons
        generic_buttons = driver.find_elements(
            By.XPATH,
            "//button[normalize-space()='OK' or normalize-space()='Ok' "
            "or normalize-space()='Yes' or normalize-space()='Continue']",
        )
        if generic_buttons:
            driver.execute_script("arguments[0].click();", generic_buttons[0])
            print("Generic popup button clicked.")
            return

        # 3️⃣ Close (×) buttons
        close_buttons = driver.find_elements(By.CSS_SELECTOR, "button.close")
        if close_buttons:
            driver.execute_script("arguments[0].click();", close_buttons[0])
            print("Popup closed via close icon.")
            return

        # 4️⃣ ESC key fallback (safe even if no modal)
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)

    except Exception:
        # Absolutely silent – no errors raised
        pass


def get_visible_search():
    elems = driver.find_elements(By.ID, "searchText")
    elems = [e for e in elems if e.is_displayed()]
    return elems[0] if elems else None


# ---------- Configurable locators ----------

PRINT_LOCATORS = [
    (By.ID, "printButton"),
    (By.CSS_SELECTOR, "span.glyphicons.print[title='Print']"),
    (By.XPATH, "//span[@id='printButton']"),
    (By.XPATH, "//span[@title='Print' and contains(@class,'print')]"),
]

SKIP_LOCATORS = [
    (
        By.XPATH,
        "//button[.//span[normalize-space(text())='Skip Adding Patient Identifiers']]",
    ),
    (By.XPATH, "//button[normalize-space()='Skip Adding Patient Identifiers']"),
    (
        By.XPATH,
        "//span[normalize-space(text())='Skip Adding Patient Identifiers']/ancestor::button[1]",
    ),
]

PRINT_START_LOCATORS = [
    (By.ID, "printStartButton"),
    (By.CSS_SELECTOR, "button#printStartButton"),
    (By.XPATH, "//button[.//span[normalize-space(.)='Print']]"),
    (By.XPATH, "//button[normalize-space(.)='Print']"),
]

DONE_LOCATORS = [
    (By.XPATH, "//button[.//span[normalize-space(.)='Done']]"),
    (By.XPATH, "//button[normalize-space(.)='Done']"),
]

# Global Varibles

load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")


def main():
    ACCOUNTS = load_accounts_from_sql(practice_id=2113, lookback_days=4)
    url = os.getenv("URL")
    usr = os.getenv("USR")
    pwd = os.getenv("PWD")
    ACCOUNT_NO = os.getenv("ACCOUNT_NO")

    today = date.today()

    todate = today.strftime("%m/%d/%Y")

    fromdate = (today - timedelta(days=15)).strftime("%m/%d/%Y")

    global save_path, processed_path
    save_path = r"C:\\code\\potomac\\Notes"
    processed_path = r"C:\\code\\potomac\\Notes\\Processed"

    os.makedirs(save_path, exist_ok=True)

    options = webdriver.ChromeOptions()
    prefs = {
        "printing.print_preview_sticky_settings.appState": """
        {
            "recentDestinations": [{"id": "Save as PDF", "origin": "local"}],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }
        """,
        "savefile.default_directory": save_path,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--kiosk-printing")

    options.add_argument("--start-maximized")
    global driver
    driver = webdriver.Chrome(options=options)

    driver.maximize_window()

    driver.get(url)
    time.sleep(10)

    driver.find_element(
        "xpath", "/html/body/div/div[1]/div[1]/div[1]/div[4]/div/div/div[1]/div/input"
    ).send_keys(usr)

    # click_next
    driver.find_element(
        "xpath", "/html/body/div/div[1]/div[1]/div[1]/div[4]/div/div/div[3]/input"
    ).click()

    # password
    driver.find_element(
        "xpath",
        "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[2]/div[3]/div[1]/input",
    ).send_keys(pwd)
    # Login
    driver.find_element(
        "xpath",
        "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[2]/div[4]/input",
    ).send_keys(Keys.ENTER)

    input("Press Enter after login to continue...")

    for ACCOUNT_NO in ACCOUNTS:
        print(f"\n========== Processing account: {ACCOUNT_NO} ==========\n")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        try:
            popup_close = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'btn-lblue') and text()='Close']",
                    )
                )
            )
            popup_close.click()
            print("Popup closed.")
        except TimeoutException:
            print("Popup not found — proceeding...")

        try:
            # Important codes
            wait = WebDriverWait(driver, 20)

            # 1. Click "Action" dropdown toggle
            action_dropdown = wait.until(
                EC.element_to_be_clickable((By.ID, "jellybean-panelLink66"))
            )
            action_dropdown.click()

            # 2. Click "Patient Lookup" from dropdown
            patient_lookup = wait.until(
                EC.element_to_be_clickable((By.ID, "jellybean-panelLink67"))
            )
            patient_lookup.click()

            dropdown_container = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class,'dropdown') and contains(@class,'mt5')]"
                        "[.//div[@title='Name' and @data-toggle='dropdown']]",
                    )
                )
            )
            print("Dropdown container found.")
            trigger = dropdown_container.find_element(
                By.XPATH, ".//div[@title='Name' and @data-toggle='dropdown']"
            )

            # Bring into view & click (JS click is more reliable with Angular/Bootstrap dropdowns)
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", trigger
            )
            try:
                wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, ".//div[@title='Name' and @data-toggle='dropdown']")
                    )
                )
                trigger.click()
            except Exception:
                driver.execute_script("arguments[0].click();", trigger)

            # 2) Wait for the dropdown menu to be visible
            menu = wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class,'dropdown') and contains(@class,'mt5')]//ul[contains(@class,'dropdown-menu')]",
                    )
                )
            )

            # 3) Click "Acct No (MRN)" inside this menu
            # (Some items may be hidden via ng-hide; target the visible one)
            acct_item = wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//ul[contains(@class,'dropdown-menu')]//*[normalize-space(text())='Acct No (MRN)']",
                    )
                )
            )

            try:
                acct_item.click()
            except Exception:
                ActionChains(driver).move_to_element(acct_item).click().perform()

            # 1) Wait for the real input to show up
            wait.until(lambda d: get_visible_search() is not None)
            search_box = get_visible_search()

            # 2) Bring into view & try normal typing first
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", search_box
                )
                wait.until(EC.element_to_be_clickable((By.ID, "searchText")))
                search_box.click()
                # clear robustly
                search_box.send_keys(Keys.CONTROL, "a")
                search_box.send_keys(Keys.BACKSPACE)
                search_box.send_keys(ACCOUNT_NO)
            except (
                ElementNotInteractableException,
                StaleElementReferenceException,
                TimeoutException,
            ):
                # 3) JS fallback: set value + fire Angular-friendly events
                search_box = get_visible_search() or driver.find_element(
                    By.ID, "searchText"
                )
                driver.execute_script(
                    """
                    const el = arguments[0], val = arguments[1];
                    try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch(e){}
                    el.focus();
                    // clear existing text
                    el.value = '';
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    // set new value
                    el.value = val;
                    // notify frameworks (Angular listens to input/change)
                    el.dispatchEvent(new Event('input',  { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                    search_box,
                    ACCOUNT_NO,
                )

            # 4) Ensure value really landed, then submit (ENTER)
            wait.until(
                lambda d: (get_visible_search() or search_box).get_attribute("value")
                == ACCOUNT_NO
            )

            try:
                (get_visible_search() or search_box).send_keys(Keys.ENTER)
            except Exception:
                # Fallback: dispatch an ENTER keypress via JS
                driver.execute_script(
                    """
                    const el = arguments[0];
                    el.focus();
                    ['keydown','keypress','keyup'].forEach(t => {
                    const e = new KeyboardEvent(t, { key: 'Enter', code: 'Enter', which: 13, keyCode: 13, bubbles: true });
                    el.dispatchEvent(e);
                    });
                """,
                    get_visible_search() or search_box,
                )

            # Wait for results to load (table rows present)
            # Then click the "First Name" of the first row (dynamic id; use contains)
            first_name = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "(//td[contains(@class,'patientName')]//span[contains(@id,'patientFName')])[1]",
                    )
                )
            )
            # Ensure it’s interactable; JS-click fallback avoids overlay issues
            try:
                first_name.click()
            except Exception:
                driver.execute_script("arguments[0].click();", first_name)

            print("First name clicked, loading patient details...")
            time.sleep(5)
            print("now starting old code")
            click_duplicate_patient_if_exists(driver)
            time.sleep(1)
            handle_other_popups_if_exists(driver)
            # input("Press Enter to continue to the next step...")
            # --- 1) If a duplicate patient warning (or any modal) is up, stop for user action ---
            try:
                modal = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            "//div[contains(@class,'modal') and (contains(@class,'in') or contains(@class,'show'))]",
                        )
                    )
                )

                print("⚠️ Duplicate patient warning (or another modal) is open.")
                print("Please handle it manually in the browser (click OK / Cancel).")
                input(
                    "Press Enter here in the console once you've closed the modal... "
                )

                # Wait until the modal is actually gone before proceeding
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located(
                        (
                            By.XPATH,
                            "//div[contains(@class,'modal') and (contains(@class,'in') or contains(@class,'show'))]",
                        )
                    )
                )
            except TimeoutException:
                # No modal visible; continue
                pass

            wait.until(EC.element_to_be_clickable((By.ID, "patient-hubLink12"))).click()
            table_rows = wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//table[@id='Encounter-lookupTbl2']//tr[.//span[contains(@ng-bind, 'enc.status')]]",
                    )
                )
            )
            count = 0
            print("Total encounter rows found:", len(table_rows))
            print("table rows details:", [row.text for row in table_rows])

            for idx, row in enumerate(table_rows, start=1):
                try:

                    status_span = row.find_element(
                        By.XPATH, ".//span[contains(@ng-bind, 'enc.status')]"
                    )
                    status = status_span.text.strip()
                    if status == "CHK" and count == 0:
                        count = count + 1
                        type_cell = row.find_element(
                            By.XPATH, ".//td[contains(@ng-click,'viewEncClick')]"
                        )
                        print(
                            f"[Row {idx}] Clicking Type with CHK status: {type_cell.text.strip()}"
                        )

                        driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                            type_cell,
                        )
                        # wait.until(EC.element_to_be_clickable(type_cell))
                        print(
                            f"DOM CHK row: idx={idx}, type={type_cell.text.strip()}, displayed={row.is_displayed()}"
                        )
                        driver.execute_script("arguments[0].click();", type_cell)
                        print("Type clicked.")
                        time.sleep(3)
                        try:
                            print("Waiting for expanded view to load...")
                            print_button = wait.until(
                                EC.presence_of_element_located((By.ID, "printID"))
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView(true);", print_button
                            )
                            driver.execute_script("arguments[0].click();", print_button)

                            print("Expanded view loaded successfully.")
                        except TimeoutException:
                            print(f"[Row {idx}] Error: Expanded view did not load.")
                            continue

                        print("Print button clicked.")
                        time.sleep(3)

                        wait_and_rename_pdf(ACCOUNT_NO, save_path, processed_path)
                        print("PDF saved and renamed successfully.")
                        close_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH,
                                    "//button[@class='close' and @ng-click='encDtlCtrl.closeEncouterPreviewDialog()']",
                                )
                            )
                        )
                        close_button.click()
                        print("Close button clicked.")
                    else:
                        print(f"[Row {idx}] Skipped - Status: {status}")
                except Exception as e:
                    print(f"[Row {idx}] Skipped - No status found or error: {str(e)}")
                    continue
            try:
                encounter_close_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "Encounter-lookupBtn1"))
                )
                encounter_close_btn.click()
                print("Closed Encounter modal.")
            except Exception as e:
                print(f"Could not close Encounter modal: {e}")
            # ==========================
            # PATIENT DOCS → MULTIPLE FOLDERS (left-click only)
            # ==========================
            try:
                # Open Patient Docs once
                docs_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "patient-hubBtn11"))
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});",
                    docs_btn,
                )
                driver.execute_script("arguments[0].click();", docs_btn)
                print("[OK] Opened Patient Docs.")

                # Process each requested document type
                doc_jobs = [
                    ("X-Ray Documents", "X-Ray Documents", "xraydocument"),
                    ("Referrals", "Referrals", "referrals"),
                    ("Lab Documents", "Lab Documents", "lab_documents"),
                    ("Path Report", "Path Report", "path_report"),
                    (
                        " IS_Radiology",
                        "IS_Radiology",
                        "is_radiology",
                    ),  # note leading space
                    # ("Scheduled Surgery", "Scheduled Surgery", "Scheduled_Surgery"),
                ]

                for search_term, folder_text, default_base in doc_jobs:
                    try:
                        process_doc_type(
                            search_term, folder_text, default_base, ACCOUNT_NO
                        )
                    except Exception as e:
                        print(f"[WARN] '{folder_text}' flow error: {e}")
                # close it

            except Exception as e:
                print(f"[WARN] Patient Docs open/process error: {e}")
        except Exception as e:
            print(f"[WARN] Patient Docs open/process error: {e}")

        # close all pages
        OUTPUT_FOLDER_PATH = r"C:\code\potomac\Notes"

        for filename in os.listdir(OUTPUT_FOLDER_PATH):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(OUTPUT_FOLDER_PATH, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        print("All PDF files deleted from the folder (subfolders untouched).")
        close_modal_if_exists(driver)
        time.sleep(2)
        close_patient_hub_if_exists(driver)
        time.sleep(2)
        # input("Press Enter to continue to the next account...")


if __name__ == "__main__":
    main()
