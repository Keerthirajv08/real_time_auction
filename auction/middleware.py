#add security and logging to the django settings
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django_redis import get_redis_connection
import time

class RateLimitMiddleware:
    #DSA configuration: Token Bucket
    BUCKET_CAPACITY = 10
    # Refill Rate: How fast tokens regnerate (10 reqs per 60 secs = 1 req per 6 secs)
    REFILL_RATE = 10.0 / 60.0

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply DSA limits to critical endpoints to save resources
        if request.path.startswith('/api/bid/'):
            if not self.check_rate_limit(request):
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429
                )           
        response = self.get_response(request)
        return response

    def check_rate_limit(self, request):
        """Executes the Token Bucket algorithm atomically using Redis Lua script.
        Returns True if the request is allowed, False otherwise."""
        user_id = request.user.id if request.user.is_authenticated else None
        ip = self.get_client_ip(request)

        # Unique key for this user or IP combo
        key = f'rate_limit_bid_{user_id or ip}'
        requests = cache.get(key, [])
        now = time.time()

        requests = [req_time for req_time in requests if now - req_time < 60]

        if len(requests) >= 10:
            return False
        
        requests.append(now)
        cache.set(key, requests, 60)
        return True
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def allow_request(self, request):

        user_id = request.user.id if request.user.is_authenticated else "anon"
        ip = self.get_client_ip(request)

        key = f"rate_limit:{user_id}:{ip}"

        con = get_redis_connection("default")

        lua_script = """
            local key = KEYS[1]
            local rate = tonumber(ARGV[1])
            local capacity = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            local requested = tonumber(ARGV[4])
            
            -- Fetch current state (tokens, last_refill_time)
            local data = redis.call('hmget', key, 'tokens', 'last_refill')
        local tokens = tonumber(data[1])
        local last_refill = tonumber(data[2])

        -- Initialize if not exists
        if not tokens then
            tokens = capacity
            last_refill = now
        end

        -- Calculate refill based on time passed
        local delta = math.max(0, now - last_refill)
        local filled_tokens = math.min(capacity, tokens + (delta * rate))

        -- Check if we have enough tokens
        local allowed = false
        if filled_tokens >= requested then
            filled_tokens = filled_tokens - requested
            allowed = true
            -- Update state in Redis
            redis.call('hmset', key, 'tokens', filled_tokens, 'last_refill', now)
            -- Set expiry to clean up inactive users (e.g., 60 seconds)
            redis.call('expire', key, 60)
        end

        return allowed
        """

        current_time = time.time()

        is_allowed = con.eval(
            lua_script,
            1,
            key,
            self.REFILL_RATE,
            self.BUCKET_CAPACITY,
            current_time,
            1
        )

        return bool(is_allowed)

   

