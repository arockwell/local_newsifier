"""Authentication router for admin access."""

import os
import pathlib

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from local_newsifier.config.settings import settings

router = APIRouter(
    tags=["auth"],
)

# Get templates directory path - works in both development and production
if os.path.exists("src/local_newsifier/api/templates"):
    # Development environment
    templates_dir = "src/local_newsifier/api/templates"
else:
    # Production environment - use package-relative path
    templates_dir = str(pathlib.Path(__file__).parent.parent / "templates")

templates = Jinja2Templates(directory=templates_dir)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page.

    Args:
        request: FastAPI request

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
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/system/tables"),  # Default redirect
):
    """Process login form submission.

    Args:
        request: FastAPI request
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
