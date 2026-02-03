use std::env;

/// Configuration from environment
pub(crate) struct Config {
    pub(crate) host: String,
    pub(crate) port: u16,
    pub(crate) debug: bool,
}

impl Config {
    pub(crate) fn from_env() -> Self {
        dotenv::dotenv().ok();
        let host = env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port = env::var("PORT").ok()
            .and_then(|p| p.parse::<u16>().ok())
            .unwrap_or(5000);
        let debug = env::var("DEBUG").unwrap_or_else(|_| "false".to_string())
            .to_lowercase() == "true";
        Config { host, port, debug }
    }
}