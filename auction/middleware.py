#add security and logging to the django settings

from django.core.cache import cache
from django.http import JsonResponse
import time


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/bid/'):
            if not self.check_rate_limit(request):
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429
                )           
        response = self.get_response(request)
        return response


    def check_rate_limit(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        ip = self.get_client_ip(request)

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


