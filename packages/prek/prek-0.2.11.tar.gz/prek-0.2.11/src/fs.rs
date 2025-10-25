// MIT License
//
// Copyright (c) 2023 Astral Software Inc.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

use std::fmt::Display;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;
use tracing::{debug, error, info, trace};

use anyhow::Context;

pub static CWD: LazyLock<PathBuf> =
    LazyLock::new(|| std::env::current_dir().expect("The current directory must be exist"));

/// A file lock that is automatically released when dropped.
#[derive(Debug)]
pub struct LockedFile(fs_err::File);

impl LockedFile {
    /// Inner implementation for [`LockedFile::acquire_blocking`] and [`LockedFile::acquire`].
    fn lock_file_blocking(file: fs_err::File, resource: &str) -> Result<Self, std::io::Error> {
        trace!(
            resource,
            path = %file.path().display(),
            "Checking lock",
        );
        match file.try_lock() {
            Ok(()) => {
                debug!(resource, "Acquired lock");
                Ok(Self(file))
            }
            Err(err) => {
                // Log error code and enum kind to help debugging more exotic failures
                if !matches!(err, std::fs::TryLockError::WouldBlock) {
                    trace!(error = ?err, "Try lock error");
                }
                info!(
                    resource,
                    path = %file.path().display(),
                    "Waiting to acquire lock",
                );
                file.lock().map_err(|err| {
                    // Not a fs_err method, we need to build our own path context
                    std::io::Error::other(format!(
                        "Could not acquire lock for `{resource}` at `{}`: {}",
                        file.path().display(),
                        err
                    ))
                })?;

                trace!(resource, "Acquired lock");
                Ok(Self(file))
            }
        }
    }

    /// Acquire a cross-process lock for a resource using a file at the provided path.
    pub async fn acquire(
        path: impl AsRef<Path>,
        resource: impl Display,
    ) -> Result<Self, std::io::Error> {
        let file = fs_err::File::create(path.as_ref())?;
        let resource = resource.to_string();
        tokio::task::spawn_blocking(move || Self::lock_file_blocking(file, &resource)).await?
    }
}

impl Drop for LockedFile {
    fn drop(&mut self) {
        if let Err(err) = self.0.file().unlock() {
            error!(
                "Failed to unlock {}; program may be stuck: {}",
                self.0.path().display(),
                err
            );
        } else {
            trace!(path = %self.0.path().display(), "Released lock");
        }
    }
}

/// Normalizes a path to use `/` as a separator everywhere, even on platforms
/// that recognize other characters as separators.
#[cfg(unix)]
pub(crate) fn normalize_path(path: PathBuf) -> PathBuf {
    // UNIX only uses /, so we're good.
    path
}

/// Normalizes a path to use `/` as a separator everywhere, even on platforms
/// that recognize other characters as separators.
#[cfg(not(unix))]
pub(crate) fn normalize_path(path: PathBuf) -> PathBuf {
    use std::ffi::OsString;
    use std::path::is_separator;

    let mut path = path.into_os_string().into_encoded_bytes();
    for c in &mut path {
        if *c == b'/' || !is_separator(char::from(*c)) {
            continue;
        }
        *c = b'/';
    }

    let os_str = OsString::from(String::from_utf8_lossy(&path).to_string());
    PathBuf::from(os_str)
}

/// Compute a path describing `path` relative to `base`.
///
/// `lib/python/site-packages/foo/__init__.py` and `lib/python/site-packages` -> `foo/__init__.py`
/// `lib/marker.txt` and `lib/python/site-packages` -> `../../marker.txt`
/// `bin/foo_launcher` and `lib/python/site-packages` -> `../../../bin/foo_launcher`
///
/// Returns `Err` if there is no relative path between `path` and `base` (for example, if the paths
/// are on different drives on Windows).
pub fn relative_to(
    path: impl AsRef<Path>,
    base: impl AsRef<Path>,
) -> Result<PathBuf, std::io::Error> {
    // Find the longest common prefix, and also return the path stripped from that prefix
    let (stripped, common_prefix) = base
        .as_ref()
        .ancestors()
        .find_map(|ancestor| {
            // Simplifying removes the UNC path prefix on windows.
            dunce::simplified(path.as_ref())
                .strip_prefix(dunce::simplified(ancestor))
                .ok()
                .map(|stripped| (stripped, ancestor))
        })
        .ok_or_else(|| {
            std::io::Error::other(format!(
                "Trivial strip failed: {} vs. {}",
                path.as_ref().display(),
                base.as_ref().display()
            ))
        })?;

    // go as many levels up as required
    let levels_up = base.as_ref().components().count() - common_prefix.components().count();
    let up = std::iter::repeat_n("..", levels_up).collect::<PathBuf>();

    Ok(up.join(stripped))
}

