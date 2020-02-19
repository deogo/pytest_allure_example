# -*- coding: utf-8 -*-
import pytest
import allure
from datetime import datetime, date
import random
from itertools import permutations
from faker import Faker

from fixer.common import (
    fixer_send_req, fixer_200_checks, exp_symbols_latest, fixer_400_checks, valid_years,
    symbols_by_year, symbols_for_date
)
fake = Faker()
fakes_pool = [fake.password, fake.pystr, fake.pyint, fake.pyfloat, fake.pydict]


def _rnd_str():
    return str(random.choice(fakes_pool)())


def _rand_syms(year = date.today().year):
    return random.sample(
        symbols_by_year[year],
        random.randint(2, len(symbols_by_year[year])))


def _year_sym_rnd_list(n_years):
    l = []
    for i in range(n_years):
        year = random.choice(valid_years)
        l.append((year, _rand_syms(year)))
    return l


def _year_sym_list(year):
    return [(year, sym) for sym in symbols_by_year[year]]


def _rand_year_permutations(year):
    return [(year, base, sym) for base, sym in list(permutations(symbols_by_year[year], 2))[:20]]


def _year_base_symbols_rnd(year):
    return [(year, random.choice(symbols_by_year[year]), _rand_syms(year)) for i in range(15)]


class TestLatest:

    def test_latest_accessible(self):
        fixer_200_checks(fixer_send_req("latest"), "EUR",
                         datetime.utcnow().date(), exp_symbols_latest)

    def test_empty_base(self):
        fixer_200_checks(fixer_send_req("latest", {"base": "", }), "EUR",
                         datetime.utcnow().date(), exp_symbols_latest)

    def test_empty_symbols(self):
        fixer_200_checks(fixer_send_req("latest", {"symbols": "", }), "EUR",
                         datetime.utcnow().date(), exp_symbols_latest)

    def test_empty_base_symbols(self):
        fixer_200_checks(fixer_send_req("latest", {"symbols": "", "base": "", }), "EUR",
                         datetime.utcnow().date(), exp_symbols_latest)

    def test_unknown_params(self):
        fixer_200_checks(fixer_send_req("latest", {"symbolss": "USD", "bases": "RUB", }), "EUR",
                         datetime.utcnow().date(), exp_symbols_latest)

    @allure.title("test_base_{base_name}")
    @pytest.mark.parametrize("base_name", exp_symbols_latest)
    def test_base(self, base_name):
        fixer_200_checks(fixer_send_req(
            "latest", {"base": base_name, }), base_name, datetime.utcnow().date(), exp_symbols_latest)

    @allure.title("test_symbols_{sym}")
    @pytest.mark.parametrize("sym", exp_symbols_latest)
    def test_symbols(self, sym):
        fixer_200_checks(fixer_send_req(
            "latest", {"symbols": sym, }), "EUR", datetime.utcnow().date(), [sym])

    @allure.title("test_random_symbols_{syms}")
    @pytest.mark.parametrize("syms", [_rand_syms() for i in range(15)])
    def test_random_symbols(self, syms):
        fixer_200_checks(fixer_send_req(
            "latest", {"symbols": ",".join(syms), }), "EUR", datetime.utcnow().date(), syms)

    @allure.title("test_base_and_symbol_{base}-{symbol}")
    @pytest.mark.parametrize("base,symbol", list(permutations(exp_symbols_latest, 2))[:20])
    def test_base_and_symbol(self, base, symbol):  # 20/1056 tests for demo-purpose
        fixer_200_checks(fixer_send_req(
            "latest", {"base": base, "symbols": symbol, }), base, datetime.utcnow().date(), [symbol])

    @allure.title("test_base_and_random_symbols_{base}-{symbols}")
    @pytest.mark.parametrize("base,symbols",
                             [(random.choice(exp_symbols_latest), _rand_syms()) for i in range(15)])
    def test_base_and_random_symbols(self, base, symbols):
        fixer_200_checks(fixer_send_req(
            "latest", {"base": base, "symbols": ",".join(symbols), }), base, datetime.utcnow().date(), symbols)

    @allure.description("При множестве параметром используется первый base и все symbols")
    def test_multiparams(self):
        bases = [random.choice(exp_symbols_latest) for i in range(3)]
        symbols = [random.choice(exp_symbols_latest) for i in range(5)]
        fixer_200_checks(fixer_send_req(
            "latest", {"base": bases, "symbols": symbols, }), bases[0],
            datetime.utcnow().date(), symbols)

    @pytest.mark.parametrize("base", [_rnd_str() for i in range(15)])
    def test_base_bad_format(self, base):
        fixer_400_checks(fixer_send_req(
            "latest", {"base": base}), f"Base '{base}' is not supported.")

    @pytest.mark.parametrize("i", [i for i in range(10)])
    def test_symbols_bad_format(self, i):
        symbols = []
        for i in range(random.randint(1, 5)):
            symbols.append(_rnd_str())
        symbols.append(random.choice(exp_symbols_latest))
        s_syms = ",".join(symbols)
        fixer_400_checks(fixer_send_req(
            "latest", {"base": random.choice(exp_symbols_latest), "symbols": s_syms, }),
            f"Symbols '{s_syms}' are invalid for date {datetime.utcnow().date()}.")

    @pytest.mark.parametrize("i", [i for i in range(10)])
    def test_unknown_currencies(self, i):
        while True:
            base = fake.currency_code()
            if base not in exp_symbols_latest:
                break
        symbols = random.sample(exp_symbols_latest, 3)
        fixer_400_checks(fixer_send_req(
            "latest", {"base": base, "symbols": symbols, }), f"Base '{base}' is not supported.")


