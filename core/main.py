from fastapi_swagger import patch_fastapi
from fastapi import FastAPI, Response, Request, status
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from tasks.routes import router as tasks_routes
from users.routes import router as users_routes
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.redis import RedisJobStore
from core.config import settings
import time
import httpx
import logging
from urllib.parse import urlparse
redis_url = urlparse(settings.REDIS_URL)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


jobstores = {
    "default": RedisJobStore(
        jobs_key="apscheduler.job",
        run_times_key="apscheduler.run_times",
        host=redis_url.hostname,
        port=redis_url.port,
        password=redis_url.password,
        db=1,
    )
}


scheduler = AsyncIOScheduler(jobstores=jobstores)


def my_task():
    logger.info(f"Task executed at {time.strftime('%Y-%m-%d %H:%M-%S')}")


tags_metadata = [
    {
        "name": "tasks",
        "description": "Operations related to task management",
        "externalDocs": {
            "description": "More about tasks",
            "url": "https://github.com/AliGanji14",
        },
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup")
    scheduler.add_job(
        my_task, IntervalTrigger(seconds=10), id="my_task", replace_existing=True
    )
    scheduler.start()
    yield
    scheduler.shutdown()
    print("Application shutdown")


app = FastAPI(
    docs_url=None,
    swagger_ui_oauth2_redirect_url=None,
    title="Todo Application",
    description=(
        "A simple and efficient Todo management API built with FastAPI. "
        "This API allows users to create, retrieve, update, and delete tasks. "
        "It is designed for task tracking and productivity improvement "
    ),
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Ali Ganji",
        "url": "https://github.com/AliGanji14",
        "email": "aliganji1309@gmail.com",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)
patch_fastapi(app)
app.include_router(tasks_routes)
app.include_router(users_routes)


@app.post("/set-cookie")
def set_cookie(response: Response):
    response.set_cookie(key="test", value="something")
    return {"message": "cookie has been set successfully."}


@app.get("/get-cookie")
def get_cookie(request: Request):
    print(request.cookies.get("test"))
    return {"message": "cookie has been set successfully."}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    error_response = {
        "error": True,
        "status_code": exc.status_code,
        "message": str(exc.detail),
    }
    return JSONResponse(status_code=exc.status_code, content=error_response)


@app.exception_handler(RequestValidationError)
async def http_validation_exception_handler(request, exc):
    error_response = {
        "error": True,
        "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "message": "There was a problem with your form request",
        "content": exc.errors(),
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=error_response
    )


def start_task():
    print("start task")
    print("doing the process")
    time.sleep(10)
    print("finished task")


@app.get("/initiate-task", status_code=200)
async def initiate_task(background_tasks: BackgroundTasks):
    background_tasks.add_task(start_task)
    return JSONResponse(content={"detail": "task is done"})


# caching example


from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


from redis import asyncio as aioredis

# Set up the cache backend
redis = aioredis.from_url(settings.REDIS_URL)
cache_backend = RedisBackend(redis)
FastAPICache.init(cache_backend, prefix="fastapi-cache")


async def request_current_weather(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        current_weather = data.get("current", {})
        return current_weather
    else:
        return None


@app.get("/fetch-current-weather", status_code=200)
@cache(expire=10)
async def fetch_current_weather(latitude: float = 40.7128, longitude: float = -74.0060):
    current_weather = await request_current_weather(latitude, longitude)
    if current_weather:

        return JSONResponse(content={"current_weather": current_weather})
    else:
        return JSONResponse(
            content={"detail": "Failed to fetch weather"}, status_code=500
        )


from core.email_util import send_email


# Endpoint to send email
@app.get("/test-send-mail", status_code=200)
async def test_send_mail():
    await send_email(
        subject="Test Email from FastAPI",
        recipients=["recipient@example.com"],
        body="This is a test email sent using the email_util function.",
    )
    return JSONResponse(content={"detail": "Email has been sent"})


from core.celery_conf import add_number
from celery.result import AsyncResult 

@app.get("/initiate-celery-task", status_code=200)
async def initiate_celery_task():
    add_number.delay(1, 2)
    return JSONResponse(content={"detail": add_number.delay(1, 2).id})


@app.get("/check-celery-task-result", status_code=200)
async def initiate_celery_task(task_id:str):
    result = AsyncResult(task_id).ready()
    return JSONResponse(content={"result": result})



