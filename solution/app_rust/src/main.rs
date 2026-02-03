mod routes;
mod config;
mod system;

use actix_web::{middleware::Logger, App, HttpServer};
use chrono::{DateTime, Utc};
use log::LevelFilter;
use lazy_static::lazy_static;

lazy_static! {
    static ref START_TIME: DateTime<Utc> = Utc::now();
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let cfg = config::Config::from_env();
    env_logger::Builder::from_default_env()
        .filter_level(if cfg.debug { LevelFilter::Debug } else { LevelFilter::Info })
        .init();

    log::info!("Starting DevOps Info Service on {}:{} at {}", cfg.host, cfg.port, START_TIME.to_utc());

    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .service(routes::root)
            .service(routes::health)
    })
        .bind((cfg.host, cfg.port))?
        .run()
        .await
}
