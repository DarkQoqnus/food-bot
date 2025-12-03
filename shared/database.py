import redis
import json
from shared.config import Config

class Database:
    def __init__(self):
        self.redis_client = None
        if Config.REDIS_URL:
            self.redis_client = redis.from_url(Config.REDIS_URL)
    
    def set_status(self, key, value):
        if self.redis_client:
            self.redis_client.set(key, json.dumps(value))
        else:
            # Fallback to file or memory
            pass
    
    def get_status(self, key):
        if self.redis_client:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        return None

db = Database()
