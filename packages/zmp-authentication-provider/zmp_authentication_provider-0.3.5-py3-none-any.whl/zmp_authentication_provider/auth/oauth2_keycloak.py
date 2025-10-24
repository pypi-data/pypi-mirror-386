"""OAuth2 Keycloak module for the AIops Pilot."""

import logging

import jwt
import requests
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt import ExpiredSignatureError, InvalidIssuedAtError, InvalidKeyError, PyJWTError
from jwt.algorithms import RSAAlgorithm

from zmp_authentication_provider.exceptions import (
    AuthError,
    OauthTokenValidationException,
)
from zmp_authentication_provider.scheme.auth_model import TokenData
from zmp_authentication_provider.setting import auth_default_settings, keycloak_settings

log = logging.getLogger(__name__)

# KeyCloak Configuration using the settings
KEYCLOAK_SERVER_URL = keycloak_settings.server_url
KEYCLOAK_REALM = keycloak_settings.realm
KEYCLOAK_CLIENT_ID = keycloak_settings.client_id
KEYCLOAK_CLIENT_SECRET = keycloak_settings.client_secret
KEYCLOAK_REDIRECT_URI = keycloak_settings.redirect_uri
KEYCLOAK_SCOPE = keycloak_settings.scope
ALGORITHM = keycloak_settings.algorithm

HTTP_CLIENT_SSL_VERIFY = auth_default_settings.http_client_ssl_verify

# KeyCloak Endpoints
KEYCLOAK_REALM_ROOT_URL = (
    f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect"
)
KEYCLOAK_JWKS_ENDPOINT = f"{KEYCLOAK_REALM_ROOT_URL}/certs"
KEYCLOAK_AUTH_ENDPOINT = f"{KEYCLOAK_REALM_ROOT_URL}/auth"
KEYCLOAK_TOKEN_ENDPOINT = KEYCLOAK_REFRESH_ENDPOINT = f"{KEYCLOAK_REALM_ROOT_URL}/token"
KEYCLOAK_USER_ENDPOINT = f"{KEYCLOAK_REALM_ROOT_URL}/userinfo"
KEYCLOAK_END_SESSION_ENDPOINT = f"{KEYCLOAK_REALM_ROOT_URL}/logout"

# TODO: add the introspect_token endpoint from the idp server
# TODO: add the scopes for the token e.g. openid, profile, email


def get_public_key():
    """Get the public key."""
    response = requests.get(
        KEYCLOAK_JWKS_ENDPOINT, verify=HTTP_CLIENT_SSL_VERIFY
    )  # verify=False: because of the SKCC self-signed certificate
    jwks = response.json()

    public_key = None
    try:
        public_key = RSAAlgorithm.from_jwk(jwks["keys"][0])
    except InvalidKeyError as ike:
        log.error(f"InvalidKeyError: {ike}")

    return public_key


PUBLIC_KEY = get_public_key()
# oauth2_token_scheme = OAuth2PasswordBearer(tokenUrl=KEYCLOAK_TOKEN_ENDPOINT)

oauth2_auth_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=KEYCLOAK_AUTH_ENDPOINT,
    tokenUrl=KEYCLOAK_TOKEN_ENDPOINT,
    refreshUrl=KEYCLOAK_USER_ENDPOINT,
    # scopes={"openid": "openid", "profile": "profile", "email": "email"}
)


def verify_token(token: str) -> TokenData:
    """Verify the token."""
    log.debug(f"Verifying token: {token}")
    # NOTE: there are two options to verify the token
    # 1. jwt.decode
    # 2. introspect_token from the idp server
    # currently, we are using the jwt.decode with the verify_signature option
    try:
        payload = jwt.decode(
            jwt=token,
            key=PUBLIC_KEY,
            algorithms=[ALGORITHM],
            audience=KEYCLOAK_CLIENT_ID,
            # options={"verify_aud": False, "verify_iat": False},
            options={"verify_signature": False},
            leeway=60,
        )
        log.debug(f"Payload after decoding: {payload}")
        """
        PyJWT source code:
        if not options["verify_signature"]:
            options.setdefault("verify_exp", False)
            options.setdefault("verify_nbf", False)
            options.setdefault("verify_iat", False)
            options.setdefault("verify_aud", False)
            options.setdefault("verify_iss", False)
            options.setdefault("verify_sub", False)
            options.setdefault("verify_jti", False)
        """
        if payload is None:
            raise OauthTokenValidationException(
                AuthError.INVALID_TOKEN, details="jwt docode failed"
            )
        # NOTE: preferred_username is not always available from the idp server
        # if not available, use the email as the username
        username = payload.get("preferred_username")
        if not username:
            username = payload.get("email")
        token_data = TokenData(username=username, **payload)
    except ExpiredSignatureError as ese:
        log.error(f"ExpiredSignatureError: {ese}")
        raise OauthTokenValidationException(AuthError.EXPIRED_TOKEN, details=str(ese))
    except InvalidIssuedAtError as iiae:
        log.error(f"InvalidIssuedAtError: {iiae}")
        raise OauthTokenValidationException(AuthError.INVALID_TOKEN, details=str(iiae))
    except PyJWTError as jwte:
        log.error(f"JWTError: {jwte}")
        raise OauthTokenValidationException(AuthError.INVALID_TOKEN, details=str(jwte))

    return token_data


async def get_current_user(token: str = Depends(oauth2_auth_scheme)) -> TokenData:
    """Get the current user from the token."""
    return verify_token(token)
