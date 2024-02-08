#!/usr/bin/env python3
import sys
from getpass import getpass
from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_user_passwd(name_system: str):
    try:
        while True:
            username = input(f"{name_system} User: ").strip()
            passwd = getpass("Password: ").strip()
            if username and passwd:
                return username, passwd
    except KeyboardInterrupt:
        print("\nGood bye!")
        sys.exit()


def get_url(name_system: str):
    try:
        while True:
            url = input(f"{name_system} Url: ").strip()
            if "://" in url:
                return url
            else:
                print(f"Url invalid {url}")
    except KeyboardInterrupt:
        print("\nGood bye!")
        sys.exit()


def get_date_month(month: int | None = 0, year: int | None = 0) -> tuple:
    date_now = datetime.now()
    month = month or date_now.month
    year = year or date_now.year

    fmt_date = "%Y-%m"

    time_from = datetime.strptime(f"{year}-{month:02}", fmt_date)
    time_till = time_from + relativedelta(months=1)
    if time_till > date_now:
        time_till = date_now

    delta = time_till - time_from
    time_from = int(time_from.timestamp())
    time_till = int(time_till.timestamp())

    return (time_from, time_till, int(delta.total_seconds()))


if __name__ == "__main__":
    name_sys = "Granafa"
    print(get_user_passwd(name_sys))
