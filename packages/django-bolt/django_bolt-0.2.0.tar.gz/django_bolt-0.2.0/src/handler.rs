use actix_web::http::header::{HeaderName, HeaderValue};
use actix_web::{http::StatusCode, web, HttpRequest, HttpResponse};
use ahash::AHashMap;
use bytes::Bytes;
use futures_util::stream;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyTuple};
use std::sync::Arc;
use tokio::fs::File;
use tokio::io::AsyncReadExt;

use crate::direct_stream;
use crate::error;
use crate::metadata::CorsConfig;
use crate::middleware;
use crate::middleware::auth::{authenticate, populate_auth_context};
use crate::permissions::{evaluate_guards, GuardResult};
use crate::request::PyRequest;
use crate::router::parse_query_string;
use crate::state::{AppState, GLOBAL_ROUTER, ROUTE_METADATA, TASK_LOCALS};
use crate::streaming::create_python_stream;

// Reuse the global Python asyncio event loop created at server startup (TASK_LOCALS)

/// Add CORS headers to response using Rust-native config (NO GIL required)
/// This replaces the Python-based CORS header addition
fn add_cors_headers_rust(
    response: &mut HttpResponse,
    request_origin: Option<&str>,
    cors_config: &CorsConfig,
    global_origins: &[String],
) {
    // Merge route-specific origins with global origins
    let origins = if !cors_config.origins.is_empty() {
        &cors_config.origins
    } else if !global_origins.is_empty() {
        global_origins
    } else {
        // No CORS configured
        return;
    };

    // SECURITY: Validate wildcard + credentials
    let is_wildcard = origins.iter().any(|o| o == "*");
    if is_wildcard && cors_config.credentials {
        // Invalid configuration - skip adding headers
        return;
    }

    // Determine origin to use
    let origin_to_use = if is_wildcard {
        "*"
    } else if let Some(req_origin) = request_origin {
        // Check if request origin is allowed
        if origins.iter().any(|o| o == req_origin) {
            req_origin
        } else {
            return; // Origin not allowed
        }
    } else {
        origins.first().map(|s| s.as_str()).unwrap_or("*")
    };

    // Add Access-Control-Allow-Origin
    if let Ok(val) = HeaderValue::from_str(origin_to_use) {
        response
            .headers_mut()
            .insert(actix_web::http::header::ACCESS_CONTROL_ALLOW_ORIGIN, val);
    }

    // Add Vary: Origin when not using wildcard
    if origin_to_use != "*" {
        response.headers_mut().insert(
            actix_web::http::header::VARY,
            HeaderValue::from_static("Origin"),
        );
    }

    // Add credentials header if enabled
    if cors_config.credentials {
        response.headers_mut().insert(
            actix_web::http::header::ACCESS_CONTROL_ALLOW_CREDENTIALS,
            HeaderValue::from_static("true"),
        );
    }

    // Add exposed headers if specified (uses pre-computed string - zero allocations)
    if !cors_config.expose_headers.is_empty() {
        if let Ok(val) = HeaderValue::from_str(&cors_config.expose_headers_str) {
            response
                .headers_mut()
                .insert(actix_web::http::header::ACCESS_CONTROL_EXPOSE_HEADERS, val);
        }
    }
}

/// Add CORS preflight headers for OPTIONS requests (uses pre-computed strings - zero allocations)
fn add_cors_preflight_headers(response: &mut HttpResponse, cors_config: &CorsConfig) {
    // Use pre-computed methods_str - no allocation!
    if let Ok(val) = HeaderValue::from_str(&cors_config.methods_str) {
        response
            .headers_mut()
            .insert(actix_web::http::header::ACCESS_CONTROL_ALLOW_METHODS, val);
    }

    // Use pre-computed headers_str - no allocation!
    if let Ok(val) = HeaderValue::from_str(&cors_config.headers_str) {
        response
            .headers_mut()
            .insert(actix_web::http::header::ACCESS_CONTROL_ALLOW_HEADERS, val);
    }

    // Use pre-computed max_age_str - no allocation!
    if let Ok(val) = HeaderValue::from_str(&cors_config.max_age_str) {
        response
            .headers_mut()
            .insert(actix_web::http::header::ACCESS_CONTROL_MAX_AGE, val);
    }
}

