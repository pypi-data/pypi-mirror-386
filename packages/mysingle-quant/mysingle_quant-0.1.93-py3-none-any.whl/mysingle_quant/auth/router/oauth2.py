from fastapi import APIRouter, Query, Request, Response
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback

from mysingle_quant.auth.schemas.auth import LoginResponse

from ...core.config import settings
from ..authenticate import SecretType, authenticator
from ..exceptions import AuthenticationFailed
from ..oauth2.clients import get_oauth2_client
from ..schemas import OAuth2AuthorizeResponse, UserResponse
from ..security.jwt import get_jwt_manager
from ..user_manager import UserManager

user_manager = UserManager()
jwt_manager = get_jwt_manager()


def get_oauth2_router() -> APIRouter:
    """Generate a router with the OAuth routes to associate an authenticated user."""

    router = APIRouter()

    def get_oauth2_authorize_callback(provider: str) -> OAuth2AuthorizeCallback:
        oauth_client = get_oauth2_client(provider_name=provider)
        return OAuth2AuthorizeCallback(oauth_client)

    def generate_state_token(data: dict[str, str], secret: SecretType) -> str:
        data["aud"] = "users:oauth-state"
        # OAuth state 토큰 생성 (특수 payload)
        import jwt

        return jwt.encode(data, secret, algorithm="HS256")

    @router.get(
        "/{provider}/authorize",
        response_model=OAuth2AuthorizeResponse,
    )
    async def authorize(
        provider: str,
        redirect_url: str | None = None,
        state: str | None = Query(None),
    ) -> OAuth2AuthorizeResponse:
        """
        Initiate the OAuth2 authorization process for associating an OAuth account
        with the currently authenticated user.
        """
        oauth_client = get_oauth2_client(provider_name=provider)

        if redirect_url is not None:
            authorize_redirect_url = redirect_url
        else:
            authorize_redirect_url = (
                f"{settings.FRONTEND_URL}/api/oauth2/{provider}/callback"
            )

        # state_data: dict[str, str] = {}
        # state = generate_state_token(state_data, settings.SECRET_KEY)

        authorization_url = await oauth_client.get_authorization_url(
            redirect_uri=authorize_redirect_url,
            # state=state,
        )

        return OAuth2AuthorizeResponse(authorization_url=authorization_url)

    @router.get(
        "/{provider}/callback",
        response_model=LoginResponse,
        description="The response varies based on the authentication backend used.",
    )
    async def callback(
        response: Response,
        request: Request,
        provider: str,
        code: str = Query(...),
    ) -> LoginResponse:
        oauth_client = get_oauth2_client(provider_name=provider)
        token, state = await get_oauth2_authorize_callback(provider)(request)

        account_id, account_email = await oauth_client.get_id_email(
            token["access_token"]
        )

        if account_email is None:
            raise AuthenticationFailed("OAuth provider did not provide email")
        # if not state:
        #     raise AuthenticationFailed("Missing OAuth state token")
        # try:
        #     decode_jwt(state, settings.SECRET_KEY, ["users:oauth-state"])
        # except DecodeError:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        user = await user_manager.oauth_callback(
            oauth_client.name,
            token["access_token"],
            account_id,
            account_email,
            token.get("expires_at"),
            token.get("refresh_token"),
            request,
        )
        user_response = UserResponse.model_validate(user, from_attributes=True)
        token_data = authenticator.login(user=user, response=response)

        if settings.TOKEN_TRANSPORT_TYPE in ["bearer", "hybrid"]:
            # Bearer 또는 Hybrid 방식: 응답에 토큰 포함
            return LoginResponse(
                access_token=token_data["access_token"] if token_data else "",
                refresh_token=token_data["refresh_token"] if token_data else "",
                token_type="bearer",
                user_info=user_response,
            )
        else:
            # Cookie 방식: 토큰은 쿠키에만 설정, 응답에는 사용자 정보만
            return LoginResponse(
                user_info=user_response,
            )

    return router
