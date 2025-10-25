use std::ffi::OsStr;
use std::fmt::{Display, Formatter};
use std::hash::{Hash, Hasher};
use std::ops::Deref;
use std::path::{Path, PathBuf};
use std::sync::{Arc, OnceLock};

use anyhow::{Context, Result};
use clap::ValueEnum;
use constants::MANIFEST_FILE;
use rustc_hash::{FxBuildHasher, FxHashMap, FxHashSet};
use serde::{Deserialize, Serialize};
use thiserror::Error;
use tracing::{error, trace};

use crate::config::{
    self, Config, HookOptions, Language, LocalHook, ManifestHook, MetaHook, RemoteHook, SerdeRegex,
    Stage, read_manifest,
};
use crate::languages::version::LanguageRequest;
use crate::languages::{extract_metadata_from_entry, resolve_command};
use crate::store::Store;
use crate::workspace::Project;

#[derive(Error, Debug)]
pub(crate) enum Error {
    #[error(transparent)]
    Config(#[from] config::Error),

    #[error("Hook `{hook}` is invalid")]
    Hook {
        hook: String,
        #[source]
        error: anyhow::Error,
    },

    #[error("Failed to read manifest of `{repo}`")]
    Manifest {
        repo: String,
        #[source]
        error: config::Error,
    },

    #[error("Failed to create directory for hook environment")]
    TmpDir(#[from] std::io::Error),
}

#[derive(Debug, Clone)]
pub(crate) enum Repo {
    Remote {
        /// Path to the cloned repo.
        path: PathBuf,
        url: String,
        rev: String,
        hooks: Vec<ManifestHook>,
    },
    Local {
        hooks: Vec<ManifestHook>,
    },
    Meta {
        hooks: Vec<ManifestHook>,
    },
}

impl Repo {
    /// Load the remote repo manifest from the path.
    pub(crate) fn remote(url: String, rev: String, path: PathBuf) -> Result<Self, Error> {
        let manifest = read_manifest(&path.join(MANIFEST_FILE)).map_err(|e| Error::Manifest {
            repo: url.to_string(),
            error: e,
        })?;
        let hooks = manifest.hooks;

        Ok(Self::Remote {
            path,
            url,
            rev,
            hooks,
        })
    }

    /// Construct a local repo from a list of hooks.
    pub(crate) fn local(hooks: Vec<LocalHook>) -> Self {
        Self::Local { hooks }
    }

    /// Construct a meta repo.
    pub(crate) fn meta(hooks: Vec<MetaHook>) -> Self {
        Self::Meta {
            hooks: hooks.into_iter().map(ManifestHook::from).collect(),
        }
    }

    /// Get the path to the cloned repo if it is a remote repo.
    pub(crate) fn path(&self) -> Option<&Path> {
        match self {
            Repo::Remote { path, .. } => Some(path),
            _ => None,
        }
    }

    /// Get a hook by id.
    pub(crate) fn get_hook(&self, id: &str) -> Option<&ManifestHook> {
        let hooks = match self {
            Repo::Remote { hooks, .. } => hooks,
            Repo::Local { hooks } => hooks,
            Repo::Meta { hooks } => hooks,
        };
        hooks.iter().find(|hook| hook.id == id)
    }
}

impl Display for Repo {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Repo::Remote { url, rev, .. } => write!(f, "{url}@{rev}"),
            Repo::Local { .. } => write!(f, "local"),
            Repo::Meta { .. } => write!(f, "meta"),
        }
    }
}

pub(crate) struct HookBuilder {
    project: Arc<Project>,
    repo: Arc<Repo>,
    config: ManifestHook,
    // The index of the hook in the project configuration.
    idx: usize,
}

impl HookBuilder {
    pub(crate) fn new(
        project: Arc<Project>,
        repo: Arc<Repo>,
        config: ManifestHook,
        idx: usize,
    ) -> Self {
        Self {
            project,
            repo,
            config,
            idx,
        }
    }

    /// Update the hook from the project level hook configuration.
    pub(crate) fn update(&mut self, config: &RemoteHook) -> &mut Self {
        if let Some(name) = &config.name {
            self.config.name.clone_from(name);
        }
        if let Some(entry) = &config.entry {
            self.config.entry.clone_from(entry);
        }
        if let Some(language) = &config.language {
            self.config.language.clone_from(language);
        }

        self.config.options.update(&config.options);

        self
    }

