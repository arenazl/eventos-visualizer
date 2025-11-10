"""
Endpoints de autenticación con Google OAuth2
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from datetime import datetime, timedelta
from typing import Optional
import logging

from database.connection import get_db
from models.users import User
from utils.config import settings
from utils.auth_utils import create_access_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Configurar OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/google/login")
async def google_login(request: Request):
    """
    Inicia el flujo de autenticación con Google
    Redirige al usuario a la página de login de Google
    """
    # Construir redirect_uri explícitamente
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Callback de Google OAuth
    Procesa la respuesta de Google y crea/actualiza el usuario
    """
    try:
        # Obtener token de Google
        token = await oauth.google.authorize_access_token(request)

        # Obtener información del usuario
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo obtener información del usuario de Google"
            )

        # Buscar o crear usuario
        user = db.query(User).filter(User.google_id == user_info['sub']).first()

        if not user:
            # Crear nuevo usuario
            user = User(
                email=user_info['email'],
                name=user_info.get('name', user_info['email']),
                avatar_url=user_info.get('picture'),
                google_id=user_info['sub'],
                google_access_token=token['access_token'],
                google_refresh_token=token.get('refresh_token'),
                last_login=datetime.utcnow()
            )
            db.add(user)
            logger.info(f"🆕 Nuevo usuario creado: {user.email}")
        else:
            # Actualizar usuario existente
            user.google_access_token = token['access_token']
            if token.get('refresh_token'):
                user.google_refresh_token = token['refresh_token']
            user.last_login = datetime.utcnow()
            user.avatar_url = user_info.get('picture', user.avatar_url)
            logger.info(f"🔄 Usuario actualizado: {user.email}")

        db.commit()
        db.refresh(user)

        # Crear JWT token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email}
        )

        # Redirigir al frontend con el token
        redirect_url = f"{settings.frontend_url}/auth/callback?token={access_token}"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"❌ Error en callback de Google: {str(e)}")
        return RedirectResponse(url=f"{settings.frontend_url}/auth/error?message={str(e)}")

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Obtiene la información del usuario autenticado
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "location": {
            "latitude": float(current_user.latitude) if current_user.latitude else None,
            "longitude": float(current_user.longitude) if current_user.longitude else None,
            "city": current_user.city,
            "country": current_user.country,
            "radius_km": current_user.radius_km
        },
        "preferences": {
            "timezone": current_user.timezone,
            "locale": current_user.locale,
            "push_enabled": current_user.push_enabled,
            "favorite_categories": current_user.favorite_categories,
            "notification_preferences": current_user.notification_preferences
        },
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Cierra la sesión del usuario
    En un sistema JWT, el logout es manejado por el cliente eliminando el token
    """
    logger.info(f"👋 Usuario cerró sesión: {current_user.email}")
    return {"message": "Sesión cerrada exitosamente"}

@router.put("/profile")
async def update_profile(
    name: Optional[str] = None,
    city: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[int] = None,
    favorite_categories: Optional[list] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el perfil del usuario
    """
    if name:
        current_user.name = name
    if city:
        current_user.city = city
    if latitude is not None:
        current_user.latitude = latitude
    if longitude is not None:
        current_user.longitude = longitude
    if radius_km is not None:
        current_user.radius_km = radius_km
    if favorite_categories is not None:
        current_user.favorite_categories = favorite_categories

    current_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    logger.info(f"✏️ Perfil actualizado: {current_user.email}")

    return {"message": "Perfil actualizado exitosamente", "user": current_user}

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina la cuenta del usuario
    """
    email = current_user.email
    db.delete(current_user)
    db.commit()

    logger.warning(f"🗑️ Cuenta eliminada: {email}")

    return {"message": "Cuenta eliminada exitosamente"}
