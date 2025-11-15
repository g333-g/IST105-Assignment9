from django.shortcuts import render
import requests
from requests.auth import HTTPBasicAuth
from dnac_config import DNAC, MONGODB
import urllib3
from pymongo import MongoClient
from datetime import datetime

urllib3.disable_warnings()

client = MongoClient(f"mongodb://{MONGODB['host']}:{MONGODB['port']}/")
db = client[MONGODB['database']]
logs_collection = db['logs']

def get_auth_token():
    try:
        url = f"https://{DNAC['host']}:{DNAC['port']}/dna/system/api/v1/auth/token"
        response = requests.post(
            url,
            auth=HTTPBasicAuth(DNAC['username'], DNAC['password']),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        return response.json()['Token']
    except Exception as e:
        return None

def authenticate(request):
    token = get_auth_token()
    
    logs_collection.insert_one({
        'timestamp': datetime.now(),
        'action': 'authenticate',
        'result': 'success' if token else 'failure'
    })
    
    return render(request, 'authenticate.html', {'token': token})

def list_devices(request):
    token = get_auth_token()
    devices = None
    
    if token:
        try:
            url = f"https://{DNAC['host']}:{DNAC['port']}/api/v1/network-device"
            headers = {"X-Auth-Token": token}
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()
            devices = response.json().get('response', [])
            
            logs_collection.insert_one({
                'timestamp': datetime.now(),
                'action': 'list_devices',
                'result': 'success'
            })
        except Exception as e:
            logs_collection.insert_one({
                'timestamp': datetime.now(),
                'action': 'list_devices',
                'result': 'failure'
            })
    
    return render(request, 'list_devices.html', {'devices': devices})

def device_interfaces(request):
    device_ip = request.GET.get('ip', '')
    token = get_auth_token()
    interfaces = None
    
    if token and device_ip:
        try:
            url = f"https://{DNAC['host']}:{DNAC['port']}/api/v1/network-device"
            headers = {"X-Auth-Token": token}
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            devices = response.json().get('response', [])
            
            device = next((d for d in devices if d.get('managementIpAddress') == device_ip), None)
            
            if device:
                url = f"https://{DNAC['host']}:{DNAC['port']}/api/v1/interface"
                params = {"deviceId": device['id']}
                response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
                interfaces = response.json().get('response', [])
                
                logs_collection.insert_one({
                    'timestamp': datetime.now(),
                    'action': 'device_interfaces',
                    'device_ip': device_ip,
                    'result': 'success'
                })
        except Exception as e:
            logs_collection.insert_one({
                'timestamp': datetime.now(),
                'action': 'device_interfaces',
                'device_ip': device_ip,
                'result': 'failure'
            })
    
    return render(request, 'device_interfaces.html', {'interfaces': interfaces, 'device_ip': device_ip})

