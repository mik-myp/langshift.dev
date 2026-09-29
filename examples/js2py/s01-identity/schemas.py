from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class InputModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_default=True)


class LoginInput(InputModel):
    login: str = Field(min_length=1, max_length=80)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("login")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("login must not be blank")
        return value


class NewPassword(InputModel):
    password: SecretStr = Field(min_length=15, max_length=128)


class PasswordChange(InputModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=15, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    login: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
