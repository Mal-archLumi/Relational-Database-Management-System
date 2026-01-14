"""
Buffer pool for caching pages (simplified for now)
"""
from collections import OrderedDict

class BufferPool:
    """Simple LRU cache for pages"""
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        """Get item from cache, mark as recently used"""
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        """Add item to cache, evict LRU if full"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def clear(self):
        """Clear the cache"""
        self.cache.clear()