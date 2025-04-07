import fastapi

from fastapi.openapi.docs import get_swagger_ui_html

router = fastapi.APIRouter()


@router.get("/docs", include_in_schema=False)
async def swagger_ui_html(request: fastapi.Request):
    return get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=request.app.title + " - Swagger UI",
        oauth2_redirect_url=request.app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )
