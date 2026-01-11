from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, status

from . import config
from .api_utils.api_schema import (
    AgentRequest,
    AgentResponse,
    Governance,
    GovernanceResponse,
)
from .api_utils.constants import (
    TOKEN_EXPIRATION_HOURS,
    email_to_user,
    user_permission,
    users,
    users_passwords,
)
from .supervisor_agent import run_agent

app = FastAPI()
active_tokens = {}


@app.post("/auth", response_model=GovernanceResponse)
def generate_token(user: Governance):
    if user.username not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User doest not exist"
        )

    username = (
        user.username if "@" not in user.username else email_to_user[user.username]
    )

    password = user.password

    if password != users_passwords[username]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password"
        )

    token = str(uuid4())

    active_tokens[token] = {
        "username": username,
        "expires_at": datetime.now() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
        "permissions": user_permission[username],
    }

    return GovernanceResponse(token=token)


def validate_token(auth: Optional[str] = Header(None)):
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    token = auth.replace("Bearer ", "")

    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    token_data = active_tokens[token]

    if datetime.now() > token_data["expires_at"]:
        del active_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )

    return token_data["username"]


@app.post("/prompt", response_model=AgentResponse)
async def get_answer(request: AgentRequest, user: str = Depends(validate_token)):
    prompt = request.prompt
    answer = await run_agent(prompt)
    return AgentResponse(content=answer, data=None)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
