use std::sync::Arc;
use std::time::Duration;

use anyhow::anyhow;
use cas_types::{REQUEST_ID_HEADER, SESSION_ID_HEADER};
use error_printer::{ErrorPrinter, OptionPrinter};
use http::{Extensions, StatusCode};
use reqwest::header::{AUTHORIZATION, HeaderValue};
use reqwest::{Request, Response};
use reqwest_middleware::{ClientBuilder, ClientWithMiddleware, Middleware, Next};
use reqwest_retry::policies::ExponentialBackoff;
use reqwest_retry::{
    DefaultRetryableStrategy, RetryTransientMiddleware, Retryable, RetryableStrategy, default_on_request_failure,
    default_on_request_success,
};
use tokio::sync::Mutex;
use tracing::{Instrument, info, info_span, warn};
use utils::auth::{AuthConfig, TokenProvider};

use crate::constants::{CLIENT_IDLE_CONNECTION_TIMEOUT, CLIENT_MAX_IDLE_CONNECTIONS};
use crate::retry_wrapper::on_request_failure;
use crate::{CasClientError, error};

pub(crate) const NUM_RETRIES: u32 = 5;
pub(crate) const BASE_RETRY_DELAY_MS: u64 = 3000; // 3s
pub(crate) const BASE_RETRY_MAX_DURATION_MS: u64 = 6 * 60 * 1000; // 6m

/// A strategy that doesn't retry on 429, and defaults to `DefaultRetryableStrategy` otherwise.
pub struct No429RetryStrategy;

impl RetryableStrategy for No429RetryStrategy {
    fn handle(&self, res: &Result<Response, reqwest_middleware::Error>) -> Option<Retryable> {
        if let Ok(success) = res
            && success.status() == StatusCode::TOO_MANY_REQUESTS
        {
            return Some(Retryable::Fatal);
        }

        const DEFAULT_STRATEGY: DefaultRetryableStrategy = DefaultRetryableStrategy;
        DEFAULT_STRATEGY.handle(res)
    }
}

/// A strategy that retries on 5xx/400/429 status codes, and retries on transient errors.
pub struct XetRetryStrategy;

impl RetryableStrategy for XetRetryStrategy {
    fn handle(&self, res: &Result<Response, reqwest_middleware::Error>) -> Option<Retryable> {
        match res {
            Ok(success) => default_on_request_success(success),
            Err(error) => on_request_failure(error),
        }
    }
}

pub struct RetryConfig<R: RetryableStrategy> {
    /// Number of retries for transient errors.
    pub num_retries: u32,

    /// Base delay before retrying, default to 3s.
    pub min_retry_interval_ms: u64,

    /// Base max duration for retry attempts, default to 6m.
    pub max_retry_interval_ms: u64,

    pub strategy: R,
}

impl Default for RetryConfig<XetRetryStrategy> {
    fn default() -> Self {
        Self {
            num_retries: NUM_RETRIES,
            min_retry_interval_ms: BASE_RETRY_DELAY_MS,
            max_retry_interval_ms: BASE_RETRY_MAX_DURATION_MS,
            strategy: XetRetryStrategy,
        }
    }
}

impl RetryConfig<No429RetryStrategy> {
    pub fn no429retry() -> Self {
        Self {
            num_retries: NUM_RETRIES,
            min_retry_interval_ms: BASE_RETRY_DELAY_MS,
            max_retry_interval_ms: BASE_RETRY_MAX_DURATION_MS,
            strategy: No429RetryStrategy,
        }
    }
}

fn reqwest_client() -> Result<reqwest::Client, CasClientError> {
    // custom dns resolver not supported in WASM. no access to getaddrinfo/any other dns interface.
    #[cfg(target_family = "wasm")]
    {
        static CLIENT: std::sync::LazyLock<reqwest::Client> = std::sync::LazyLock::new(|| reqwest::Client::new());
        Ok((&*CLIENT).clone())
    }

    #[cfg(not(target_family = "wasm"))]
    {
        use xet_runtime::XetRuntime;

        let client = XetRuntime::get_or_create_reqwest_client(|| {
            reqwest::Client::builder()
                .pool_idle_timeout(*CLIENT_IDLE_CONNECTION_TIMEOUT)
                .pool_max_idle_per_host(*CLIENT_MAX_IDLE_CONNECTIONS)
                .build()
        })?;

        info!(
            idle_timeout=?*CLIENT_IDLE_CONNECTION_TIMEOUT,
            max_idle_connections=*CLIENT_MAX_IDLE_CONNECTIONS,
            "HTTP client configured"
        );

        Ok(client)
    }
}

