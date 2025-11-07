import psutil
import time
from datetime import datetime
from config import *

start_time = time.time()

def get_system_status():
    try:
        memory = psutil.virtual_memory()
        memory_usage = f"{memory.percent}٪"
        cpu_usage = f"{psutil.cpu_percent()}٪"
        
        uptime_seconds = time.time() - start_time
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime = f"{uptime_hours}h {uptime_minutes}m"
        
        return {
            'memory': memory_usage,
            'cpu': cpu_usage,
            'uptime': uptime
        }
    except:
        return {'memory': '?', 'cpu': '?', 'uptime': '?'}

def get_status_text():
    status = get_system_status()
    active_accounts = sum(1 for acc in ACCOUNTS if acc['active'])
    
    return (
        f"🔄 وضعیت سیستم\n\n"
        f"🤖 ربات: 🟢 آنلاین\n"
        f"💾 حافظه: {status['memory']}\n"
        f"⚡ پردازنده: {status['cpu']}\n"
        f"⏰ آپتایم: {status['uptime']}\n"
        f"👥 اکانت‌ها: {active_accounts}\n"
        f"🏢 فیلتر: {current_filter}"
    )
