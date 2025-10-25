//! Recorder-wide error façade for CodeTracer components.
//!
//! The crate defines a structured [`RecorderError`] type backed by
//! [`ErrorKind`] and [`ErrorCode`] classifications. Use the provided macros
//! (`usage!`, `enverr!`, `target!`, `bug!`, `ensure_usage!`, `ensure_env!`, etc.)
//! to author failures consistently across the workspace.

use std::borrow::Cow;
use std::collections::BTreeMap;
use std::error::Error as StdError;
use std::fmt;
use std::io;

/// Result alias used throughout the recorder workspace.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ErrorCode, ErrorKind, RecorderError, RecorderResult};
///
/// fn validate(flag: &str) -> RecorderResult<()> {
///     if flag == "ok" {
///         Ok(())
///     } else {
///         Err(RecorderError::new(
///             ErrorKind::Usage,
///             ErrorCode::UnsupportedFormat,
///             "flag must be 'ok'",
///         ))
///     }
/// }
///
/// assert!(validate("ok").is_ok());
/// assert!(validate("nope").is_err());
/// ```
pub type RecorderResult<T> = Result<T, RecorderError>;

/// Key-value metadata associated with an error.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ContextMap, RecorderError, ErrorKind, ErrorCode};
///
/// let mut context: ContextMap = ContextMap::new();
/// context.insert("path", "/tmp/trace.json".into());
///
/// let error = RecorderError::new(
///     ErrorKind::Environment,
///     ErrorCode::Io,
///     "failed to write trace",
/// )
/// .with_context("path", "/tmp/trace.json");
///
/// assert_eq!(context.get("path"), Some(&"/tmp/trace.json".to_owned()));
/// assert_eq!(error.context.get("path"), Some(&"/tmp/trace.json".to_owned()));
/// ```
pub type ContextMap = BTreeMap<&'static str, String>;

/// High-level grouping of recorder failures.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
///
/// let err = RecorderError::new(ErrorKind::Target, ErrorCode::TraceIncomplete, "target failed");
///
/// match err.kind {
///     ErrorKind::Target => {
///         // Target code misbehaved; take recovery action.
///     }
///     // Non-exhaustive enums require a catch-all branch for forward compatibility.
///     _ => {}
/// }
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[non_exhaustive]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum ErrorKind {
    /// Caller provided invalid input or violated usage constraints.
    Usage,
    /// External environment or IO prevented the recorder from continuing.
    Environment,
    /// Target code being traced raised/behaved unexpectedly.
    Target,
    /// Internal bug or invariant violation inside the recorder.
    Internal,
}

/// Stable error codes used for analytics and tooling.
///
/// # Examples
///
/// ```
/// use recorder_errors::ErrorCode;
///
/// let code = ErrorCode::TraceMissing;
/// assert_eq!(code.as_str(), "ERR_TRACE_MISSING");
/// assert_eq!(ErrorCode::parse("ERR_TRACE_MISSING"), Some(ErrorCode::TraceMissing));
/// assert_eq!(ErrorCode::parse("ERR_DOES_NOT_EXIST"), None);
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[non_exhaustive]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum ErrorCode {
    /// Fallback code used when no specific code applies yet.
    Unknown,
    /// Attempted to start tracing while another session runs.
    AlreadyTracing,
    /// Requested trace directory exists but is not a directory.
    TraceDirectoryConflict,
    /// Failed to create the trace directory due to IO errors.
    TraceDirectoryCreateFailed,
    /// User requested an unsupported trace format.
    UnsupportedFormat,
    /// Introspection of positional arguments failed.
    MissingPositionalArgument,
    /// Introspection of keyword arguments failed.
    MissingKeywordArgument,
    /// Failed to resolve frame locals or metadata.
    FrameIntrospectionFailed,
    /// Failed to resolve frame globals during introspection.
    GlobalsIntrospectionFailed,
    /// Attempted to install multiple tracers simultaneously.
    TracerInstallConflict,
    /// General IO failure propagated from lower layers.
    Io,
    /// Invalid runtime policy configuration value.
    InvalidPolicyValue,
    /// Recorder was configured to require a trace but none was produced.
    TraceMissing,
    /// Recorder stopped early leaving partial trace artefacts behind.
    TraceIncomplete,
}

