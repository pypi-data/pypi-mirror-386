use std::env::consts::EXE_EXTENSION;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use anyhow::{Context, Result};
use tracing::{debug, trace};

use constants::env_vars::EnvVars;

use crate::cli::reporter::HookInstallReporter;
use crate::hook::InstalledHook;
use crate::hook::{Hook, InstallInfo};
use crate::languages::LanguageImpl;
use crate::languages::python::PythonRequest;
use crate::languages::python::uv::Uv;
use crate::languages::version::LanguageRequest;
use crate::process;
use crate::process::Cmd;
use crate::run::{prepend_paths, run_by_batch};
use crate::store::{Store, ToolBucket};

#[derive(Debug, Copy, Clone)]
pub(crate) struct Python;

pub(crate) struct PythonInfo {
    pub(crate) version: semver::Version,
    pub(crate) python_exec: PathBuf,
}

pub(crate) async fn query_python_info(python: &Path) -> Result<PythonInfo> {
    static QUERY_PYTHON_INFO: &str = indoc::indoc! {r#"
    import sys
    print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(sys.base_exec_prefix)
    "#};

    let stdout = Cmd::new(python, "python -c")
        .arg("-I")
        .arg("-c")
        .arg(QUERY_PYTHON_INFO)
        .check(true)
        .output()
        .await?
        .stdout;

    let stdout = String::from_utf8(stdout).context("Failed to parse Python info output")?;
    let mut lines = stdout.lines();
    let version = lines
        .next()
        .context("Failed to get Python version")?
        .to_string()
        .parse()
        .context("Failed to parse Python version")?;
    let base_exec_prefix = lines
        .next()
        .context("Failed to get Python base_exec_prefix")?
        .to_string();
    let python_exec = python_exec(Path::new(&base_exec_prefix));

    Ok(PythonInfo {
        version,
        python_exec,
    })
}

impl LanguageImpl for Python {
    async fn install(
        &self,
        hook: Arc<Hook>,
        store: &Store,
        reporter: &HookInstallReporter,
    ) -> Result<InstalledHook> {
        let progress = reporter.on_install_start(&hook);

        let uv_dir = store.tools_path(ToolBucket::Uv);
        let uv = Uv::install(store, &uv_dir)
            .await
            .context("Failed to install uv")?;

        let mut info = InstallInfo::new(
            hook.language,
            hook.dependencies().clone(),
            &store.hooks_dir(),
        )?;

        debug!(%hook, target = %info.env_path.display(), "Installing environment");

        // Create venv (auto download Python if needed)
        Self::create_venv(&uv, store, &info, &hook.language_request)
            .await
            .context("Failed to create Python virtual environment")?;

        // Install dependencies
        if let Some(repo_path) = hook.repo_path() {
            trace!(
                "Installing dependencies from repo path: {}",
                repo_path.display()
            );
            uv.cmd("uv pip install", store)
                .arg("pip")
                .arg("install")
                .arg(".")
                .args(&hook.additional_dependencies)
                .current_dir(repo_path)
                .env("VIRTUAL_ENV", &info.env_path)
                .check(true)
                .output()
                .await?;
        } else if !hook.additional_dependencies.is_empty() {
            trace!("Installing additional dependencies for local hook");
            uv.cmd("uv pip install", store)
                .arg("pip")
                .arg("install")
                .args(&hook.additional_dependencies)
                .env("VIRTUAL_ENV", &info.env_path)
                .check(true)
                .output()
                .await?;
        } else {
            debug!("No additional dependencies to install");
        }

        let python = python_exec(&info.env_path);
        let python_info = query_python_info(&python)
            .await
            .context("Failed to query Python info")?;

        info.with_language_version(python_info.version)
            .with_toolchain(python_info.python_exec);

        reporter.on_install_complete(progress);

        Ok(InstalledHook::Installed {
            hook,
            info: Arc::new(info),
        })
    }

    async fn check_health(&self, info: &InstallInfo) -> Result<()> {
        let python = python_exec(&info.env_path);
        let python_info = query_python_info(&python)
            .await
            .context("Failed to query Python info")?;

        if python_info.version != info.language_version {
            anyhow::bail!(
                "Python version mismatch: expected {}, found {}",
                info.language_version,
                python_info.version
            );
        }

        if python_info.python_exec != info.toolchain {
            anyhow::bail!(
                "Python executable mismatch: expected {}, found {}",
                info.toolchain.display(),
                python_info.python_exec.display()
            );
        }

        Ok(())
    }

    async fn run(
        &self,
        hook: &InstalledHook,
        filenames: &[&Path],
        _store: &Store,
    ) -> Result<(i32, Vec<u8>)> {
        let env_dir = hook.env_path().expect("Python must have env path");
        let new_path = prepend_paths(&[&bin_dir(env_dir)]).context("Failed to join PATH")?;
        let entry = hook.entry.resolve(Some(&new_path))?;

        let run = async move |batch: &[&Path]| {
            let mut output = Cmd::new(&entry[0], "python hook")
                .current_dir(hook.work_dir())
                .args(&entry[1..])
                .env("VIRTUAL_ENV", env_dir)
                .env("PATH", &new_path)
                .env_remove("PYTHONHOME")
                .args(&hook.args)
                .args(batch)
                .check(false)
                .pty_output()
                .await?;

            output.stdout.extend(output.stderr);
            let code = output.status.code().unwrap_or(1);
            anyhow::Ok((code, output.stdout))
        };

        let results = run_by_batch(hook, filenames, run).await?;

        // Collect results
        let mut combined_status = 0;
        let mut combined_output = Vec::new();

        for (code, output) in results {
            combined_status |= code;
            combined_output.extend(output);
        }

        Ok((combined_status, combined_output))
    }
}

fn to_uv_python_request(request: &LanguageRequest) -> Option<String> {
    match request {
        LanguageRequest::Any { .. } => None,
        LanguageRequest::Python(request) => match request {
            PythonRequest::Any => None,
            PythonRequest::Major(major) => Some(format!("{major}")),
            PythonRequest::MajorMinor(major, minor) => Some(format!("{major}.{minor}")),
            PythonRequest::MajorMinorPatch(major, minor, patch) => {
                Some(format!("{major}.{minor}.{patch}"))
            }
            PythonRequest::Range(_, raw) => Some(raw.clone()),
            PythonRequest::Path(path) => Some(path.to_string_lossy().to_string()),
        },
        _ => unreachable!(),
    }
}

impl Python {
    async fn create_venv(
        uv: &Uv,
        store: &Store,
        info: &InstallInfo,
        python_request: &LanguageRequest,
    ) -> Result<()> {
        // Try creating venv without downloads first
        match Self::create_venv_command(uv, store, info, python_request, false, false)
            .check(true)
            .output()
            .await
        {
            Ok(_) => {
                debug!(
                    "Venv created successfully with no downloads: `{}`",
                    info.env_path.display()
                );
                Ok(())
            }
            Err(e @ process::Error::Status { .. }) => {
                // Check if we can retry with downloads
                if Self::can_retry_with_downloads(&e) {
                    if !python_request.allows_download() {
                        anyhow::bail!(
                            "No suitable system Python version found and downloads are disabled"
                        );
                    }

                    debug!(
                        "Retrying venv creation with managed Python downloads: `{}`",
                        info.env_path.display()
                    );
                    Self::create_venv_command(uv, store, info, python_request, true, true)
                        .check(true)
                        .output()
                        .await?;
                    return Ok(());
                }
                // If we can't retry, return the original error
                Err(e.into())
            }
            Err(e) => {
                debug!("Failed to create venv `{}`: {e}", info.env_path.display());
                Err(e.into())
            }
        }
    }

    fn create_venv_command(
        uv: &Uv,
        store: &Store,
        info: &InstallInfo,
        python_request: &LanguageRequest,
        set_install_dir: bool,
        allow_downloads: bool,
    ) -> Cmd {
        let mut cmd = uv.cmd("create venv", store);
        cmd.arg("venv")
            .arg(&info.env_path)
            .arg("--python-preference")
            .arg("managed")
            .arg("--no-project")
            .arg("--no-config")
            // `--managed_python` conflicts with `--python-preference`, ignore any user setting
            .env_remove(EnvVars::UV_MANAGED_PYTHON)
            .env_remove(EnvVars::UV_NO_MANAGED_PYTHON);

        if set_install_dir {
            cmd.env(
                EnvVars::UV_PYTHON_INSTALL_DIR,
                store.tools_path(ToolBucket::Python),
            );
        }
        if allow_downloads {
            cmd.arg("--allow-python-downloads");
        } else {
            cmd.arg("--no-python-downloads");
        }

        if let Some(python) = to_uv_python_request(python_request) {
            cmd.arg("--python").arg(python);
        }

        cmd
    }

    fn can_retry_with_downloads(error: &process::Error) -> bool {
        let process::Error::Status {
            error:
                process::StatusError {
                    output: Some(output),
                    ..
                },
            ..
        } = error
        else {
            return false;
        };

        let stderr = String::from_utf8_lossy(&output.stderr);
        stderr.contains("A managed Python download is available")
    }
}

fn bin_dir(venv: &Path) -> PathBuf {
    if cfg!(windows) {
        venv.join("Scripts")
    } else {
        venv.join("bin")
    }
}

pub(crate) fn python_exec(venv: &Path) -> PathBuf {
    bin_dir(venv).join("python").with_extension(EXE_EXTENSION)
}
