"""
Debug utilities to find actual selectors on the page.
"""

from playwright.async_api import Page
from loguru import logger


async def find_all_buttons_with_text(page: Page, search_text: str) -> list:
    """
    Find all buttons/links containing specific text.
    
    Args:
        page: Playwright page object
        search_text: Text to search for
        
    Returns:
        List of element info dicts
    """
    results = []
    try:
        # Find all buttons and links
        elements = await page.query_selector_all("button, a")
        
        for element in elements:
            try:
                text = await element.text_content()
                if text and search_text.lower() in text.lower():
                    tag = await element.evaluate("el => el.tagName")
                    classes = await element.get_attribute("class") or ""
                    element_id = await element.get_attribute("id") or ""
                    href = await element.get_attribute("href") or ""
                    data_testid = await element.get_attribute("data-testid") or ""
                    data_qa = await element.get_attribute("data-qa") or ""
                    
                    # Generate possible selectors
                    selectors = []
                    if element_id:
                        selectors.append(f"#{element_id}")
                    if classes:
                        for cls in classes.split():
                            if cls:
                                selectors.append(f".{cls}")
                    if data_testid:
                        selectors.append(f"[data-testid='{data_testid}']")
                    if data_qa:
                        selectors.append(f"[data-qa='{data_qa}']")
                    if href:
                        selectors.append(f"a[href='{href}']")
                    selectors.append(f"{tag.lower()}:has-text('{text.strip()}')")
                    
                    results.append({
                        "text": text.strip(),
                        "tag": tag,
                        "id": element_id,
                        "class": classes,
                        "href": href,
                        "data-testid": data_testid,
                        "data-qa": data_qa,
                        "selectors": selectors,
                        "is_visible": await element.is_visible(),
                    })
            except:
                continue
        
        return results
    except Exception as e:
        logger.error(f"Error finding buttons: {e}")
        return []


async def find_all_textareas(page: Page) -> list:
    """
    Find all textareas and contenteditable elements on the page.
    
    Args:
        page: Playwright page object
        
    Returns:
        List of element info dicts
    """
    results = []
    try:
        # Find textareas
        textareas = await page.query_selector_all("textarea")
        for element in textareas:
            try:
                placeholder = await element.get_attribute("placeholder") or ""
                name = await element.get_attribute("name") or ""
                element_id = await element.get_attribute("id") or ""
                classes = await element.get_attribute("class") or ""
                
                selectors = []
                if element_id:
                    selectors.append(f"textarea#{element_id}")
                if name:
                    selectors.append(f"textarea[name='{name}']")
                if placeholder:
                    selectors.append(f"textarea[placeholder='{placeholder}']")
                if classes:
                    for cls in classes.split():
                        if cls:
                            selectors.append(f"textarea.{cls}")
                selectors.append("textarea")
                
                results.append({
                    "type": "textarea",
                    "placeholder": placeholder,
                    "name": name,
                    "id": element_id,
                    "class": classes,
                    "selectors": selectors,
                    "is_visible": await element.is_visible(),
                })
            except:
                continue
        
        # Find contenteditable divs
        contenteditables = await page.query_selector_all("[contenteditable='true']")
        for element in contenteditables:
            try:
                classes = await element.get_attribute("class") or ""
                element_id = await element.get_attribute("id") or ""
                
                selectors = []
                if element_id:
                    selectors.append(f"#{element_id}")
                if classes:
                    for cls in classes.split():
                        if cls:
                            selectors.append(f".{cls}")
                selectors.append("div[contenteditable='true']")
                
                results.append({
                    "type": "contenteditable",
                    "id": element_id,
                    "class": classes,
                    "selectors": selectors,
                    "is_visible": await element.is_visible(),
                })
            except:
                continue
        
        return results
    except Exception as e:
        logger.error(f"Error finding textareas: {e}")
        return []


