from datetime import timedelta, datetime
from typing import Dict
import jwt


class JWTHandler:
    def __init__(
        self,
        redis_cli,
        secret_key,
        reset_secret,
        access_exp: int = 60,
        refresh_exp: int = 3600,
        algorithm: str = "HS256",
    ):
        self.redis = redis_cli
        self.secret_key = secret_key
        self.reset_secret = reset_secret
        self.algorithm = algorithm
        self.access_exp = access_exp
        self.refresh_exp = refresh_exp

    def create_jwt_token(self, data: dict, expires_delta: timedelta) -> str:
        """Creates a JWT Token with `data` and `expire_delta`"""
        data = data.copy()
        expire = datetime.now() + expires_delta
        data.update({"exp": expire})
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def get_data(self, token: str) -> Dict:
        """Decode JWT token and return payload or error"""
        try:
            data = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {"data": data, "error": None}
        except jwt.exceptions.ExpiredSignatureError:
            return {"data": None, "error": "EXPIRED"}
        except jwt.exceptions.InvalidTokenError:
            return {"data": None, "error": "INVALID"}

    async def create_reset_password_token(self, data: dict, expires_delta: timedelta) -> str:
        """Create reset token and store in Redis with TTL"""
        data = data.copy()
        expire = datetime.now() + expires_delta
        data.update({"exp": expire})
        encoded_jwt = jwt.encode(data, self.reset_secret, algorithm=self.algorithm)

        await self.redis.setex(
            f"reset_token:{encoded_jwt}",
            int(expires_delta.total_seconds()),
            "valid",
        )
        return encoded_jwt

    async def get_reset_password_data(self, token: str) -> Dict | None:
        """Validate reset token against Redis + decode"""
        if not await self.redis.get(f"reset_token:{token}"):
            return None
        try:
            return jwt.decode(token, self.reset_secret, algorithms=[self.algorithm])
        except jwt.exceptions.ExpiredSignatureError:
            return None
        except jwt.exceptions.InvalidTokenError:
            return None

    async def invalidate_reset_token(self, token: str):
        await self.redis.delete(f"reset_token:{token}")

    def create_access_token(self, data: Dict) -> str:
        return self.create_jwt_token(data, timedelta(minutes=self.access_exp))

    async def create_refresh_token(self, data: Dict) -> str:
        refresh_token: str = self.create_jwt_token(data, timedelta(minutes=self.refresh_exp))
        await self.redis.sadd("refresh_tokens", refresh_token)
        return refresh_token

    async def invalidate_refresh_token(self, refresh_token: str) -> None:
        if refresh_token in await self.redis.smembers("refresh_tokens"):
            await self.redis.srem("refresh_tokens", refresh_token)

    async def check_refresh_token(self, refresh_token: str) -> Dict | None:
        members = await self.redis.smembers("refresh_tokens")
        if refresh_token in members:
            token_data = self.get_data(refresh_token)  # sync decode
            return token_data.get("data")
        return None

    async def generate_tokens(self, data: Dict) -> Dict:
        access_token: str = self.create_access_token(data)
        refresh_token: str = await self.create_refresh_token(data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
