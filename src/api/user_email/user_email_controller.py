from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from src.core.dependencies import get_user_email_service
from src.schema.request.user_email import UserEmailRequest, UserEmailUpdateRequest
from src.schema.response.user_email import UserEmailResponse
from src.service.user_email import UserEmailService

NO_CONTENT = 204

router = APIRouter(prefix="/user-email", tags=["User Emails"])
@cbv(router)
class UserEmailController:

    service: UserEmailService = Depends(get_user_email_service)


    @router.post("/create", response_model=UserEmailResponse)
    def create_user_email(self, request: UserEmailRequest) -> UserEmailResponse:
        return self.service.create_user_email(request)

    @router.put("/update", response_model=UserEmailResponse)
    def update_user_email(self, request: UserEmailUpdateRequest) -> UserEmailResponse:
        return self.service.update_user_email(request)

    @router.get("/all", response_model=list[UserEmailResponse])
    def find_user_emails(self) -> list[UserEmailResponse]:
        return self.service.find_user_emails()

    @router.delete("/delete/{user_email_id}", status_code=NO_CONTENT)
    def delete_user_email(self, user_email_id: int) -> None:
        self.service.delete_user_email(user_email_id)
