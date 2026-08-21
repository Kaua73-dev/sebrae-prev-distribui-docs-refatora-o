from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from src.core.dependencies import get_current_user, get_user_service, require_admin
from src.model.user import User
from src.schema.request.user import LoginRequest, RegisterRequest
from src.schema.response.user import TokenResponse, UserResponse
from src.service.user import UserService

CREATED = 201

router = APIRouter(prefix="/auth", tags=["Auth"])
@cbv(router)
class UserController:

    service: UserService = Depends(get_user_service)


    @router.post("/login", response_model=TokenResponse)
    def login(self, request: LoginRequest) -> TokenResponse:
        return self.service.login(request)

    # require_admin ja engloba get_current_user: sem token nao passa, e com token de
    # ROLE USER passa pela autenticacao mas para na autorizacao.
    @router.post("/register", response_model=UserResponse, status_code=CREATED)
    def register(self, request: RegisterRequest, _: User = Depends(require_admin)) -> UserResponse:
        return self.service.register(request)

    @router.get("/me", response_model=UserResponse)
    def me(self, current_user: User = Depends(get_current_user)) -> UserResponse:
        return UserResponse.model_validate(current_user)
