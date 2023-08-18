#!/usr/bin/env python3
"""Gerador de relatorio de sinal rx das ONUs

Coleta os hosts ativos no Zabbix contendo "OLT" no nome e em seguida faz
uma busca pelos os itens com as tags "ONU: Sinal" e "ONU: PON" para gerar
um arquivo CSV.
"""
__version__ = "1.0.1"
__author__ = "Afonso R Filho"

from dotenv import load_dotenv
from pyzabbix import ZabbixAPI
from datetime import datetime
from time import sleep
from tqdm import tqdm
import os
import re
import csv

# Variables
load_dotenv()
url = os.getenv("URL")
username = os.getenv("ZBX_USERNAME") or None
passwd = os.getenv("ZBX_PASSWD") or None
api_token = os.getenv("ZBX_TOKEN_API") or None

search_host = {"name": "OLT"}

item_tags = [{"tag": "ONU", "value": "Sinal"}, {"tag": "ONU", "value": "PON"}]

# Zabbix connect
zapi = ZabbixAPI(url)
zapi.login(user=username, password=passwd, api_token=api_token)
print(f"Connected to Zabbix API Version {zapi.api_version()}.")
sleep(1)

print("Collecting the hosts")
# Collecting the hosts
get_hosts = zapi.host.get(
    monitored_host=1,
    output=["hostid", "host", "name"],
    filter={"status": 0},
    search=search_host,
)

hosts = {info["hostid"]: info["host"] for info in tqdm(get_hosts, ncols=70)}

print(f"Collecting item info from {len(hosts)} hosts")
get_items = []
for info in tqdm(get_hosts, ncols=70):
    item = zapi.item.get(
        hostids=info["hostid"],
        output=["hostid", "key_", "name", "lastvalue"],
        tags=item_tags,
    )
    if item:
        get_items.append(item)

print(f"Organizing the collected information ({len(get_items)}).")
onu_list = []
for info in tqdm(get_items, ncols=70):
    if info:
        onus = []
        set_onu = set()
        for item in info:
            if item:
                onu_id = re.search("\[(.*)\]", item["key_"]).group(1)
                if onu_id in set_onu:
                    if onu_id == onu["id"]:
                        if not "sinal" in onu:
                            onu["sinal"] = item["lastvalue"]
                        if not "pon" in onu:
                            onu["pon"] = item["lastvalue"]
                else:
                    onu = dict()
                    onu["id"] = onu_id
                    if "sinalonu" in item["key_"].lower():
                        onu["sinal"] = item["lastvalue"]
                    if "ponport" in item["key_"].lower():
                        onu["pon"] = item["lastvalue"]
                    onu["name"] = re.search(":: (.*) ::", item["name"]).group(1).strip()
                    onu["host"] = hosts[item["hostid"]]
                    onus.append(onu)
                    set_onu.add(onu_id)

        if onus:
            onu_list.append(onus)

print("Preparing the info for writing")
list_result = []  # HOST, ONU, SINAL, PON
for host in tqdm(range(len(onu_list)), ncols=70):
    for info in onu_list[host]:
        if info:
            list_result.append(
                [
                    info["host"],
                    info["name"],
                    round(float(info["sinal"]), 2) if "sinal" in info else "",
                    info["pon"] if "pon" in info else "",
                ]
            )


today = datetime.strftime(datetime.now(), "%Y-%m-%d")
file_csv = f"onu_sinal_{today}"
print(len(onu_list))
print(f"Saving the file {file_csv}")
total_rows = len(list_result)

if total_rows > 500000:
    parts = total_rows // 300000 + 1
    print(f"The list has more than 500K rows ({total_rows} rows).")
    print(f"The list will be divided into {parts} parts.")
    num = 0

    for i in tqdm(range(1, parts + 1), ncols=70):
        print(f"     {i} of {parts} parts.")
        with open(f"{file_csv}_part-{i:>02}.csv", "w", newline="") as csvfile:
            csv.writer(csvfile, delimiter=",").writerow(["HOST", "ONU", "SINAL", "PON"])
            for o in tqdm(range(300000), ncols=70, desc=f"Part {i} of {parts}-"):
                if not num < total_rows:
                    break
                else:
                    if len(list_result[num]):
                        csv.writer(csvfile, delimiter=",").writerow(list_result[num])
                num += 1

else:
    with open(f"{file_csv}.csv", "w", newline="") as csvfile:
        csv.writer(csvfile, delimiter=",").writerow(["HOST", "ONU", "SINAL", "PON"])
        for row in tqdm(range(total_rows), ncols=70):
            if len(list_result[row]):
                csv.writer(csvfile, delimiter=",").writerow(list_result[row])


print('Completed successfully.')