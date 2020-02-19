# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from faker import Faker
import json

from common import get_suggests, wait_suggests_hidden, wait_suggests_active

DEPTH = 2
'''Lets assume we need some static checks
db generation is LONG!'''
queries_list = []  # for debugging

if __name__ == "__main__":
    def recurse_suggests(storeto, qry, depth = 0):
        q.clear()
        wait_suggests_hidden(wait)
        q.send_keys(qry)
        try:
            wait_suggests_active(wait)
        except TimeoutException:
            return
        suggs = get_suggests(driver)
        for sug in suggs:
            storeto[sug.text] = {}
        if depth < DEPTH:
            for sug, d_ in storeto.items():
                recurse_suggests(d_, sug, depth + 1)

    fake_ru = Faker(locale = "ru_RU")
    fake_en = Faker(locale = "en_US")
    db = {}
    with webdriver.Firefox() as driver:
        driver.get("https://go.mail.ru/")
        wait = WebDriverWait(driver, 3)
        q = driver.find_element_by_css_selector("#q")
        queries = [
            "the quick brown fox jumps over the lazy dog",
            " ".join([fake_en.word() for i in range(4)]),
            " ".join([fake_ru.word() for i in range(4)])
        ]
        for words in map(lambda s: s.split(), queries):
            qry = []
            q.clear()
            wait_suggests_hidden(wait)
            for word in words:
                qry.append(word)
                s_qry = " ".join(qry)
                db[s_qry] = {}
                recurse_suggests(db[s_qry], s_qry)
        json.dump(db, open("db.json", "w", encoding = "utf-8"), ensure_ascii = False)