/// Builds authenticated HTTP Client to talk to CAS.
/// Includes retry middleware with exponential backoff.
pub fn build_auth_http_client<R: RetryableStrategy + Send + Sync + 'static>(
    auth_config: &Option<AuthConfig>,
    retry_config: RetryConfig<R>,
    session_id: &str,
) -> Result<ClientWithMiddleware, CasClientError> {
    let auth_middleware = auth_config.as_ref().map(AuthMiddleware::from);
    let logging_middleware = Some(LoggingMiddleware);
    let session_middleware = (!session_id.is_empty()).then(|| SessionMiddleware(session_id.to_owned()));

    let client = ClientBuilder::new(reqwest_client()?)
        .maybe_with(auth_middleware)
        .with(get_retry_middleware(retry_config))
        .maybe_with(logging_middleware)
        .maybe_with(session_middleware)
        .build();
    Ok(client)
}

/// Builds authenticated HTTP Client to talk to CAS.
pub fn build_auth_http_client_no_retry(
    auth_config: &Option<AuthConfig>,
    session_id: &str,
) -> Result<ClientWithMiddleware, CasClientError> {
    let auth_middleware = auth_config.as_ref().map(AuthMiddleware::from).info_none("CAS auth disabled");
    let logging_middleware = Some(LoggingMiddleware);
    let session_middleware = (!session_id.is_empty()).then(|| SessionMiddleware(session_id.to_owned()));
    Ok(ClientBuilder::new(reqwest_client()?)
        .maybe_with(auth_middleware)
        .maybe_with(logging_middleware)
        .maybe_with(session_middleware)
        .build())
}

/// Builds HTTP Client to talk to CAS.
/// Includes retry middleware with exponential backoff.
pub fn build_http_client<R: RetryableStrategy + Send + Sync + 'static>(
    retry_config: RetryConfig<R>,
    session_id: &str,
) -> Result<ClientWithMiddleware, CasClientError> {
    build_auth_http_client(&None, retry_config, session_id)
}

/// Builds HTTP Client to talk to CAS.
/// Includes retry middleware with exponential backoff.
pub fn build_http_client_no_retry(session_id: &str) -> Result<ClientWithMiddleware, CasClientError> {
    build_auth_http_client_no_retry(&None, session_id)
}

/// RetryStrategy
pub fn get_retry_policy_and_strategy<R: RetryableStrategy + Send + Sync>(
    config: RetryConfig<R>,
) -> (ExponentialBackoff, R) {
    (
        ExponentialBackoff::builder()
            .retry_bounds(
                Duration::from_millis(config.min_retry_interval_ms),
                Duration::from_millis(config.max_retry_interval_ms),
            )
            .build_with_max_retries(config.num_retries),
        config.strategy,
    )
}

/// Configurable Retry middleware with exponential backoff and configurable number of retries using reqwest-retry
fn get_retry_middleware<R: RetryableStrategy + Send + Sync>(
    config: RetryConfig<R>,
) -> RetryTransientMiddleware<ExponentialBackoff, R> {
    let (policy, strategy) = get_retry_policy_and_strategy(config);
    RetryTransientMiddleware::new_with_policy_and_strategy(policy, strategy)
}

/// Helper trait to allow the reqwest_middleware client to optionally add a middleware.
trait OptionalMiddleware {
    fn maybe_with<M: Middleware>(self, middleware: Option<M>) -> Self;
}

impl OptionalMiddleware for ClientBuilder {
    fn maybe_with<M: Middleware>(self, middleware: Option<M>) -> Self {
        match middleware {
            Some(m) => self.with(m),
            None => self,
        }
    }
}

