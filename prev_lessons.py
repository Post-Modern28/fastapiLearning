

#
# # === AUTH ===
#
#
# def docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
#     correct_username = secrets.compare_digest(credentials.username, DOCS_USER)
#     correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
#     if not (correct_username and correct_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authentication",
#             headers={"WWW-Authenticate": "Basic"},
#         )
#
#
# @app.get("/docs", include_in_schema=False)
# def custom_swagger_ui_html(credentials: HTTPBasicCredentials = Depends(docs_auth)):
#     return get_swagger_ui_html(openapi_url="/openapi.json", title="Secure Docs")
#
#
# @app.get("/openapi.json", include_in_schema=False)
# def custom_openapi(credentials: HTTPBasicCredentials = Depends(docs_auth)):
#     return JSONResponse(
#         get_openapi(title="Secure Docs", version="1.0.0", routes=app.routes)
#     )
#
#
# # === USER UTILS ===
#
#
# def get_user_from_db(username: str):
#     for user in USER_DATA:
#         if user.username == username:
#             return user
#     return None
#
#
# def get_password_hash(password):
#     return pwd_context.hash(password)
#
#
# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)
#
#
# def auth_user_dep(credentials: HTTPBasicCredentials = Depends(security)):
#     for user in USER_DATA:
#         if secrets.compare_digest(
#             credentials.username.encode("utf-8"), user.username.encode("utf-8")
#         ) and verify_password(credentials.password, user.hashed_password):
#             return user
#
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Invalid credentials",
#         headers={"WWW-Authenticate": "Basic"},
#     )
#
#
# # === ROUTES ===
#
#
# @app.post(
#     "/register",
#     responses={
#         200: {"description": "Успешная регистрация"},
#         409: {
#             "description": "Пользователь уже существует",
#             "content": {
#                 "application/json": {
#                     "example": {"message": "User Mike already exists!"}
#                 }
#             },
#         },
#     },
# )
# async def register_user(usr: User):
#     for user in USER_DATA:
#         if secrets.compare_digest(
#             usr.username.encode("utf-8"), user.username.encode("utf-8")
#         ):
#             return JSONResponse(
#                 status_code=409,
#                 content={"message": f"User {usr.username} already exists!"},
#             )
#     USER_DATA.append(
#         UserInDB(username=usr.username, hashed_password=get_password_hash(usr.password))
#     )
#     return JSONResponse(
#         status_code=200,
#         content={"message": f"User {usr.username} has been successfully registered!"},
#     )
#
#
# @app.get("/login")
# async def log_in(user: User = Depends(auth_user_dep)):
#     return {"message": f"Welcome, {user.username}!"}



