impl ErrorCode {
    /// Stable identifier string for this error code.
    ///
    /// # Examples
    ///
    /// ```
    /// use recorder_errors::ErrorCode;
    ///
    /// assert_eq!(ErrorCode::Io.as_str(), "ERR_IO");
    /// ```
    pub const fn as_str(self) -> &'static str {
        match self {
            ErrorCode::Unknown => "ERR_UNKNOWN",
            ErrorCode::AlreadyTracing => "ERR_ALREADY_TRACING",
            ErrorCode::TraceDirectoryConflict => "ERR_TRACE_DIR_CONFLICT",
            ErrorCode::TraceDirectoryCreateFailed => "ERR_TRACE_DIR_CREATE_FAILED",
            ErrorCode::UnsupportedFormat => "ERR_UNSUPPORTED_FORMAT",
            ErrorCode::MissingPositionalArgument => "ERR_MISSING_POSITIONAL_ARG",
            ErrorCode::MissingKeywordArgument => "ERR_MISSING_KEYWORD_ARG",
            ErrorCode::FrameIntrospectionFailed => "ERR_FRAME_INTROSPECTION_FAILED",
            ErrorCode::GlobalsIntrospectionFailed => "ERR_GLOBALS_INTROSPECTION_FAILED",
            ErrorCode::TracerInstallConflict => "ERR_TRACER_INSTALL_CONFLICT",
            ErrorCode::Io => "ERR_IO",
            ErrorCode::InvalidPolicyValue => "ERR_INVALID_POLICY_VALUE",
            ErrorCode::TraceMissing => "ERR_TRACE_MISSING",
            ErrorCode::TraceIncomplete => "ERR_TRACE_INCOMPLETE",
        }
    }

    /// Parse a string representation (e.g. `ERR_TRACE_MISSING`) back into an `ErrorCode`.
    ///
    /// # Examples
    ///
    /// ```
    /// use recorder_errors::ErrorCode;
    ///
    /// let parsed = ErrorCode::parse("ERR_TRACE_INCOMPLETE");
    /// assert_eq!(parsed, Some(ErrorCode::TraceIncomplete));
    /// assert!(ErrorCode::parse("ERR_UNKNOWN_CODE").is_none());
    /// ```
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "ERR_UNKNOWN" => Some(ErrorCode::Unknown),
            "ERR_ALREADY_TRACING" => Some(ErrorCode::AlreadyTracing),
            "ERR_TRACE_DIR_CONFLICT" => Some(ErrorCode::TraceDirectoryConflict),
            "ERR_TRACE_DIR_CREATE_FAILED" => Some(ErrorCode::TraceDirectoryCreateFailed),
            "ERR_UNSUPPORTED_FORMAT" => Some(ErrorCode::UnsupportedFormat),
            "ERR_MISSING_POSITIONAL_ARG" => Some(ErrorCode::MissingPositionalArgument),
            "ERR_MISSING_KEYWORD_ARG" => Some(ErrorCode::MissingKeywordArgument),
            "ERR_FRAME_INTROSPECTION_FAILED" => Some(ErrorCode::FrameIntrospectionFailed),
            "ERR_GLOBALS_INTROSPECTION_FAILED" => Some(ErrorCode::GlobalsIntrospectionFailed),
            "ERR_TRACER_INSTALL_CONFLICT" => Some(ErrorCode::TracerInstallConflict),
            "ERR_IO" => Some(ErrorCode::Io),
            "ERR_INVALID_POLICY_VALUE" => Some(ErrorCode::InvalidPolicyValue),
            "ERR_TRACE_MISSING" => Some(ErrorCode::TraceMissing),
            "ERR_TRACE_INCOMPLETE" => Some(ErrorCode::TraceIncomplete),
            _ => None,
        }
    }
}

impl fmt::Display for ErrorCode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Canonical error type flowing through the recorder workspace.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
///
/// let err = RecorderError::new(
///     ErrorKind::Environment,
///     ErrorCode::Io,
///     "failed to create trace directory",
/// )
/// .with_context("path", "/tmp/trace")
/// .with_message("unable to prepare trace output");
///
/// assert_eq!(err.message(), "unable to prepare trace output");
/// assert_eq!(err.context.get("path"), Some(&"/tmp/trace".to_owned()));
/// ```
#[derive(Debug)]
pub struct RecorderError {
    pub kind: ErrorKind,
    pub code: ErrorCode,
    pub message: Cow<'static, str>,
    pub context: ContextMap,
    source: Option<Box<dyn StdError + Send + Sync + 'static>>,
}

