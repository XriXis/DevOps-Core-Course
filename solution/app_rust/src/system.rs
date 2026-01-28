use chrono::Utc;
use serde::Serialize;

#[derive(Serialize)]
pub(crate) struct ServiceInfo {
    pub(crate) name: String,
    pub(crate) version: String,
    pub(crate) description: String,
    pub(crate) framework: String,
}

#[derive(Serialize)]
pub(crate) struct SystemInfo {
    pub(crate) hostname: String,
    pub(crate) platform: String,
    pub(crate) platform_version: String,
    pub(crate) architecture: String,
    pub(crate) cpu_count: usize,
    pub(crate) rust_version: String,
}

#[derive(Serialize)]
pub(crate) struct RuntimeInfo {
    pub(crate) uptime_seconds: i64,
    pub(crate) uptime_human: String,
    pub(crate) current_time: String,
    pub(crate) timezone: String,
}

/// Calculate uptime
pub(crate) fn get_uptime() -> RuntimeInfo {
    let now = Utc::now();
    let delta = now.signed_duration_since(*crate::START_TIME);
    let hours = delta.num_hours();
    let minutes = delta.num_minutes() % 60 ;
    RuntimeInfo {
        uptime_seconds: delta.num_seconds(),
        uptime_human: format!("{} hours, {} minutes", hours, minutes),
        current_time: now.format("%Y-%m-%d %H:%M:%S").to_string(),
        timezone: "UTC".to_string(),
    }
}

