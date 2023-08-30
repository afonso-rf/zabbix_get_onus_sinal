#!/usr/bin/env python3
"""Gerador de relatorio de sinal rx das ONUs

Coleta os hosts ativos no Zabbix contendo "OLT" no nome e em seguida faz
uma busca pelos os itens com as tags "ONU: Sinal" e "ONU: PON" para gerar
um arquivo CSV.

As url de servidores poderão ser lidas do arquivo `file_url.csv` ou 
informadas via interação.
"""
__version__ = "1.2.0"
__author__ = "Afonso R Filho"

from pyzabbix import ZabbixAPI
from datetime import datetime
from time import sleep
from tqdm import tqdm
from getpass import getpass
import os
import sys
import re

# Variables
path = os.curdir
file_url = os.path.join(path, "file_url.csv")

search_host = {"name": "OLT"}

item_tags = [{"tag": "ONU", "value": "Sinal"}, {"tag": "ONU", "value": "PON"}]

def csv_to_list(filecsv, delimiter=","):
    result = []
    with open(filecsv, encoding="utf-8") as file_:
        for line in file_:
            result.append(line.strip("\n").split(delimiter))

    return result

try:
    url_list = csv_to_list(file_url)
    try:
        if len(url_list[1:]) > 1:
            while True:
                    os.system("clear")
                    print("#" * 40)
                    print(f"#{'Escolha um dos servidores abaixo':^38}#")
                    print("#" * 40)
                    print()
                    for i in range(1,len(url_list)):
                        print(f" [ {i} ] - Zabbix {url_list[i][0].upper()}")
                    print()
                    index = input("Escolha o zabbix desejado (Crtl+C sair): ").strip()
                    if index.isdigit() and 0 < int(index) < len(url_list):
                        server = int(index)
                        break
                    else:
                        print(f"Invalid `{index}`")
                        print(f"Escolha entre 1 a {len(url_list) - 1}.")
                        sleep(1.5)
            
        else:
            server = 1
    except Exception as error:
        print(error)
    
    try:
        zabbixname = url_list[server][0].strip().upper()
        url = ''
        for item in url_list[server]:
            if "://" in item:
                url = item
        if not url:
            url = input("Url Zabbix: ")
    except IndexError:
        url = input("Url Zabbix: ")
    
    try:
        api_token = ""
        if url_list[server][2]:
            api_token =  url_list[server][2].strip()
            username = ""
            passwd = ""
        if not api_token:
            while True:
                username = input("Zabbix User: ")  
                passwd = getpass("Password")
                if username and passwd:
                    break
    except IndexError:
        while True:
            username = input("Zabbix User: ")  
            passwd = getpass("Password: ")
            api_token = ""
            if username and passwd:
                break
except FileNotFoundError:
    try:
        while True:
            url = input("Url Zabbix: ")
            if "://" in url:
                break
            else:
                print(f"Url invalid {url}")
    except KeyboardInterrupt:
        print("\nGood bye.")
        sys.exit(1)
    try:
        while True:
            username = input("Zabbix User: ")  
            passwd = getpass("Password: ")
            if username and passwd:
                break
    except KeyboardInterrupt:
        print("\nGood bye.")
        sys.exit(1)

except KeyboardInterrupt:
    print("Good bye.")
    sys.exit(1)
except Exception as error:
        print(error)
        sys.exit(1)

# Zabbix connect
while True:
    zapi = ZabbixAPI(url)
    try: 
        if api_token:
            zapi.login(api_token=api_token)
        else:
            zapi.login(user=username, password=passwd)
        
        print(f"Connected to Zabbix {zabbixname} API Version {zapi.api_version()}.")
        sleep(1)
        break
    except KeyboardInterrupt:
        print("\nGood bye.")
        sys.exit(1)
    except Exception as error:
        if "Login name or password is incorrect" in str(error):
            print("Login name or password is incorrect")
            username = input("Zabbix User: ")  
            passwd = getpass("Password: ")
        elif "404 Client Error: Not Found for url" in str(error):
            print("404 Client Error: Not Found for url")
            url = input("Url Zabbix: ")
        elif "Invalid URL" in str(error):
            print(f"Invalid URL `{url}`.")
            url = input("Url Zabbix: ")
        else:
            print(str(error)) 


# Collecting the hosts
print("Collecting the hosts")

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
        onu_ids = set()
        for item in info:
            if item:
                onu_id = re.search("\[(.*)\]", item["key_"]).group(1)
                if onu_id in onu_ids:
                    for onu in onus:
                        if onu_id == onu["id"]:
                            if not "sinal" in onu:
                                onu["sinal"] = item["lastvalue"]
                            if not "pon" in onu:
                                onu["pon"] = item["lastvalue"]
                            break
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
                    onu_ids.add(onu_id)

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
        with open(f"{file_csv}_part-{i:>02}.csv", "w", encoding="utf-8") as file_:
            file_.write(",".join("HOST", "ONU", "SINAL", "PON") + "\n")
            for o in tqdm(range(300000), ncols=70, desc=f"Part {i} of {parts}-"):
                if not num < total_rows:
                    break
                else:
                    if len(list_result[num]):
                       file_.write(",".join(list_result[num]) + "\n")
                num += 1

else:
    with open(f"{file_csv}.csv", "w", encoding="utf-8") as file_:
        file_.write(",".join("HOST", "ONU", "SINAL", "PON") + "\n")
        for row in tqdm(range(total_rows), ncols=70):
            if len(list_result[row]):
                file_.write(",".join(list_result[row]) + "\n")
                

print('Completed successfully.')