pub trait Simplified {
    /// Simplify a [`Path`].
    ///
    /// On Windows, this will strip the `\\?\` prefix from paths. On other platforms, it's a no-op.
    fn simplified(&self) -> &Path;

    /// Render a [`Path`] for display.
    ///
    /// On Windows, this will strip the `\\?\` prefix from paths. On other platforms, it's
    /// equivalent to [`std::path::Display`].
    fn simplified_display(&self) -> impl Display;

    /// Render a [`Path`] for user-facing display.
    ///
    /// Like [`simplified_display`], but relativizes the path against the current working directory.
    fn user_display(&self) -> impl Display;
}

impl<T: AsRef<Path>> Simplified for T {
    fn simplified(&self) -> &Path {
        dunce::simplified(self.as_ref())
    }

    fn simplified_display(&self) -> impl Display {
        dunce::simplified(self.as_ref()).display()
    }

    fn user_display(&self) -> impl Display {
        let path = dunce::simplified(self.as_ref());

        // If current working directory is root, display the path as-is.
        if CWD.ancestors().nth(1).is_none() {
            return path.display();
        }

        // Attempt to strip the current working directory, then the canonicalized current working
        // directory, in case they differ.
        let path = path.strip_prefix(CWD.simplified()).unwrap_or(path);

        path.display()
    }
}

/// Create a symlink or copy the file on Windows.
/// Tries symlink first, falls back to copy if symlink fails.
pub(crate) async fn create_symlink_or_copy(source: &Path, target: &Path) -> anyhow::Result<()> {
    if target.exists() {
        fs_err::tokio::remove_file(target).await?;
    }

    #[cfg(not(windows))]
    {
        // Try symlink on Unix systems
        match fs_err::tokio::symlink(source, target).await {
            Ok(()) => {
                trace!(
                    "Created symlink from {} to {}",
                    source.display(),
                    target.display()
                );
                return Ok(());
            }
            Err(e) => {
                trace!(
                    "Failed to create symlink from {} to {}: {}",
                    source.display(),
                    target.display(),
                    e
                );
            }
        }
    }

    #[cfg(windows)]
    {
        // Try Windows symlink API (requires admin privileges)
        use std::os::windows::fs::symlink_file;
        match symlink_file(source, target) {
            Ok(()) => {
                trace!(
                    "Created Windows symlink from {} to {}",
                    source.display(),
                    target.display()
                );
                return Ok(());
            }
            Err(e) => {
                trace!(
                    "Failed to create Windows symlink from {} to {}: {}",
                    source.display(),
                    target.display(),
                    e
                );
            }
        }
    }

    // Fallback to copy
    trace!(
        "Falling back to copy from {} to {}",
        source.display(),
        target.display()
    );
    fs_err::tokio::copy(source, target).await.with_context(|| {
        format!(
            "Failed to copy file from {} to {}",
            source.display(),
            target.display(),
        )
    })?;

    Ok(())
}

pub(crate) async fn rename_or_copy(source: &Path, target: &Path) -> std::io::Result<()> {
    // Try to rename first
    match fs_err::tokio::rename(source, target).await {
        Ok(()) => {
            trace!("Renamed `{}` to `{}`", source.display(), target.display());
            Ok(())
        }
        Err(e) if e.kind() == std::io::ErrorKind::CrossesDevices => {
            trace!(
                "Falling back to copy from `{}` to `{}`",
                source.display(),
                target.display()
            );
            fs_err::tokio::copy(source, target).await?;
            fs_err::tokio::remove_file(source).await?;
            Ok(())
        }
        Err(e) => {
            trace!(
                "Failed to rename `{}` to `{}`: {}",
                source.display(),
                target.display(),
                e
            );
            Err(e)
        }
    }
}
