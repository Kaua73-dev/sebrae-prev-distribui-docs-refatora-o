from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from core.dependencies import get_user_email_service
from schema.request.user_email import UserEmailRequest, UserEmailUpdateRequest
from schema.response.user_email import UserEmailResponse
from src.service.user_email.user_email_service import UserEmailService

router = APIRouter(tags=['user_email'])
@cbv(router)
class UserEmailController:


    service: UserEmailService = Depends(get_user_email_service())



    @router.post("/create", response_model=UserEmailResponse)
    def create_user_email(self, request: UserEmailRequest) -> UserEmailResponse:
        return self.service.create_user_email(request)


    @router.get("/all", response_model=list[UserEmailResponse])
    def get_all_user_emails(self) -> list[UserEmailResponse]:
        return self.service.find_user_emails()

    @router.patch("/update", response_model=UserEmailResponse)
    def update_user_email(self, request: UserEmailUpdateRequest, user_email_id: int) -> UserEmailResponse:
        return self.service.update_user_email(request)


    @router.delete("/delete", response_model=UserEmailResponse)
    def delete_user_email(self, user_email_id: int, request: UserEmailRequest) -> UserEmailResponse:
        return self.delete_user_email(user_email_id, request)