#!/usr/bin/env python3
"""Cadastro de hosts Zabbix

Gera uma lista hosts apartir de um arquivo `csv`
ex:
host;name;ip;interfacetype;port;snmpversion;community;groups;templates;macros;tags;proxy;description


interface type default -> agent
port default agent -> 10050
port default snmp -> 161
snmp version default -> v2c

Culunas com mais de um valor são separados por vigula ","
e para colunas com chave e valor é utiliazdo `key=value`
ex:
[macros]
macro=value,macro=value
[tags]
tag1=value,tag2=value,tag3=value

"""
__version__ = "0.1.0"
__author__ = "Afonso Filho"
# %%
from pyzabbix import ZabbixAPI
from pprint import pprint as pp
from getpass import getpass
from datetime import datetime
from pathlib import Path
import csv
import sys
import urllib3

# %%
# Variables
# TODO: Adicionar lista de servidores e interação para adição
url = input("Url Zabbix: ").strip()
username = ""
passwd = ""
api_token = ""

# url = "http://localhost:8080/"
# username = "Admin"
# passwd = "zabbix"

filename = "hosts.csv"

arguments = sys.argv[1:]
# if arguments:
#     filename = arguments[0]

ROOT_PATH = Path(__file__).parent
FILE_CSV_PATH = ROOT_PATH / filename


# %%
def file_csv_to_list(file_csv, delimiter=","):
    result = []
    with open(file_csv, "r", encoding="utf-8") as csvfile:
        file_csv = csv.reader(csvfile, delimiter=delimiter, lineterminator="\n")
        for line in file_csv:
            if not "#" in line[0][:5]:
                result.append(line)
    
    return result

#%%
def host_tmpl(*host):
    parms = {
    "host": host[0].strip(),  # Index 0 -> string
    "name": host[1].strip(),  # Index 1 -> string
    }

    interface = {
        "type": 1,
        "main": 1,
    }

    if host[2].strip().replace(".", "").isdigit():  # Index 2 -> IP/DNS
        interface["ip"] = host[2].strip()
        interface["useip"] = 1
        interface["dns"] = ""
    else:
        interface["dns"] = host[2].strip()
        interface["useip"] = 0
        interface["ip"] = ""

    if not host[3].strip():  # Index 3 -> interface type
        interface["type"] = 1
        interface["port"] = "10050"  # Index 4 -> Port
    elif host[3].strip().lower() == "agent":  # Index 3 -> interface type
        interface["type"] = 1
        if not host[4].strip():  # Index 4 -> Port
            interface["port"] = "10050"
        else:
            interface["port"] = host[4].strip()
    elif host[3].strip().lower() == "snmp":  # Index 3 -> interface type
        interface["type"] = 2
        if not host[4].strip():  # Index 4 -> Port
            interface["port"] = "161"
        else:
            interface["port"] = host[4].strip()

        details = dict()
        details["community"] = "{$SNMP_COMMUNITY}"
        if not host[5].strip():      # Index 5 -> SNMP version Index 5
            details["version"] = 2
        elif host[5].strip().lower() in "v1":
            details["version"] = 1
        elif host[5].strip().lower() in "v2c":
            details["version"] = 2
        elif "3" in host[5].strip().lower():
            # TODO: Adicionar auth/privpassphrase e auth/privprotocol
            details["version"] = 3
            details["contextname"], details["securityname"] = host[5].split(",").strip()

        interface["details"] = details
    elif host[3].strip().lower() == "ipmi":  # Index 3 -> interface type
        interface["type"] = 3
        if not host[4].strip():  # Index 4 -> Port
            interface["port"] = "623"
        else:
            interface["port"] = host[4].strip()
    elif host[3].strip().lower() == "jmx":  # Index 3 -> interface type
        interface["type"] = 4
        if not host[4].strip():  # Index 4 -> Port
            interface["port"] = "12345"
        else:
            interface["port"] = host[4].strip()

    parms["interfaces"] = interface  # Arry of Obj

    groups = []
    if host[7].strip():  # Index 7 -> Groups
        for group_name in host[7].split(","):
            if group_name:
                groups.append({"name": group_name.strip()})

    parms["groups"] = groups  # Arry of Obj {"groupid": value}

    templates = []
    if host[8].strip():  # Index 8 -> Templates
        for tmpl_name in host[8].split(","):
            if tmpl_name:
                templates.append({"name": tmpl_name.strip()})

    parms["templates"] = templates  # Arry of Obj {"templateid": value}

    macros = []
    if interface["type"] == 2 and host[6].strip():  # Index 6 -> SNMP Community
        macros.append(
            {
                "macro": "{$SNMP_COMMUNITY}",
                "value": host[6].strip(),
            }
        )
    if host[9].strip():  # Index 9 -> Macros
        for macro in host[9].split(","):
            if "=" in macro:
                macro_, value = macro.split("=")
                macros.append(
                    {
                        "macro": macro_.strip(),
                        "value": value.strip(),
                    }
                )
    parms["macros"] = macros  # Arry of Obj {"macro": string, "value": string}

    tags = []
    if host[10].strip():  # Index 10 -> Tags
        for tag in host[10].split(","):
            if "=" in tag:
                tag_, value = tag.split("=")
                tags.append(
                    {
                        "tag": tag_.strip(),
                        "value": value.strip(),
                    }
                )
    parms["tags"] = tags  # Arry of Obj {"tag": string, "value": string}

    proxy = ""
    if host[11].strip():  # Index 11 -> PROXY
        proxy = host[11].strip()
    parms["proxy_hostid"] = proxy  # string

    description = ""
    if host[12].strip():  # Index 12 -> Description
        description = host[12].strip()
    parms["description"] = description  # string

    return parms


