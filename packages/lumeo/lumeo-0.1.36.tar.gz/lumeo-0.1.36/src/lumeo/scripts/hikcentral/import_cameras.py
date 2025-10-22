import requests
import argparse
import asyncio
import urllib3
import base64
import hashlib
import hmac

from datetime import datetime
from urllib.parse import urlparse

from lumeo.api import LumeoApiClient
from lumeo.utils import print_banner

urllib3.disable_warnings()

state = {
    "lumeo_app_id": "",
    "lumeo_app_token": "",
    "system_info": None,
    "hik_server": "",
    "hik_username": "",
    "hik_password": "",
    "hik_token": None,
    "start_time": None,
    "duration": None,
    "session": requests.Session(),
    "cameras": [],
    "created_tags": {}
}

async def request_with_auth(method, path, json=None, params=None, **kwargs):
    """
    Make authenticated request to HikCentral API and handle common response parsing
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., '/artemis/api/resource/v1/site/siteList')
        json: JSON body for request
        params: Query parameters
        
    Returns:
        Tuple of (success: bool, data: dict/list, error_msg: str)
    """
    # Build full URL
    url = f"https://{state['hik_server']}{path}"
    
    # Parse URL to get path for signature
    parsed_url = urlparse(url)
    url_path = parsed_url.path
    if parsed_url.query:
        url_path += "?" + parsed_url.query
        
    # Compute signature
    text_to_sign = ""
    text_to_sign += method.upper() + "\n"
    text_to_sign += "application/json\n"
    text_to_sign += "application/json\n"
    text_to_sign += url_path
    
    # Create HMAC-SHA256 signature
    signature = base64.b64encode(
        hmac.new(
            state['hik_password'].encode('utf-8'),
            text_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    # Set authentication headers
    headers = kwargs.get('headers', {})
    headers.update({
        'X-Ca-Key': state['hik_username'],
        'X-Ca-Signature': signature,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    resp = state['session'].request(
        method, url, json=json, params=params, headers=headers, **kwargs
    )
    
    # Handle response parsing
    if not resp.ok:
        return False, None, f"HTTP {resp.status_code}: {resp.text}"
    
    try:
        response_data = resp.json()
    except Exception as e:
        return False, None, f"Failed to parse JSON response: {str(e)}"
    
    # Check HikCentral API response code
    if response_data.get('code') != '0':
        return False, None, response_data.get('msg', 'Unknown API error')
    
    return True, response_data.get('data'), None
        

async def select_or_verify_gateway():
    if state['gateway_id']:
        gateway = await state['lumeo_api_client'].get_gateway(state['gateway_id'])
        if gateway:
            print(f"Linking to gateway {gateway['name']} with ID {gateway['id']}")
            return gateway['id']
        else:
            print(f"No gateway found with ID {state['gateway_id']}")
            return None
    else:
        gateways = await state['lumeo_api_client'].get_gateways()        
        available_gateways = [gateway['id'] for gateway in gateways]
        if gateways:
            print("Select a Lumeo AI Gateway to process the imported cameras:")
            print("-" * 100)
            for idx, gateway in enumerate(gateways):
                print(f"{idx}. {gateway['id']}: {gateway['name']} ({gateway['status']})")
            while True:
                gateway_id = input("Enter the number or ID of the gateway to link imported cameras to: ")
                if gateway_id in available_gateways:
                    state['gateway_id'] = gateway_id
                    return state['gateway_id']
                elif gateway_id.isdigit() and int(gateway_id) in range(len(gateways)):
                    state['gateway_id'] = gateways[int(gateway_id)]['id']
                    return state['gateway_id']
                else:
                    print(f"Invalid gateway ID. Pick from the list above.")
        else:
            print("No gateways found in this workspace.")
            return None


async def fetch_system_info():    
    success, data, error = await request_with_auth('POST', '/artemis/api/common/v1/version')
    if success:
        state['system_info'] = data
        print(f"Connecting to {data['produceName']} ({data['softVersion']})")
        return True

    print(f"Failed to fetch HikCentral system info. Please check the HikCentral server parameter. Error: {error}")        
    return False


async def fetch_sites():
    """
    Fetch all sites from HikCentral with pagination
    """
    all_sites = []
    page_no = 1
    page_size = 100
    
    while True:
        body = {
            "pageNo": page_no,
            "pageSize": page_size
        }
        
        success, data, error = await request_with_auth('POST', '/artemis/api/resource/v1/site/siteList', json=body)
        
        if not success:
            print(f"Failed to fetch sites (page {page_no}): {error}")
            break
        
        sites = data.get('list', [])
        all_sites.extend(sites)
        
        # Check if we have more pages
        total = data.get('total', 0)
        if page_no * page_size >= total:
            break
            
        page_no += 1
    
    return all_sites


async def fetch_regions_for_site(site_index_code):
    """
    Fetch all regions for a specific site with pagination
    """
    all_regions = []
    page_no = 1
    page_size = 200
    
    while True:
        body = {
            "pageNo": page_no,
            "pageSize": page_size,
            "siteIndexCode": site_index_code
        }
        
        success, data, error = await request_with_auth('POST', '/artemis/api/resource/v1/regions', json=body)
        
        if not success:
            print(f"Failed to fetch regions for site {site_index_code} (page {page_no}): {error}")
            break
        
        regions = data.get('list', [])
        all_regions.extend(regions)
        
        # Check if we have more pages
        total = data.get('total', 0)
        if page_no * page_size >= total:
            break
            
        page_no += 1
    
    return all_regions


def build_region_hierarchy(regions):
    """
    Build a hierarchy of regions and return a mapping of region codes to full paths
    """
    region_map = {region['indexCode']: region for region in regions}
    region_paths = {}
    
    def get_region_path(region_code):
        if region_code in region_paths:
            return region_paths[region_code]
        
        region = region_map.get(region_code)
        if not region:
            return ""
        
        parent_code = region.get('parentIndexCode')
        sanitized_name = region['name'].replace('/', '_')
        if parent_code == '-1' or not parent_code or parent_code == region_code:
            path = sanitized_name
        else:
            parent_path = get_region_path(parent_code)
            path = f"{parent_path}/{sanitized_name}" if parent_path else sanitized_name
        
        region_paths[region_code] = path
        return path
    
    # Build paths for all regions
    for region in regions:
        get_region_path(region['indexCode'])    
    
    return region_paths


async def fetch_cameras_for_site(site_index_code):
    """
    Fetch all cameras for a specific site with pagination
    """
    all_cameras = []
    page_no = 1
    page_size = 100
    
    while True:
        body = {
            "pageNo": page_no,
            "pageSize": page_size,
            "siteIndexCode": site_index_code,
            "deviceType": "encodeDevice"
        }
        
        success, data, error = await request_with_auth('POST', '/artemis/api/resource/v1/cameras', json=body)
        
        if not success:
            print(f"Failed to fetch cameras for site {site_index_code} (page {page_no}): {error}")
            break
        
        cameras = data.get('list', [])
        all_cameras.extend(cameras)
        
        # Check if we have more pages
        total = data.get('total', 0)
        if page_no * page_size >= total:
            break
            
        page_no += 1
    
    return all_cameras


async def get_camera_stream_url(camera_index_code):
    """
    Get the stream URL for a specific camera
    """
    body = {
        "cameraIndexCode": camera_index_code,
        "streamType": 0 if state['quality'] == 'hi' else 1,
        "protocol": "rtsp_s",
        "transmode": 1,
        "requestWebsocketProtocol": 0
    }
    
    success, data, error = await request_with_auth('POST', '/artemis/api/video/v1/cameras/previewURLs', json=body)
    
    if success:
        return data.get('url')
    else:
        print(f"Failed to get stream URL for camera {camera_index_code}: {error}")
        return None


async def fetch_cameras():
    """
    Fetch all cameras from all sites in HikCentral
    """
    print("Fetching sites...")
    sites = await fetch_sites()
    
    if not sites:
        print("No sites found")
        return
    
    all_cameras = []
    
    for site in sites:
        site_index_code = site['siteIndexCode']
        site_name = site['siteName']
        
        print(f"Fetching regions for site: {site_name}")
        regions = await fetch_regions_for_site(site_index_code)
        region_paths = build_region_hierarchy(regions)
        
        print(f"Fetching cameras for site: {site_name}")
        cameras = await fetch_cameras_for_site(site_index_code)
        
        for camera in cameras:
            camera['site_name'] = site_name
            camera['site_index_code'] = site_index_code
            
            # Map region ID to region path
            region_index_code = camera.get('regionIndexCode')
            if region_index_code and region_index_code in region_paths:
                camera['region_path'] = region_paths[region_index_code]
            else:
                camera['region_path'] = 'Unknown Region'
            
            all_cameras.append(camera)
    
    all_cameras.sort(key=lambda x: (x.get('site_name', ''), x.get('region_path', ''), x.get('cameraName', '')))
    state['cameras'] = all_cameras
    
    print("Available cameras:")
    print("{:<10} {:<40} {:<40} {:<40} {:<10}".format('Index', 'Camera Name', 'Site Name', 'Region Path', 'Status'))
    print("-" * 140)
    for index, camera in enumerate(all_cameras):
        print("{:<10} {:<40} {:<40} {:<40} {:<10}".format(
            index, 
            camera.get('cameraName', '')[:39], 
            camera.get('site_name', '')[:39], 
            camera.get('region_path', '')[:39],
            camera.get('status', '')
        ))

async def import_cameras():
    # Ask for the cameras to be imported
    camera_indices_to_import = input("Enter the indices or names of the cameras to import, separated by commas (Ctrl-c to exit) : ").split(',')

    # Use the Lumeo API to create streams with a specific stream URL
    for camera_index_or_name in camera_indices_to_import:
        camera = None
        if camera_index_or_name.strip().isdigit():
            camera_index = int(camera_index_or_name.strip())
            if 0 <= camera_index < len(state['cameras']):
                camera = state['cameras'][camera_index]
        else:
            camera = next((c for c in state['cameras'] if c['cameraName'] == camera_index_or_name.strip()), None)

        if camera:
            await import_camera(camera)
        else:
            print(f"No camera found with index or name {camera_index_or_name.strip()}")    


async def import_camera(camera):
    """
    This function uses the Lumeo API to create a stream with a specific stream URL from HikCentral.
    """
    camera_name = camera['cameraName']
    camera_index_code = camera['cameraIndexCode']
    site_name = camera['site_name']
    region_path = camera['region_path']
    
    # Get the stream URL for this camera
    stream_url = await get_camera_stream_url(camera_index_code)
    if not stream_url:
        print(f"Failed to get stream URL for camera {camera_name}")
        return
    
    if state['start_time'] and state['duration']:
        stream_name = f"{camera_name} ({state['start_time']} - {state['duration']}s)"
        new_stream = await state['lumeo_api_client'].create_file_stream(stream_name, stream_url, camera_id=None, gateway_id=state['gateway_id'], disable_tls_verification=True)
    else:
        stream_name = f"{region_path}/{camera_name}" if region_path else camera_name
        new_stream = await state['lumeo_api_client'].create_live_stream(stream_name, stream_url, gateway_id=state['gateway_id'])

    # Create tag path using site and region information
    lumeo_tag_path = f"HikCentral/{site_name}"
    if region_path:
        lumeo_tag_path = f"{lumeo_tag_path}/{region_path}"
    
    if lumeo_tag_path and lumeo_tag_path not in state['created_tags']:
        tag_id = await state['lumeo_api_client'].create_tag_path(lumeo_tag_path)
        state['created_tags'][lumeo_tag_path] = tag_id

    if lumeo_tag_path and lumeo_tag_path in state['created_tags']:
        await state['lumeo_api_client'].add_tag_to_stream(new_stream['id'], state['created_tags'][lumeo_tag_path])

    if new_stream:
        print(f"Successfully imported camera {camera_name} from {site_name}/{region_path}")
    else:
        print(f"Failed to import camera {camera_name}")
    

async def main():    
    print_banner("Lumeo HikCentral Camera Importer")
    
    parser = argparse.ArgumentParser(description='Fetch HikCentral cameras and import them to Lumeo.')
    parser.add_argument("-l", "--lumeo_app_id", required=True, help='Your Lumeo workspace/application ID.')
    parser.add_argument("-t", "--lumeo_app_token", required=True, help='Your Lumeo workspace/application token.')
    parser.add_argument("-s", "--hik_server", required=True, help='The server IP/FQDN of your HikCentral system. Format: IP:PORT or FQDN:PORT.')
    parser.add_argument("-u", "--hik_openapi_userkey", required=True, help='Your HikCentral OpenAPI User Key.')
    parser.add_argument("-p", "--hik_openapi_usersecret", required=True, help='Your HikCentral OpenAPI User Secret.')
    parser.add_argument("-g", "--gateway_id", help='The ID of a gateway in your Lumeo workspace to connect the cameras to. Will prompt if not specified.')
    parser.add_argument("-q", "--quality", default='high', help='Options: high/low. Determines quality of video stream. Default is high.')    
    #parser.add_argument("-i", "--start_time", help='The start time of the stream in ISO format. ex. 2024-05-02T14:30:00. If specified, will create a stream with this start time. Else creates a live stream.')
    #parser.add_argument("-d", "--duration", help='The duration of the stream in seconds. ex. 3600. Required if --start_time is specified.')
    args = parser.parse_args()

    state['lumeo_app_id'] = args.lumeo_app_id
    state['lumeo_app_token'] = args.lumeo_app_token
    state['hik_username'] = args.hik_openapi_userkey
    state['hik_password'] = args.hik_openapi_usersecret    
    state['quality'] = args.quality
    if state['quality'] == 'high':
        state['quality'] = 'hi'
    else:
        state['quality'] = 'lo'
    state['gateway_id'] = args.gateway_id
    state['session'].verify = False
    #state['start_time'] = args.start_time
    #state['duration'] = args.duration
    
    if args.start_time:
        try:
            # Try parsing with various formats
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    parsed_time = datetime.strptime(args.start_time, fmt)
                    state['start_time'] = parsed_time.isoformat()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Unable to parse the provided start time.")
            
            if not state['duration']:
                raise ValueError("--duration is required if --start_time is specified.")
            
            state['duration'] = int(state['duration'])  # Ensure duration is an integer
        except ValueError as e:
            print(f"Error: {str(e)}")
            return
    
    # Connect to HikCentral system
    state['hik_server'] = args.hik_server.removeprefix('http://').removeprefix('https://').rstrip('/')
            
    # Connect to Lumeo
    state['lumeo_api_client'] = LumeoApiClient(state['lumeo_app_id'], state['lumeo_app_token'])

    state['gateway_id'] = await select_or_verify_gateway()
    if not state['gateway_id']:
        return
    
    system_connected = await fetch_system_info()
    if not system_connected:
        return        

    await fetch_cameras()
    
    while True:
        await import_cameras()        
        if input("Do you want to import more cameras? (y/n): ").lower() != 'y':
            break
        
def run_main():
    asyncio.run(main())
        
if __name__ == "__main__":
    run_main()
