#!/usr/bin/env python3

import os, sys
from pyzabbix import ZabbixAPI, ZabbixAPIException
import urllib3
from time import sleep
from datetime import datetime
from modules import get_user_passwd, get_url, get_date_month, banner



def zbx_connect(
    zbxname: str = "Zabbix",
    url: str = "",
    api_token: str = ""
        ):
    
    zbxname = zbxname.upper().strip()
    if not url:
        url = get_url(zbxname)
    url = url.strip()
    api_token = api_token.strip()
    
    banner(f'Connect Zabbix {zbxname}',bottom_text="")
    
    while True:
        zapi = ZabbixAPI(url)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        zapi.session.verify = False

        try: 
            if api_token:
                zapi.login(api_token=api_token)
            else:
                username, passwd = get_user_passwd(zbxname)
                zapi.login(username, passwd)
            
            print(f"Connected to Zabbix {zbxname} API Version {zapi.api_version()}.")
            sleep(1)
            break
        except ZabbixAPIException as error:
            os.system('cls' if os.name == 'nt' else 'clear')
            if "name or password" in str(error): 
                print("[ERROR] Login name or password is incorrect")
            elif "Not Found for url" in str(error):
                print("[ERROR] Not Found for url")
                url = get_url()
            elif "Invalid URL" in str(error):
                print("[ERROR] " + str(error))
                url = get_url(zbxname)
            elif "Failed to establish a new connection" in str(error):
                print(f"[ERROR] Failed to establish a new connection `{url}`.")
                url = get_url(zbxname)
            else:
                print('aqui')
                print(type(error).__name__, error) 
                sys.exit(1)
        except Exception as error:
            if type(error).__name__ == "MissingSchema":
                print(error)
                url = get_url(zbxname)
            elif type(error).__name__ == "ConnectionError":
                print("Connection error: Enter the correct URL")
                url = get_url(zbxname)
            else:
                print(f'[ERRO] {type(error).__name__}: {error}') 
                sys.exit(1)
            
    return zapi

def get_problems(
    zapi: ZabbixAPI,
    hostid: str,
    month: int | None = 0,
    year: int | None = 0,
    alert_name: str = "Unavailable by ICMP ping",
) -> list:
    zapi = zapi
    hostid = hostid
    month = int(month) or datetime.now().month
    year = int(year) or datetime.now().year
    alert_name = alert_name

    time_from, time_till, *_ = get_date_month(month, year)
    
    resolveds = dict()
    for resolved in zapi.event.get(
        hostids=hostid,
        output=["name", "clock"],
        time_from=time_from,
        time_till=time_till,
        search={"name": alert_name},
        filter={"value": 0},
        sortfild="clock",
    ):
        resolveds[resolved["eventid"]] = resolved["clock"]

    problems = []
    for problem in zapi.event.get(
        hostids=hostid,
        output=["name", "clock", "r_eventid", "acknowledged", "value"],
        select_acknowledges=["message"],
        problem_time_from=time_from,
        problem_time_till=time_till,
        search={"name": alert_name},
        sortfild="clock",
    ):
        if problem["r_eventid"] != "0":
            r_clock = resolveds.get(problem["r_eventid"])
        else:
            r_clock = time_till - 1

        if not r_clock:
            r_clock = time_till - 1

        clock = problem["clock"] if int(problem["clock"]) >= time_from else time_from

        messages = []
        for e in problem["acknowledges"]:
            msg = ""
            if e.get("message"):
                msg = e["message"].strip().replace("\n", "/")
                msg = msg.replace("\r", "/")
                msg = msg.replace(",", " | ")
            messages.append(msg)
        
        messages_join = ";".join(messages)
        clock = int(clock)
        r_clock = int(r_clock)
        delta = r_clock - clock
        info = {
            "hostid": hostid,
            "name": problem["name"],
            "hostid": hostid,
            "clock": clock,
            "r_clock": r_clock,
            "duration": delta,
            "ack": problem["acknowledged"],
            "messages": messages_join,
        }

        problems.append(info)
    return problems

def parms_get_hosts(
    zbx_version: float = 6.0,
    search: dict | None = {},
    filter: dict | None = {},
) -> dict:
    zbx_version = zbx_version
    parms = {
        "output": ["host", "name", "status"],
        "selectTags": ["tag", "value"],
        "selectMacros": ["macro", "value"],
        "search": search,
        "filter": filter,
    }
    
    if zbx_version >= 6:
        parms["selectHostGroups"] = ["name", "groupid"]  # Zabbix >=6.0
    else:
        parms["selectGroups"] = ["name", "groupid"]  # Zabbix <=6.0
        
    return parms


def host_info(**host_get_return: dict) -> dict:
    host = {
        "hostid": host_get_return["hostid"],
        "host": host_get_return["host"],
        "name": host_get_return["name"],
        "status": "enabled" if host_get_return["status"] == "0" else "disabled",
        "tags": "",
        "macros": "",
    }
    
    if host_get_return.get("hostgroups"):
        groups = [i["name"] for i in host_get_return["hostgroups"]]
    else:
        groups = [i["name"] for i in host_get_return["groups"]] # Zabbix <=6.0
    host["hostgroups"] = ";".join(groups)

    macros = []
    for macro in host_get_return["macros"]:
        macros.append(f"{macro['macro']}={macro['value']}")
    host["macros"] = ";".join(macros)

    tags = []
    for tag in host_get_return["tags"]:
        tags.append(f"{tag['tag']}={tag['value']}")
    host["tags"] = ";".join(tags)

    return host


#if __name__ == "__main__":