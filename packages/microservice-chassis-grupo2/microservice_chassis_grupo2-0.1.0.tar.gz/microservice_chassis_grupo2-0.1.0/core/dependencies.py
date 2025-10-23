import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security import decode_token

logger = logging.getLogger(__name__)
auth_scheme = HTTPBearer()

# Database #########################################################################################
async def get_db():
    """Generates database sessions and closes them when finished."""
    from sql.database import SessionLocal
    logger.debug("Getting database SessionLocal")
    db = SessionLocal()
    try:
        yield db
        await db.commit()
    except:
        await db.rollback()
    finally:
        await db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    """
    Decodifica el JWT y obtiene el usuario actual desde la base de datos.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token) 
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    return user_id