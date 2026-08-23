import time
import psutil
import requests
import json
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
AGENT_TOKEN = os.getenv("AGENT_TOKEN", "default-dev-token")

def get_disk_info(path: str = "/") -> dict:
    usage = psutil.disk_usage(path)
    return {
        "mount_point": path,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "utilization_pct": round(usage.percent, 2),
    }

def main():
    print("Starting DiskMind Agent...")
    while True:
        try:
            # For hackathon demo, we check C:\ on windows and / on linux
            path = "C:\\" if os.name == 'nt' else "/"
            info = get_disk_info(path)
            
            payload = {
                "token": AGENT_TOKEN,
                "disk_info": info,
                "file_count": 0, # Placeholder for extended scanner
                "dir_count": 0,
                "daily_growth_bytes": 0
            }
            
            response = requests.post(f"{API_URL}/api/agent/upload", json=payload)
            if response.status_code == 200:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Successfully uploaded metrics: {info['utilization_pct']}% full")
            else:
                print(f"Failed to upload. Status: {response.status_code}, {response.text}")
                
        except Exception as e:
            print(f"Error during collection: {e}")
            
        # Run every 60 seconds for demo purposes
        time.sleep(60)

if __name__ == "__main__":
    main()
