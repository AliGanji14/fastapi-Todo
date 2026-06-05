from fastapi_swagger import patch_fastapi
from fastapi import FastAPI, Response, Request
from contextlib import asynccontextmanager
from tasks.routes import router as tasks_routes
from users.routes import router as users_routes
from fastapi.middleware.cors import CORSMiddleware
import time


tags_metadata = [
    {
        'name': 'tasks',
        'description': 'Operations related to task management',
        'externalDocs': {
            'description': 'More about tasks',
            'url': 'https://github.com/AliGanji14'
        }
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Application startup')
    yield
    print('Application shutdown')

app = FastAPI(docs_url=None,
              swagger_ui_oauth2_redirect_url=None,
              title="Todo Application",
              description=('A simple and efficient Todo management API built with FastAPI. '
                           'This API allows users to create, retrieve, update, and delete tasks. '
                           'It is designed for task tracking and productivity improvement '),
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
              openapi_tags=tags_metadata)
patch_fastapi(app)
app.include_router(tasks_routes)
app.include_router(users_routes)


@app.post('/set-cookie')
def set_cookie(response: Response):
    response.set_cookie(key='test', value='something')
    return {'message': 'cookie has been set successfully.'}


@app.get('/get-cookie')
def get_cookie(request: Request):
    print(request.cookies.get('test'))
    return {'message': 'cookie has been set successfully.'}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_method=['*'],
    allow_headers=['*'],
)