pub async fn handle_request(
    req: HttpRequest,
    body: web::Bytes,
    state: web::Data<Arc<AppState>>,
) -> HttpResponse {
    let method = req.method().as_str().to_string();
    let path = req.path().to_string();

    // Clone path and method for error handling
    let path_clone = path.clone();
    let method_clone = method.clone();

    let router = GLOBAL_ROUTER.get().expect("Router not initialized");

    // Find the route for the requested method and path
    let (route_handler, path_params, handler_id) = {
        if let Some((route, path_params, handler_id)) = router.find(&method, &path) {
            (
                Python::attach(|py| route.handler.clone_ref(py)),
                path_params,
                handler_id,
            )
        } else {
            // No explicit handler found - check for automatic OPTIONS
            if method == "OPTIONS" {
                let available_methods = router.find_all_methods(&path);
                if !available_methods.is_empty() {
                    let allow_header = available_methods.join(", ");
                    let mut response = HttpResponse::NoContent()
                        .insert_header(("Allow", allow_header))
                        .insert_header(("Content-Type", "application/json"))
                        .finish();

                    // Try to find a GET route at this path to get CORS metadata
                    if let Some((_, _, get_handler_id)) = router.find("GET", &path) {
                        // Get route metadata for CORS config - clone once to release lock immediately
                        let route_meta = ROUTE_METADATA
                            .get()
                            .and_then(|meta_map| meta_map.get(&get_handler_id).cloned());

                        // Add CORS headers if configured
                        if let Some(ref meta) = route_meta {
                            if let Some(ref cors_cfg) = meta.cors_config {
                                // Direct header lookup - no HashMap allocation
                                let origin =
                                    req.headers().get("origin").and_then(|v| v.to_str().ok());
                                add_cors_headers_rust(
                                    &mut response,
                                    origin,
                                    cors_cfg,
                                    &state.cors_allowed_origins,
                                );
                                // Add preflight-specific headers for OPTIONS
                                add_cors_preflight_headers(&mut response, cors_cfg);
                            }
                        }
                    }

                    return response;
                }
            }

            return HttpResponse::NotFound()
                .content_type("text/plain; charset=utf-8")
                .body("Not Found");
        }
    };

    let query_params = if let Some(q) = req.uri().query() {
        parse_query_string(q)
    } else {
        AHashMap::new()
    };

    // Extract headers early for middleware processing - pre-allocate with typical size
    let mut headers: AHashMap<String, String> = AHashMap::with_capacity(16);

    // SECURITY: Use limits from AppState (configured once at startup)
    const MAX_HEADERS: usize = 100;
    let max_header_size = state.max_header_size;
    let mut header_count = 0;

    for (name, value) in req.headers().iter() {
        // Check header count limit
        header_count += 1;
        if header_count > MAX_HEADERS {
            return HttpResponse::BadRequest()
                .content_type("text/plain; charset=utf-8")
                .body("Too many headers");
        }

        if let Ok(v) = value.to_str() {
            // SECURITY: Validate header value size
            if v.len() > max_header_size {
                return HttpResponse::BadRequest()
                    .content_type("text/plain; charset=utf-8")
                    .body(format!(
                        "Header value too large (max {} bytes)",
                        max_header_size
                    ));
            }

            headers.insert(name.as_str().to_ascii_lowercase(), v.to_string());
        }
    }

    // Get peer address for rate limiting fallback
    let peer_addr = req.peer_addr().map(|addr| addr.ip().to_string());

    // Get parsed route metadata (Rust-native) - clone to release DashMap lock immediately
    // This trade-off: small clone cost < lock contention across concurrent requests
    let route_metadata = ROUTE_METADATA
        .get()
        .and_then(|meta_map| meta_map.get(&handler_id).cloned());

    // Compute skip flags (e.g., skip compression)
    let skip_compression = route_metadata
        .as_ref()
        .map(|m| m.skip.contains("compression"))
        .unwrap_or(false);

    // Process rate limiting (Rust-native, no GIL)
    if let Some(ref route_meta) = route_metadata {
        if let Some(ref rate_config) = route_meta.rate_limit_config {
            if let Some(response) = middleware::rate_limit::check_rate_limit(
                handler_id,
                &headers,
                peer_addr.as_deref(),
                rate_config,
            ) {
                return response;
            }
        }
    }

    // Execute authentication and guards (new system)
    let auth_ctx = if let Some(ref route_meta) = route_metadata {
        if !route_meta.auth_backends.is_empty() {
            authenticate(&headers, &route_meta.auth_backends)
        } else {
            None
        }
    } else {
        None
    };

    // Evaluate guards
    if let Some(ref route_meta) = route_metadata {
        if !route_meta.guards.is_empty() {
            match evaluate_guards(&route_meta.guards, auth_ctx.as_ref()) {
                GuardResult::Allow => {
                    // Pass through
                }
                GuardResult::Unauthorized => {
                    return HttpResponse::Unauthorized()
                        .content_type("application/json")
                        .body(r#"{"detail":"Authentication required"}"#);
                }
                GuardResult::Forbidden => {
                    return HttpResponse::Forbidden()
                        .content_type("application/json")
                        .body(r#"{"detail":"Permission denied"}"#);
                }
            }
        }
    }

    // Pre-parse cookies outside of GIL
    let mut cookies: AHashMap<String, String> = AHashMap::with_capacity(8);
    if let Some(raw_cookie) = headers.get("cookie") {
        for pair in raw_cookie.split(';') {
            let part = pair.trim();
            if let Some(eq) = part.find('=') {
                let (k, v) = part.split_at(eq);
                let v2 = &v[1..];
                if !k.is_empty() {
                    cookies.insert(k.to_string(), v2.to_string());
                }
            }
        }
    }

    // Check if this is a HEAD request (needed for body stripping after Python handler)
    let is_head_request = method == "HEAD";

    // Single GIL acquisition for all Python operations
    let fut = match Python::attach(|py| -> PyResult<_> {
        // Clone Python objects
        let dispatch = state.dispatch.clone_ref(py);
        let handler = route_handler.clone_ref(py);

        // Create context dict if auth is present
        let context = if auth_ctx.is_some() {
            let ctx_dict = PyDict::new(py);
            let ctx_py = ctx_dict.unbind();
            // Populate with auth context if present
            if let Some(ref auth) = auth_ctx {
                populate_auth_context(&ctx_py, auth, py);
            }
            Some(ctx_py)
        } else {
            None
        };

        let request = PyRequest {
            method,
            path,
            body: body.to_vec(),
            path_params,
            query_params,
            headers,
            cookies,
            context,
        };
        let request_obj = Py::new(py, request)?;

        // Reuse the global event loop locals initialized at server startup
        let locals = TASK_LOCALS.get().ok_or_else(|| {
            pyo3::exceptions::PyRuntimeError::new_err("Asyncio loop not initialized")
        })?;

        // Pass handler_id to dispatch so it can lookup the original API instance
        let coroutine = dispatch.call1(py, (handler, request_obj, handler_id))?;
        pyo3_async_runtimes::into_future_with_locals(locals, coroutine.into_bound(py))
    }) {
        Ok(f) => f,
        Err(e) => {
            // Use new error handler
            return Python::attach(|py| {
                // Convert PyErr to exception instance
                e.restore(py);
                if let Some(exc) = PyErr::take(py) {
                    let exc_value = exc.value(py);
                    error::handle_python_exception(
                        py,
                        exc_value,
                        &path_clone,
                        &method_clone,
                        state.debug,
                    )
                } else {
                    error::build_error_response(
                        py,
                        500,
                        "Handler error: failed to create coroutine".to_string(),
                        vec![],
                        None,
                        state.debug,
                    )
                }
            });
        }
    };

    match fut.await {
        Ok(result_obj) => {
            // Fast-path: minimize GIL time for tuple responses (status, headers, body)
            let fast_tuple: Option<(u16, Vec<(String, String)>, Py<PyAny>, *const u8, usize)> =
                Python::attach(|py| {
                    let obj = result_obj.bind(py);
                    let tuple = obj.downcast::<PyTuple>().ok()?;
                    if tuple.len() != 3 {
                        return None;
                    }

                    // 0: status
                    let status_code: u16 = tuple.get_item(0).ok()?.extract::<u16>().ok()?;

                    // 1: headers
                    let resp_headers: Vec<(String, String)> = tuple
                        .get_item(1)
                        .ok()?
                        .extract::<Vec<(String, String)>>()
                        .ok()?;

                    // 2: body (bytes or bytearray)
                    let body_obj = match tuple.get_item(2) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };
                    // Only support bytes (tuple serializer returns bytes)
                    if let Ok(pybytes) = body_obj.downcast::<PyBytes>() {
                        let slice = pybytes.as_bytes();
                        let len = slice.len();
                        let ptr = slice.as_ptr();
                        let owner: Py<PyAny> = body_obj.unbind();
                        Some((status_code, resp_headers, owner, ptr, len))
                    } else {
                        None
                    }
                });

            if let Some((status_code, resp_headers, body_owner, body_ptr, body_len)) = fast_tuple {
                let status = StatusCode::from_u16(status_code).unwrap_or(StatusCode::OK);
                let mut file_path: Option<String> = None;
                let mut headers: Vec<(String, String)> = Vec::with_capacity(resp_headers.len());
                for (k, v) in resp_headers {
                    if k.eq_ignore_ascii_case("x-bolt-file-path") {
                        file_path = Some(v);
                    } else {
                        headers.push((k, v));
                    }
                }
                if let Some(path) = file_path {
                    // Use direct tokio file I/O instead of NamedFile
                    // NamedFile::into_response() does expensive synchronous work (MIME detection, ETag, etc.)
                    // Python already provides content-type, so we skip all that overhead
                    return match File::open(&path).await {
                        Ok(mut file) => {
                            // Get file size
                            let file_size = match file.metadata().await {
                                Ok(metadata) => metadata.len(),
                                Err(e) => {
                                    return HttpResponse::InternalServerError()
                                        .content_type("text/plain; charset=utf-8")
                                        .body(format!("Failed to read file metadata: {}", e));
                                }
                            };

                            // For small files (<10MB), read into memory for better performance
                            // This avoids chunked encoding and allows proper Content-Length header
                            let file_bytes = if file_size < 10 * 1024 * 1024 {
                                let mut buffer = Vec::with_capacity(file_size as usize);
                                match file.read_to_end(&mut buffer).await {
                                    Ok(_) => buffer,
                                    Err(e) => {
                                        return HttpResponse::InternalServerError()
                                            .content_type("text/plain; charset=utf-8")
                                            .body(format!("Failed to read file: {}", e));
                                    }
                                }
                            } else {
                                // For large files, use streaming (or empty body for HEAD)
                                let mut builder = HttpResponse::build(status);
                                for (k, v) in headers {
                                    if let Ok(name) = HeaderName::try_from(k) {
                                        if let Ok(val) = HeaderValue::try_from(v) {
                                            builder.append_header((name, val));
                                        }
                                    }
                                }
                                if skip_compression {
                                    builder.append_header(("content-encoding", "identity"));
                                }

                                // HEAD requests must have empty body per RFC 7231
                                if is_head_request {
                                    return builder.body(Vec::<u8>::new());
                                }

                                // Create streaming response with 64KB chunks
                                let stream = stream::unfold(file, |mut file| async move {
                                    let mut buffer = vec![0u8; 64 * 1024];
                                    match file.read(&mut buffer).await {
                                        Ok(0) => None, // EOF
                                        Ok(n) => {
                                            buffer.truncate(n);
                                            Some((
                                                Ok::<_, std::io::Error>(Bytes::from(buffer)),
                                                file,
                                            ))
                                        }
                                        Err(e) => Some((Err(e), file)),
                                    }
                                });
                                return builder.streaming(stream);
                            };

                            // Build response with file bytes (small file path)
                            let mut builder = HttpResponse::build(status);

                            // Apply headers from Python (already includes content-type)
                            for (k, v) in headers {
                                if let Ok(name) = HeaderName::try_from(k) {
                                    if let Ok(val) = HeaderValue::try_from(v) {
                                        builder.append_header((name, val));
                                    }
                                }
                            }

                            if skip_compression {
                                builder.append_header(("content-encoding", "identity"));
                            }

                            // HEAD requests must have empty body per RFC 7231
                            let response_body = if is_head_request {
                                Vec::new()
                            } else {
                                file_bytes
                            };
                            builder.body(response_body)
                        }
                        Err(e) => {
                            // Return appropriate HTTP status based on error kind
                            use std::io::ErrorKind;
                            match e.kind() {
                                ErrorKind::NotFound => HttpResponse::NotFound()
                                    .content_type("text/plain; charset=utf-8")
                                    .body("File not found"),
                                ErrorKind::PermissionDenied => HttpResponse::Forbidden()
                                    .content_type("text/plain; charset=utf-8")
                                    .body("Permission denied"),
                                _ => HttpResponse::InternalServerError()
                                    .content_type("text/plain; charset=utf-8")
                                    .body(format!("File error: {}", e)),
                            }
                        }
                    };
                } else {
                    let mut builder = HttpResponse::build(status);
                    for (k, v) in headers {
                        builder.append_header((k, v));
                    }
                    if skip_compression {
                        builder.append_header(("Content-Encoding", "identity"));
                    }

                    // HEAD requests must have empty body per RFC 7231
                    let mut response = if is_head_request {
                        builder.body(Vec::<u8>::new())
                    } else {
                        // Copy body bytes outside of the GIL
                        let mut body_vec = Vec::<u8>::with_capacity(body_len);
                        unsafe {
                            body_vec.set_len(body_len);
                            std::ptr::copy_nonoverlapping(
                                body_ptr,
                                body_vec.as_mut_ptr(),
                                body_len,
                            );
                        }
                        // Drop the Python owner with the GIL attached
                        let _ = Python::attach(|_| drop(body_owner));
                        builder.body(body_vec)
                    };

                    // Add CORS headers if configured (NO GIL - uses Rust-native config)
                    if let Some(ref route_meta) = route_metadata {
                        if let Some(ref cors_cfg) = route_meta.cors_config {
                            let origin = req.headers().get("origin").and_then(|v| v.to_str().ok());
                            add_cors_headers_rust(
                                &mut response,
                                origin,
                                cors_cfg,
                                &state.cors_allowed_origins,
                            );
                        }
                    }

                    return response;
                }
            } else {
                // Fallback: handle tuple by extracting Vec<u8> under the GIL (compat path)
                if let Ok((status_code, resp_headers, body_bytes)) = Python::attach(|py| {
                    result_obj.extract::<(u16, Vec<(String, String)>, Vec<u8>)>(py)
                }) {
                    let status = StatusCode::from_u16(status_code).unwrap_or(StatusCode::OK);
                    let mut file_path: Option<String> = None;
                    let mut headers: Vec<(String, String)> = Vec::with_capacity(resp_headers.len());
                    for (k, v) in resp_headers {
                        if k.eq_ignore_ascii_case("x-bolt-file-path") {
                            file_path = Some(v);
                        } else {
                            headers.push((k, v));
                        }
                    }
                    if let Some(path) = file_path {
                        return match File::open(&path).await {
                            Ok(mut file) => {
                                let file_size = match file.metadata().await {
                                    Ok(metadata) => metadata.len(),
                                    Err(e) => {
                                        return HttpResponse::InternalServerError()
                                            .content_type("text/plain; charset=utf-8")
                                            .body(format!("Failed to read file metadata: {}", e));
                                    }
                                };
                                let file_bytes = if file_size < 10 * 1024 * 1024 {
                                    let mut buffer = Vec::with_capacity(file_size as usize);
                                    match file.read_to_end(&mut buffer).await {
                                        Ok(_) => buffer,
                                        Err(e) => {
                                            return HttpResponse::InternalServerError()
                                                .content_type("text/plain; charset=utf-8")
                                                .body(format!("Failed to read file: {}", e));
                                        }
                                    }
                                } else {
                                    let mut builder = HttpResponse::build(status);
                                    for (k, v) in headers {
                                        if let Ok(name) = HeaderName::try_from(k) {
                                            if let Ok(val) = HeaderValue::try_from(v) {
                                                builder.append_header((name, val));
                                            }
                                        }
                                    }
                                    if skip_compression {
                                        builder.append_header(("content-encoding", "identity"));
                                    }
                                    if is_head_request {
                                        return builder.body(Vec::<u8>::new());
                                    }
                                    let stream = stream::unfold(file, |mut file| async move {
                                        let mut buffer = vec![0u8; 64 * 1024];
                                        match file.read(&mut buffer).await {
                                            Ok(0) => None,
                                            Ok(n) => {
                                                buffer.truncate(n);
                                                Some((
                                                    Ok::<_, std::io::Error>(Bytes::from(buffer)),
                                                    file,
                                                ))
                                            }
                                            Err(e) => Some((Err(e), file)),
                                        }
                                    });
                                    return builder.streaming(stream);
                                };
                                let mut builder = HttpResponse::build(status);
                                for (k, v) in headers {
                                    if let Ok(name) = HeaderName::try_from(k) {
                                        if let Ok(val) = HeaderValue::try_from(v) {
                                            builder.append_header((name, val));
                                        }
                                    }
                                }
                                if skip_compression {
                                    builder.append_header(("content-encoding", "identity"));
                                }
                                let response_body = if is_head_request {
                                    Vec::new()
                                } else {
                                    file_bytes
                                };
                                builder.body(response_body)
                            }
                            Err(e) => {
                                use std::io::ErrorKind;
                                match e.kind() {
                                    ErrorKind::NotFound => HttpResponse::NotFound()
                                        .content_type("text/plain; charset=utf-8")
                                        .body("File not found"),
                                    ErrorKind::PermissionDenied => HttpResponse::Forbidden()
                                        .content_type("text/plain; charset=utf-8")
                                        .body("Permission denied"),
                                    _ => HttpResponse::InternalServerError()
                                        .content_type("text/plain; charset=utf-8")
                                        .body(format!("File error: {}", e)),
                                }
                            }
                        };
                    } else {
                        let mut builder = HttpResponse::build(status);
                        for (k, v) in headers {
                            builder.append_header((k, v));
                        }
                        if skip_compression {
                            builder.append_header(("Content-Encoding", "identity"));
                        }
                        let response_body = if is_head_request {
                            Vec::new()
                        } else {
                            body_bytes
                        };
                        let mut response = builder.body(response_body);
                        if let Some(ref route_meta) = route_metadata {
                            if let Some(ref cors_cfg) = route_meta.cors_config {
                                let origin =
                                    req.headers().get("origin").and_then(|v| v.to_str().ok());
                                add_cors_headers_rust(
                                    &mut response,
                                    origin,
                                    cors_cfg,
                                    &state.cors_allowed_origins,
                                );
                            }
                        }
                        return response;
                    }
                }
                let streaming = Python::attach(|py| {
                    let obj = result_obj.bind(py);
                    let is_streaming = (|| -> PyResult<bool> {
                        let m = py.import("django_bolt.responses")?;
                        let cls = m.getattr("StreamingResponse")?;
                        obj.is_instance(&cls)
                    })()
                    .unwrap_or(false);
                    if !is_streaming && !obj.hasattr("content").unwrap_or(false) {
                        return None;
                    }
                    let status_code: u16 = obj
                        .getattr("status_code")
                        .and_then(|v| v.extract())
                        .unwrap_or(200);
                    let mut headers: Vec<(String, String)> = Vec::new();
                    if let Ok(hobj) = obj.getattr("headers") {
                        if let Ok(hdict) = hobj.downcast::<PyDict>() {
                            for (k, v) in hdict {
                                if let (Ok(ks), Ok(vs)) =
                                    (k.extract::<String>(), v.extract::<String>())
                                {
                                    headers.push((ks, vs));
                                }
                            }
                        }
                    }
                    let media_type: String = obj
                        .getattr("media_type")
                        .and_then(|v| v.extract())
                        .unwrap_or_else(|_| "application/octet-stream".to_string());
                    let has_ct = headers
                        .iter()
                        .any(|(k, _)| k.eq_ignore_ascii_case("content-type"));
                    if !has_ct {
                        headers.push(("content-type".to_string(), media_type.clone()));
                    }
                    let content_obj: Py<PyAny> = match obj.getattr("content") {
                        Ok(c) => c.unbind(),
                        Err(_) => return None,
                    };
                    Some((status_code, headers, media_type, content_obj))
                });

                if let Some((status_code, headers, media_type, content_obj)) = streaming {
                    let status = StatusCode::from_u16(status_code).unwrap_or(StatusCode::OK);
                    let mut builder = HttpResponse::build(status);
                    for (k, v) in headers {
                        builder.append_header((k, v));
                    }
                    if media_type == "text/event-stream" {
                        // HEAD requests must have empty body per RFC 7231
                        if is_head_request {
                            builder.content_type("text/event-stream");
                            builder.append_header(("X-Accel-Buffering", "no"));
                            builder.append_header((
                                "Cache-Control",
                                "no-cache, no-store, must-revalidate",
                            ));
                            builder.append_header(("Pragma", "no-cache"));
                            builder.append_header(("Expires", "0"));
                            if skip_compression {
                                builder.append_header(("Content-Encoding", "identity"));
                            }
                            return builder.body(Vec::<u8>::new());
                        }

                        let mut final_content_obj = content_obj;
                        // Combine async check and wrapping into single GIL acquisition
                        let (is_async_sse, wrapped_content) = Python::attach(|py| {
                            let obj = final_content_obj.bind(py);
                            let has_async = obj.hasattr("__aiter__").unwrap_or(false)
                                || obj.hasattr("__anext__").unwrap_or(false);
                            if !has_async {
                                return (false, None);
                            }
                            // Try to wrap async iterator
                            let wrapped = (|| -> Option<Py<PyAny>> {
                                let collector_module =
                                    py.import("django_bolt.async_collector").ok()?;
                                let collector_class =
                                    collector_module.getattr("AsyncToSyncCollector").ok()?;
                                collector_class
                                    .call1((obj.clone(), 5, 1))
                                    .ok()
                                    .map(|w| w.unbind())
                            })();
                            (wrapped.is_none(), wrapped)
                        });
                        if let Some(w) = wrapped_content {
                            final_content_obj = w;
                        }
                        if is_async_sse {
                            builder.append_header(("X-Accel-Buffering", "no"));
                            builder.append_header((
                                "Cache-Control",
                                "no-cache, no-store, must-revalidate",
                            ));
                            builder.append_header(("Pragma", "no-cache"));
                            builder.append_header(("Expires", "0"));
                            if skip_compression {
                                builder.append_header(("Content-Encoding", "identity"));
                            }
                            builder.content_type("text/event-stream");
                            return builder.streaming(create_python_stream(final_content_obj));
                        } else {
                            match direct_stream::create_sse_response(final_content_obj) {
                                Ok(mut resp) => {
                                    if skip_compression {
                                        if let Ok(val) = HeaderValue::try_from("identity") {
                                            resp.headers_mut().insert(
                                                actix_web::http::header::CONTENT_ENCODING,
                                                val,
                                            );
                                        }
                                    }
                                    return resp;
                                }
                                Err(_) => {
                                    builder.append_header(("X-Accel-Buffering", "no"));
                                    builder.append_header((
                                        "Cache-Control",
                                        "no-cache, no-store, must-revalidate",
                                    ));
                                    builder.append_header(("Pragma", "no-cache"));
                                    builder.append_header(("Expires", "0"));
                                    if skip_compression {
                                        builder.append_header(("Content-Encoding", "identity"));
                                    }
                                    return builder.content_type("text/event-stream").body("");
                                }
                            }
                        }
                    } else {
                        // HEAD requests must have empty body per RFC 7231
                        if is_head_request {
                            if skip_compression {
                                builder.append_header(("Content-Encoding", "identity"));
                            }
                            return builder.body(Vec::<u8>::new());
                        }

                        let mut final_content = content_obj;
                        // Combine async check and wrapping into single GIL acquisition
                        let (needs_async_stream, wrapped_content) = Python::attach(|py| {
                            let obj = final_content.bind(py);
                            let has_async = obj.hasattr("__aiter__").unwrap_or(false)
                                || obj.hasattr("__anext__").unwrap_or(false);
                            if !has_async {
                                return (false, None);
                            }
                            // Try to wrap async iterator
                            let wrapped = (|| -> Option<Py<PyAny>> {
                                let collector_module =
                                    py.import("django_bolt.async_collector").ok()?;
                                let collector_class =
                                    collector_module.getattr("AsyncToSyncCollector").ok()?;
                                collector_class
                                    .call1((obj.clone(), 20, 2))
                                    .ok()
                                    .map(|w| w.unbind())
                            })();
                            (wrapped.is_none(), wrapped)
                        });

                        if needs_async_stream {
                            if skip_compression {
                                builder.append_header(("Content-Encoding", "identity"));
                            }
                            let stream = create_python_stream(final_content);
                            return builder.streaming(stream);
                        }

                        if let Some(w) = wrapped_content {
                            final_content = w;
                        }
                        {
                            let mut direct = direct_stream::PythonDirectStream::new(final_content);
                            if let Some(body) = direct.try_collect_small() {
                                if skip_compression {
                                    builder.append_header(("Content-Encoding", "identity"));
                                }
                                return builder.body(body);
                            }
                            if skip_compression {
                                builder.append_header(("Content-Encoding", "identity"));
                            }
                            return builder.streaming(Box::pin(direct));
                        }
                    }
                } else {
                    return Python::attach(|py| {
                        error::build_error_response(
                            py,
                            500,
                            "Handler returned unsupported response type (expected tuple or StreamingResponse)".to_string(),
                            vec![],
                            None,
                            state.debug,
                        )
                    });
                }
            }
        }
        Err(e) => {
            // Use new error handler for Python exceptions during handler execution
            return Python::attach(|py| {
                // Convert PyErr to exception instance
                e.restore(py);
                if let Some(exc) = PyErr::take(py) {
                    let exc_value = exc.value(py);
                    error::handle_python_exception(
                        py,
                        exc_value,
                        &path_clone,
                        &method_clone,
                        state.debug,
                    )
                } else {
                    error::build_error_response(
                        py,
                        500,
                        "Handler execution error".to_string(),
                        vec![],
                        None,
                        state.debug,
                    )
                }
            });
        }
    }
}
