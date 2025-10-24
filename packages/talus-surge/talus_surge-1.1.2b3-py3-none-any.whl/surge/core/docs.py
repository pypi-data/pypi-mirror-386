# -*- coding: utf-8 -*-
from fastapi import APIRouter
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html
)

# Prepare the OpenAPI URL.
PREFIX_STATIC: str = "/static"
URL_OPENAPI: str = "/v1/openapi.json"
URL_SWAGGER_OAUTH2_REDIRECT: str = "/docs/oauth2-redirect"
APP_TITLE: str = "Surge Monitor API"
# Prepare the router for docs.
router = APIRouter()


@router.get("/docs", include_in_schema=False)
async def core_custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=URL_OPENAPI,
        title = f"{APP_TITLE} - Swagger UI",
        swagger_js_url=f"{PREFIX_STATIC}/swagger-ui-bundle.js",
        swagger_css_url=f"{PREFIX_STATIC}/swagger-ui.css",
        swagger_favicon_url=f"{PREFIX_STATIC}/favicon.png",
    )


@router.get(URL_SWAGGER_OAUTH2_REDIRECT, include_in_schema=False)
async def core_swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@router.get("/redoc", include_in_schema=False)
async def core_redoc_html():
    return get_redoc_html(
        openapi_url=URL_OPENAPI,
        title=f"{APP_TITLE} - ReDoc",
        redoc_js_url=f"{PREFIX_STATIC}/redoc.standalone.js",
        redoc_favicon_url=f"{PREFIX_STATIC}/favicon.png",
    )
