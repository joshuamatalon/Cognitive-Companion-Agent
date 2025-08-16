"""
Rate limiting and request validation for API security.
"""
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
from functools import wraps
from typing import Optional, Callable, Any

class RateLimiter:
    """Token bucket rate limiter for API protection."""
    
    def __init__(
        self, 
        rate: int = 100,  # requests per minute
        burst: int = 20    # burst capacity
    ):
        self.rate = rate
        self.burst = burst
        self.buckets = defaultdict(lambda: {
            'tokens': burst,
            'last_refill': datetime.now()
        })
        self.lock = threading.Lock()
    
    def _refill_tokens(self, bucket):
        """Refill tokens based on time elapsed."""
        now = datetime.now()
        time_passed = (now - bucket['last_refill']).total_seconds()
        
        # Add tokens based on rate
        tokens_to_add = time_passed * (self.rate / 60.0)
        bucket['tokens'] = min(self.burst, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
    
    def allow_request(self, key: str) -> bool:
        """Check if request is allowed."""
        with self.lock:
            bucket = self.buckets[key]
            self._refill_tokens(bucket)
            
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True
            
            return False
    
    def get_wait_time(self, key: str) -> float:
        """Get seconds to wait before next request is allowed."""
        with self.lock:
            bucket = self.buckets[key]
            self._refill_tokens(bucket)
            
            if bucket['tokens'] >= 1:
                return 0.0
            
            # Calculate time needed for one token
            seconds_per_token = 60.0 / self.rate
            return seconds_per_token
    
    def decorator(self, get_key_func: Optional[Callable] = None):
        """Decorator for rate limiting functions."""
        def decorator_wrapper(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Determine the key for rate limiting
                if get_key_func:
                    key = get_key_func(*args, **kwargs)
                else:
                    # Default to using the function name
                    key = func.__name__
                
                if not self.allow_request(key):
                    wait_time = self.get_wait_time(key)
                    raise Exception(f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator_wrapper
    
    def reset(self, key: Optional[str] = None):
        """Reset rate limit for a specific key or all keys."""
        with self.lock:
            if key:
                if key in self.buckets:
                    self.buckets[key] = {
                        'tokens': self.burst,
                        'last_refill': datetime.now()
                    }
            else:
                self.buckets.clear()

# Global rate limiters for different operations
search_limiter = RateLimiter(rate=120, burst=30)  # 120 searches per minute
upload_limiter = RateLimiter(rate=10, burst=5)    # 10 uploads per minute
api_limiter = RateLimiter(rate=200, burst=50)     # 200 API calls per minute
