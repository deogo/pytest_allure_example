# -*- coding: utf-8 -*-
import requests
from datetime import timedelta, datetime, date
import allure
import json

from fixer.symbols import symbols_by_year

session = requests.Session()
fixer_base_url = "https://api.exchangeratesapi.io/"
exp_symbols_latest = symbols_by_year[date.today().year]
valid_years = list(range(1999, datetime.now().year + 1))


def symbols_for_date(date_obj = date.today()):
    return symbols_by_year[date_obj.year]


def fixer_send_req(ep, params = {}):
    return http_get(fixer_base_url + ep, params)


@allure.step
def http_get(url, params):
    return session.get(url, params = params)


def attach_req(resp):
    ret = {"response": {}, "request": {}, }
    for field in ["status_code", "headers", "url", "encoding", "history", "reason", "elapsed"]:
        ret["response"][field] = str(resp.__dict__.get(field))
    ret["response"]["cookies"] = resp.cookies.get_dict()
    try:
        ret["response"]["json"] = resp.json()
    except:
        ret["response"]["content"] = resp.content
    for field in ["method", "headers", "url", "body"]:
        ret["request"][field] = str(resp.request.__dict__.get(field))
    ret["request"]["cookies"] = resp.request._cookies.get_dict()
    allure.attach(json.dumps(ret["response"], ensure_ascii = False, indent = 4),
                  "Response data", allure.attachment_type.JSON)
    allure.attach(json.dumps(ret["request"], ensure_ascii = False, indent = 4),
                  "Requst data", allure.attachment_type.JSON)


@allure.step
def fixer_200_checks(resp, base, date_exp, symbols):
    info = f"url={resp.url}"
    attach_req(resp)
    date_3days = date_exp - timedelta(days = 3)
    assert resp.status_code == 200, info
    json = resp.json()
    assert json, info
    assert json.get("base") == base
    assert str(date_3days) <= json.get("date") <= str(date_exp), info
    assert set(json.get("rates").keys()) == set(symbols), info


@allure.step
def fixer_400_checks(resp, error):
    info = f"url={resp.url}"
    attach_req(resp)
    assert resp.status_code == 400, info
    json = resp.json()
    assert json, info
    assert json.get("error") == error, info