    /// Combine the hook configuration with the project level configuration.
    pub(crate) fn combine(&mut self, config: &Config) {
        let options = &mut self.config.options;
        let language = self.config.language;
        if options.language_version.is_none() {
            options.language_version = config
                .default_language_version
                .as_ref()
                .and_then(|v| v.get(&language).cloned());
        }

        if options.stages.is_none() {
            options.stages.clone_from(&config.default_stages);
        }
    }

    /// Fill in the default values for the hook configuration.
    fn fill_in_defaults(&mut self) {
        let options = &mut self.config.options;
        options.language_version.get_or_insert_default();
        options.alias.get_or_insert_default();
        options.args.get_or_insert_default();
        options.types.get_or_insert(vec!["file".to_string()]);
        options.types_or.get_or_insert_default();
        options.exclude_types.get_or_insert_default();
        options.always_run.get_or_insert(false);
        options.fail_fast.get_or_insert(false);
        options.pass_filenames.get_or_insert(true);
        options.require_serial.get_or_insert(false);
        options.verbose.get_or_insert(false);
        options.additional_dependencies.get_or_insert_default();
    }

    /// Check the hook configuration.
    fn check(&self) -> Result<(), Error> {
        let language = self.config.language;
        let HookOptions {
            language_version,
            additional_dependencies,
            ..
        } = &self.config.options;

        let additional_dependencies = additional_dependencies
            .as_ref()
            .map_or(&[][..], |deps| deps.as_slice());

        if !additional_dependencies.is_empty() {
            if !language.supports_install_env() {
                return Err(Error::Hook {
                    hook: self.config.id.clone(),
                    error: anyhow::anyhow!(
                        "Hook specified `additional_dependencies: {}` but the language `{}` does not install an environment",
                        additional_dependencies.join(", "),
                        language,
                    ),
                });
            }

            if !language.supports_dependency() {
                return Err(Error::Hook {
                    hook: self.config.id.clone(),
                    error: anyhow::anyhow!(
                        "Hook specified `additional_dependencies: {}` but the language `{}` does not support installing dependencies for now",
                        additional_dependencies.join(", "),
                        language,
                    ),
                });
            }
        }

        if !language.supports_language_version() {
            if let Some(language_version) = language_version
                && language_version != "default"
            {
                return Err(Error::Hook {
                    hook: self.config.id.clone(),
                    error: anyhow::anyhow!(
                        "Hook specified `language_version: {language_version}` but the language `{language}` does not support toolchain installation for now",
                    ),
                });
            }
        }

        Ok(())
    }

    /// Build the hook.
    pub(crate) async fn build(mut self) -> Result<Hook, Error> {
        self.check()?;
        self.fill_in_defaults();

        let options = self.config.options;
        let language_version = options.language_version.expect("language_version not set");
        let language_request = LanguageRequest::parse(self.config.language, &language_version)
            .map_err(|e| Error::Hook {
                hook: self.config.id.clone(),
                error: anyhow::anyhow!(e),
            })?;

        let entry = Entry::new(self.config.id.clone(), self.config.entry);

        let additional_dependencies = options
            .additional_dependencies
            .expect("additional_dependencies should not be None")
            .into_iter()
            .collect::<FxHashSet<_>>();

        let stages = match options.stages {
            Some(stages) => {
                let stages: FxHashSet<_> = stages.into_iter().collect();
                if stages.is_empty() || stages.len() == Stage::value_variants().len() {
                    Stages::All
                } else {
                    Stages::Some(stages)
                }
            }
            None => Stages::All,
        };

        let mut hook = Hook {
            entry,
            stages,
            language_request,
            additional_dependencies,
            dependencies: OnceLock::new(),
            project: self.project,
            repo: self.repo,
            idx: self.idx,
            id: self.config.id,
            name: self.config.name,
            language: self.config.language,
            alias: options.alias.expect("alias not set"),
            files: options.files,
            exclude: options.exclude,
            types: options.types.expect("types not set"),
            types_or: options.types_or.expect("types_or not set"),
            exclude_types: options.exclude_types.expect("exclude_types not set"),
            args: options.args.expect("args not set"),
            always_run: options.always_run.expect("always_run not set"),
            fail_fast: options.fail_fast.expect("fail_fast not set"),
            pass_filenames: options.pass_filenames.expect("pass_filenames not set"),
            description: options.description,
            log_file: options.log_file,
            require_serial: options.require_serial.expect("require_serial not set"),
            verbose: options.verbose.expect("verbose not set"),
            minimum_prek_version: options.minimum_prek_version,
        };

        if let Err(err) = extract_metadata_from_entry(&mut hook).await {
            if err
                .downcast_ref::<std::io::Error>()
                .is_some_and(|e| e.kind() != std::io::ErrorKind::NotFound)
            {
                trace!("Failed to extract metadata from entry for hook `{hook}`: {err}");
            }
        }

        Ok(hook)
    }
}

