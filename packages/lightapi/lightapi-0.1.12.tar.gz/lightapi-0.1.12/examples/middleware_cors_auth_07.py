from sqlalchemy import Column, String

from lightapi.auth import JWTAuthentication
from lightapi.cache import RedisCache
from lightapi.core import AuthenticationMiddleware, CORSMiddleware, Middleware, Response
from lightapi.models import Base
from lightapi.filters import ParameterFilter
from lightapi.lightapi import LightApi
from lightapi.pagination import Paginator
from lightapi.rest import RestEndpoint, Validator


class CustomEndpointValidator(Validator):
    def validate_name(self, value):
        return value

    def validate_email(self, value):
        return value

    def validate_website(self, value):
        return value


class Company(Base, RestEndpoint):
    __table_args__ = {"extend_existing": True}
    name = Column(String)
    email = Column(String, unique=True)
    website = Column(String)

    class Configuration:
        http_method_names = ["GET", "POST", "OPTIONS"]
        validator_class = CustomEndpointValidator
        filter_class = ParameterFilter

    async def post(self, request):
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok", "data": await request.get_data()}, status_code=200)

    def get(self, request):
        return {"data": "ok"}, 200

    def headers(self, request):
        # Headers in starlette are typically immutable during request processing
        # This method demonstrates header handling but shouldn't modify request headers
        # Instead, headers should be modified in the response
        return request


class CustomPaginator(Paginator):
    limit = 100
    sort = True


class CustomEndpoint(Base, RestEndpoint):
    class Configuration:
        # Remove the http_method_names restriction to get full CRUD automatically
        # http_method_names = ['GET', 'POST', 'OPTIONS']  # This was limiting the methods!
        # OR specify all CRUD methods explicitly:
        http_method_names = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        authentication_class = JWTAuthentication
        caching_class = RedisCache
        caching_method_names = ["GET"]
        pagination_class = CustomPaginator

    def get(self, request):
        """Retrieve resource(s)."""
        return {"data": "ok", "message": "GET request successful"}, 200

    async def post(self, request):
        """Create a new resource."""
        return {
            "data": "ok",
            "message": "POST request successful",
            "body": await request.get_data(),
        }, 200

    async def put(self, request):
        """Update an existing resource (full update)."""
        return {
            "data": "updated",
            "message": "PUT request successful",
            "body": await request.get_data(),
        }, 200

    async def patch(self, request):
        """Partially update an existing resource."""
        return {
            "data": "patched",
            "message": "PATCH request successful",
            "body": await request.get_data(),
        }, 200

    def delete(self, request):
        """Delete a resource."""
        return {"data": "deleted", "message": "DELETE request successful"}, 200

    async def options(self, request):
        """Return allowed HTTP methods."""
        return {
            "allowed_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "message": "OPTIONS request successful",
        }, 200


def create_app():
    app = LightApi()
    app.register(Company)
    app.register(CustomEndpoint)
    # Use built-in middleware classes
    app.add_middleware([CORSMiddleware, AuthenticationMiddleware])
    return app


if __name__ == "__main__":
    create_app().run()
