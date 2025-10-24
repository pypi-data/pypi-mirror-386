"""sw.py."""

import os

try:
    from jose import jwt
except ModuleNotFoundError:
    pass


def get_sw_headers(add_proxy_jwt: bool = False) -> dict[str, str]:
    """Returns Stangreworks Headers."""
    retval = {}
    if add_proxy_jwt:
        resource_slug: str | None = os.getenv(
            "STRANGEWORKS_CONFIG__PROXY_JWT_RESOURCE_SLUG"
        )
        if not resource_slug:
            raise RuntimeError(
                "Cannot add proxy jwt without a resource slug. Set STRANGEWORKS_CONFIG__PROXY_JWT_RESOURCE_SLUG envvar to a valid resource slug"
            )
        workspace_member_slug: str | None = os.getenv(
            "STRANGEWORKS_CONFIG__PROXY_JWT_WM_SLUG"
        )
        if not resource_slug:
            raise RuntimeError(
                "Cannot add proxy jwt without a workspace member slug. Set STRANGEWORKS_CONFIG__PROXY_JWT_WM_SLUG envvar to a valid workspace member slug"
            )
        product_slug: str = (
            os.getenv("STRANGEWORKS_CONFIG__PROXY_JWT_PRODUCT_SLUG") or "ibm_qua"
        )
        if not product_slug:
            raise RuntimeError(
                "Cannot add proxy jwt without a product slug. Set STRANGEWORKS_CONFIG__PROXY_JWT_PRODUCT_SLUG envvar to a valid product slug"
            )
        message = {
            "ResourceSlug": resource_slug,
            "WorkspaceMemberSlug": workspace_member_slug,
            "ProductSlug": product_slug,
            "ResourceTokenID": "abcd-1234",
            "ResourceEntitlements": [],
            "iss": "strangeworks",
        }
        proxy_jwt = jwt.encode(message, key="dev-is-good")
        retval["x-strangeworks-access-token"] = proxy_jwt
    return retval
