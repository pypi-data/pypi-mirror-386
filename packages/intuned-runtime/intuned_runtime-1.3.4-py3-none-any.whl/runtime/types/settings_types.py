from typing import List
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class CaptchaSettings(BaseModel):
    enabled: bool = Field(default=False)


class CaptchaSolverSolveSettings(BaseModel):
    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
    auto_solve: bool = Field(default=True, alias="autoSolve")
    solve_delay: int = Field(default=2000, alias="solveDelay")
    max_retries: int = Field(default=3, alias="maxRetries")
    timeout: int = Field(default=30000)


class CustomCaptchaSettings(CaptchaSettings):
    model_config = {
        "serialize_by_alias": True,
    }

    image_locators: List[str] = Field(alias="imageLocators", default=[])
    submit_locators: List[str] = Field(alias="submitLocators", default=[])
    input_locators: List[str] = Field(alias="inputLocators", default=[])


class TextCaptchaSettings(CaptchaSettings):
    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
    label_locators: List[str] = Field(alias="labelLocators", default=[])
    submit_locators: List[str] = Field(alias="submitLocators", default=[])
    input_locators: List[str] = Field(alias="inputLocators", default=[])


class CaptchaSolverSettings(BaseModel):
    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }

    enabled: bool = Field(default=False)
    cloudflare: CaptchaSettings = Field(default_factory=CaptchaSettings)
    google_recaptcha_v2: CaptchaSettings = Field(alias="googleRecaptchaV2", default_factory=CaptchaSettings)
    google_recaptcha_v3: CaptchaSettings = Field(alias="googleRecaptchaV3", default_factory=CaptchaSettings)
    awscaptcha: CaptchaSettings = Field(default_factory=CaptchaSettings)
    hcaptcha: CaptchaSettings = Field(default_factory=CaptchaSettings)
    funcaptcha: CaptchaSettings = Field(default_factory=CaptchaSettings)
    geetest: CaptchaSettings = Field(default_factory=CaptchaSettings)
    lemin: CaptchaSettings = Field(default_factory=CaptchaSettings)
    custom_captcha: CustomCaptchaSettings = Field(alias="customCaptcha", default_factory=CustomCaptchaSettings)
    text: TextCaptchaSettings = Field(default_factory=TextCaptchaSettings)
    settings: CaptchaSolverSolveSettings = Field(default_factory=CaptchaSolverSolveSettings)


class IntunedJsonDisabledAuthSessions(BaseModel):
    enabled: Literal[False]


class IntunedJsonEnabledAuthSessions(BaseModel):
    enabled: Literal[True]
    type: Literal["API", "MANUAL"]
    start_url: str | None = Field(default=None, alias="startUrl")
    finish_url: str | None = Field(default=None, alias="finishUrl")


class IntunedJson(BaseModel):
    model_config = {"populate_by_name": True}

    auth_sessions: IntunedJsonDisabledAuthSessions | IntunedJsonEnabledAuthSessions = Field(alias="authSessions")
    project_name: str | None = Field(alias="projectName", default=None)
    workspace_id: str | None = Field(alias="workspaceId", default=None)
    captcha_solver: CaptchaSolverSettings | None = Field(alias="captchaSolver", default=None)
