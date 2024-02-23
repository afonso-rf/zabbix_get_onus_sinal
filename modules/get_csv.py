#!/usr/bin/env python3
import csv

def csv_to_list(file_csv, delimiter=",") -> list[list]:
    result = []
    
    with open(file_csv, encoding="UTF-8") as file_:
        file_csv = csv.reader(file_, delimiter=delimiter)
        for line in file_csv:
            if line and "#" not in line[0]:
                result.append(line)

    return result