async def find_all_iframes(page: Page) -> list:
    """
    Find all iframes on the page.
    
    Args:
        page: Playwright page object
        
    Returns:
        List of iframe info
    """
    results = []
    try:
        iframes = await page.query_selector_all("iframe")
        for i, iframe in enumerate(iframes):
            try:
                src = await iframe.get_attribute("src") or ""
                element_id = await iframe.get_attribute("id") or ""
                classes = await iframe.get_attribute("class") or ""
                
                # Try to access iframe content
                frame = await iframe.content_frame()
                textareas_in_frame = []
                if frame:
                    try:
                        frame_textareas = await frame.query_selector_all("textarea, [contenteditable='true']")
                        textareas_in_frame = [f"textarea in iframe #{i}"]
                    except:
                        pass
                
                results.append({
                    "index": i,
                    "src": src,
                    "id": element_id,
                    "class": classes,
                    "has_content": frame is not None,
                    "textareas_inside": textareas_in_frame,
                })
            except:
                continue
        
        return results
    except Exception as e:
        logger.error(f"Error finding iframes: {e}")
        return []


async def debug_page_elements(page: Page, step: str = "") -> None:
    """
    Debug function to find all relevant elements on the page.
    Prints all possible selectors for buttons, textareas, etc.
    
    Args:
        page: Playwright page object
        step: Description of current step (e.g., "after_message_button_click")
    """
    logger.info(f"🔍 DEBUG: Analyzing page elements - {step}")
    logger.info("=" * 60)
    
    # Find message/contact buttons
    logger.info("📌 Searching for 'Nachricht'/'Kontakt' buttons...")
    buttons = await find_all_buttons_with_text(page, "nachricht")
    buttons.extend(await find_all_buttons_with_text(page, "kontakt"))
    buttons.extend(await find_all_buttons_with_text(page, "schreiben"))
    
    if buttons:
        logger.info(f"Found {len(buttons)} relevant buttons:")
        for i, btn in enumerate(buttons, 1):
            logger.info(f"\n  Button #{i}:")
            logger.info(f"    Text: {btn['text']}")
            logger.info(f"    Tag: {btn['tag']}")
            logger.info(f"    ID: {btn['id']}")
            logger.info(f"    Class: {btn['class']}")
            logger.info(f"    Visible: {btn['is_visible']}")
            logger.info(f"    Suggested selectors:")
            for sel in btn['selectors'][:5]:  # Show first 5
                logger.info(f"      - {sel}")
    else:
        logger.warning("❌ No 'Nachricht'/'Kontakt' buttons found!")
    
    logger.info("\n" + "-" * 60)
    
    # Find textareas
    logger.info("📌 Searching for textareas and contenteditable elements...")
    textareas = await find_all_textareas(page)
    
    if textareas:
        logger.info(f"Found {len(textareas)} textarea/contenteditable elements:")
        for i, ta in enumerate(textareas, 1):
            logger.info(f"\n  Element #{i}:")
            logger.info(f"    Type: {ta['type']}")
            if 'placeholder' in ta:
                logger.info(f"    Placeholder: {ta['placeholder']}")
            if 'name' in ta:
                logger.info(f"    Name: {ta['name']}")
            logger.info(f"    ID: {ta.get('id', '')}")
            logger.info(f"    Class: {ta.get('class', '')}")
            logger.info(f"    Visible: {ta['is_visible']}")
            logger.info(f"    Suggested selectors:")
            for sel in ta['selectors'][:5]:
                logger.info(f"      - {sel}")
    else:
        logger.warning("❌ No textareas or contenteditable elements found!")
    
    logger.info("\n" + "-" * 60)
    
    # Find iframes
    logger.info("📌 Searching for iframes...")
    iframes = await find_all_iframes(page)
    
    if iframes:
        logger.info(f"Found {len(iframes)} iframes:")
        for iframe in iframes:
            logger.info(f"  Iframe #{iframe['index']}:")
            logger.info(f"    Src: {iframe['src']}")
            logger.info(f"    Has content: {iframe['has_content']}")
            if iframe['textareas_inside']:
                logger.info(f"    Textareas inside: {iframe['textareas_inside']}")
    else:
        logger.info("No iframes found")
    
    logger.info("=" * 60)

