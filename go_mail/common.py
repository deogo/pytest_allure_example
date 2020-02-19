# -*- coding: utf-8 -*-
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pytest
import urllib
from faker import Faker
import random

go_mail_url = 'https://go.mail.ru/'
fakers = {loc: Faker(locale = loc) for loc in ["ru_RU", "en_US"]}


def get_suggests(driver):
    return driver.find_elements_by_css_selector(".go-suggests__items > *")


def wait_suggests_hidden(wait: WebDriverWait):
    wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, "#go-suggests")))


def wait_suggests_active(wait: WebDriverWait):
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#go-suggests")))


def get_url_prm(url, param):
    l = urllib.parse.parse_qs(url).get(param, [])
    return l and l[0] or None


def chance(percent: int) -> bool:
    '''
    :percent: 1-100 percent chance to return True'''
    return random.random() <= 0.01 * percent


class MyTimeoutException(pytest.fail.Exception, TimeoutException):

    def __init__(self, **kwargs):
        pytest.fail.Exception.__init__(self, pytrace = True)
        TimeoutException.__init__(self, **kwargs)


class CWait(WebDriverWait):

    def until(self, method, message = ''):
        try:
            super().until(method, message)
        except TimeoutException as oEx:
            raise MyTimeoutException(**oEx.__dict__)

    def until_not(self, method, message = ''):
        try:
            super().until_not(method, message)
        except TimeoutException as oEx:
            raise MyTimeoutException(**oEx.__dict__)


class CSuggs:

    def __init__(self, elements = [], texts = []):
        self.elements = elements
        self.texts = texts

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, x):
        return self.elements[x]

    def __iter__(self):
        for el in self.elements:
            yield el