# %%
# TODO: Criar interação para solicitação de user/senha
# Zabbix connect
zapi = ZabbixAPI(url)
# Disable SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
zapi.session.verify = False
while True:
    if api_token:
        zapi.login(api_token=api_token)
        break
    elif username and passwd:
        zapi.login(username, passwd)
        break
    else:
        username = input("User Zabbix: ").strip()
        passwd = getpass("Password: ").strip()
pp(f"Connected to Zabbix API Version {zapi.api_version()}.")

# %%
result = [["HOST NAME", "STATUS"]]

host_list = file_csv_to_list(FILE_CSV_PATH, ",")

# Addcion hosts
for i in range(len(host_list)):
    host_data = host_tmpl(*host_list[i])
    hostname = host_data["host"]
    groups = host_data["groups"]
    templates = host_data["templates"]
    proxy = host_data["proxy_hostid"]
    
    
    if host_data["interfaces"]["ip"] != "":
        ip_dns =  "ip", host_data["interfaces"]["ip"]
    else:
        ip_dns =   "dns", host_data["interfaces"]["dns"]

    group_invalid = []
    if groups != []:
        for group in groups:
            groupid = zapi.hostgroup.get(filter={"name": group["name"]})

            if groupid != []:
                group["groupid"] = groupid[0]["groupid"]
            else:
                group_invalid.append(group["name"])

    template_invalid = []
    if templates != []:
        for template in templates:
            templateid = zapi.template.get(filter={"name": template["name"]})
            if templateid != []:
                template["templateid"] = templateid[0]["templateid"]
            else:
                template_invalid.append(template["name"])
    
    if proxy:
        proxyid = zapi.proxy.get(filter={"host": proxy})
        if proxyid != []:
            host_data["proxy_hostid"] = proxyid[0]["proxyid"]
        else:
            del host_data["proxy_hostid"]
    else:
        del host_data["proxy_hostid"]
    
    if not hostname:
        print("Sem hostname")
    else:
        print("Iniciando verificação de cadastro")
        hosts_valid = zapi.host.get(filter={"host": hostname})
        if ip_dns[0] == "ip":
            ip_valid = zapi.hostinterface.get(filter={"ip": ip_dns[1]})
        else:
            ip_valid = zapi.hostinterface.get(filter={"dns": ip_dns[1]})
            
        if hosts_valid != []:
            print(f"`{host_data['name']}` host already registered")
            result.append([host_data["name"], "host already registered"])
        elif " " in hostname:
            print(f"`{host_data['name']}` incorrect characters used")
            result.append([host_data["name"], "Incorrect characters used"])
        elif ip_valid != []:
            print(f"`{host_data['name']}` IP or DNS already registered")
            result.append([host_data["name"], f"IP or DNS already registered `{ip_dns}`"])
        elif group_invalid != []:
            print(f"`{host_data['name']}` Hostgroup unknown `{group_invalid}`")
            result.append([host_data["name"], f"Hostgroup unknown `{group_invalid}`"])
        elif template_invalid != []:
            print(f"`{host_data['name']}` Template unknown `{template_invalid}`")
            result.append([host_data["name"], f"Template unknown `{template_invalid}`"])

        else:
            print("Unregistered host")
            print(f"Starting `{host_data['name']}` registration")
            # TODO: Adição do try/except para tratativa de erro no zapi.host.create
            new_host = zapi.host.create(host_data)
            print(f"Successfully")
            result.append([host_data["name"], "Successfully"])

# %%
today = datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M")
file_result = ROOT_PATH / f"create_result_{today}.csv"
with open(file_result, 'w', encoding="utf-8") as file_:
    spamwriter = csv.writer(file_, lineterminator="\n")
    for item in result:
        spamwriter.writerow(item)
# %%
