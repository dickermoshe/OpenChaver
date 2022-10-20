import logging
import requests

from .const import API_BASE_URL

logger = logging.getLogger(__name__)

def get_json(r: requests.Response) -> dict:
    """Get JSON from a requests response"""
    try:
        return r.json()
    except:
        return {}

def api(url,data=None,method='POST') -> list[bool,dict]:
    try:
        logger.info(f"Calling {API_BASE_URL + url} as {method}")
        r = requests.request(method, API_BASE_URL + url, json=data,verify=False)
    except:
        logger.error(f"Failed to call {API_BASE_URL + url}")
        return False, {}
    
    json = get_json(r)
    
    logger.info(f"Status: {r.status_code}")

    if str(r.status_code).startswith('2'):
        status = True
    else:
        status = False

    return status, json

