import asyncio
import os
import json

import msgspec
import pytest

from django_bolt import BoltAPI, JSON, StreamingResponse
from django_bolt.param_functions import Query, Path, Header, Cookie, Depends, Form, File as FileParam
from django_bolt.responses import PlainText, HTML, Redirect, File, FileResponse
from django_bolt.exceptions import HTTPException
from django_bolt.testing import TestClient
from typing import Annotated


@pytest.fixture(scope="module")
def api():
    """Create the test API with all routes"""
    api = BoltAPI()

    class Item(msgspec.Struct):
        name: str
        price: float
        is_offer: bool | None = None

    @api.get("/")
    async def root():
        return {"ok": True}

    @api.get("/items/{item_id}")
    async def get_item(item_id: int, q: str | None = None):
        return {"item_id": item_id, "q": q}

    @api.get("/types")
    async def get_types(b: bool | None = None, f: float | None = None):
        return {"b": b, "f": f}

    @api.put("/items/{item_id}")
    async def put_item(item_id: int, item: Item):
        return {"item_id": item_id, "item_name": item.name, "is_offer": item.is_offer}

    @api.get("/str")
    async def ret_str():
        return "hello"

    @api.get("/bytes")
    async def ret_bytes():
        return b"abc"

    @api.get("/json")
    async def ret_json():
        return JSON({"x": 1}, status_code=201, headers={"X-Test": "1"})

    @api.get("/req/{x}")
    async def req_only(req):
        return {"p": req["params"].get("x"), "q": req["query"].get("y")}

    @api.post("/m")
    async def post_m():
        return {"m": "post"}

    @api.patch("/m")
    async def patch_m():
        return {"m": "patch"}

    @api.delete("/m")
    async def delete_m():
        return {"m": "delete"}

    @api.head("/m")
    async def head_m():
        return {"m": "head"}

    # Test HEAD with query params (should work like GET)
    @api.head("/items/{item_id}")
    async def head_item(item_id: int, q: str | None = None):
        return {"item_id": item_id, "q": q}

    # Response coercion from objects to msgspec.Struct
    class Mini(msgspec.Struct):
        id: int
        username: str

    class Model:
        def __init__(self, id: int, username: str | None):
            self.id = id
            self.username = username

    @api.get("/coerce/mini", response_model=list[Mini])
    async def coerce_mini() -> list[Mini]:
        return [Model(1, "a"), Model(2, "b")]

    @api.get("/coerce/mini-bad", response_model=list[Mini])
    async def coerce_mini_bad() -> list[Mini]:
        return [Model(1, None)]

    @api.get("/ok-list", response_model=list[Item])
    async def ok_list():
        return [
            {"name": "a", "price": 1.0, "is_offer": True},
            {"name": "b", "price": 2.0, "is_offer": False},
        ]

    @api.get("/bad-list", response_model=list[Item])
    async def bad_list():
        return [{"name": "x", "is_offer": True}]

    @api.get("/anno-list")
    async def anno_list() -> list[Item]:
        return [Item(name="c", price=3.0, is_offer=None)]

    @api.get("/anno-bad")
    async def anno_bad() -> list[Item]:
        return [{"name": "d"}]

    @api.get("/both-override", response_model=list[Item])
    async def both_override() -> list[str]:
        return [{"name": "o", "price": 1.0, "is_offer": False}]

    @api.get("/no-validate")
    async def no_validate():
        return [{"anything": 1, "extra": "ok"}]

    @api.get("/status-default", status_code=201)
    async def status_default():
        return {"ok": True}

    @api.get("/headers-cookies")
    async def headers_cookies(agent: str = Depends(lambda user_agent: user_agent)):
        return {"ok": True}

    @api.get("/header")
    async def get_header(x: Annotated[str, Header(alias="x-test")]):
        return PlainText(x)

    @api.get("/cookie")
    async def get_cookie(val: Annotated[str, Cookie(alias="session")]):
        return PlainText(val)

    @api.get("/exc")
    async def raise_exc():
        raise HTTPException(418, {"detail": "teapot"}, headers={"X-Err": "1"})

    @api.get("/html")
    async def get_html():
        return HTML("<h1>Hi</h1>")

    @api.get("/redirect")
    async def get_redirect():
        return Redirect("/", status_code=302)

    THIS_FILE = os.path.abspath(__file__)

    @api.get("/file")
    async def get_file():
        return File(THIS_FILE, filename="test_syntax.py")

    @api.get("/fileresponse")
    async def get_fileresponse():
        return FileResponse(THIS_FILE, filename="test_syntax.py")

    @api.get("/stream-plain")
    async def stream_plain():
        def gen():
            for i in range(3):
                yield f"p{i},"
        return StreamingResponse(gen, media_type="text/plain")

    @api.get("/stream-bytes")
    async def stream_bytes():
        def gen():
            for i in range(2):
                yield str(i).encode()
        return StreamingResponse(gen)

    @api.get("/sse")
    async def stream_sse():
        def gen():
            yield "event: message\ndata: hello\n\n"
            yield "data: 1\n\n"
            yield ": comment\n\n"
        return StreamingResponse(gen, media_type="text/event-stream")

    @api.get("/stream-async")
    async def stream_async():
        async def async_gen():
            for i in range(3):
                await asyncio.sleep(0.001)
                yield f"async-{i},".encode()
        return StreamingResponse(async_gen(), media_type="text/plain")

    @api.get("/stream-async-sse")
    async def stream_async_sse():
        async def async_gen():
            yield "event: start\ndata: beginning\n\n"
            await asyncio.sleep(0.001)
            yield "event: message\ndata: async data\n\n"
            await asyncio.sleep(0.001)
            yield "event: end\ndata: finished\n\n"
        return StreamingResponse(async_gen(), media_type="text/event-stream")

    @api.get("/stream-async-large")
    async def stream_async_large():
        async def async_gen():
            for i in range(10):
                await asyncio.sleep(0.001)
                chunk = f"chunk-{i:02d}-{'x' * 100}\n".encode()
                yield chunk
        return StreamingResponse(async_gen(), media_type="application/octet-stream")

    @api.get("/stream-async-mixed-types")
    async def stream_async_mixed_types():
        async def async_gen():
            yield b"bytes-chunk\n"
            await asyncio.sleep(0.001)
            yield "string-chunk\n"
            await asyncio.sleep(0.001)
            yield bytearray(b"bytearray-chunk\n")
            await asyncio.sleep(0.001)
            yield memoryview(b"memoryview-chunk\n")
        return StreamingResponse(async_gen(), media_type="text/plain")

    @api.get("/stream-async-error")
    async def stream_async_error():
        async def async_gen():
            yield b"chunk1\n"
            await asyncio.sleep(0.001)
            yield b"chunk2\n"
            await asyncio.sleep(0.001)
            raise ValueError("Simulated async error")
        return StreamingResponse(async_gen(), media_type="text/plain")

    @api.post("/form-urlencoded")
    async def form_urlencoded(a: Annotated[str, Form()], b: Annotated[int, Form()]):
        return {"a": a, "b": b}

    @api.post("/upload")
    async def upload(files: Annotated[list[dict], FileParam(alias="file")]):
        return {"count": len(files), "names": [f.get("filename") for f in files]}

    @api.get("/sse-async-test")
    async def sse_async_test():
        async def agen():
            for i in range(3):
                yield f"data: {i}\n\n"
                await asyncio.sleep(0)
        return StreamingResponse(agen(), media_type="text/event-stream")

    @api.post("/v1/chat/completions-async-test")
    async def chat_completions_async_test(payload: dict):
        if payload.get("stream", True):
            async def agen():
                for i in range(payload.get("n_chunks", 2)):
                    data = {"chunk": i, "content": " hello"}
                    yield f"data: {json.dumps(data)}\n\n"
                    await asyncio.sleep(0)
                yield "data: [DONE]\n\n"
            return StreamingResponse(agen(), media_type="text/event-stream")
        return {"non_streaming": True}

    return api