impl RecorderError {
    /// Create a new error with the provided classification and message.
    ///
    /// # Examples
    ///
    /// ```
    /// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
    ///
    /// let err = RecorderError::new(
    ///     ErrorKind::Usage,
    ///     ErrorCode::UnsupportedFormat,
    ///     "format must be json",
    /// );
    /// assert_eq!(err.code, ErrorCode::UnsupportedFormat);
    /// ```
    pub fn new(kind: ErrorKind, code: ErrorCode, message: impl Into<Cow<'static, str>>) -> Self {
        Self {
            kind,
            code,
            message: message.into(),
            context: ContextMap::new(),
            source: None,
        }
    }

    /// Attach a context key/value pair to the error.
    ///
    /// # Examples
    ///
    /// ```
    /// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
    ///
    /// let err = RecorderError::new(ErrorKind::Target, ErrorCode::TraceIncomplete, "failed")
    ///     .with_context("function", "process_event");
    /// assert_eq!(err.context.get("function"), Some(&"process_event".to_owned()));
    /// ```
    pub fn with_context(mut self, key: &'static str, value: impl Into<String>) -> Self {
        self.context.insert(key, value.into());
        self
    }

    /// Attach an underlying error source.
    ///
    /// # Examples
    ///
    /// ```
    /// use std::io;
    /// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
    ///
    /// let io_err = io::Error::new(io::ErrorKind::Other, "disk full");
    /// let err = RecorderError::new(ErrorKind::Environment, ErrorCode::Io, "write failed")
    ///     .with_source(io_err);
    /// assert!(err.source_ref().is_some());
    /// ```
    pub fn with_source<E>(mut self, source: E) -> Self
    where
        E: StdError + Send + Sync + 'static,
    {
        self.source = Some(Box::new(source));
        self
    }

    /// Update the error message while retaining classification and metadata.
    ///
    /// # Examples
    ///
    /// ```
    /// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
    ///
    /// let err = RecorderError::new(ErrorKind::Usage, ErrorCode::TraceMissing, "not found")
    ///     .with_message("trace is required");
    /// assert_eq!(err.message(), "trace is required");
    /// ```
    pub fn with_message(mut self, message: impl Into<Cow<'static, str>>) -> Self {
        self.message = message.into();
        self
    }

    /// Borrow the primary human-readable message.
    ///
    /// # Examples
    ///
    /// ```
    /// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
    ///
    /// let err = RecorderError::new(ErrorKind::Usage, ErrorCode::MissingKeywordArgument, "missing");
    /// assert_eq!(err.message(), "missing");
    /// ```
    pub fn message(&self) -> &str {
        self.message.as_ref()
    }

    /// Borrow the optional underlying source.
    ///
    /// # Examples
    ///
    /// ```
    /// use std::io;
    /// use recorder_errors::{ErrorCode, ErrorKind, RecorderError};
    ///
    /// let io_err = io::Error::new(io::ErrorKind::Other, "network down");
    /// let err = RecorderError::new(ErrorKind::Environment, ErrorCode::Io, "request failed")
    ///     .with_source(io_err);
    /// assert!(err.source_ref().is_some());
    /// ```
    pub fn source_ref(&self) -> Option<&(dyn StdError + Send + Sync + 'static)> {
        self.source.as_deref()
    }
}

