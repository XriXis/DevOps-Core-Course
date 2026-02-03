use actix_web::{get, HttpRequest, HttpResponse, Responder};
use serde_json::json;
use rustc_version::version;
use crate::system;

/// GET /
#[get("/")]
async fn root(req: HttpRequest) -> impl Responder {
    log::debug!("Request: {} {}", req.method(), req.path());

    let service = system::ServiceInfo {
        name: "devops-info-service".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        description: "DevOps course info service".to_string(),
        framework: "Actix-web".to_string(),
    };

    let system = system::SystemInfo {
        hostname: sys_info::hostname().unwrap_or_default(),
        platform: sys_info::os_type().unwrap_or_default(),
        platform_version: sys_info::os_release().unwrap_or_default(),
        architecture: std::env::consts::ARCH.to_string(),
        cpu_count: sys_info::cpu_num().unwrap_or(1) as usize,
        rust_version: version()
            .map(|v| v.to_string())
            .unwrap_or_else(|_| "unknown".to_string()),
    };

    let uptime = system::get_uptime();

    HttpResponse::Ok().json(serde_json::json!({
        "service": service,
        "system": system,
        "runtime": uptime,
        "request": {
            "client_ip": req.peer_addr().map(|a| a.ip().to_string()).unwrap_or("unknown".to_string()),
            "user_agent": req.headers().get("User-Agent").map(|v| v.to_str().unwrap_or("unknown")).unwrap_or("unknown"),
            "method": req.method().to_string(),
            "path": req.path(),
        },
        "endpoints": vec![
            json!({"path": "/", "method": "GET", "description": "System and service info about the server"}),
            json!({"path": "/health", "method": "GET", "description": "Health check"})
        ]
    }))
}

/// GET /health
#[get("/health")]
async fn health(_req: HttpRequest) -> impl Responder {
    log::debug!("Health check request");
    let runtime = system::get_uptime();
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "timestamp": runtime.current_time,
        "uptime_seconds": runtime.uptime_seconds
    }))
}