@pytest.fixture(scope="module")
def client(api):
    """Create TestClient for the API"""
    with TestClient(api) as client:
        yield client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_path_and_query_binding(client):
    response = client.get("/items/42?q=hello")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": "hello"}


def test_bool_and_float_binding(client):
    response = client.get("/types?b=true&f=1.25")
    assert response.status_code == 200
    assert response.json() == {"b": True, "f": 1.25}


def test_body_decoding(client):
    response = client.put("/items/5", json={"name": "x", "price": 1.5, "is_offer": True})
    assert response.status_code == 200
    assert response.json() == {"item_id": 5, "item_name": "x", "is_offer": True}


def test_response_types(client):
    # str
    response = client.get("/str")
    assert response.status_code == 200
    assert response.content == b"hello"
    assert response.headers.get("content-type", "").startswith("text/plain")
    # bytes
    response = client.get("/bytes")
    assert response.status_code == 200
    assert response.content == b"abc"
    assert response.headers.get("content-type", "").startswith("application/octet-stream")


def test_json_response_status_and_headers(client):
    response = client.get("/json")
    assert response.status_code == 201
    assert response.headers.get("x-test") == "1"
    assert response.json() == {"x": 1}


def test_request_only_handler(client):
    response = client.get("/req/9?y=z")
    assert response.status_code == 200
    assert response.json() == {"p": "9", "q": "z"}


