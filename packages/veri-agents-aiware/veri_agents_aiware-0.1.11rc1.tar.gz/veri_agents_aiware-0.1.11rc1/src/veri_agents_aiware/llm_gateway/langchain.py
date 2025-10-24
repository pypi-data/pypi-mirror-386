import os
from typing import Dict, Optional, Any, cast
from langchain_openai import ChatOpenAI
from pydantic import Field, model_validator
from pydantic.types import SecretStr
from langchain_core.utils.utils import secret_from_env


class AiwareGatewayLLM(ChatOpenAI):
    use_responses_api: Optional[bool] = False
    llm_gateway_api: str = Field(  # pyright: ignore[reportAssignmentType]
        default=None
    )

    llm_gateway_key: SecretStr = Field(  # pyright: ignore[reportAssignmentType]
        default=None
    )
    aiware_session: Optional[SecretStr] = Field(
        default_factory=secret_from_env("AIWARE_SESSION", default=None)
    )
    aiware_api_key: Optional[SecretStr] = Field(
        default_factory=secret_from_env("AIWARE_API_KEY", default=None)
    )

    @model_validator(mode="before")
    @classmethod
    def transform_input(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        data["aiware_session"] = cast(
            SecretStr | None,
            data.get("aiware_session") or secret_from_env("AIWARE_SESSION", default=None)(),
        )
        if aiware_session := data.get("aiware_session"):
            default_headers = data.get("default_headers", {})
            default_headers["x-aiware-session"] = aiware_session.get_secret_value()
            data["default_headers"] = default_headers

        data["aiware_api_key"] = cast(
            SecretStr | None,
            data.get("aiware_api_key") or secret_from_env("AIWARE_API_KEY", default=None)(),
        )
        if aiware_api_key := data.get("aiware_api_key"):
            default_headers = data.get("default_headers", {})
            default_headers["x-aiware-api-token"] = aiware_api_key.get_secret_value()
            data["default_headers"] = default_headers

        data["llm_gateway_api"] = (
            data.get("openai_api_base")
            or data.get("llm_gateway_api")
            or os.environ.get("LLM_GATEWAY_API")
            or "https://llm-gateway.aisglabs1.aiware.run"
        )
        data["openai_api_base"] = data["llm_gateway_api"]

        data["llm_gateway_key"] = data.get("llm_gateway_key") or secret_from_env("LLM_GATEWAY_KEY", default=None)()
        data["api_key"] = data["llm_gateway_key"]

        data["model"] = cast(
            str | None,
            data.get("model") or os.environ.get("LLM_GATEWAY_MODEL"),
        )

        return data
