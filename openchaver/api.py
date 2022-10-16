import requests

from .const import API_BASE_URL

def api(url,data=None,method='POST'):
    try:
        r = requests.request(method, API_BASE_URL + url, json=data,verify=False)
        if str(r.status_code).startswith('2'):
            try:
                return r.json()
            except:
                return True
        else:
            return False
    except:
        return False