#[derive(Copy, Clone)]
pub struct Api(pub &'static str);

/// Adds logging middleware that will trace::warn! on retryable errors.
pub struct LoggingMiddleware;

#[cfg_attr(not(target_family = "wasm"), async_trait::async_trait)]
#[cfg_attr(target_family = "wasm", async_trait::async_trait(?Send))]
impl Middleware for LoggingMiddleware {
    async fn handle(
        &self,
        req: Request,
        extensions: &mut http::Extensions,
        next: Next<'_>,
    ) -> reqwest_middleware::Result<Response> {
        let api = extensions.get::<Api>().map(|a| a.0);
        next.run(req, extensions)
            .instrument(info_span!("client::request", api))
            .await
            .inspect(|res| {
                // Response received, debug log it and use the status code
                // to check if we are retrying or not.
                let status_code = res.status().as_u16();
                let request_id = request_id_from_response(res);
                info!(request_id, status_code, "Received CAS response");
                if Some(Retryable::Transient) == default_on_request_success(res) {
                    warn!(request_id, status_code, "Retrying...");
                }
            })
            .inspect_err(|err| {
                // Error received, check if we are retrying or not.
                if Some(Retryable::Transient) == default_on_request_failure(err) {
                    warn!(?err, "Retrying...");
                }
            })
    }
}

/// AuthMiddleware is a thread-safe middleware that adds a CAS auth token to outbound requests.
/// If the token it holds is expired, it will automatically be refreshed.
pub struct AuthMiddleware {
    token_provider: Arc<Mutex<TokenProvider>>,
}

impl AuthMiddleware {
    /// Fetches a token from our TokenProvider. This locks the TokenProvider as we might need
    /// to refresh the token if it has expired.
    ///
    /// In the common case, this lock is held only to read the underlying token stored
    /// in memory. However, in the event of an expired token (e.g. once every 15 min),
    /// we will need to hold the lock while making a call to refresh the token
    /// (e.g. to a remote service). During this time, no other CAS requests can proceed
    /// from this client until the token has been fetched. This is expected/ok since we
    /// don't have a valid token and thus any calls would fail.
    async fn get_token(&self) -> Result<String, anyhow::Error> {
        let mut provider = self.token_provider.lock().await;
        provider
            .get_valid_token()
            .await
            .map_err(|err| {
                warn!(?err, "Token refresh failed");
                anyhow!("couldn't get token: {err:?}")
            })
            .inspect(|_token| {
                info!("Token refresh successful for CAS authentication");
            })
    }
}

impl From<&AuthConfig> for AuthMiddleware {
    fn from(cfg: &AuthConfig) -> Self {
        Self {
            token_provider: Arc::new(Mutex::new(TokenProvider::new(cfg))),
        }
    }
}

#[cfg_attr(not(target_family = "wasm"), async_trait::async_trait)]
#[cfg_attr(target_family = "wasm", async_trait::async_trait(?Send))]
impl Middleware for AuthMiddleware {
    async fn handle(
        &self,
        mut req: Request,
        extensions: &mut http::Extensions,
        next: Next<'_>,
    ) -> reqwest_middleware::Result<Response> {
        let token = self.get_token().await.map_err(reqwest_middleware::Error::Middleware)?;

        let headers = req.headers_mut();
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&format!("Bearer {token}")).unwrap());
        next.run(req, extensions).await
    }
}

pub struct SessionMiddleware(String);

// WASM compatibility; note the use of the pattern:
//
// #[cfg_attr(not(target_family = "wasm"), async_trait::async_trait)]
// #[cfg_attr(target_family = "wasm", async_trait::async_trait(?Send))]
// instead of just #[async_trait::async_trait]
// this makes the use of the async_trait wasm compatible to not enforce `Send` bounds when
// compiling for wasm, while those Send bounds are useful in non-wasm mode.