# SESSION_MAX_AGE = 60  # 5 minutes
# SESSION_REFRESH_THRESHOLD = 50  # 3 minutes
#
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#
# app = FastAPI()
# app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
#
# config = load_config()
# serializer = URLSafeSerializer(config.secret_key, salt="cookie-signature")
#
# if config.debug:
#     app.debug = True
# else:
#     app.debug = False
#
# users = {
#     'm.romanov': {"password": "1234", "user_id": str(uuid.uuid4())},
#     'a.aliev': {"password": "4321", "user_id": str(uuid.uuid4())},
#     'v.zelensky': {"password": "1488", "user_id": str(uuid.uuid4())},
# }
#
#
# def create_session_token(user_id: str) -> str:
#     timestamp = int(time.time())
#     data = f"{user_id}.{timestamp}"
#     signature = serializer.dumps(data).split(".")[-1]
#     return f"{user_id}.{timestamp}.{signature}"
#
#
# def verify_session_token(token: str):
#     try:
#         user_id, timestamp_str, signature = token.split(".")
#         expected_data = f"{user_id}.{timestamp_str}"
#         expected_signature = serializer.dumps(expected_data).split(".")[-1]
#         if expected_signature != signature:
#             raise HTTPException(status_code=401, detail={"message": "Invalid session"})
#
#         timestamp = int(timestamp_str)
#         now = int(time.time())
#
#         if now - timestamp > SESSION_MAX_AGE:
#             raise HTTPException(status_code=401, detail={"message": "Session expired"})
#
#         return user_id, timestamp
#
#     except (ValueError, BadSignature):
#         raise HTTPException(status_code=401, detail={"message": "Invalid session"})
#
#
#
# @app.get("/login")
# async def login_get():
#     html_path = os.path.join(BASE_DIR, "login.html")
#     return FileResponse(html_path)
#
#
#
# @app.post("/login")
# async def login(response: Response, username: str = Form(...), password: str = Form(...)):
#     user = users.get(username)
#     if user and user["password"] == password:
#         session_token = create_session_token(user["user_id"])
#         redirect = RedirectResponse(url="/profile", status_code=302)
#         redirect.set_cookie(
#             key="session_token",
#             value=session_token,
#             httponly=True,
#             secure=False,  # In production: True
#             max_age=SESSION_MAX_AGE
#         )
#         return redirect
#     return FileResponse(os.path.join(BASE_DIR, "login.html"))
#
#
# @app.get("/profile")
# async def profile(request: Request, session_token: str = Cookie(None)):
#     if not session_token:
#         raise HTTPException(status_code=401, detail={"message": "Session expired"})
#
#     user_id, last_activity = verify_session_token(session_token)
#     now = int(time.time())
#
#     response = JSONResponse(content={"message": f"Welcome back! Your user ID is {user_id}"})
#
#     if SESSION_REFRESH_THRESHOLD <= now - last_activity < SESSION_MAX_AGE:
#         new_token = create_session_token(user_id)
#         response.set_cookie(
#             key="session_token",
#             value=new_token,
#             httponly=True,
#             secure=False,  # In production: True
#             max_age=SESSION_MAX_AGE
#         )
#
#     return response
#
#
# @app.get("/")
# async def root(request: Request):
#     username = request.cookies.get("username")
#     if not username:
#         return RedirectResponse(url="/login", status_code=302)
#
#     html_path = os.path.join(BASE_DIR, "mainPage.html")
#     return FileResponse(html_path)
#
#
#
#
# @app.post("/user")
# async def show_user(usr: User):
#     return {"name": usr.name,
#             "age": usr.age,
#             "is_adult": usr.age>=18}
#
# fake_db = []
#
# @app.post("/feedback")
# async def send_feedback(feedback: Feedback, is_premium: bool=False):
#     fake_db.append({"name": feedback.name, "comments": feedback.message})
#     if is_premium:
#         return f"Thank you, {feedback.name}! Your feedback will be our priority!"
#     return f"Feedback received. Thank you, {feedback.name}!"
#
# @app.get("/comments")
# async def show_feedback():
#     return fake_db
#
#
# @app.post("/items/")
# async def create_item(item: Item):
#     return item
#
#
# # Headers
# async def get_common_headers(
#     user_agent: Annotated[str, Header()],
#     accept_language: Annotated[str, Header()],
#     x_current_version: Annotated[str, Header()]
# ) -> CommonHeaders:
#     headers_dict = {
#         "user-agent": user_agent,
#         "accept-language": accept_language,
#         "x-current-version": x_current_version
#     }
#     return CommonHeaders(**headers_dict)
#
# @app.get("/headers")
# async def check_headers(headers: Annotated[CommonHeaders, Depends(get_common_headers)]):
#     return {
#         "User-Agent": headers.user_agent,
#         "Accept-Language": headers.accept_language,
#         "X-Current-Version": headers.x_current_version
#     }
#
# @app.get("/info")
# async def check_headers(headers: Annotated[CommonHeaders, Depends(get_common_headers)]):
#     server_time = datetime.now().isoformat()
#     return {
#         "headers": {
#             "User-Agent": headers.user_agent,
#             "Accept-Language": headers.accept_language,
#             "X-Current-Version": headers.x_current_version
#         },
#         "server_time": server_time,
#         "message": "Добро пожаловать! Ваши заголовки успешно обработаны."
#     }
#
#
#
# # Cookies
# from fastapi import Response
#
# @app.get("/set-cookie/")
# async def set_cookie(response: Response):
#     response.set_cookie(key="ads_id", value="ABC123", max_age=120, httponly=True)
#     return {"message": "Cookie set!"}
#
# @app.get("/items/")
# async def read_items(ads_id: str | None = Cookie(default=None)):
#     return {"ads_id": ads_id}
# Authentification


# def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
#     user = get_user_from_db(credentials.username)
#     if user is None or user.password != credentials.password:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#     return user

# @app.get("/protected_resource/")
# def get_protected_resource(user: User = Depends(authenticate_user)):
#     response = JSONResponse("You got my secret, welcome!")
#     return response
#     # return {"message": "You have access to the protected resource!", "user_info": user}
