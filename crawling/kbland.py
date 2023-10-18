import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException


class KB_crawling:
    def __init__(self, driver, building_name, search_query, square_meter):
        self.building_name = building_name
        self.search_query = search_query
        self.square_meter = square_meter
        self.driver = driver
        self.wait = WebDriverWait(
            self.driver, 2
        )  # driver waits fot maximum 2sec to be appeared

    ### 자연어 처리
    def levenshtein_distance(self, s1, s2):
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost
                )

        return dp[m][n]

    def most_similar_string_index(self, target, strings):
        min_distance = float("inf")
        most_similar_index = None

        for index, s in enumerate(strings):
            distance = self.levenshtein_distance(target, s)
            if distance < min_distance:
                min_distance = distance
                most_similar_index = index

        return most_similar_index

    def extract_text(self, pattern, raw_text):
        return re.search(pattern, raw_text).group(1)

    ### 크롤링 순서대로 동작
    def activate_search_box(self):
        find_search_box = self.driver.find_element_by_class_name(
            "homeSerchBox"
        )  # click to find search box : 검색 상자 활성화
        self.driver.execute_script(
            "arguments[0].click();", find_search_box
        )  # Using js to click

    def search_apartment(self):
        search_box = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[type="text"]:nth-child(1)')
            )
        )
        search_box.send_keys(self.search_query)
        search_box.send_keys(Keys.RETURN)

        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='list-search-poi']")
                )
            )
            item_elements = self.driver.find_elements(By.XPATH, "//span[@class='text']")
            item_text = [item.get_attribute("innerText") for item in item_elements]

            opimal_index = self.most_similar_string_index(self.building_name, item_text)
            self.driver.execute_script(
                "arguments[0].click();", item_elements[opimal_index]
            )  # Using js to click

        except TimeoutException:
            pass

    def click_to_check_detail(self):
        try:
            span_name_value = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='nameValue']"))
            )
            self.driver.execute_script(
                "arguments[0].click();", span_name_value
            )  # Using js to click
        except TimeoutException:
            print("cannot find such element")
            pass

    def get_room_info(self):
        try:
            type_elements = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//span[em and contains(text(), {self.square_meter})]")
                )
            )
            next_sibling = type_elements.find_element_by_xpath(
                "following-sibling::*[1]"
            )
            room_text = next_sibling.get_attribute("innerText")

            pattern1 = r"\n(.+?)개"  # 방 개수, 정규표현식을 사용하여 문자 추출
            pattern2 = r"개/(.+?)개"  # 화장실 개수, 정규표현식을 사용하여 문자 추출

            room = self.extract_text(pattern1, room_text)
            bathroom = self.extract_text(pattern2, room_text)

            return [int(room), int(bathroom)]

        except TimeoutException:
            return [0, 0]  # 해당하는 유형의 세대를 찾지 못했을 경우 0,0을 반환

    def get_parking_info(self):  # 평균 주차 대 수 찾기
        try:
            parking_element = self.driver.find_element(
                By.XPATH, '//span[contains(text(), "주차")]'
            )
            parking_text = parking_element.get_attribute("innerText")

            pattern3 = r"주차 (.+?)대"
            parking_lot = self.extract_text(pattern3, parking_text)

            return float(parking_lot)

        except:
            return 0

    def get_primary_school_info(self):
        # 배정된 초등학교의 거리 찾기
        try:
            primary_school_element = self.driver.find_element(
                By.XPATH, '//em[@class="textellipsis" and contains(text(), "초등학교")]'
            )
            grandparent_elememt = primary_school_element.find_element_by_xpath("../..")
            sibling_grandparent = grandparent_elememt.find_element_by_xpath(
                "following-sibling::*[1]"
            )
            school_distance_element = sibling_grandparent.find_element(
                By.XPATH, '//em[contains(text(), "m")]'
            )
            school_distance_text = school_distance_element.get_attribute("innerText")

            pattern4 = r"(.+?)m"
            school_distance = self.extract_text(
                pattern4, school_distance_text
            )  # 텍스트 추출

            return int(school_distance)

        except:
            return 0

    def back_to_home(self):
        home_btn = self.driver.find_element(
            By.XPATH, "//button[@class='btn btn-nav home' and text()=' 홈']"
        )
        self.driver.execute_script("arguments[0].click();", home_btn)