#[derive(Debug, Clone)]
pub(crate) enum Stages {
    All,
    Some(FxHashSet<Stage>),
}

impl Stages {
    pub(crate) fn contains(&self, stage: Stage) -> bool {
        match self {
            Stages::All => true,
            Stages::Some(stages) => stages.contains(&stage),
        }
    }
}

impl Display for Stages {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Stages::All => write!(f, "all"),
            Stages::Some(stages) => {
                let stages_str = stages
                    .iter()
                    .map(Stage::as_str)
                    .collect::<Vec<_>>()
                    .join(", ");
                write!(f, "{stages_str}")
            }
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct Entry {
    hook: String,
    entry: String,
}

impl Entry {
    pub(crate) fn new(hook: String, entry: String) -> Self {
        Self { hook, entry }
    }

    /// Split the entry and resolve the command by parsing its shebang.
    pub(crate) fn resolve(&self, env_path: Option<&OsStr>) -> Result<Vec<String>, Error> {
        let split = self.split()?;

        Ok(resolve_command(split, env_path))
    }

    /// Split the entry into a list of commands.
    pub(crate) fn split(&self) -> Result<Vec<String>, Error> {
        shlex::split(&self.entry).ok_or_else(|| Error::Hook {
            hook: self.hook.clone(),
            error: anyhow::anyhow!("Failed to parse entry `{}` as commands", &self.entry),
        })
    }

    /// Get the original entry string.
    pub(crate) fn raw(&self) -> &str {
        &self.entry
    }
}

#[allow(clippy::struct_excessive_bools)]
#[derive(Debug, Clone)]
pub(crate) struct Hook {
    project: Arc<Project>,
    repo: Arc<Repo>,
    // Cached computed dependencies.
    dependencies: OnceLock<FxHashSet<String>>,

    /// The index of the hook defined in the configuration file.
    pub idx: usize,
    pub id: String,
    pub name: String,
    pub entry: Entry,
    pub language: Language,
    pub alias: String,
    pub files: Option<SerdeRegex>,
    pub exclude: Option<SerdeRegex>,
    pub types: Vec<String>,
    pub types_or: Vec<String>,
    pub exclude_types: Vec<String>,
    pub additional_dependencies: FxHashSet<String>,
    pub args: Vec<String>,
    pub always_run: bool,
    pub fail_fast: bool,
    pub pass_filenames: bool,
    pub description: Option<String>,
    pub language_request: LanguageRequest,
    pub log_file: Option<String>,
    pub require_serial: bool,
    pub stages: Stages,
    pub verbose: bool,
    pub minimum_prek_version: Option<String>,
}

impl Display for Hook {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        if f.alternate() {
            write!(f, "{}:{}", self.repo, self.id)
        } else {
            write!(f, "{}", self.id)
        }
    }
}

impl Hook {
    pub(crate) fn project(&self) -> &Project {
        &self.project
    }

    pub(crate) fn repo(&self) -> &Repo {
        &self.repo
    }

    /// Get the path to the repository that contains the hook.
    pub(crate) fn repo_path(&self) -> Option<&Path> {
        self.repo.path()
    }

    pub(crate) fn full_id(&self) -> String {
        let path = self.project.relative_path();
        if path.as_os_str().is_empty() {
            format!(".:{}", self.id)
        } else {
            format!("{}:{}", path.display(), self.id)
        }
    }

    /// Get the path where the hook should be executed.
    pub(crate) fn work_dir(&self) -> &Path {
        self.project.path()
    }

    pub(crate) fn is_remote(&self) -> bool {
        matches!(&*self.repo, Repo::Remote { .. })
    }

