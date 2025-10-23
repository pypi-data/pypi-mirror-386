"""
Oppman API routes for admin management functions
Provides web interface for oppman.py functionality
"""
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from fastapi_users.password import PasswordHelper
import hashlib
import hmac
import os
from datetime import datetime

# Simple authentication for base assets mode
from fastapi import HTTPException, status
from fastapi_users.password import PasswordHelper
from models import User
from db import AsyncSessionLocal
from sqlalchemy import text
from sqlmodel import SQLModel

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def get_current_superuser(request: Request):
    """Superuser authentication using unified auth system"""
    from core.services.auth import get_current_superuser_from_cookies
    return await get_current_superuser_from_cookies(request)


def get_settings():
    """Simple settings for base assets mode"""
    class SimpleSettings:
        def __init__(self):
            self.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
            self.emergency_access_enabled = os.getenv("EMERGENCY_ACCESS_ENABLED", "false").lower() in ("true", "1", "yes")
    
    return SimpleSettings()


def verify_emergency_secret_key(provided_key: str, expected_key: str) -> bool:
    """Verify emergency access by comparing SECRET_KEYs"""
    try:
        return hmac.compare_digest(provided_key, expected_key)
    except Exception:
        return False


def is_emergency_access_enabled() -> bool:
    """Check if emergency access is enabled via settings"""
    settings = get_settings()
    return settings.emergency_access_enabled


async def ensure_database_initialized() -> bool:
    """Ensure database is initialized, create tables if they don't exist"""
    try:
        # Check if users table exists
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                # Create all tables
                from db import async_engine
                async with async_engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
                return True
            return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


async def change_user_password(email: str, new_password: str) -> dict:
    """Change a user's password by email address"""
    async with AsyncSessionLocal() as session:
        try:
            # Find the user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return {"success": False, "message": f"User not found: {email}"}
            
            if not user.is_active:
                return {"success": False, "message": f"User is inactive: {email}"}
            
            # Hash the new password
            password_helper = PasswordHelper()
            hashed_password = password_helper.hash(new_password)
            
            # Update the user's password
            user.hashed_password = hashed_password
            await session.commit()
            
            return {"success": True, "message": f"Password changed successfully for user: {email}"}
            
        except Exception as e:
            await session.rollback()
            return {"success": False, "message": f"Error changing password: {str(e)}"}