impl fmt::Display for RecorderError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl StdError for RecorderError {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.source
            .as_deref()
            .map(|err| err as &(dyn StdError + 'static))
    }
}

impl From<io::Error> for RecorderError {
    /// Convert an `io::Error` into a recorder error with `ErrorKind::Environment`.
    ///
    /// # Examples
    ///
    /// ```
    /// use std::io;
    /// use recorder_errors::{ErrorCode, RecorderError};
    ///
    /// let io_err = io::Error::new(io::ErrorKind::Other, "disk full");
    /// let err: RecorderError = io_err.into();
    /// assert_eq!(err.code, ErrorCode::Io);
    /// ```
    fn from(err: io::Error) -> Self {
        RecorderError::new(ErrorKind::Environment, ErrorCode::Io, err.to_string()).with_source(err)
    }
}

/// Declare a recorder error using formatting syntax.
///
/// # Examples
///
/// ```
/// let err = recorder_errors::recorder_error!(
///     recorder_errors::ErrorKind::Usage,
///     recorder_errors::ErrorCode::UnsupportedFormat,
///     "format not supported",
/// );
/// assert_eq!(err.code, recorder_errors::ErrorCode::UnsupportedFormat);
/// ```
#[macro_export]
macro_rules! recorder_error {
    ($kind:expr, $code:expr, $msg:literal $(,)?) => {
        $crate::RecorderError::new($kind, $code, $msg)
    };
    ($kind:expr, $code:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::RecorderError::new($kind, $code, ::std::borrow::Cow::Owned(format!($fmt, $($arg)+)))
    };
}

/// Convenience macro for usage errors.
///
/// # Examples
///
/// ```
/// let err = recorder_errors::usage!(
///     recorder_errors::ErrorCode::MissingPositionalArgument,
///     "argument missing",
/// );
/// assert_eq!(err.kind, recorder_errors::ErrorKind::Usage);
/// ```
#[macro_export]
macro_rules! usage {
    ($code:expr, $msg:literal $(,)?) => {
        $crate::recorder_error!($crate::ErrorKind::Usage, $code, $msg)
    };
    ($code:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::recorder_error!($crate::ErrorKind::Usage, $code, $fmt, $($arg)+)
    };
}

/// Convenience macro for environment/IO errors.
///
/// # Examples
///
/// ```
/// let err = recorder_errors::enverr!(
///     recorder_errors::ErrorCode::Io,
///     "failed to write",
/// );
/// assert_eq!(err.kind, recorder_errors::ErrorKind::Environment);
/// ```
#[macro_export]
macro_rules! enverr {
    ($code:expr, $msg:literal $(,)?) => {
        $crate::recorder_error!($crate::ErrorKind::Environment, $code, $msg)
    };
    ($code:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::recorder_error!($crate::ErrorKind::Environment, $code, $fmt, $($arg)+)
    };
}

/// Convenience macro for target errors.
///
/// # Examples
///
/// ```
/// let err = recorder_errors::target!(
///     recorder_errors::ErrorCode::TraceIncomplete,
///     "target raised",
/// );
/// assert_eq!(err.kind, recorder_errors::ErrorKind::Target);
/// ```
#[macro_export]
macro_rules! target {
    ($code:expr, $msg:literal $(,)?) => {
        $crate::recorder_error!($crate::ErrorKind::Target, $code, $msg)
    };
    ($code:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::recorder_error!($crate::ErrorKind::Target, $code, $fmt, $($arg)+)
    };
}

/// Convenience macro for internal bugs/invariants.
///
/// # Examples
///
/// ```
/// let err = recorder_errors::bug!(
///     recorder_errors::ErrorCode::TraceIncomplete,
///     "unexpected state",
/// );
/// assert_eq!(err.kind, recorder_errors::ErrorKind::Internal);
/// ```
#[macro_export]
macro_rules! bug {
    ($code:expr, $msg:literal $(,)?) => {
        $crate::recorder_error!($crate::ErrorKind::Internal, $code, $msg)
    };
    ($code:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::recorder_error!($crate::ErrorKind::Internal, $code, $fmt, $($arg)+)
    };
}

/// Ensure a predicate holds, returning a usage error when it does not.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ErrorCode, RecorderResult};
///
/// fn guard(active: bool) -> RecorderResult<()> {
///     recorder_errors::ensure_usage!(active, ErrorCode::AlreadyTracing, "already tracing");
///     Ok(())
/// }
///
/// assert!(guard(true).is_ok());
/// assert_eq!(guard(false).unwrap_err().code, ErrorCode::AlreadyTracing);
/// ```
#[macro_export]
macro_rules! ensure_usage {
    ($cond:expr, $code:expr, $msg:literal $(,)?) => {
        if !$cond {
            return Err($crate::usage!($code, $msg));
        }
    };
    ($cond:expr, $code:expr, $fmt:expr, $($arg:tt)+) => {
        if !$cond {
            return Err($crate::usage!($code, $fmt, $($arg)+));
        }
    };
}

/// Ensure a predicate holds, returning an environment error when it does not.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ErrorCode, RecorderResult};
///
/// fn guard(io_ready: bool) -> RecorderResult<()> {
///     recorder_errors::ensure_env!(io_ready, ErrorCode::Io, "io failure");
///     Ok(())
/// }
///
/// assert!(guard(true).is_ok());
/// assert_eq!(guard(false).unwrap_err().code, ErrorCode::Io);
/// ```
#[macro_export]
macro_rules! ensure_env {
    ($cond:expr, $code:expr, $msg:literal $(,)?) => {
        if !$cond {
            return Err($crate::enverr!($code, $msg));
        }
    };
    ($cond:expr, $code:expr, $fmt:expr, $($arg:tt)+) => {
        if !$cond {
            return Err($crate::enverr!($code, $fmt, $($arg)+));
        }
    };
}

/// Ensure a predicate holds, returning an internal bug otherwise.
///
/// # Examples
///
/// ```
/// use recorder_errors::{ErrorCode, RecorderResult};
///
/// fn guard(invariant_ok: bool) -> RecorderResult<()> {
///     recorder_errors::ensure_internal!(invariant_ok, ErrorCode::TraceIncomplete, "corrupted state");
///     Ok(())
/// }
///
/// assert!(guard(true).is_ok());
/// assert_eq!(guard(false).unwrap_err().kind, recorder_errors::ErrorKind::Internal);
/// ```
#[macro_export]
macro_rules! ensure_internal {
    ($cond:expr, $code:expr, $msg:literal $(,)?) => {
        if !$cond {
            return Err($crate::bug!($code, $msg));
        }
    };
    ($cond:expr, $code:expr, $fmt:expr, $($arg:tt)+) => {
        if !$cond {
            return Err($crate::bug!($code, $fmt, $($arg)+));
        }
    };
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn usage_macro_builds_error() {
        let err = usage!(ErrorCode::UnsupportedFormat, "unsupported");
        assert_eq!(err.kind, ErrorKind::Usage);
        assert_eq!(err.code, ErrorCode::UnsupportedFormat);
        assert_eq!(err.message, "unsupported");
    }

    #[test]
    fn ensure_usage_fails() -> RecorderResult<()> {
        fn guarded(value: bool) -> RecorderResult<()> {
            ensure_usage!(value, ErrorCode::AlreadyTracing, "still tracing");
            Ok(())
        }

        let failure = guarded(false).expect_err("guard should fail");
        assert_eq!(failure.kind, ErrorKind::Usage);
        assert_eq!(failure.code, ErrorCode::AlreadyTracing);
        guarded(true)?;
        Ok(())
    }

    #[test]
    fn context_and_source_roundtrip() {
        let io_err = io::Error::new(io::ErrorKind::Other, "disk full");
        let err = RecorderError::from(io_err)
            .with_context("path", "/tmp/out")
            .with_message("failed to write trace");
        assert_eq!(err.kind, ErrorKind::Environment);
        assert_eq!(err.code, ErrorCode::Io);
        assert_eq!(err.context.get("path"), Some(&"/tmp/out".to_string()));
        assert_eq!(err.to_string(), "failed to write trace");
        assert!(err.source_ref().is_some());
    }

    #[test]
    fn ensure_env_reports_environment() {
        fn guarded(value: bool) -> RecorderResult<()> {
            ensure_env!(value, ErrorCode::TraceDirectoryCreateFailed, "io failure");
            Ok(())
        }

        let err = guarded(false).expect_err("should fail");
        assert_eq!(err.kind, ErrorKind::Environment);
        assert_eq!(err.code, ErrorCode::TraceDirectoryCreateFailed);
    }

    #[test]
    fn bug_macro_marks_internal() {
        let err = bug!(ErrorCode::FrameIntrospectionFailed, "panic avoided");
        assert_eq!(err.kind, ErrorKind::Internal);
        assert_eq!(err.code, ErrorCode::FrameIntrospectionFailed);
    }

    #[test]
    fn target_macro_marks_target_error() {
        let err = target!(ErrorCode::TraceIncomplete, "target callback failed");
        assert_eq!(err.kind, ErrorKind::Target);
        assert_eq!(err.code, ErrorCode::TraceIncomplete);
    }

    #[test]
    fn ensure_internal_marks_internal_failures() {
        fn guarded(assert_ok: bool) -> RecorderResult<()> {
            ensure_internal!(assert_ok, ErrorCode::TraceIncomplete, "invariant broken");
            Ok(())
        }

        let err = guarded(false).expect_err("expected invariant failure");
        assert_eq!(err.kind, ErrorKind::Internal);
        assert_eq!(err.code, ErrorCode::TraceIncomplete);
        guarded(true).expect("guarded success");
    }

    #[test]
    fn parse_roundtrip_matches_known_codes() {
        for code in [
            ErrorCode::Unknown,
            ErrorCode::AlreadyTracing,
            ErrorCode::TraceDirectoryConflict,
            ErrorCode::TraceDirectoryCreateFailed,
            ErrorCode::UnsupportedFormat,
            ErrorCode::MissingPositionalArgument,
            ErrorCode::MissingKeywordArgument,
            ErrorCode::FrameIntrospectionFailed,
            ErrorCode::GlobalsIntrospectionFailed,
            ErrorCode::TracerInstallConflict,
            ErrorCode::Io,
            ErrorCode::InvalidPolicyValue,
            ErrorCode::TraceMissing,
            ErrorCode::TraceIncomplete,
        ] {
            let code_str = code.as_str();
            assert_eq!(ErrorCode::parse(code_str), Some(code));
        }
        assert_eq!(ErrorCode::parse("ERR_NOT_REAL"), None);
    }
}
