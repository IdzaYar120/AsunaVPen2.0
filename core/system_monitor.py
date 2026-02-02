
import psutil
import time

class SystemMonitor:
    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()
        
    def get_stats(self):
        # CPU
        cpu = psutil.cpu_percent(interval=None)
        
        # RAM
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_used_gb = round(mem.used / (1024**3), 1)
        ram_total_gb = round(mem.total / (1024**3), 1)
        
        # Disk (C:)
        try:
            disk = psutil.disk_usage('C:\\')
            disk_free_gb = round(disk.free / (1024**3), 1)
            disk_percent = disk.percent
        except:
            disk_free_gb = 0
            disk_percent = 0
            
        # Battery
        battery = psutil.sensors_battery()
        bat_percent = battery.percent if battery else None
        is_plugged = battery.power_plugged if battery else True
        
        # Network Speed Calculation
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        
        elapsed = current_time - self.last_time
        if elapsed < 1: elapsed = 1 # Prevent division by zero
        
        bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv
        
        # Convert to KB/s or MB/s inside UI or here
        upload_speed = bytes_sent / elapsed
        download_speed = bytes_recv / elapsed
        
        self.last_net_io = current_net_io
        self.last_time = current_time
        
        return {
            "cpu": cpu,
            "ram_percent": ram_percent,
            "ram_text": f"{ram_used_gb}/{ram_total_gb} GB",
            "disk_free": f"{disk_free_gb} GB",
            "battery": bat_percent,
            "plugged": is_plugged,
            "upload": upload_speed,
            "download": download_speed
        }