class TestDates:
    @property
    def path(self):  # random valid path/date
        dt = fake.date_object().replace(year = random.choice(valid_years))
        return str(dt), dt

    @pytest.mark.parametrize("year", [y for y in valid_years])
    def test_valid_dates(self, year: int):
        date_obj = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(
            str(date_obj)), "EUR", date_obj, symbols_by_year.get(year, []))

    @pytest.mark.parametrize("year", [1994, 1995, 1996, 1997, 1998])
    def test_invalid_old_dates(self, year: int):
        date_obj = fake.date_object().replace(year = year)
        fixer_400_checks(fixer_send_req(
            str(date_obj)), "There is no data for dates older then 1999-01-04.")

    @allure.description("Для будущего отдаются данные ближайшей текущей даты")
    @pytest.mark.parametrize("year", [(date.today().year + i) for i in range(1, 6)])
    def test_future_dates(self, year: int):
        date_obj = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(
            str(date_obj)), "EUR", date.today(), exp_symbols_latest)

    def test_empty_base(self):
        path, dt = self.path
        fixer_200_checks(fixer_send_req(path, {"base": "", }), "EUR",
                         dt, symbols_for_date(dt))

    def test_empty_symbols(self):
        path, dt = self.path
        fixer_200_checks(fixer_send_req(path, {"symbols": "", }), "EUR",
                         dt, symbols_for_date(dt))

    def test_empty_base_symbols(self):
        path, dt = self.path
        fixer_200_checks(fixer_send_req(path, {"symbols": "", "base": ""}), "EUR",
                         dt, symbols_for_date(dt))

    def test_unknown_params(self):
        path, dt = self.path
        fixer_200_checks(fixer_send_req(path, {"symbolss": "USD", "bases": "RUB"}), "EUR",
                         dt, symbols_for_date(dt))

    @allure.title("test_base_random_date_{year}-{base_name}")
    @pytest.mark.parametrize("year,base_name", _year_sym_list(random.choice(valid_years)))
    def test_base_random_date(self, year, base_name):
        dt = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(str(dt), {"base": base_name, }),
                         base_name, dt, symbols_for_date(dt))

    @allure.title("test_symbols_random_date_{year}-{sym}")
    @pytest.mark.parametrize("year,sym", _year_sym_list(random.choice(valid_years)))
    def test_symbols_random_date(self, year, sym):
        dt = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(str(dt), {"symbols": sym}),
                         "EUR", dt, [sym])

    @allure.title("test_random_symbols_{year}-{syms}")
    @pytest.mark.parametrize("year,syms", _year_sym_rnd_list(5))
    def test_random_symbols(self, year, syms):
        dt = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(
            str(dt), {"symbols": ",".join(syms), }), "EUR", dt, syms)

    @allure.title("test_base_and_symbol_{year}-{base}-{symbol}")
    @pytest.mark.parametrize("year,base,symbol", _rand_year_permutations(random.choice(valid_years)))
    def test_base_and_symbol(self, year, base, symbol):
        dt = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(
            str(dt), {"base": base, "symbols": symbol, }), base, dt, [symbol])

    @allure.title("test_base_and_random_symbols_{year}-{base}-{symbols}")
    @pytest.mark.parametrize("year,base,symbols", _year_base_symbols_rnd(random.choice(valid_years)))
    def test_base_and_random_symbols(self, year, base, symbols):
        dt = fake.date_object().replace(year = year)
        fixer_200_checks(fixer_send_req(
            str(dt), {"base": base, "symbols": ",".join(symbols), }), base, dt, symbols)

    @allure.description("При множестве параметром используется первый base и все symbols")
    def test_multiparams(self):
        path, dt = self.path
        bases = [random.choice(symbols_by_year[dt.year]) for i in range(3)]
        symbols = [random.choice(symbols_by_year[dt.year]) for i in range(5)]
        fixer_200_checks(fixer_send_req(
            path, {"base": bases, "symbols": symbols, }), bases[0],
            dt, symbols)

    @pytest.mark.parametrize("base", [_rnd_str() for i in range(15)])
    def test_base_bad_format(self, base):
        path, dt = self.path
        fixer_400_checks(fixer_send_req(
            path, {"base": base}), f"Base '{base}' is not supported.")

    @pytest.mark.parametrize("i", [i for i in range(10)])
    def test_symbols_bad_format(self, i):
        path, dt = self.path
        symbols = []
        for i in range(random.randint(1, 5)):
            symbols.append(_rnd_str())
        symbols.append(random.choice(symbols_by_year[dt.year]))
        s_syms = ",".join(symbols)
        fixer_400_checks(fixer_send_req(
            path, {"base": random.choice(symbols_by_year[dt.year]), "symbols": s_syms, }),
            f"Symbols '{s_syms}' are invalid for date {dt}.")

    @pytest.mark.parametrize("i", [i for i in range(10)])
    def test_unknown_base_currency(self, i):
        path, dt = self.path
        while True:
            base = fake.currency_code()
            if base not in symbols_by_year[dt.year]:
                break
        symbols = random.sample(symbols_by_year[dt.year], 3)
        fixer_400_checks(fixer_send_req(
            path, {"base": base, "symbols": ",".join(symbols), }), f"Base '{base}' is not supported.")
