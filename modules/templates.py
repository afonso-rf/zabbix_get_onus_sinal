#!/usr/bin/env python3


def user_create_tmpl(*users_list):
    result = dict()

    for user in users_list:
        if user:
            fullname = user[0].strip().split()
            email = user[1].strip().lower()
            login = email.split("@")[0]

            passwd = (
                f"{login[:2].lower()}"
                f"{len(email):>02}"
                f"{login.split('.')[1][:3].upper() if len(login.split('.')) > 1  else login[-3:].upper()}"
                f"{len(user[0]):>02}"
                "#Mudar"
            )

            usr = {
                "name": " ".join(fullname).title(),
                "email": email,
                "login": login,
                "password": passwd,
            }
            result[login] = usr

    return result
