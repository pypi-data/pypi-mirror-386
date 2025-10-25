// Copyright (c) 2023 Axo Developer Co.
//
// Permission is hereby granted, free of charge, to any
// person obtaining a copy of this software and associated
// documentation files (the "Software"), to deal in the
// Software without restriction, including without
// limitation the rights to use, copy, modify, merge,
// publish, distribute, sublicense, and/or sell copies of
// the Software, and to permit persons to whom the Software
// is furnished to do so, subject to the following
// conditions:
//
// The above copyright notice and this permission notice
// shall be included in all copies or substantial portions
// of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
// ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
// TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
// SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
// CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
// IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
// DEALINGS IN THE SOFTWARE.

/// Adapt [axoprocess] to use [`tokio::process::Process`] instead of [`std::process::Command`].
use std::fmt::Display;
use std::process::Output;
use std::{
    ffi::OsStr,
    path::Path,
    process::{CommandArgs, CommandEnvs, ExitStatus, Stdio},
};

use owo_colors::OwoColorize;
use thiserror::Error;
use tracing::trace;

use crate::git::GIT;

/// An error from executing a Command
#[derive(Debug, Error)]
pub enum Error {
    /// The command fundamentally failed to execute (usually means it didn't exist)
    #[error("run command `{summary}` failed")]
    Exec {
        /// Summary of what the Command was trying to do
        summary: String,
        /// What failed
        #[source]
        cause: std::io::Error,
    },
    #[error("command `{summary}` exited with an error:\n{error}")]
    Status { summary: String, error: StatusError },
    #[cfg(not(windows))]
    #[error("failed to open pty")]
    Pty(#[from] pty::Error),
    #[error("failed to setup subprocess for pty")]
    PtySetup(#[from] std::io::Error),
}

/// The command ran but signaled some kind of error condition
/// (assuming the exit code is used for that)
#[derive(Debug)]
pub struct StatusError {
    pub status: ExitStatus,
    pub output: Option<Output>,
}

impl Display for StatusError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "\n{}\n{}", "[status]".red(), self.status)?;

        if let Some(output) = &self.output {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let stderr = String::from_utf8_lossy(&output.stderr);
            let stdout = stdout
                .split('\n')
                .filter_map(|line| {
                    let line = line.trim();
                    if line.is_empty() { None } else { Some(line) }
                })
                .collect::<Vec<_>>();
            let stderr = stderr
                .split('\n')
                .filter_map(|line| {
                    let line = line.trim();
                    if line.is_empty() { None } else { Some(line) }
                })
                .collect::<Vec<_>>();

            if !stdout.is_empty() {
                writeln!(f, "\n{}\n{}", "[stdout]".red(), stdout.join("\n"))?;
            }
            if !stderr.is_empty() {
                writeln!(f, "\n{}\n{}", "[stderr]".red(), stderr.join("\n"))?;
            }
        }

        Ok(())
    }
}

/// A fancier Command, see the crate's top-level docs!
pub struct Cmd {
    /// The inner Command, in case you need to access it
    pub inner: tokio::process::Command,
    summary: String,
    check_status: bool,
}

/// Constructors
impl Cmd {
    /// Create a new Command with an additional "summary" of what this is trying to do
    pub fn new(command: impl AsRef<OsStr>, summary: impl Into<String>) -> Self {
        let inner = tokio::process::Command::new(command);
        Self {
            summary: summary.into(),
            inner,
            check_status: true,
        }
    }
}

/// Builder APIs
impl Cmd {
    /// Pipe stdout into stderr
    ///
    /// This is useful for cases where you want your program to livestream
    /// the output of a command to give your user realtime feedback, but the command
    /// randomly writes some things to stdout, and you don't want your own stdout tainted.
    pub fn stdout_to_stderr(&mut self) -> &mut Self {
        self.inner.stdout(std::io::stderr());

        self
    }

    /// Set whether `Status::success` should be checked after executions
    /// (except `spawn`, which doesn't yet have a Status to check).
    ///
    /// Defaults to `true`.
    ///
    /// If true, an Err will be produced by those execution commands.
    ///
    /// Executions which produce status will pass them to [`Cmd::maybe_check_status`][],
    /// which uses this setting.
    pub fn check(&mut self, checked: bool) -> &mut Self {
        self.check_status = checked;
        self
    }
}

/// Execution APIs
impl Cmd {
    /// Equivalent to [`Cmd::status`][],
    /// but doesn't bother returning the actual status code (because it's captured in the Result)
    pub async fn run(&mut self) -> Result<(), Error> {
        self.status().await?;
        Ok(())
    }

    /// Equivalent to [`std::process::Command::spawn`][],
    /// but logged and with the error wrapped.
    pub fn spawn(&mut self) -> Result<tokio::process::Child, Error> {
        self.log_command();
        self.inner.spawn().map_err(|cause| Error::Exec {
            summary: self.summary.clone(),
            cause,
        })
    }

    /// Equivalent to [`std::process::Command::output`][],
    /// but logged, with the error wrapped, and status checked (by default)
    pub async fn output(&mut self) -> Result<Output, Error> {
        self.log_command();
        let output = self.inner.output().await.map_err(|cause| Error::Exec {
            summary: self.summary.clone(),
            cause,
        })?;
        self.maybe_check_output(&output)?;
        Ok(output)
    }

    #[cfg(windows)]
    pub async fn pty_output(&mut self) -> Result<Output, Error> {
        return self.output().await;
    }

    #[cfg(not(windows))]
    pub async fn pty_output(&mut self) -> Result<Output, Error> {
        use tokio::io::AsyncReadExt;

        // If color is not used, fallback to piped output.
        if !*crate::run::USE_COLOR {
            return self.output().await;
        }

        let (mut pty, pts) = pty::open()?;
        let (stdin, stdout, stderr) = pts.setup_subprocess()?;

        self.inner.stdin(stdin);
        self.inner.stdout(stdout);
        self.inner.stderr(stderr);

        let session_leader = pts.session_leader();
        unsafe { self.inner.pre_exec(session_leader) };

        let mut child = self.spawn()?;

        let mut stdout = Vec::new();
        let mut buffer = [0u8; 4096];

        let status = loop {
            tokio::select! {
                read_result = pty.read(&mut buffer) => {
                    match read_result {
                        Ok(0) => {
                            // EOF from PTY, child should be done
                            break child.wait().await?;
                        }
                        Ok(n) => {
                            stdout.extend_from_slice(&buffer[..n]);
                        }
                        Err(e) => {
                            // PTY error, try to get child status
                            if let Ok(Some(status)) = child.try_wait() {
                                break status;
                            }
                            return Err(Error::PtySetup(e));
                        }
                    }
                }
                status = child.wait() => {
                    let status = status?;
                    // On linux, after child exited, the pty `AsyncFd.poll_read_ready` will hang immediately.
                    // Don't know why, so commenting this out for now.

                    // Child finished, do one final read to get any remaining output
                    // loop {
                    //     match pty.read(&mut buffer).await {
                    //         Ok(0) => break, // EOF
                    //         Ok(n) => stdout.extend_from_slice(&buffer[..n]),
                    //         Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => break,
                    //         Err(_) => break, // Other errors, stop reading
                    //     }
                    // }
                    break status;
                }
            }
        };

        child.stdin.take();
        child.stdout.take();
        child.stderr.take();

        let output = Output {
            status,
            stdout,
            stderr: Vec::new(),
        };

        self.maybe_check_output(&output)?;
        Ok(output)
    }

    /// Equivalent to [`std::process::Command::status`][]
    /// but logged, with the error wrapped, and status checked (by default)
    pub async fn status(&mut self) -> Result<ExitStatus, Error> {
        self.log_command();
        let status = self.inner.status().await.map_err(|cause| Error::Exec {
            summary: self.summary.clone(),
            cause,
        })?;
        self.maybe_check_status(status)?;
        Ok(status)
    }
}

/// Transparently forwarded [`std::process::Command`][] APIs
impl Cmd {
    /// Forwards to [`std::process::Command::arg`][]
    pub fn arg<S: AsRef<OsStr>>(&mut self, arg: S) -> &mut Self {
        self.inner.arg(arg);
        self
    }

    /// Forwards to [`std::process::Command::args`][]
    pub fn args<I, S>(&mut self, args: I) -> &mut Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<OsStr>,
    {
        self.inner.args(args);
        self
    }

    /// Forwards to [`std::process::Command::env`][]
    pub fn env<K, V>(&mut self, key: K, val: V) -> &mut Self
    where
        K: AsRef<OsStr>,
        V: AsRef<OsStr>,
    {
        self.inner.env(key, val);
        self
    }

    /// Forwards to [`std::process::Command::envs`][]
    pub fn envs<I, K, V>(&mut self, vars: I) -> &mut Self
    where
        I: IntoIterator<Item = (K, V)>,
        K: AsRef<OsStr>,
        V: AsRef<OsStr>,
    {
        self.inner.envs(vars);
        self
    }

    /// Forwards to [`std::process::Command::env_remove`][]
    pub fn env_remove<K: AsRef<OsStr>>(&mut self, key: K) -> &mut Self {
        self.inner.env_remove(key);
        self
    }

    /// Forwards to [`std::process::Command::env_clear`][]
    pub fn env_clear(&mut self) -> &mut Self {
        self.inner.env_clear();
        self
    }

    /// Forwards to [`std::process::Command::current_dir`][]
    pub fn current_dir<P: AsRef<Path>>(&mut self, dir: P) -> &mut Self {
        self.inner.current_dir(dir);
        self
    }

