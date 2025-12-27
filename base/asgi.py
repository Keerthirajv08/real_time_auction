import os
from django.core.asgi import get_asgi_application

# 1. Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')

# 2. Initialize the Django ASGI application FIRST
# This ensures that Django's AppRegistry is ready before any app code is imported.

# 3. NOW it is safe to import Channels routing and your consumers
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import auction.routing

# 4. Define the ASGI application
application = ProtocolTypeRouter({
    # Use the initialized Django app for HTTP requests
    "http": get_asgi_application(),
    
    # Route WebSocket requests to your consumers
    "websocket": AuthMiddlewareStack(
        URLRouter(
            auction.routing.websocket_urlpatterns
        )
    ),
})




