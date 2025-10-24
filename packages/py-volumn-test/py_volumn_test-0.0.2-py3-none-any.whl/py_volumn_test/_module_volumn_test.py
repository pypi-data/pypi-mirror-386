import sys
import subprocess
import requests
import re
from zoneinfo import ZoneInfo
import json
from datetime import datetime as dt
from pyFileSizeUtils import BinarySize,SizeUnit
import hvac
import os
from h_vault_extractor_xethhung12 import GetSecrets, Pair

def exec():
    secrets = load_from_vault()
    host=secrets['host']
    collection_name=secrets['collection_name']
    bootstrap_id=secrets['bootstrap_id']
    filter_name=secrets['filter_name']
    api_key=secrets['api_key']
    # api_key, host, collection_name, filter_name, bootstrap_id
    url=f"https://{host}/rest/{collection_name}"
    def get_resource(id: str):
        return f"{url}/{id}"

    HKT = ZoneInfo("Asia/Hong_Kong")
    headers = {
        'content-type': "application/json",
        'x-apikey': api_key,
        'cache-control': "no-cache"
        }

    body = requests.get(get_resource(bootstrap_id), headers=headers)
    print(body.text)
    data = body.json()['data']

    def get_value(data: [str], value: str)->str|None:
        matched_result=None
        for r in data:
            rr=pattern.match(r)
            if rr is not None:
                matched_result=rr
                return matched_result[value] if matched_result is not None else None
        return None

    def get_line(data)->str|None:
        matched_result=None
        for r in data:
            rr=pattern.match(r)
            if rr is not None:
                return r

    def get_used_percent(data: [str])->str|None:
        return get_value(data, "used_percent")

    def get_used_size(data: [str])->str|None:
        return get_value(data, "used_size")
        
    def get_available(data: [str])->str|None:
        return get_value(data, "available_size")


    df_result = sys.stdin.readlines()
    # result_shell = subprocess.run(f"df", shell=True, capture_output=True, text=True)
    # df_result=result_shell.stdout.split("\n")
    for d in  data:
        host=d['host']
        if host != filter_name:
            continue
            
        device = d['device']
        mount_at = d['mount-at']
        result_at = d['result-at']
        pattern = re.compile(f"^{device} +(?P<block_size>\\d+) +(?P<used_size>\\d+) +(?P<available_size>\\d+) +(?P<used_percent>\\d+)% +{mount_at}$")
        raw_line=get_line(df_result)
        used_percent=get_used_percent(df_result)
        used_size=BinarySize.ofKBFromInt(int(get_used_size(df_result)))
        available=BinarySize.ofKBFromInt(int(get_available(df_result)))
        data = {
                "type":d['type'],
                "host":d['host'],
                "device":device,
                "mount-at": mount_at,
                "used_percentage": f"{int(used_percent)} %",
                "used": f"{round(float(used_size.inMB()),2)} MB",
                "used_size": int(used_size.inKB()),
                "available": f"{round(float(available.inMB()),2)} MB",
                "available_size": int(available.inKB()),
                "raw": raw_line,
                "last-update": dt.now(HKT).strftime("%Y-%m-%d %H:%M:%S")
                }
        print(json.dumps(data, ensure_ascii=False, indent=2))
        encoded_data = {
                "_id": result_at,
                "data": data
                }

        requests.put(get_resource(result_at), data=json.dumps(encoded_data,indent=2), headers=headers)

        # ===============


def load_from_vault():
# Vault configuration
    vault_addr = os.environ.get('VAULT_ADDR')
    role_id = os.environ.get('vault_role_id')  # Set this environment variable
    secret_id = os.environ.get('vault_secret_id')  # Set this environment variable
    mount_point = os.environ.get('vault_mount_point')  # Set this environment variable
    secret_path = os.environ.get('vault_secret_path')  # Set this environment variable
    secret = GetSecrets(
        vault_addr=vault_addr, role_id=role_id, secret_id=secret_id,
        mount_point=mount_point, secret_path=secret_path,keys_to_extract = [
            Pair("api_key","api_key"),
            Pair("host","host"),
            Pair("collection_name","collection_name"),
            Pair("filter_name","filter_name"),
            Pair("bootstrap_id","bootstrap_id")
        ]
    )

    return secret
