"""Bound the request stream before the multipart parser spools it to disk."""
from fastapi import HTTPException, Request
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException

from app.core.config import get_settings


class DocumentRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def handler(request: Request):
            if request.method != "POST":
                return await original_handler(request)
            # Small allowance for multipart boundaries and text fields.
            maximum = get_settings().max_upload_size_bytes + 64 * 1024
            length = request.headers.get("content-length")
            if length is not None:
                try:
                    declared = int(length)
                    if declared < 0:
                        raise ValueError
                except ValueError:
                    raise HTTPException(400, "Invalid Content-Length") from None
                if declared > maximum:
                    raise HTTPException(413, "Request exceeds upload size limit")
            received = 0
            exceeded = False

            async def receive():
                nonlocal received, exceeded
                message = await request.receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > maximum:
                        exceeded = True
                        # Starlette closes temporary upload files on this exception.
                        raise MultiPartException("Request exceeds upload size limit")
                return message

            try:
                return await original_handler(Request(request.scope, receive=receive))
            except StarletteHTTPException:
                if exceeded:
                    raise HTTPException(413, "Request exceeds upload size limit") from None
                raise

        return handler
