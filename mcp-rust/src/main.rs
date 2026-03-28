// MCP Server for Date and Time

use anyhow::Result;
use chrono::{Datelike, Local};
use rmcp::{
    ServerHandler,
    handler::server::{router::tool::ToolRouter},
    model::*,
    tool, tool_handler, tool_router,
    transport::streamable_http_server::{
        StreamableHttpService, session::local::LocalSessionManager,
    },
};
//use rmcp::{schemars, handler::server::{tool::Parameters}};

//use tokio::time::{Duration, sleep};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

//#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
//pub struct LocRequest {
//    #[schemars(description = "location")]
//    pub input: String,
//}

#[derive(Debug, Clone)]
pub struct Server {
    tool_router: ToolRouter<Self>,
}

#[tool_router]
impl Server {
    pub fn new() -> Self {
        Self {
            tool_router: Self::tool_router(),
        }
    }

    //#[tool(description = "Get weather forecast for a location")]
    //async fn get_weather(
    //    &self,
    //    Parameters(LocRequest { input }): Parameters<LocRequest>,
    //) -> String {
    //    tracing::info!("Received get_weather() request with input: {}", input);
    //    //sleep(Duration::from_secs(2)).await;
    //    tracing::info!("Completed request");
    //    format!("Place: '{}'\n Temperature: 10°C\n Wind: 5km/h", input)
    //}

    #[tool(description = "Get today's date")]
    async fn get_date(&self) -> String {
        tracing::info!("Received get_date() request");
        let now = Local::now();
        let date = now.date_naive();
        let weekday = now.weekday();
        //format!("Today is Saturday 2026/03/28")
        format!("Today is {} ({})", date, weekday)
    }

    #[tool(description = "Get current time")]
    async fn get_time(&self) -> String {
        tracing::info!("Received get_time() request");
        let now = Local::now();
        let time = now.time();
        format!("Current time: {}", time.format("%H:%M:%S"))
    }
}

#[tool_handler]
impl ServerHandler for Server {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            instructions: Some("Date/Time MCP server".into()),
            capabilities: ServerCapabilities::builder().enable_tools().build(),
            ..Default::default()
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "debug".to_string().into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let service = StreamableHttpService::new(
        || Ok(Server::new()),
        LocalSessionManager::default().into(),
        Default::default(),
    );

    let router = axum::Router::new().nest_service("/mcp", service);
    //let tcp_listener = tokio::net::TcpListener::bind("127.0.0.1:8000").await?;
    //tracing::info!("MCP server listening on 127.0.0.1:8000");
    let tcp_listener = tokio::net::TcpListener::bind("0.0.0.0:8000").await?;
    tracing::info!("MCP server listening on 0.0.0.0:8000");

    axum::serve(tcp_listener, router)
        .with_graceful_shutdown(async { tokio::signal::ctrl_c().await.unwrap() })
        .await?;
    Ok(())
}