    /// Forwards to [`std::process::Command::stdin`][]
    pub fn stdin<T: Into<Stdio>>(&mut self, cfg: T) -> &mut Self {
        self.inner.stdin(cfg);
        self
    }

    /// Forwards to [`std::process::Command::stdout`][]
    pub fn stdout<T: Into<Stdio>>(&mut self, cfg: T) -> &mut Self {
        self.inner.stdout(cfg);
        self
    }

    /// Forwards to [`std::process::Command::stderr`][]
    pub fn stderr<T: Into<Stdio>>(&mut self, cfg: T) -> &mut Self {
        self.inner.stderr(cfg);
        self
    }

    /// Forwards to [`std::process::Command::get_program`][]
    pub fn get_program(&self) -> &OsStr {
        self.inner.as_std().get_program()
    }

    /// Forwards to [`std::process::Command::get_args`][]
    pub fn get_args(&self) -> CommandArgs<'_> {
        self.inner.as_std().get_args()
    }

    /// Forwards to [`std::process::Command::get_envs`][]
    pub fn get_envs(&self) -> CommandEnvs<'_> {
        self.inner.as_std().get_envs()
    }

    /// Forwards to [`std::process::Command::get_current_dir`][]
    pub fn get_current_dir(&self) -> Option<&Path> {
        self.inner.as_std().get_current_dir()
    }

    pub fn remove_git_env(&mut self) -> &mut Self {
        for (key, _) in crate::git::GIT_ENV_TO_REMOVE.iter() {
            self.inner.env_remove(key);
        }
        self
    }
}

/// Diagnostic APIs (used internally, but available for yourself)
impl Cmd {
    /// Check `Status::success`, producing a contextual Error if it's `false`.
    pub fn check_status(&self, status: ExitStatus) -> Result<(), Error> {
        if status.success() {
            Ok(())
        } else {
            Err(Error::Status {
                summary: self.summary.clone(),
                error: StatusError {
                    status,
                    output: None,
                },
            })
        }
    }

    pub fn check_output(&self, output: &Output) -> Result<(), Error> {
        if output.status.success() {
            Ok(())
        } else {
            Err(Error::Status {
                summary: self.summary.clone(),
                error: StatusError {
                    status: output.status,
                    output: Some(output.clone()),
                },
            })
        }
    }

    /// Invoke [`Cmd::check_status`][] if [`Cmd::check`][] is `true`
    /// (defaults to `true`).
    pub fn maybe_check_status(&self, status: ExitStatus) -> Result<(), Error> {
        if self.check_status {
            self.check_status(status)?;
        }
        Ok(())
    }

    /// Invoke [`Cmd::check_status`][] if [`Cmd::check`][] is `true`
    /// (defaults to `true`).
    pub fn maybe_check_output(&self, output: &Output) -> Result<(), Error> {
        if self.check_status {
            self.check_output(output)?;
        }
        Ok(())
    }

    /// Log the current Command using the method specified by [`Cmd::log`][]
    /// (defaults to [`tracing::info!`][]).
    pub fn log_command(&self) {
        trace!("Executing `{self}`");
    }
}

/// Returns the number of arguments to skip.
fn skip_args(cmd: &OsStr, cur: &OsStr, next: Option<&&OsStr>) -> usize {
    if GIT.as_ref().is_ok_and(|git| cmd == git) {
        if cur == "-c" {
            if let Some(flag) = next {
                let flag = flag.as_encoded_bytes();
                if flag.starts_with(b"core.useBuiltinFSMonitor")
                    || flag.starts_with(b"protocol.version")
                {
                    return 2;
                }
            }
        } else if cur == "--no-ext-diff"
            || cur == "--no-textconv"
            || cur == "--ignore-submodules"
            || cur == "--no-color"
        {
            return 1;
        }
    }
    0
}

/// Simplified Command Debug output, with args truncated if they're too long.
impl Display for Cmd {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let Some(cwd) = self.get_current_dir() {
            write!(f, "cd {} && ", cwd.to_string_lossy())?;
        }
        let program = self.get_program();
        let mut args = self.get_args().peekable();

        write!(f, "{}", program.to_string_lossy())?;
        if args.peek().is_some_and(|arg| *arg == program) {
            args.next(); // Skip the program if it's repeated
        }

        let mut len = 0;
        while let Some(arg) = args.next() {
            let skip = skip_args(program, arg, args.peek());
            if skip > 0 {
                for _ in 1..skip {
                    args.next();
                }
                continue;
            }
            write!(f, " {}", arg.to_string_lossy())?;
            len += arg.len() + 1;
            if len > 100 {
                write!(f, " [...]",)?;
                break;
            }
        }
        Ok(())
    }
}
