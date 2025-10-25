
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)
from selenium.webdriver.support import expected_conditions as EC
import re
import time


SYOSETU_URL = "https://ncode.syosetu.com/"


def get_episode_id(url: str) -> str | None:
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts[-1].isdigit() else None

def extract_main_novel_body(html: str) -> str | None:
    pattern = re.compile(
        r'<div\s+class="js-novel-text\s+p-novel__text".*?</div>',
        re.DOTALL
    )
    match = pattern.search(html)
    if match:
        return match.group(0)
    else:
        return None

def clean_novel_body(html: str | None) -> str | None:
    """ clean up ruby tags and etc, from novel_body html.
    """
    
    if not html:
        return None
    
    ruby_cleaned_html = re.sub(
        r'<ruby>(.*?)<rp>.*?</rp><rt>(.*?)</rt>(.*?)</ruby>',
        r'\1(\2)\3',
        html
    )
    tag_cleaned_html = re.sub(r'<.*?>', '', ruby_cleaned_html)

    return tag_cleaned_html


class Crawler():
    """
    본 프로젝트에서는 비동기 크롤링을 하지 않으므로, 모든 기능을 클래스 함수로 구현함.
    """
    browser = None
    
    def _open():
        Crawler.browser = webdriver.Chrome()
    
    def _close():
        Crawler.browser.quit()
    
    
    def crawl_syosetu_episode(
        novel_id: str,
        episode_id: str
    ) -> list[dict|str|None] | None:
        """
        crawl novel text from [syosetukani narou], with novel_id and episode_id.
        TimeoutException | no page error -> return error message str
        return [episode_text, next_episode]
        no next episode -> next_episode = None
        """
        
        start_time = time.time()
        
        if not Crawler.browser:
            Crawler._open()
        for _ in range(10):
            try:
                print(str(SYOSETU_URL + novel_id + "/" + episode_id))
                Crawler.browser.get(SYOSETU_URL + novel_id + "/" + episode_id)
                break
            except WebDriverException:
                Crawler._close()
                Crawler._open()
            
        try:
            WebDriverWait(Crawler.browser, 300).until(
                EC.presence_of_element_located(
                    (
                        By.CLASS_NAME,
                        "p-novel__body"
                    )
                )
            )
        except TimeoutException:
            print(f"{novel_id} - {episode_id} : timeout")
            return None
        
        try:
            Crawler.browser.find_element(
                By.CLASS_NAME,
                "p-novel__body"
            )
        except NoSuchElementException:
            print(f"{novel_id} - {episode_id} : page_error")
            return None
        
        print("loaded")

        chapter = Crawler.browser.find_elements(
            By.TAG_NAME,
            "span"
        )[5].text.strip()
        
        title = Crawler.browser.find_element(
            By.TAG_NAME,
            "h1"
        ).text.strip()
    
        novel_body_element = Crawler.browser.find_element(
            By.CLASS_NAME,
            "p-novel__body"
        )
        novel_body = novel_body_element.get_attribute("innerHTML")
        main_novel_body = extract_main_novel_body(novel_body)
        text = clean_novel_body(main_novel_body)
        
        episode_data = {
            "chapter": chapter,
            "title": title,
            "text": text
        }
        
        try:
            next_link = Crawler.browser.find_element(
                By.XPATH,
                '//a[contains(text(), "次へ")]'
            ).get_attribute("href")
            next_episode_id = get_episode_id(next_link)
        except NoSuchElementException:
            next_episode_id = None
        
        passed_time = time.time() - start_time
        if passed_time < 0.5:
            time.sleep(0.5 - passed_time)
        
        return [episode_data, next_episode_id]
