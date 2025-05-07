"""Authentication router for admin access."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from local_newsifier.api.dependencies import get_templates
from local_newsifier.config.settings import settings

router = APIRouter(
    tags=["auth"],
)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)]
):
    """Render the login page.

    Args:
        request: FastAPI request
        templates: Jinja2 templates

    Returns:
        HTML response with login form
    """
    next_url = request.query_params.get("next", "/system/tables")
    return templates.TemplateResponse(
        "login.html", {"request": request, "title": "Admin Login", "next_url": next_url}
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/system/tables"),  # Default redirect
):
    """Process login form submission.

    Args:
        request: FastAPI request
        templates: Jinja2 templates
        username: Submitted username
        password: Submitted password
        next_url: URL to redirect to after successful login

    Returns:
        Redirect to next_url on success or login page with error on failure
    """
    # Verify against environment variables
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url=next_url, status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Admin Login",
            "error": "Invalid credentials",
            "next_url": next_url,
        },
    )


@router.get("/logout")
async def logout(request: Request):
    """Log out the current user by clearing the session.

    Args:
        request: FastAPI request

    Returns:
        Redirect to home page
    """
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
