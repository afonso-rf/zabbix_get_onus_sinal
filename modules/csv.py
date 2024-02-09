#!/usr/bin/env python3


def csv_to_list(file_csv, delimiter=",") -> list:
    result = []
    for line in open(file_csv, encoding="UTF-8"):
        line = line.strip()
        if "#" not in line[:4]:
            info = line.split(delimiter)
            if len(info) > 1:
                result.append(info)

    return result
