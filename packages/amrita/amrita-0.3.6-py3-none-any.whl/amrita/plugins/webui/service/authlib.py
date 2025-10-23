from __future__ import annotations

import asyncio
import re
import secrets
from abc import ABC
from asyncio import Lock
from datetime import datetime, timedelta
from typing import TypeVar, overload

import bcrypt
from fastapi import HTTPException, Request
from nonebot import logger
from pydantic import BaseModel, Field
from typing_extensions import Self

from amrita.plugins.webui.service.config import get_webui_config

T = TypeVar("T")


def get_restful_auth_header(request: Request) -> str | None:
    if auth_header := request.headers.get("Authorization"):
        search = r"Bearer (.+)"
        result = re.search(search, auth_header)
        if not result:
            raise HTTPException(status_code=403, detail="未授权的访问")
        return result.group(1)


class NOT_GIVEN(ABC):
    @classmethod
    def __bool__(cls):
        return False


class TokenData(BaseModel):
    username: str
    expire: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=30)
    )
    onetime_token: str | None = None


class OnetimeTokenData(BaseModel):
    token: str
    expire: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=10)
    )


class TokenManager:
    _instance = None
    __tokens_lock: Lock
    __tokens: dict[str, TokenData]
    __onetime_token_index: dict[str, OnetimeTokenData]  # one time token->token

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.__tokens_lock = Lock()
            cls.__tokens = {}
            cls.__onetime_token_index = {}
        return cls._instance

    async def has_token(self, token: str) -> bool:
        async with self.__tokens_lock:
            return token in self.__tokens

    async def has_one_time_token(self, token: str) -> bool:
        async with self.__tokens_lock:
            if token in self.__onetime_token_index:
                auth: bool = False
                otk_data = self.__onetime_token_index[token]
                if not otk_data.expire < datetime.utcnow():
                    auth = True
                self.__onetime_token_index.pop(token, None)
                self.__tokens[otk_data.token].onetime_token = None
                return auth
            return False

    @overload
    async def get_token_data(self, token: str, /) -> TokenData: ...

    @overload
    async def get_token_data(self, token: str, default: T) -> TokenData | T: ...

    async def get_token_data(self, token: str, default: object = NOT_GIVEN):
        async with self.__tokens_lock:
            if default == NOT_GIVEN:
                return self.__tokens[token]
            else:
                return self.__tokens.get(token, default)

    @overload
    async def pop_token_data(self, token: str) -> TokenData: ...
    @overload
    async def pop_token_data(self, token: str, default: T) -> T | TokenData: ...

    async def pop_token_data(self, token: str, default: object = NOT_GIVEN):
        async with self.__tokens_lock:
            if default is not NOT_GIVEN:
                return self.__tokens.pop(token, default)
            else:
                return self.__tokens.pop(token)

    async def _expire_token_waiter(self, token: str, expire_at: datetime):
        await asyncio.sleep((expire_at - datetime.utcnow()).total_seconds())

        if data := await self.pop_token_data(token, None):
            async with self.__tokens_lock:
                if data.onetime_token:
                    self.__onetime_token_index.pop(data.onetime_token, None)

    async def _expire_onetime_token_waiter(self, token: str, expire_at: datetime):
        await asyncio.sleep((expire_at - datetime.utcnow()).total_seconds())
        if otk_data := self.__onetime_token_index.pop(token, None):
            self.__tokens[otk_data.token].onetime_token = None

    async def create_one_time_token(self, token_id: str) -> str:
        logger.debug(f"Creating one time token for '{token_id[:10]}...'")
        token = secrets.token_urlsafe(32)
        async with self.__tokens_lock:
            self.__tokens[token_id].onetime_token = token
            expire_at = datetime.utcnow() + timedelta(minutes=10)
            self.__onetime_token_index[token] = OnetimeTokenData(
                token=token_id, expire=expire_at
            )
            asyncio.create_task(self._expire_onetime_token_waiter(token, expire_at))  # noqa: RUF006
        return token

    async def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ):
        logger.debug(f"Creating access token for {data}")
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        encoded_jwt = secrets.token_urlsafe(32)

        async with self.__tokens_lock:
            self.__tokens[encoded_jwt] = TokenData(
                username=to_encode["sub"], expire=expire
            )
            asyncio.create_task(self._expire_token_waiter(encoded_jwt, expire))  # noqa: RUF006
        return encoded_jwt

    async def refresh_token(self, token: str) -> str:
        async with self.__tokens_lock:
            data_cache = self.__tokens[token]
            if onetime_token := data_cache.onetime_token:
                self.__onetime_token_index.pop(onetime_token, None)
            self.__tokens.pop(token, None)
        access_token_expires = timedelta(minutes=30)
        access_token = await self.create_access_token(
            data={"sub": data_cache.username}, expires_delta=access_token_expires
        )
        return access_token


class AuthManager:
    _instance = None
    _token_manager: TokenManager
    __users: dict[str, str]

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._token_manager = TokenManager()
            cls.__users = {
                get_webui_config().webui_user_name: cls._hash_password(
                    password=get_webui_config().webui_password
                )
            }
        return cls._instance

    async def check_otk_request(self, header: str):
        if not await self._token_manager.has_one_time_token(header):
            raise HTTPException(status_code=403, detail="访问不合法")

    async def check_current_user(self, request: Request):
        if otk := get_restful_auth_header(request):
            return await self.check_otk_request(otk)
        token = request.cookies.get("access_token")
        token_manager = self._token_manager
        if not token or (not await token_manager.has_token(token)):
            raise HTTPException(status_code=401, detail="未认证")
        token_data = await token_manager.get_token_data(token)
        if token_data.expire < datetime.utcnow():
            await token_manager.pop_token_data(token, None)
            raise HTTPException(status_code=401, detail="认证已过期")

    @staticmethod
    def _hash_password(*, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def authenticate_user(self, username: str, password: str) -> bool:
        if username in self.__users:
            return self._verify_password(password, self.__users[username])
        return False

    async def create_token(self, username: str, expire: timedelta) -> str:
        token = await self._token_manager.create_access_token(
            data={"sub": username}, expires_delta=expire
        )
        return token

    async def user_log_out(self, token: str):
        await self._token_manager.pop_token_data(token)

    async def refresh_token(self, request: Request):
        await self.check_current_user(request)
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="未认证")
        return await self._token_manager.refresh_token(token)