#[cfg_attr(not(target_family = "wasm"), async_trait::async_trait)]
#[cfg_attr(target_family = "wasm", async_trait::async_trait(?Send))]
impl Middleware for SessionMiddleware {
    async fn handle(
        &self,
        mut req: Request,
        extensions: &mut Extensions,
        next: Next<'_>,
    ) -> reqwest_middleware::Result<Response> {
        req.headers_mut()
            .insert(SESSION_ID_HEADER, HeaderValue::from_str(&self.0).unwrap());
        next.run(req, extensions).await
    }
}

/// Helper trait to log the different types of errors that come back from a request to CAS,
/// transforming the implementation into some new error type.
pub trait ResponseErrorLogger<T> {
    fn process_error(self, api: &str) -> T;
}

/// Add ResponseErrorLogger to Result<Response> for our requests.
/// This logs an error if one occurred before receiving a response or
/// if the status code indicates a failure.
/// As a result of these checks, the response is also transformed into a
/// cas_client::error::Result instead of the raw reqwest_middleware::Result.
impl ResponseErrorLogger<error::Result<Response>> for reqwest_middleware::Result<Response> {
    fn process_error(self, api: &str) -> error::Result<Response> {
        let res = self
            .map_err(CasClientError::from)
            .log_error(format!("error invoking {api} api"))?;
        let request_id = request_id_from_response(&res);
        let error_message = format!("{api} api failed: request id: {request_id}");
        let status = res.status();
        let res = res.error_for_status().map_err(CasClientError::from);
        match (api, status) {
            ("get_reconstruction", StatusCode::RANGE_NOT_SATISFIABLE) => res.debug_error(&error_message),
            // not all status codes mean fatal error
            _ => res.info_error(&error_message),
        }
    }
}

