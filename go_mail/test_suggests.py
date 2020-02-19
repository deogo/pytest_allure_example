# -*- coding: utf-8 -*-
import shutil
import os
import pytest
import allure
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import random
from uuid import uuid4

from go_mail.common import (
    go_mail_url, get_suggests, wait_suggests_active, wait_suggests_hidden, CSuggs,
    get_url_prm, fakers, CWait
)


@pytest.fixture(params=["firefox"], scope="class")
def driver_init(request):
    if request.param == "chrome":
        web_driver = webdriver.Chrome()
    if request.param == "firefox":
        web_driver = webdriver.Firefox()
    request.cls.driver = web_driver
    yield
    web_driver.close()


@pytest.mark.usefixtures("driver_init")
class Base:
    driver = None
    wait = None
    db = None
    pics_dir = "./pics/"
    wait_timeout = 2

    @allure.title("Очистка")
    @pytest.fixture(autouse=True)
    def __cleanup(self, request):
        if self.driver.current_url != go_mail_url:
            self.driver.get("https://go.mail.ru/")
        if not self.wait:
            self.wait = CWait(self.driver, self.wait_timeout)
        if not self.db:
            self.db = json.load(open(r"./go_mail/db.json", "r", encoding = "utf-8"))
            self._parse_db()
        self.q = self.driver.find_element_by_css_selector("#q")
        self.q.clear()
        wait_suggests_hidden(self.wait)

    @pytest.fixture(autouse=True)
    def __pic(self, request):
        yield
        if not os.path.exists(self.pics_dir):
            os.makedirs(self.pics_dir, mode = 755, exist_ok = True)
        p = os.path.join(self.pics_dir, f"{uuid4()}.png")
        self.driver.get_screenshot_as_file(p)
        allure.attach.file(p, attachment_type = allure.attachment_type.PNG)

    def _parse_db(self):

        def _helper(db, store_to):
            for k in db.keys():
                if db[k]:
                    if not k in store_to:
                        store_to[k] = list(db[k].keys())
                    _helper(db[k], store_to)

        self.static_results = {}
        _helper(self.db, self.static_results)
        self.static_queries = list(self.static_results.keys())

    @allure.step("Получение текущих саджестов")
    def _get_suggs(self, may_be_empty = False):
        try:
            wait_suggests_active(self.wait)
        except TimeoutException:
            if may_be_empty:
                return CSuggs()
            raise
        suggs_el = get_suggests(self.driver)
        suggs_txt = list(map(lambda s: s.text, suggs_el))
        allure.attach(json.dumps(suggs_txt, ensure_ascii = False, indent = 4),
                      "Suggests", allure.attachment_type.JSON)
        return CSuggs(elements = suggs_el, texts = suggs_txt)

    @allure.step("Проверка отсутствия саджестов")
    def _ensure_no_suggests(self):
        try:
            wait_suggests_active(self.wait)
        except TimeoutException:
            return
        raise Exception("Some suggests found while not expected")

    def _get_q_text(self):
        return self.driver.find_element_by_css_selector(".input-inline-suggest > .current").text

    @allure.step("Ожидание текста q")
    def _wait_q_text(self, text: str):
        allure.attach(text, "Waiting for", allure.attachment_type.TEXT)
        allure.attach(self._get_q_text(), "Current text", allure.attachment_type.TEXT)
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".input-inline-suggest > .current"),
                text))
        return self._get_q_text()

    @allure.step("Ввод запроса")
    def _query_enter(self, query):
        allure.attach(query, "Query", allure.attachment_type.TEXT)
        self.q.clear()
        wait_suggests_hidden(self.wait)
        self.q.send_keys(query)

    @allure.step("Дополнение запроса")
    def _query_append(self, query):
        allure.attach(query, "Appendage", allure.attachment_type.TEXT)
        self.q.send_keys(query)

    @allure.step("Выбор саджеста")
    def _check_sugg_invoke(self, sugg, use_enter = False):  # meant to be last action for now
        sugg_text = sugg.text
        allure.attach(sugg_text, "Target suggestion", allure.attachment_type.TEXT)
        url = self.driver.current_url
        if use_enter:
            self._query_append(Keys.ENTER)
        else:
            sugg.click()
        self.wait.until(EC.url_changes(url))
        allure.attach(self.driver.current_url, "URL", allure.attachment_type.TEXT)
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#q")))
        q = self.driver.find_element_by_css_selector("#q")
        allure.attach(q.get_attribute("value"), "q value", allure.attachment_type.TEXT)
        assert q.get_attribute("value") == sugg_text
        url_q = get_url_prm(self.driver.current_url, "q")
        assert url_q == sugg_text

    def _get_random_static_query(self):
        return random.choice(self.static_queries)

    @allure.step("Проверка отсутствия дубликатов в саджестах")
    def _check_sugg_dublicates(self, suggs: CSuggs):
        allure.attach(json.dumps(suggs.texts, ensure_ascii = False, indent = 4),
                      "Suggests", allure.attachment_type.JSON)
        assert len(suggs.texts) == len(set(suggs.texts)), "Some dublicates found"

    def _get_selected_sugg(self):
        l = self.driver.find_elements_by_css_selector(".go-suggests__item_select")
        return l and l[0] or None

    def _wait_selected_sugg(self):
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".go-suggests__item_select")))
        return self._get_selected_sugg()

    @allure.step("Проверка что ни один саджест не выбран")
    def _check_no_suggests_selected(self):
        assert self._get_selected_sugg() == None

    @allure.step("Проверка выбранного саджеста на соответствие переданному")
    def _check_selected_suggest(self, sugg):
        sugg_selected = self._wait_selected_sugg()
        allure.attach(sugg_selected.text, "Selected suggest", allure.attachment_type.TEXT)
        allure.attach(sugg.text, "Target suggest", allure.attachment_type.TEXT)
        assert sugg_selected.text == sugg.text


