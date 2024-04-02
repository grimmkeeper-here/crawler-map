import json
import re
import time
from collections.abc import Generator
from typing import List, Optional

from pydantic import BaseModel
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# DEFINE
PARSING_URL = "https://www.google.com/maps/search/Company/@10.4655968,105.6244045,15z/data=!4m6!2m5!3m4!2s10.465339,+105.634508!4m2!1d105.6345085!2d10.4653385?entry=ttu"  # noqa: E501
FILE_JSON = "data.json"


class ParserRecord(BaseModel):
    name: Optional[str]
    type: Optional[str]
    address: Optional[str]
    phone: Optional[str]


def is_phone_number(phone: str) -> bool:
    if "Open" in phone or "Closes" in phone:
        return False
    regex = r"[+\d][+ \d]*[\d]"
    matches = re.findall(regex, phone, re.MULTILINE)
    return len(matches) > 0


def export_json_file(data: List[ParserRecord]) -> None:
    with open(FILE_JSON, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class WebParser:
    def scroll_page(self, driver: webdriver.Chrome) -> WebElement:
        """
        Find element here
        """
        # Local var
        scroll_xpath = '//div[contains(@aria-label, "Results for")]'
        end_page_xpath = (
            '//span[contains(text(), "You\'ve reached the end of the list.")]'
        )
        interval = 1  # seconds
        scroll_length = 2000

        # Wait until scroll bar already load
        WebDriverWait(driver=driver, timeout=interval).until(
            EC.visibility_of_element_located((By.XPATH, scroll_xpath))
        )
        ele = driver.find_element(By.XPATH, scroll_xpath)

        # Scroll to end of page
        end_ele = None
        try:
            end_ele = driver.find_element(By.XPATH, end_page_xpath)
        except NoSuchElementException:
            pass

        # Scroll until find element end of page
        while not end_ele:
            time.sleep(interval)
            scroll_origin = ScrollOrigin.from_element(ele)
            ActionChains(driver).scroll_from_origin(
                scroll_origin, 0, scroll_length
            ).perform()
            try:
                end_ele = driver.find_element(By.XPATH, end_page_xpath)
            except NoSuchElementException:
                pass

        return ele

    def crawl_record(
        self, parent_ele: WebElement
    ) -> Generator[WebElement, None, None]:  # noqa: E501
        # Local var
        ele_xpath = "div"

        for ele in parent_ele.find_elements(By.XPATH, ele_xpath):
            yield ele

    def parse_record_info(self, parent_ele: WebElement) -> ParserRecord:
        result = ParserRecord(name=None, type=None, address=None, phone=None)
        # Local var
        ele_xpath = 'div[1]/div[2]/div[4]/div[1]/div[1]/div[1]/div[contains(@class, "fontBodyMedium")]'  # noqa: E501

        name_xpath = 'div[1]/div[contains(@class, "fontHeadlineSmall")]'
        type_xpath = "div[4]/div[1]/span[1]"
        addr_xpath = "div[4]/div[1]/span[2]/span[2]"
        phone_xpath_1 = "div[4]/div[2]/span/span"
        phone_xpath_2 = "div[4]/div[2]/span[2]/span[2]"

        ele = None
        try:
            ele = parent_ele.find_element(By.XPATH, ele_xpath)

        except NoSuchElementException:
            pass

        if ele:
            try:
                result.name = ele.find_element(By.XPATH, name_xpath).text
            except NoSuchElementException:
                pass

            try:
                result.type = ele.find_element(By.XPATH, type_xpath).text
            except NoSuchElementException:
                pass

            try:
                result.address = ele.find_element(By.XPATH, addr_xpath).text
            except NoSuchElementException:
                pass

            phone: str = ""
            try:
                phone = ele.find_element(By.XPATH, phone_xpath_1).text
            except NoSuchElementException:
                pass

            if len(phone) == 0 or not is_phone_number(phone):
                try:
                    phone = ele.find_element(By.XPATH, phone_xpath_2).text
                except NoSuchElementException:
                    pass
            if len(phone) != 0 and is_phone_number(phone):
                result.phone = phone

        return result


def main():
    # Init webdriver
    web_parser = WebParser()
    driver = webdriver.Chrome()
    # Open web driver
    driver.get(PARSING_URL)

    # Scroll all page
    parent_ele = web_parser.scroll_page(driver=driver)

    list_result: list = []
    for record in web_parser.crawl_record(parent_ele):
        if not record.get_attribute("class"):
            parsing_record = web_parser.parse_record_info(record)
            if parsing_record.name:
                list_result.append(parsing_record.__dict__)

    export_json_file(data=list_result)
    driver.close()


if __name__ == "__main__":
    main()
