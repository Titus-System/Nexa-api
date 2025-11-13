from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from pydantic import BaseModel, EmailStr, ValidationError
from app.services.user_service import UserService
from app.core.logger_config import logger


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_name: str = "USER"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResource(Resource):
    def __init__(self):
        self.user_service = UserService()
        self.logger = logger

    def post(self):
        try:
            body = RegisterRequest(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400

        try:
            user = self.user_service.create(
                name=body.name,
                email=body.email,
                password=body.password,
                role_name=body.role_name
            )
            return {
                "message": "User created successfully",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            }, 201
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            self.logger.exception(f"Error creating user: {e}")
            return {"error": "Internal server error"}, 500


class LoginResource(Resource):
    def __init__(self):
        self.user_service = UserService()
        self.logger = logger

    def post(self):
        try:
            body = LoginRequest(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400

        user = self.user_service.get_by_email(body.email)
        if not user:
            return {"error": "Invalid email or password"}, 401

        if not self.user_service.verify_password(user, body.password):
            return {"error": "Invalid email or password"}, 401

        access_token = create_access_token(identity=str(user.id))
        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }, 200

