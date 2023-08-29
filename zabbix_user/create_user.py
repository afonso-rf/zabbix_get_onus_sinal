#!/usr/bin/env python3
# %%
import sys
import os
from pyzabbix import ZabbixAPI
from pprint import pprint as pp
from getpass import getpass

# %%
# Variavbles

path = os.curdir
filename = "create_users.csv"
file_url = "file_url.csv"

arguments = sys.argv[1:] # TODO: Tratar exceptions
# if arguments:
#     filename = arguments[0]
#     if len(arguments) > 1:
#         url_servers = arguments[1]
        
zbx_user = {
"username": input("Zabbix user: "),
"passwd" : getpass("Password: ")
    }
       

# %%
# TODO: Teste de conectividade

def file_csv_to_list(file_csv):
    result = []
    for line in open(file_csv, encoding="UTF-8"):
        result.append(line.strip("\n").split(','))

    return result

# %%
def zbx_user_create(url: str, access: dict, users_list: list):
    result = dict()

    # Zabbix connect
    zapi = ZabbixAPI(url)
    try:
        if "token" in access:
            zapi.login(api_token=access["token"])
        else:
            zapi.login(
                user=access["username"],
                password=access["passwd"],
            )
    except Exception as error:
        # TODO: Fazer a tratativa de erro
        pp(str(error))
        sys.exit(1)

    zbx_version = zapi.api_version()[:3]

    for user in users_list[1:]:
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
            "medias": [{"mediatypeid": "1", "sendto": [email]}],
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

            usr["usrgrps"] = [{"usrgrpid": usrgrp[0]["usrgrpid"]}]
            zapi.user.create(usr)
            result[username]["password"] = passwd
            result[username]["result"] = "success"
            pp(f" Successfully created user `{username}`.")
    
    return result

#%%

file_csv = os.path.join(path, filename)
file_url = os.path.join(path, file_url)

users_list = file_csv_to_list(file_csv)
url_servers = file_csv_to_list(file_url)

pp(users_list)
# result = zbx_user_create(url, zbx_user, users_list)
# pp(result)

# %%