async def list_all_users() -> List[dict]:
    """List all users for the admin interface"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "is_staff": user.is_staff,
                    "group": user.group
                })
            
            return user_list
            
        except Exception as e:
            return []


def run_oppman_command(command: str, args: List[str] = None) -> dict:
    """Run oppman command and return result"""
    try:
        cmd = ["uv", "run", "python", "oppman.py", command]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "command": f"uv run python oppman.py {command}"
        }


@router.get("/", response_class=HTMLResponse)
async def oppman_dashboard(request: Request, current_user: User = Depends(get_current_superuser)):
    """Main oppman admin dashboard"""
    users = await list_all_users()
    return templates.TemplateResponse("oppman.html", {
        "request": request,
        "users": users,
        "current_user": current_user
    })


@router.post("/change-password")
async def change_password_api(
    request: Request,
    email: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_superuser)
):
    """API endpoint to change user password"""
    if len(new_password) < 6:
        return JSONResponse({
            "success": False,
            "message": "Password must be at least 6 characters long"
        })
    
    result = await change_user_password(email, new_password)
    
    # Check if this is an HTMX request
    if 'hx-request' in request.headers:
        if result["success"]:
            return HTMLResponse(
                f'<div class="alert alert-success" role="alert">✅ {result["message"]}</div>'
            )
        else:
            return HTMLResponse(
                f'<div class="alert alert-error" role="alert">❌ {result["message"]}</div>'
            )
    else:
        return JSONResponse(result)


@router.get("/users")
async def get_users_api(current_user: User = Depends(get_current_superuser)):
    """API endpoint to get all users"""
    users = await list_all_users()
    return JSONResponse({"users": users})


@router.post("/migrate")
async def run_migration(
    request: Request,
    command: str = Form(...),
    message: str = Form(""),
    revision: str = Form(""),
    current_user: User = Depends(get_current_superuser)
):
    """API endpoint to run migration commands"""
    args = []
    
    if command == "create" and message:
        args.append(message)
    elif command in ["upgrade", "downgrade", "show", "stamp"] and revision:
        args.append(revision)
    
    result = run_oppman_command("migrate", [command] + args)
    
    # Check if this is an HTMX request
    if 'hx-request' in request.headers:
        if result["success"]:
            return HTMLResponse(
                f'<div class="alert alert-success" role="alert">✅ Migration {command} completed successfully</div>'
                f'<pre class="mt-2 p-2 bg-base-200 rounded"><code>{result["stdout"]}</code></pre>'
            )
        else:
            return HTMLResponse(
                f'<div class="alert alert-error" role="alert">❌ Migration {command} failed</div>'
                f'<pre class="mt-2 p-2 bg-base-200 rounded"><code>{result["stderr"]}</code></pre>'
            )
    else:
        return JSONResponse(result)




@router.post("/user-management")
async def run_user_management_command(
    request: Request,
    command: str = Form(...),
    current_user: User = Depends(get_current_superuser)
):
    """API endpoint to run user management commands"""
    if command not in ["check_users", "test_auth", "list_users"]:
        return JSONResponse({
            "success": False,
            "message": "Invalid user management command"
        })
    
    result = run_oppman_command(command)
    
    # Check if this is an HTMX request
    if 'hx-request' in request.headers:
        if result["success"]:
            return HTMLResponse(
                f'<div class="alert alert-success" role="alert">✅ User management {command} completed successfully</div>'
                f'<pre class="mt-2 p-2 bg-base-200 rounded"><code>{result["stdout"]}</code></pre>'
            )
        else:
            return HTMLResponse(
                f'<div class="alert alert-error" role="alert">❌ User management {command} failed</div>'
                f'<pre class="mt-2 p-2 bg-base-200 rounded"><code>{result["stderr"]}</code></pre>'
            )
    else:
        return JSONResponse(result)



# =========================
# EMERGENCY ACCESS ROUTES
# =========================

@router.get("/emergency", response_class=HTMLResponse)
async def emergency_access_page(request: Request):
    """Emergency access page for password recovery"""
    if not is_emergency_access_enabled():
        raise HTTPException(status_code=404, detail="Emergency access is disabled")
    
    return templates.TemplateResponse("emergency_access.html", {
        "request": request,
        "enabled": True
    })


@router.post("/emergency/verify")
async def verify_emergency_access(
    request: Request,
    token: str = Form(...)
):
    """Verify emergency access token and grant temporary access"""
    if not is_emergency_access_enabled():
        raise HTTPException(status_code=404, detail="Emergency access is disabled")
    
    settings = get_settings()
    if not verify_emergency_secret_key(token, settings.secret_key):
        return JSONResponse({
            "success": False,
            "message": "Invalid emergency access token"
        })
    
    # Set emergency session
    request.session["emergency_access"] = True
    request.session["emergency_granted_at"] = str(datetime.now().timestamp())
    
    return JSONResponse({
        "success": True,
        "message": "Emergency access granted. You can now access admin functions.",
        "redirect_url": "/oppman/"
    })


@router.get("/emergency/dashboard", response_class=HTMLResponse)
async def emergency_dashboard(request: Request):
    """Emergency dashboard with password reset functionality"""
    if not is_emergency_access_enabled():
        raise HTTPException(status_code=404, detail="Emergency access is disabled")
    
    # Check if emergency access is granted
    if not request.session.get("emergency_access"):
        return RedirectResponse(url="/oppman/emergency", status_code=302)
    
    # Get all users for password reset (handle case where database doesn't exist yet)
    try:
        users = await list_all_users()
    except Exception:
        # If database doesn't exist yet, return empty list
        users = []
    
    return templates.TemplateResponse("emergency_dashboard.html", {
        "request": request,
        "users": users,
        "is_emergency": True
    })


@router.post("/emergency/reset-password")
async def emergency_reset_password(
    request: Request,
    email: str = Form(...),
    new_password: str = Form(...)
):
    """Reset user password via emergency access"""
    if not is_emergency_access_enabled():
        raise HTTPException(status_code=404, detail="Emergency access is disabled")
    
    # Check if emergency access is granted
    if not request.session.get("emergency_access"):
        return JSONResponse({
            "success": False,
            "message": "Emergency access not granted"
        })
    
    if len(new_password) < 6:
        return JSONResponse({
            "success": False,
            "message": "Password must be at least 6 characters long"
        })
    
    result = await change_user_password(email, new_password)
    
    # Check if this is an HTMX request
    if 'hx-request' in request.headers:
        if result["success"]:
            return HTMLResponse(
                f'<div class="alert alert-success" role="alert">✅ {result["message"]}</div>'
            )
        else:
            return HTMLResponse(
                f'<div class="alert alert-error" role="alert">❌ {result["message"]}</div>'
            )
    else:
        return JSONResponse(result)


@router.post("/emergency/create-superuser")
async def emergency_create_superuser(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Create superuser via emergency access"""
    if not is_emergency_access_enabled():
        raise HTTPException(status_code=404, detail="Emergency access is disabled")
    
    # Check if emergency access is granted
    if not request.session.get("emergency_access"):
        return JSONResponse({
            "success": False,
            "message": "Emergency access not granted"
        })
    
    if len(password) < 6:
        return JSONResponse({
            "success": False,
            "message": "Password must be at least 6 characters long"
        })
    
    # Ensure database is initialized
    db_initialized = await ensure_database_initialized()
    if not db_initialized:
        return JSONResponse({
            "success": False,
            "message": "Failed to initialize database"
        })
    
    # Check if user already exists
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                return JSONResponse({
                    "success": False,
                    "message": f"User with email {email} already exists"
                })
            
            # Create new superuser
            password_helper = PasswordHelper()
            hashed_password = password_helper.hash(password)
            
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
                is_staff=True,
                group="admin"
            )
            
            session.add(new_user)
            await session.commit()
            
            return JSONResponse({
                "success": True,
                "message": f"Superuser created successfully: {email}"
            })
            
        except Exception as e:
            await session.rollback()
            return JSONResponse({
                "success": False,
                "message": f"Error creating superuser: {str(e)}"
            })


@router.post("/emergency/logout")
async def logout_emergency_access(request: Request):
    """Logout from emergency access and clear session"""
    if not is_emergency_access_enabled():
        raise HTTPException(status_code=404, detail="Emergency access is disabled")
    
    # Clear emergency session
    request.session.pop("emergency_access", None)
    request.session.pop("emergency_granted_at", None)
    
    return JSONResponse({
        "success": True,
        "message": "Emergency access logout successful. Session cleared."
    })
