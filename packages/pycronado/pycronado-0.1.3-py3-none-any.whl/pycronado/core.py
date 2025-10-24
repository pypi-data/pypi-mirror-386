# pycronado/core.py

import asyncio
import json
import mimetypes
import os
import re
from asyncio import run
from typing import Any, AsyncIterator, Callable, Iterator, Optional

import tornado
import tornado.iostream

from . import token
from .util import getLogger


def requires(*param_names):
    """Decorator to enforce required parameters consistently."""

    def decorator(method):
        def wrapper(self, *args, **kwargs):
            for param_name in param_names:
                value = self.param(param_name)
                if value is None:
                    return self.jsonerr(f"`{param_name}` parameter is required", 400)
                # Store the param value in kwargs for the method to use
                kwargs[param_name] = value
            return method(self, *args, **kwargs)

        return wrapper

    return decorator


class NDJSONMixin:
    def expects_ndjson(self) -> bool:
        accept = (self.request.headers.get("Accept") or "").lower()
        return "application/x-ndjson" in accept

    def _ensure_ndjson_headers(self, status: int | None = None) -> None:
        if status is not None:
            self.set_status(status)
        self.set_header("Content-Type", "application/x-ndjson")
        self.set_header("Cache-Control", "no-cache, no-transform")
        self.set_header("Connection", "keep-alive")
        # Prevent proxy buffering (e.g., nginx) of streaming responses
        self.set_header("X-Accel-Buffering", "no")
        self.set_header("Vary", "Accept")
        try:
            self.clear_header("Content-Length")
        except Exception:
            pass

    @staticmethod
    def _encode_line(data: Any) -> str:
        return (
            data
            if isinstance(data, str)
            else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        ) + "\n"

    def ndjson_start(self, status: int | None = None) -> None:
        if getattr(self, "_ndjson_started", False):
            return
        self._ensure_ndjson_headers(status)
        try:
            self.flush()
        except Exception:
            # best-effort; continue either way
            pass
        self._ndjson_started = True

    def ndjson(self, data: Any, status: int | None = None) -> None:
        if not getattr(self, "_ndjson_started", False):
            self.ndjson_start(status=status)
        line = self._encode_line(data)
        self.write(line)
        try:
            self.flush()
        except Exception:
            # swallow transient client/transport errors during streaming
            pass

    def ndjson_end(self) -> None:
        try:
            if not getattr(self, "_finished", False):
                self.finish()
        except Exception:
            pass

    def ndjson_pump(
        self,
        it: Iterator[Any],
        status: int = 200,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> None:
        """Stream a synchronous iterator into the response."""
        self.ndjson_start(status)
        try:
            for item in it:
                self.ndjson(item)

        except tornado.iostream.StreamClosedError:
            return

        except GeneratorExit:
            try:
                self.ndjson({"type": "error", "message": "stream cancelled"})
            finally:
                self.ndjson_end()

        except Exception as e:
            try:
                payload = (
                    on_error(e)
                    if on_error
                    else {"type": "error", "message": "internal server error"}
                )
                self.ndjson(payload)
            finally:
                self.ndjson_end()

        finally:
            # Idempotent; safe even if already finished above.
            self.ndjson_end()

    # ------------------------------- Async API -------------------------------

    async def andjson_start(self, status: int | None = None) -> None:
        if getattr(self, "_ndjson_started", False):
            return
        self._ensure_ndjson_headers(status)
        try:
            await self.flush()
        except tornado.iostream.StreamClosedError:
            return
        except Exception:
            pass
        self._ndjson_started = True

    async def andjson(self, data: Any, status: int | None = None) -> None:
        if not getattr(self, "_ndjson_started", False):
            await self.andjson_start(status=status)
        line = self._encode_line(data)
        self.write(line)
        try:
            # backpressure-aware; yields IOLoop so other requests keep flowing
            await self.flush()
        except tornado.iostream.StreamClosedError:
            return
        except Exception:
            pass
        # brief cooperative yield for very chatty streams
        await asyncio.sleep(0)

    async def andjson_end(self) -> None:
        try:
            if not getattr(self, "_finished", False):
                self.finish()
        except Exception:
            pass

    async def andjson_pump(
        self,
        ait: AsyncIterator[Any],
        status: int = 200,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> None:
        """Stream an asynchronous iterator into the response."""
        await self.andjson_start(status)
        try:
            async for item in ait:
                await self.andjson(item)

        except asyncio.CancelledError:
            try:
                await self.andjson({"type": "error", "message": "stream cancelled"})
            finally:
                await self.andjson_end()

        except Exception as e:
            payload = (
                on_error(e)
                if on_error
                else {"type": "error", "message": "internal server error"}
            )
            try:
                await self.andjson(payload)
            finally:
                await self.andjson_end()

        finally:
            await self.andjson_end()


class PublicJSONHandler(tornado.web.RequestHandler):
    def prepare(self):
        self._logger = None
        self._data = None
        # NOTE: no NDJSON flags here; NDJSON state is confined to NDJSONMixin.
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    def logger(self):
        if self._logger is None:
            self._logger = getLogger(f"handler:{self.request.uri}")
        return self._logger

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def jwt(self):
        auth_header = self.request.headers.get("Authorization")
        if auth_header is not None:
            return re.sub("^Bearer +", "", auth_header)
        return None

    def param(self, param_name, default=None):
        if self._data is None:
            content_type = self.request.headers.get("Content-Type", "")
            if self.request.body and "application/json" in content_type:
                try:
                    parsed = json.loads(self.request.body)
                    self._data = parsed if isinstance(parsed, dict) else {}
                except json.JSONDecodeError:
                    self._data = {}
            else:
                self._data = {}
                json_data = self.get_body_argument("json", None)
                if json_data:
                    try:
                        self._data.update(json.loads(json_data))
                    except json.JSONDecodeError:
                        pass
        return self._data.get(param_name, self.get_argument(param_name, default))

    def file_param(self, param_name, default=None, max_filesize=20 * 1024 * 1024):
        files = self.request.files.get(param_name)
        if not files:
            return default

        file_info = files[0]

        if len(file_info["body"]) > max_filesize:
            return self.jsonerr(
                f"File too large. Maximum size is {max_filesize} bytes.", 413
            )

        return file_info["body"]

    def file(self, fpath, mimetype=None):
        assert os.path.exists(fpath), f"Path {fpath} does not exist"
        assert os.path.isfile(fpath), f"Path {fpath} is not a file"

        if mimetype is None:
            content_type, _encoding = mimetypes.guess_type(fpath)
            mimetype = content_type

        assert mimetype, f"Could not infer mimetype of {fpath} and no default provided"

        self.set_header("Content-Type", mimetype)
        self.set_header("Content-Length", os.path.getsize(fpath))

        with open(fpath, "rb") as f:
            while True:
                chunk = f.read(65 * 1024)
                if not chunk:
                    break
                self.write(chunk)
                self.flush()

        self.finish()

    def filebytes(self, data, mimetype=None, extension=None):
        assert isinstance(data, bytes), f"Data must be bytes, got {type(data)}"
        assert mimetype or extension, "Mimetype or extension is required for filebytes"

        if mimetype is None:
            mimetype = mimetypes.guess_type(f"foo.{extension}")

        self.set_header("Content-Type", mimetype)
        self.set_header("Content-Length", len(data))

        chunk_size = 65 * 1024
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            self.write(chunk)
            self.flush()

        self.finish()

    def jsonerr(self, message, status=500):
        self.json({"status": "error", "message": message}, status)
        self.finish()

    def json(self, data, status=None):
        if status is not None:
            self.set_status(status)
        return self.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    def options(self, *_args, **_kwargs):
        self.set_status(204)
        self.finish()

    def ok(self, **kwargs):
        return self.json({"status": "ok", **kwargs}, 200)

    def TODO(self, **kwargs):
        return self.json({"status": "TODO", **kwargs}, 501)


class UserMixin:
    def token(self):
        if not hasattr(self, "JWT"):
            self.JWT = self.decodedJwt()
        return self.JWT

    def issuer(self):
        return self.decodedJwt()["iss"]

    def user(self):
        jwt = self.decodedJwt()
        return jwt["user"]

    def username(self):
        return self.user()["username"]

    def userId(self):
        return f"{self.issuer()}::{self.username()}"


class JSONHandler(PublicJSONHandler, UserMixin):
    def prepare(self):
        super().prepare()

        if self.request.method == "OPTIONS":
            return

        if self.jwt() is None:
            self.json({"status": "error", "message": "forbidden"}, 403)
            self.finish()
            return
        try:
            token.decode(self.jwt())
        except Exception:
            self.json({"status": "error", "message": "forbidden"}, 403)
            self.finish()
            return

    def decodedJwt(self):
        return token.decode(self.jwt())


class Default404Handler(PublicJSONHandler):
    def prepare(self):
        self.json({"status": "error", "message": "not found"}, status=404)
        self.finish()
        return self.request.connection.close()


class HealthHandler(PublicJSONHandler):
    def get(self):
        val = self.param("value", None)
        res = {"status": "ok"}
        if val is not None:
            res["value"] = str(val)[0:256]
        return self.json(res)


async def start(
    name,
    port,
    routes,
    static_path=None,
    static_url_prefix=None,
    default_handler_class=None,
    debug=False,
):
    if default_handler_class is None:
        default_handler_class = Default404Handler
    app = tornado.web.Application(
        routes,
        default_handler_class=default_handler_class,
        debug=debug,
        static_path=static_path,
        static_url_prefix=static_url_prefix,
    )
    app.logger = getLogger(name)
    app.logger.info(f"  listening on {port}...")
    app.listen(int(port))
    await asyncio.Event().wait()
