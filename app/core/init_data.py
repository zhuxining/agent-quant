import contextlib
from decimal import Decimal

from fastapi_users.exceptions import UserAlreadyExists
from loguru import logger
from sqlalchemy import true
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.deps import get_db_session, get_user_db_session, get_user_manager
from app.models import TradeAccount, TradeAccountCreate, TradeAccountRead, UserCreate

get_db_session_context = contextlib.asynccontextmanager(get_db_session)
get_user_db_session_context = contextlib.asynccontextmanager(get_user_db_session)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, is_superuser: bool = False):
	try:
		async with (
			get_db_session_context() as session,
			get_user_db_session_context(session) as user_db,
			get_user_manager_context(user_db) as user_manager,
		):
			user = await user_manager.create(
				UserCreate(email=email, password=password, is_superuser=is_superuser)
			)
			logger.success(f"User created {user}")
			return user
	except UserAlreadyExists:
		logger.warning(f"User {email} already exists")
		pass


async def create_trade_account() -> TradeAccountRead:
	async with get_db_session_context() as session:
		result = await session.execute(select(TradeAccount).where(TradeAccount.is_active == true()))
		existing_account = result.scalars().first()
		if existing_account:
			logger.info("Active trade account already exists.")
			return TradeAccountRead.model_validate(existing_account)
		new_account_data = TradeAccountCreate(
			name="Primary Account",
			account_number="ACC123456",
			balance=Decimal("100000.00"),
			buying_power=Decimal("100000.00"),
			realized_pnl=Decimal("0.00"),
			is_active=True,
			description="Initial trade account",
		)
		new_account = TradeAccount(**new_account_data.model_dump())
		session.add(new_account)
		try:
			await session.commit()
			await session.refresh(new_account)
			logger.success(f"Trade account created: {new_account}")
			return TradeAccountRead.model_validate(new_account)
		except IntegrityError as e:
			await session.rollback()
			logger.error(f"Failed to create trade account: {e}")
			raise