def test_methods(client):
    response = client.post("/m")
    assert response.status_code == 200 and response.json() == {"m": "post"}
    response = client.patch("/m")
    assert response.status_code == 200 and response.json() == {"m": "patch"}
    response = client.delete("/m")
    assert response.status_code == 200 and response.json() == {"m": "delete"}


def test_response_model_validation_ok(client):
    response = client.get("/ok-list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0]["name"] == "a" and data[0]["price"] == 1.0


def test_response_model_validation_error(client):
    response = client.get("/bad-list")
    # We currently surface server error (500) on validation problems
    assert response.status_code == 500
    assert b"Response validation error" in response.content


def test_return_annotation_validation_ok(client):
    response = client.get("/anno-list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and data[0]["name"] == "c"


def test_return_annotation_validation_error(client):
    response = client.get("/anno-bad")
    assert response.status_code == 500
    assert b"Response validation error" in response.content


def test_response_coercion_from_objects(client):
    response = client.get("/coerce/mini")
    assert response.status_code == 200
    data = response.json()
    assert data == [{"id": 1, "username": "a"}, {"id": 2, "username": "b"}]


def test_response_coercion_error_from_objects(client):
    response = client.get("/coerce/mini-bad")
    assert response.status_code == 500
    assert b"Response validation error" in response.content


def test_response_model_overrides_return_annotation(client):
    response = client.get("/both-override")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and data[0]["name"] == "o"


def test_no_validation_without_types(client):
    response = client.get("/no-validate")
    assert response.status_code == 200
    data = response.json()
    # Should return as-is since neither annotation nor response_model provided
    assert data == [{"anything": 1, "extra": "ok"}]


def test_status_code_default(client):
    response = client.get("/status-default")
    assert response.status_code == 201


def test_header_and_cookie(client):
    response = client.get("/header", headers={"x-test": "val"})
    assert response.status_code == 200 and response.content == b"val"
    # set cookie via header
    response = client.get("/cookie", cookies={"session": "abc"})
    assert response.status_code == 200 and response.content == b"abc"


def test_http_exception(client):
    response = client.get("/exc")
    assert response.status_code == 418
    assert response.headers.get("x-err") == "1"


def test_response_helpers(client):
    response = client.get("/html")
    assert response.status_code == 200 and response.headers.get("content-type", "").startswith("text/html")
    response = client.get("/redirect", follow_redirects=False)
    assert response.status_code == 302 and response.headers.get("location") == "/"
    response = client.get("/file")
    assert response.status_code == 200 and response.headers.get("content-type", "").startswith("text/")
    # FileResponse should also succeed and set content-disposition
    response = client.get("/fileresponse")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/")
    assert "attachment;" in (response.headers.get("content-disposition", "").lower())


def test_streaming_plain(client):
    response = client.get("/stream-plain")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/plain")
    assert response.content == b"p0,p1,p2,"


def test_streaming_bytes_default_content_type(client):
    response = client.get("/stream-bytes")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/octet-stream")
    assert response.content == b"01"


def test_streaming_sse_headers(client):
    response = client.get("/sse")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/event-stream")
    # SSE-friendly headers are set by the server
    # Note: Connection header may be managed by the HTTP server automatically
    assert response.headers.get("x-accel-buffering", "").lower() == "no"
    # Body should contain multiple well-formed SSE lines
    text = response.content.decode()
    assert "event: message" in text
    assert "data: hello" in text
    assert "data: 1" in text
    assert ": comment" in text


def test_streaming_async_large(client):
    """Test async streaming with larger payloads."""
    response = client.get("/stream-async-large")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/octet-stream")

    # Should have 10 chunks
    lines = response.content.decode().strip().split('\n')
    assert len(lines) == 10

    # Check format of chunks
    for i, line in enumerate(lines):
        expected_prefix = f"chunk-{i:02d}-"
        assert line.startswith(expected_prefix)
        assert len(line) >= 109  # ~109 bytes per line (110 bytes per chunk with \n)
        assert line.endswith('x' * 100)


def test_streaming_async_mixed_types(client):
    """Test async streaming with different data types."""
    response = client.get("/stream-async-mixed-types")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/plain")

    # Check all data types are properly converted
    text = response.content.decode()
    expected_chunks = [
        "bytes-chunk\n",
        "string-chunk\n",
        "bytearray-chunk\n",
        "memoryview-chunk\n"
    ]

    for expected in expected_chunks:
        assert expected in text


def test_streaming_async_vs_sync_compatibility(client):
    """Test that async and sync streaming produce the same results for equivalent data."""

    # Get sync streaming result
    sync_response = client.get("/stream-plain")

    # Get async streaming result
    async_response = client.get("/stream-async")

    # Both should succeed
    assert sync_response.status_code == 200
    assert async_response.status_code == 200

    # Both should be text/plain
    assert sync_response.headers.get("content-type", "").startswith("text/plain")
    assert async_response.headers.get("content-type", "").startswith("text/plain")

    # Content should be similar format (both have 3 items)
    sync_text = sync_response.content.decode()
    async_text = async_response.content.decode()

    # Both should have 3 comma-separated items
    assert len(sync_text.split(',')) == 4  # "p0,p1,p2," = 4 parts
    assert len(async_text.split(',')) == 4  # "async-0,async-1,async-2," = 4 parts


def test_async_bridge_endpoints_work(client):
    """Test that async SSE streaming works correctly."""

    # Test the async SSE endpoint - this should expose the real bug
    response = client.get("/sse-async-test")
    assert response.status_code == 200, f"Async SSE endpoint failed with status {response.status_code}"
    assert len(response.content) > 0, f"Async SSE endpoint returned empty body, got {len(response.content)} bytes"
    # Check that we actually get SSE formatted data
    text = response.content.decode()
    assert "data: 0" in text, f"Expected SSE data not found in response: {text[:100]}"
    assert "data: 1" in text, f"Expected SSE data not found in response: {text[:100]}"


def test_form_and_file(client):
    response = client.post("/form-urlencoded", data={"a": "x", "b": "3"})
    assert response.status_code == 200 and response.json() == {"a": "x", "b": 3}

    # Test multipart file upload
    response = client.post(
        "/upload",
        data={"note": "hi"},
        files=[
            ("file", ("a.txt", b"abc", "application/octet-stream")),
            ("file", ("b.txt", b"def", "application/octet-stream"))
        ]
    )
    data = response.json()
    assert response.status_code == 200 and data["count"] == 2 and set(data["names"]) == {"a.txt", "b.txt"}


def test_head_method(client):
    """Test HEAD method works correctly"""
    response = client.head("/m")
    assert response.status_code == 200
    # HEAD should return headers but empty body
    assert len(response.content) == 0 


def test_head_with_params(client):
    """Test HEAD method with path and query params"""
    response = client.head("/items/42?q=test")
    assert response.status_code == 200


def test_options_method_automatic(client):
    """Test automatic OPTIONS handling - returns Allow header with available methods"""
    response = client.options("/m")
    assert response.status_code == 200
    # Check Allow header is present and contains the methods
    assert "allow" in response.headers or "Allow" in response.headers
    allow_header = response.headers.get("allow") or response.headers.get("Allow")
    assert allow_header is not None
    # Should include all methods registered for /m (POST, PATCH, DELETE, HEAD)
    methods = [m.strip() for m in allow_header.split(",")]
    assert "POST" in methods
    assert "PATCH" in methods
    assert "DELETE" in methods
    assert "HEAD" in methods
    assert "OPTIONS" in methods  # Always included for automatic OPTIONS
    # Body should be empty JSON object
    assert response.json() == {}


def test_options_on_nonexistent_route(client):
    """Test OPTIONS on non-existent route returns 404"""
    response = client.options("/does-not-exist")
    assert response.status_code == 404


def test_explicit_options_handler():
    """Test that explicit OPTIONS handler overrides automatic behavior"""
    from django_bolt import Response

    api = BoltAPI()

    @api.get("/custom-options")
    async def get_custom():
        return {"result": "data"}

    @api.options("/custom-options")
    async def options_custom():
        return Response(
            {"custom": "options", "info": "This is a custom OPTIONS handler"},
            headers={"Allow": "GET, OPTIONS", "X-Custom": "header"}
        )

    from django_bolt.testing import TestClient
    with TestClient(api) as client:
        response = client.options("/custom-options")
        assert response.status_code == 200
        data = response.json()
        assert data["custom"] == "options"
        assert data["info"] == "This is a custom OPTIONS handler"
        # Check custom headers
        assert "allow" in response.headers or "Allow" in response.headers
        assert "x-custom" in response.headers or "X-Custom" in response.headers


def test_method_validation():
    """Test that HEAD and OPTIONS don't accept body parameters"""
    api = BoltAPI()

    class Body(msgspec.Struct):
        value: str

    # HEAD should not accept body
    with pytest.raises(TypeError, match="HEAD.*cannot have body parameters"):
        @api.head("/test-head")
        async def head_with_body(body: Body):
            return {"ok": True}

    # OPTIONS should not accept body
    with pytest.raises(TypeError, match="OPTIONS.*cannot have body parameters"):
        @api.options("/test-options")
        async def options_with_body(body: Body):
            return {"ok": True}
