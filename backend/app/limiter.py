from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance (M3-API-4)
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
