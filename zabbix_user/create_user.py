#!/usr/bin/env python3
# %%
import sys
import os
from pyzabbix import ZabbixAPI
from pprint import pprint as pp
from getpass import getpass
from time import sleep

# %%
# Variavbles

path = os.curdir
filename = "create_users.csv"
file_url = "file_url.csv"

def csv_to_list(file_csv, delimiter=","):
    result = []
    for line in open(file_csv, encoding="UTF-8"):
        line = line.strip()
        if "#" not in line[:4]:
            result.append(line.split(delimiter))

    return result

def banner(
    text: str, border: str = "=", ncol: int = 40, bottom_text: str = "(Ctrl+C to exit)"
):
    if len(text) > ncol:
        ncol = len(text)
        ncol_c = ""
        ncol_b = ""
    else:
        ncol_c = " " * int((ncol - len(text)) / 2)
        ncol_b = border * int((ncol - len(bottom_text)) / 2)

    print(border * ncol)
    print(ncol_c + text + ncol_c)
    print(ncol_b + bottom_text + ncol_b)
    print()

def get_url():
    banner("Enter the Zabbix url")
    try:
        while True:
            url = input("Url Zabbix: ")
            if "://" in url:
                return url
            else:
                print(f"Url invalid {url}")
    except KeyboardInterrupt:
        print("\nGood bye!")
        sys.exit()

def get_user_passwd():
    banner("Enter the username and password")
    try:
        while True:
            username = input("Zabbix User: ").strip()
            passwd = getpass("Password: ").strip()
            if username and passwd:
                return username, passwd
    except KeyboardInterrupt:
        print("\nGood bye!")
        sys.exit()

def zbx_connect(zbx_srv: list):
    zbxname = zbx_srv[0].upper().strip()
    url = zbx_srv[1].strip()
    
    try:
        api_token = zbx_srv[2].strip()
    except IndexError:
        api_token = ""
    
    while True:
        zapi = ZabbixAPI(url)
        try: 
            if api_token:
                zapi.login(api_token=api_token)
            else:
                username, passwd = get_user_passwd()
                zapi.login(user=username, password=passwd)
            
            print(f"Connected to Zabbix {zbxname} API Version {zapi.api_version()}.")
            sleep(1)
            break
        except Exception as error:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f'Connect Zabbix {zbxname}.')
            if "name or password" in str(error): 
                print("[ERROR] Login name or password is incorrect")
                username, passwd = get_user_passwd()
            elif "Not Found for url" in str(error):
                print("[ERROR] Not Found for url")
                url = get_url()
            elif "Invalid URL" in str(error):
                print("[ERROR] " + str(error))
                url = get_url()
            elif "Failed to establish a new connection" in str(error):
                print(f"[ERROR] Failed to establish a new connection `{url}`.")
                url = get_url()
            else:
                print(str(error)) 
                sys.exit(1)
    return zapi

def zbx_user_create(zapi, users_list: list):
    result = dict()
    zbx_version = zapi.api_version()[:3]

    for user in users_list:
        fullname = user[0].strip().split()
        email = user[1].strip().lower()
        user_role = user[2].strip()
        user_group = user[3].strip()

        username = email.split("@")[0]
        passwd = (
            f"{fullname[0][:2].lower()}"
            f"{len(email):>02}"
            f"{fullname[1][:3].upper() if len(fullname) > 1 else fullname[0][-3:].upper()}"
            f"{len(user[0]):>02}"
            "#Mudar"
        )

        usr = {
            "name": fullname[0].title(),
            "surname": " ".join(fullname[1:]).title(),
            "passwd": passwd,
        }
        
        if username not in result:
            result[username] = {}
        if float(zbx_version) >= 6:
            already_exist = zapi.user.get(filter={"username": username})
            role = zapi.role.get(filter={"name": user_role})
        else:
            already_exist = zapi.user.get(filter={"alias": username})
            if float(zbx_version) >= 5.2:
                role = zapi.role.get(filter={"name": user_role})

        usrgrp = zapi.usergroup.get(filter={"name": user_group})

        if already_exist != []:
            pp(f"User `{username}` already registered")
            result[username]["result"] = "existing"
        elif float(zbx_version) >= 5.2 and role == []:
            result[username]["result"] = "unknown role"
            pp(f"Unknown `{user_role}` role.")
        elif usrgrp == []:
            result[username]["result"] = "unknown group"
            pp(f"Unknown `{user_group}` group.")
        else:
            if float(zbx_version) < 6:
                usr["alias"] = username
            else:
                usr["username"] = username

            if float(zbx_version) >= 5.2:
                usr["roleid"] = role[0]["roleid"]

            if float(zbx_version) >= 5.2:
                usr["medias"] = [{"mediatypeid": "1", "sendto": [email]}]
            else:    
                usr["user_medias"] = [{"mediatypeid": "1", "sendto": [email]}]

            usr["usrgrps"] = [{"usrgrpid": usrgrp[0]["usrgrpid"]}]
            zapi.user.create(usr)
            result[username]["password"] = passwd
            result[username]["result"] = "success"
            pp(f" Successfully created user `{username}`.")

    return result

# %%

file_csv = os.path.join(path, filename)
file_url = os.path.join(path, file_url)

try:
    users_list = csv_to_list(file_csv)
except FileNotFoundError as e:
    print(str(e))
    sys.exit(1)

try:
    url_list = csv_to_list(file_url)
except FileNotFoundError:
    url = get_url()
    url_list =[("unknown", url)]
except Exception as error:
    print(error)
    sys.exit(1)

result = dict() # TODO: gerar arquivo com o resultado
for zbx_srv in url_list:
    zapi = zbx_connect(zbx_srv)
    resp = zbx_user_create(zapi, users_list)
    result[zbx_srv[0]] = resp

# %%
pp(result)
