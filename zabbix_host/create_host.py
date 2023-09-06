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
from dotenv import load_dotenv
from getpass import getpass
import os
import sys

# %%
# Variables
load_dotenv()
url = os.getenv("URL")
username = os.getenv("ZBX_USERNAME") or None
passwd = os.getenv("ZBX_PASSWD") or None
api_token = os.getenv("ZBX_TOKEN_API") or None

# url = "http://localhost:8080/"
# username = "Admin"
# passwd = "zabbix"

filename = "hosts.csv"

arguments = sys.argv[1:]
# if arguments:
#     filename = arguments[0]

path = os.curdir
file_csv = os.path.join(path, filename)


# %%
def file_csv_to_list(file_csv, delimiter=","):
    result = []
    for line in open(file_csv, encoding="UTF-8"):
        line = line.strip()
        if "#" not in line[:4]:
            result.append(line.split(delimiter))
    return result


#%%
def host_tmpl(host: list):
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
            details["contextname"] = host[5].split(",")[1].strip()
            details["securityname"] = host[5].split(",")[2].strip()

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

host_list = file_csv_to_list(file_csv, ";")
# Addcion hosts
for i in range(1, len(host_list)):
    host_date = host_tmpl(host_list[i])
    hostname = host_date["host"]
    groups = host_date["groups"]
    templates = host_date["templates"]
    proxy = host_date["proxy_hostid"]
    
    
    if host_date["interfaces"]["ip"] != "":
        ip_dns =  "ip", host_date["interfaces"]["ip"]
    else:
        ip_dns =   "dns", host_date["interfaces"]["dns"]

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
            host_date["proxy_hostid"] = proxyid[0]["proxyid"]
        else:
            del host_date["proxy_hostid"]
    else:
        del host_date["proxy_hostid"]
    
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
            print(f"`{host_date['name']}` host already registered")
            result.append([host_date["name"], "host already registered"])
        elif " " in hostname:
            print(f"`{host_date['name']}` incorrect characters used")
            result.append([host_date["name"], "Incorrect characters used"])
        elif ip_valid != []:
            print(f"`{host_date['name']}` IP or DNS already registered")
            result.append([host_date["name"], f"IP or DNS already registered `{ip_dns}`"])
        elif group_invalid != []:
            print(f"`{host_date['name']}` Hostgroup unknown `{group_invalid}`")
            result.append([host_date["name"], f"Hostgroup unknown `{group_invalid}`"])
        elif template_invalid != []:
            print(f"`{host_date['name']}` Template unknown `{template_invalid}`")
            result.append([host_date["name"], f"Template unknown `{template_invalid}`"])

        else:
            print("Unregistered host")
            print(f"Starting `{host_date['name']}` registration")
            new_host = zapi.host.create(host_date)
            print(f"Successfully")
            result.append([host_date["name"], "Successfully"])

# %%
file_result = os.path.join(path, "result.csv")
with open(file_result, "w", encoding="UTF-8") as file_:
    for line in result:
        file_.write(";".join(line) + "\n")
# %%