pub fn request_id_from_response(res: &Response) -> &str {
    res.headers()
        .get(REQUEST_ID_HEADER)
        .and_then(|h| h.to_str().ok())
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use std::time::SystemTime;

    use httpmock::prelude::*;
    use reqwest::StatusCode;
    use tracing_test::traced_test;

    use super::*;

    #[tokio::test]
    #[traced_test]
    async fn test_retry_policy_500() {
        {
            // Arrange
            let server = MockServer::start();
            let mock = server.mock(|when, then| {
                when.method(GET).path("/data");
                then.status(500).body("500: Internal Server Error");
            });

            let retry_config = RetryConfig {
                num_retries: 1,
                min_retry_interval_ms: 0,
                max_retry_interval_ms: 3000,
                strategy: DefaultRetryableStrategy,
            };
            let client = build_auth_http_client(&None, retry_config, "").unwrap();

            // Act & Assert - should retry and log
            let response = client.get(server.url("/data")).send().await.unwrap();

            // Assert
            assert!(logs_contain("status_code=500"));
            assert!(logs_contain("Retrying..."));
            assert_eq!(2, mock.hits());
            assert_eq!(response.status(), 500);
        }

        {
            // Arrange
            let server = MockServer::start();
            let mock = server.mock(|when, then| {
                when.method(GET).path("/data");
                then.status(500).body("500: Internal Server Error");
            });

            let retry_config = RetryConfig {
                num_retries: 1,
                min_retry_interval_ms: 0,
                max_retry_interval_ms: 3000,
                strategy: No429RetryStrategy,
            };
            let client = build_auth_http_client(&None, retry_config, "").unwrap();

            // Act & Assert - should retry and log
            let response = client.get(server.url("/data")).send().await.unwrap();

            // Assert
            assert!(logs_contain("status_code=500"));
            assert!(logs_contain("Retrying..."));
            assert_eq!(2, mock.hits());
            assert_eq!(response.status(), 500);
        }
    }

    #[tokio::test]
    #[traced_test]
    async fn test_retry_policy_timeout() {
        {
            // Arrange
            let server = MockServer::start();
            let mock = server.mock(|when, then| {
                when.method(GET).path("/data");
                then.status(StatusCode::REQUEST_TIMEOUT.as_u16()).body("Request Timeout");
            });

            let retry_config = RetryConfig {
                num_retries: 2,
                min_retry_interval_ms: 0,
                max_retry_interval_ms: 3000,
                strategy: DefaultRetryableStrategy,
            };
            let client = build_auth_http_client(&None, retry_config, "").unwrap();

            // Act & Assert - should retry and log
            let response = client.get(server.url("/data")).send().await.unwrap();

            // Assert
            assert!(logs_contain("status_code=408"));
            assert!(logs_contain("Retrying..."));
            assert_eq!(3, mock.hits());
            assert_eq!(response.status(), StatusCode::REQUEST_TIMEOUT);
        }

        {
            // Arrange
            let server = MockServer::start();
            let mock = server.mock(|when, then| {
                when.method(GET).path("/data");
                then.status(StatusCode::REQUEST_TIMEOUT.as_u16()).body("Request Timeout");
            });

            let retry_config = RetryConfig {
                num_retries: 2,
                min_retry_interval_ms: 0,
                max_retry_interval_ms: 3000,
                strategy: No429RetryStrategy,
            };
            let client = build_auth_http_client(&None, retry_config, "").unwrap();

            // Act & Assert - should retry and log
            let response = client.get(server.url("/data")).send().await.unwrap();

            // Assert
            assert!(logs_contain("status_code=408"));
            assert!(logs_contain("Retrying..."));
            assert_eq!(3, mock.hits());
            assert_eq!(response.status(), StatusCode::REQUEST_TIMEOUT);
        }
    }

    #[tokio::test]
    #[traced_test]
    async fn test_retry_policy_delay() {
        {
            // Arrange
            let start_time = SystemTime::now();
            let server = MockServer::start();
            let mock = server.mock(|when, then| {
                when.method(GET).path("/data");
                then.status(StatusCode::INTERNAL_SERVER_ERROR.as_u16());
            });

            let retry_config = RetryConfig {
                num_retries: 2,
                min_retry_interval_ms: 1000,
                max_retry_interval_ms: 6000,
                strategy: DefaultRetryableStrategy,
            };
            let client = build_auth_http_client(&None, retry_config, "").unwrap();

            // Act & Assert - should retry and log
            let response = client.get(server.url("/data")).send().await.unwrap();

            // Assert
            assert!(logs_contain("status_code=500"));
            assert!(logs_contain("Retrying..."));
            assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
            assert_eq!(3, mock.hits());
            assert!(start_time.elapsed().unwrap() > Duration::from_secs(0));
        }

        {
            // Arrange
            let start_time = SystemTime::now();
            let server = MockServer::start();
            let mock = server.mock(|when, then| {
                when.method(GET).path("/data");
                then.status(StatusCode::INTERNAL_SERVER_ERROR.as_u16());
            });

            let retry_config = RetryConfig {
                num_retries: 2,
                min_retry_interval_ms: 1000,
                max_retry_interval_ms: 6000,
                strategy: No429RetryStrategy,
            };
            let client = build_auth_http_client(&None, retry_config, "").unwrap();

            // Act & Assert - should retry and log
            let response = client.get(server.url("/data")).send().await.unwrap();

            // Assert
            assert!(logs_contain("status_code=500"));
            assert!(logs_contain("Retrying..."));
            assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
            assert_eq!(3, mock.hits());
            assert!(start_time.elapsed().unwrap() > Duration::from_secs(0));
        }
    }

    #[tokio::test]
    #[traced_test]
    async fn test_no_429_retry() {
        // Arrange
        let server = MockServer::start();
        let mock = server.mock(|when, then| {
            when.method(GET).path("/data");
            then.status(StatusCode::TOO_MANY_REQUESTS.as_u16());
        });

        let retry_config = RetryConfig {
            num_retries: 10,
            min_retry_interval_ms: 1000,
            max_retry_interval_ms: 6000,
            strategy: No429RetryStrategy,
        };
        let client = build_auth_http_client(&None, retry_config, "").unwrap();

        // Act & Assert - should retry and log
        let response = client.get(server.url("/data")).send().await.unwrap();

        // Assert
        assert_eq!(response.status(), StatusCode::TOO_MANY_REQUESTS);
        assert_eq!(1, mock.hits());
    }
}