class TestSuggests(Base):

    @allure.description("Базовая проверка саджестов")
    def test_base(self):
        self._query_enter("Hello")
        suggs = self._get_suggs()
        assert suggs
        self._check_sugg_dublicates(suggs)
        self._check_sugg_invoke(random.choice(suggs))

    @allure.description("Проверка отсутствия саджестов")
    def test_suggest_absent(self):
        self._query_enter("Hello Mail.ru")
        suggs = self._get_suggs(may_be_empty = True)
        assert len(suggs) == 0

    @allure.description("Проверка статических запросов/саджестов")
    @pytest.mark.parametrize("i", range(30))
    def test_static_reqs(self, i):
        qry = self._get_random_static_query()
        self._query_enter(qry)
        suggs = self._get_suggs()
        assert suggs
        assert set(suggs.texts) == set(self.static_results[qry])
        self._check_sugg_dublicates(suggs)

    @allure.description("Проверка навигации с помощью клавиатуры")
    def test_keyboard_nav1(self):
        for qry in [
            "the", " ", "rings", Keys.ARROW_LEFT * 5, "lordnights ",
            Keys.BACKSPACE * 7, " "
        ]:
            self._query_append(qry)
        self._wait_q_text("the lord rings")
        self._check_no_suggests_selected()
        suggs = self._get_suggs()
        self._query_append(Keys.ARROW_UP)  # bottom
        self._check_selected_suggest(suggs[-1])
        self._query_append(Keys.ARROW_DOWN)  # neutral
        self._check_no_suggests_selected()
        self._query_append(Keys.ARROW_DOWN)  # first
        self._check_selected_suggest(suggs[0])
        self._query_append(Keys.ARROW_UP)  # neutral
        self._check_no_suggests_selected()
        self._query_append(Keys.ARROW_DOWN * (len(suggs) + 1))  # loop down
        self._check_no_suggests_selected()
        self._query_append(Keys.ARROW_UP * (len(suggs) + 1))  # loop up
        # random select
        rnd_ind = random.randint(0, len(suggs) - 1)
        self._query_append(Keys.ARROW_DOWN * (rnd_ind + 1))
        self._check_selected_suggest(suggs[rnd_ind])
        self._check_sugg_invoke(suggs[rnd_ind], use_enter = True)

    @allure.description("Проверка навигации с помощью клавиатуры - выбор саджестов")
    def test_keyboard_nav2(self):
        self._query_enter("working hard")
        suggs = self._get_suggs()
        self._check_no_suggests_selected()

        rnd_ind = random.randint(0, len(suggs) - 1)
        sug = suggs[rnd_ind]
        self._query_append(Keys.ARROW_DOWN * (rnd_ind + 1))
        self._check_selected_suggest(sug)
        self._query_append(Keys.ARROW_RIGHT)
        self._wait_q_text(sug.text)

    @allure.description("Проверка случайных запросов, допустим мы всегда ожидаем саджесты на одно-два слова")
    @pytest.mark.parametrize("locale,n_words",
                             [(random.choice(list(fakers.keys())), random.randint(1, 3)) for _ in range(30)])
    def test_random_queries(self, locale, n_words):
        fake = fakers[locale]
        words = [fake.word() for _ in range(n_words)]
        self._query_enter(" ".join(words))
        suggs = self._get_suggs()
        self._check_sugg_dublicates(suggs)




