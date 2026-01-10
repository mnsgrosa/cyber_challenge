import pandas as pd
from handler import PsqlHandler


def extract_data(data):
    summary = [
        f"Device_name:{row['device_name']} \n CVE:{row['cve']} \n Category:{row['category_name']} \n Description:{row['description']}"
        for row in data
    ]

    return summary
