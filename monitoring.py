import os
import time
import structlog
import sentry_sdk
from prometheus_client import Counter, Histogram, start_http_server
from functools import wraps
from typing import Optional, Callable, Any
from ratelimit import limits, RateLimitException
from redis import Redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Sentry for error tracking
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "development")
)

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Initialize Redis for rate limiting
redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

# Prometheus metrics
SLACK_REQUESTS = Counter(
    "slack_requests_total",
    "Total number of Slack requests",
    ["type", "status"]
)

NINETY_REQUESTS = Counter(
    "ninety_requests_total",
    "Total number of Ninety.io requests",
    ["type", "status"]
)

REQUEST_LATENCY = Histogram(
    "request_duration_seconds",
    "Request latency in seconds",
    ["type"]
)

def start_metrics_server(port: int = 8000) -> None:
    """Start Prometheus metrics server"""
    start_http_server(port)
    logger.info("metrics_server_started", port=port)

def track_timing(metric_type: str) -> Callable:
    """Decorator to track timing of functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                REQUEST_LATENCY.labels(type=metric_type).observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                sentry_sdk.capture_exception(e)
                raise
        return wrapper
    return decorator

def rate_limit(calls: int, period: int) -> Callable:
    """Decorator for rate limiting with Redis"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a unique key for this function
            key = f"ratelimit:{func.__name__}"
            
            # Get current count from Redis
            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, period, 1)
            elif int(current) >= calls:
                raise RateLimitException(
                    f"Rate limit exceeded: {calls} calls per {period} seconds"
                )
            else:
                redis_client.incr(key)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_error(error: Exception, context: Optional[dict] = None) -> None:
    """Centralized error logging"""
    if context is None:
        context = {}
    
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context
    )
    sentry_sdk.capture_exception(error)

def track_slack_request(request_type: str, status: str = "success") -> None:
    """Track Slack request metrics"""
    SLACK_REQUESTS.labels(type=request_type, status=status).inc()

def track_ninety_request(request_type: str, status: str = "success") -> None:
    """Track Ninety.io request metrics"""
    NINETY_REQUESTS.labels(type=request_type, status=status).inc()

# Example usage:
# @track_timing("create_item")
# @rate_limit(calls=100, period=60)
# def create_item():
#     pass 