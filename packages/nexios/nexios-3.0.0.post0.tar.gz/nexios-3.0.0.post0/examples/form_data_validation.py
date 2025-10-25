from pydantic import BaseModel, EmailStr, ValidationError

from nexios import NexiosApp

app = NexiosApp()


class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    age: int


@app.post("/register")
async def register_user(req, res):
    try:
        data = await req.json
        user = UserRegistration(**data)
        return res.json({"status": "success", "user": user.dict()})
    except ValidationError as e:
        return res.json({"error": str(e)}, status_code=422)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000, reload=True)
