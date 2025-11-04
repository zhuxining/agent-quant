from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.deps import current_active_user, fastapi_users
from src.models import UserRead, UserUpdate
from src.models.user import User
from src.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/users", tags=["users"])

# User management routes
router.include_router(
	fastapi_users.get_users_router(UserRead, UserUpdate),
)


@router.get("/me", response_model=ResponseEnvelope[dict])
async def authenticated_route(
	user: Annotated[User, Depends(current_active_user)],
):
	return success_response(
		data={
			"message": f"Hello {user.email}!",
			"user": UserRead.model_validate(user),
		},
		message="查询成功",
	)
