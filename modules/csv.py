#!/usr/bin/env python3


def csv_to_list(file_csv, delimiter=","):
    result = []
    for line in open(file_csv, encoding="UTF-8"):
        line = line.strip()
        if "#" not in line[:4]:
            user = line.split(delimiter)
            if len(user) > 1:
                result.append(user)

    return result