    pub(crate) fn dependencies(&self) -> &FxHashSet<String> {
        if !self.is_remote() {
            return &self.additional_dependencies;
        }
        self.dependencies.get_or_init(|| {
            // For remote hooks, itself is an implicit dependency of the hook.
            let mut deps = FxHashSet::with_capacity_and_hasher(
                self.additional_dependencies.len() + 1,
                FxBuildHasher,
            );
            deps.extend(self.additional_dependencies.clone());
            deps.insert(self.repo.to_string());
            deps
        })
    }
}

#[derive(Debug, Clone)]
pub(crate) enum InstalledHook {
    Installed {
        hook: Arc<Hook>,
        info: Arc<InstallInfo>,
    },
    NoNeedInstall(Arc<Hook>),
}

impl Deref for InstalledHook {
    type Target = Hook;

    fn deref(&self) -> &Self::Target {
        match self {
            InstalledHook::Installed { hook, .. } => hook,
            InstalledHook::NoNeedInstall(hook) => hook,
        }
    }
}

impl Display for InstalledHook {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        // TODO: add more information
        self.deref().fmt(f)
    }
}

const HOOK_MARKER: &str = ".prek-hook.json";

impl InstalledHook {
    /// Get the path to the environment where the hook is installed.
    pub(crate) fn env_path(&self) -> Option<&Path> {
        match self {
            InstalledHook::Installed { info, .. } => Some(&info.env_path),
            InstalledHook::NoNeedInstall(_) => None,
        }
    }

    /// Get the install info of the hook if it is installed.
    pub(crate) fn install_info(&self) -> Option<&InstallInfo> {
        match self {
            InstalledHook::Installed { info, .. } => Some(info),
            InstalledHook::NoNeedInstall(_) => None,
        }
    }

    /// Mark the hook as installed in the environment.
    pub(crate) async fn mark_as_installed(&self, _store: &Store) -> Result<()> {
        let Some(info) = self.install_info() else {
            return Ok(());
        };

        let content =
            serde_json::to_string_pretty(info).context("Failed to serialize install info")?;

        fs_err::tokio::write(info.env_path.join(HOOK_MARKER), content)
            .await
            .context("Failed to write install info")?;

        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub(crate) struct InstallInfo {
    pub(crate) language: Language,
    pub(crate) language_version: semver::Version,
    pub(crate) dependencies: FxHashSet<String>,
    pub(crate) env_path: PathBuf,
    pub(crate) toolchain: PathBuf,
    extra: FxHashMap<String, String>,
}

impl Hash for InstallInfo {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.language.hash(state);
        self.language_version.hash(state);
        let mut deps = self.dependencies.iter().collect::<Vec<_>>();
        deps.sort_unstable();
        deps.hash(state);
    }
}

impl InstallInfo {
    pub(crate) fn new(
        language: Language,
        dependencies: FxHashSet<String>,
        hooks_dir: &Path,
    ) -> Result<Self, Error> {
        let env_path = tempfile::Builder::new()
            .prefix(&format!("{}-", language.as_str()))
            .rand_bytes(20)
            .tempdir_in(hooks_dir)?
            .keep();

        Ok(Self {
            language,
            dependencies,
            env_path,
            language_version: semver::Version::new(0, 0, 0),
            toolchain: PathBuf::new(),
            extra: FxHashMap::default(),
        })
    }

    pub(crate) async fn from_env_path(path: &Path) -> Result<Self> {
        let content = fs_err::tokio::read_to_string(path.join(HOOK_MARKER)).await?;
        let info: InstallInfo = serde_json::from_str(&content)?;

        Ok(info)
    }

    pub(crate) async fn check_health(&self) -> Result<()> {
        self.language.check_health(self).await
    }

    pub(crate) fn with_language_version(&mut self, version: semver::Version) -> &mut Self {
        self.language_version = version;
        self
    }

    pub(crate) fn with_toolchain(&mut self, toolchain: PathBuf) -> &mut Self {
        self.toolchain = toolchain;
        self
    }

    pub(crate) fn with_extra(&mut self, key: &str, value: &str) -> &mut Self {
        self.extra.insert(key.to_string(), value.to_string());
        self
    }

    pub(crate) fn get_extra(&self, key: &str) -> Option<&String> {
        self.extra.get(key)
    }

    pub(crate) fn matches(&self, hook: &Hook) -> bool {
        self.language == hook.language
            && &self.dependencies == hook.dependencies()
            && hook.language_request.satisfied_by(self)
    }
}
