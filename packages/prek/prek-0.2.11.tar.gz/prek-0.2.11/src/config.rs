use std::fmt::Display;
use std::ops::{Deref, RangeInclusive};
use std::path::Path;
use std::str::FromStr;
use std::sync::OnceLock;

use anyhow::Result;
use constants::{ALT_CONFIG_FILE, CONFIG_FILE};
use fancy_regex::{self as regex, Regex};
use rustc_hash::FxHashMap;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_yaml::Value;

use crate::fs::Simplified;
use crate::identify;
use crate::version;
use crate::warn_user;

#[derive(Clone)]
pub struct SerdeRegex(Regex);

impl Deref for SerdeRegex {
    type Target = Regex;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl std::fmt::Debug for SerdeRegex {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_tuple("SerdeRegex").field(&self.0.as_str()).finish()
    }
}

impl<'de> Deserialize<'de> for SerdeRegex {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Regex::new(&s)
            .map(SerdeRegex)
            .map_err(serde::de::Error::custom)
    }
}

impl Serialize for SerdeRegex {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(self.0.as_str())
    }
}

#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash, Deserialize, Serialize, clap::ValueEnum)]
#[serde(rename_all = "snake_case")]
pub enum Language {
    Conda,
    Coursier,
    Dart,
    Docker,
    DockerImage,
    Dotnet,
    Fail,
    Golang,
    Haskell,
    Lua,
    Node,
    Perl,
    Python,
    R,
    Ruby,
    Rust,
    Swift,
    Pygrep,
    Script,
    System,
}

impl Language {
    pub fn as_str(&self) -> &str {
        match self {
            Self::Conda => "conda",
            Self::Coursier => "coursier",
            Self::Dart => "dart",
            Self::Docker => "docker",
            Self::DockerImage => "docker_image",
            Self::Dotnet => "dotnet",
            Self::Fail => "fail",
            Self::Golang => "golang",
            Self::Haskell => "haskell",
            Self::Lua => "lua",
            Self::Node => "node",
            Self::Perl => "perl",
            Self::Python => "python",
            Self::R => "r",
            Self::Ruby => "ruby",
            Self::Rust => "rust",
            Self::Swift => "swift",
            Self::Pygrep => "pygrep",
            Self::Script => "script",
            Self::System => "system",
        }
    }
}

impl Display for Language {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

#[derive(Debug, Clone, Copy, Default, Deserialize, clap::ValueEnum)]
#[serde(rename_all = "kebab-case")]
pub enum HookType {
    CommitMsg,
    PostCheckout,
    PostCommit,
    PostMerge,
    PostRewrite,
    #[default]
    PreCommit,
    PreMergeCommit,
    PrePush,
    PreRebase,
    PrepareCommitMsg,
}

impl HookType {
    pub fn as_str(&self) -> &str {
        match self {
            Self::CommitMsg => "commit-msg",
            Self::PostCheckout => "post-checkout",
            Self::PostCommit => "post-commit",
            Self::PostMerge => "post-merge",
            Self::PostRewrite => "post-rewrite",
            Self::PreCommit => "pre-commit",
            Self::PreMergeCommit => "pre-merge-commit",
            Self::PrePush => "pre-push",
            Self::PreRebase => "pre-rebase",
            Self::PrepareCommitMsg => "prepare-commit-msg",
        }
    }

    /// Return the number of arguments this hook type expects.
    pub fn num_args(self) -> RangeInclusive<usize> {
        match self {
            Self::CommitMsg => 1..=1,
            Self::PostCheckout => 3..=3,
            Self::PreCommit => 0..=0,
            Self::PostCommit => 0..=0,
            Self::PreMergeCommit => 0..=0,
            Self::PostMerge => 1..=1,
            Self::PostRewrite => 1..=1,
            Self::PrePush => 2..=2,
            Self::PreRebase => 1..=2,
            Self::PrepareCommitMsg => 1..=3,
        }
    }
}

impl Display for HookType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

#[derive(
    Debug, Clone, Copy, PartialEq, Eq, Default, Hash, Deserialize, Serialize, clap::ValueEnum,
)]
#[serde(rename_all = "kebab-case")]
pub enum Stage {
    Manual,
    CommitMsg,
    PostCheckout,
    PostCommit,
    PostMerge,
    PostRewrite,
    #[default]
    #[serde(alias = "commit")]
    PreCommit,
    #[serde(alias = "merge-commit")]
    PreMergeCommit,
    #[serde(alias = "push")]
    PrePush,
    PreRebase,
    PrepareCommitMsg,
}

impl From<HookType> for Stage {
    fn from(value: HookType) -> Self {
        match value {
            HookType::CommitMsg => Self::CommitMsg,
            HookType::PostCheckout => Self::PostCheckout,
            HookType::PostCommit => Self::PostCommit,
            HookType::PostMerge => Self::PostMerge,
            HookType::PostRewrite => Self::PostRewrite,
            HookType::PreCommit => Self::PreCommit,
            HookType::PreMergeCommit => Self::PreMergeCommit,
            HookType::PrePush => Self::PrePush,
            HookType::PreRebase => Self::PreRebase,
            HookType::PrepareCommitMsg => Self::PrepareCommitMsg,
        }
    }
}

impl Stage {
    pub fn as_str(&self) -> &str {
        match self {
            Self::Manual => "manual",
            Self::CommitMsg => "commit-msg",
            Self::PostCheckout => "post-checkout",
            Self::PostCommit => "post-commit",
            Self::PostMerge => "post-merge",
            Self::PostRewrite => "post-rewrite",
            Self::PreCommit => "pre-commit",
            Self::PreMergeCommit => "pre-merge-commit",
            Self::PrePush => "pre-push",
            Self::PreRebase => "pre-rebase",
            Self::PrepareCommitMsg => "prepare-commit-msg",
        }
    }
}

impl Display for Stage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

impl Stage {
    pub fn operate_on_files(self) -> bool {
        matches!(
            self,
            Stage::Manual
                | Stage::CommitMsg
                | Stage::PreCommit
                | Stage::PreMergeCommit
                | Stage::PrePush
                | Stage::PrepareCommitMsg
        )
    }
}

fn deserialize_minimum_version<'de, D>(deserializer: D) -> Result<Option<String>, D::Error>
where
    D: Deserializer<'de>,
{
    let s = String::deserialize(deserializer)?;
    if s.is_empty() {
        return Ok(None);
    }

    let version = s
        .parse::<semver::Version>()
        .map_err(serde::de::Error::custom)?;
    let cur_version = version::version()
        .version
        .parse::<semver::Version>()
        .expect("Invalid prek version");
    if version > cur_version {
        return Err(serde::de::Error::custom(format!(
            "Required minimum prek version `{version}` is greater than current version `{cur_version}`. Please consider updating prek.",
        )));
    }

    Ok(Some(s))
}

// TODO: warn deprecated stage
// TODO: warn sensible regex
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct Config {
    pub repos: Vec<Repo>,
    /// A list of `--hook-types` which will be used by default when running `prek install`.
    /// Default is `[pre-commit]`.
    pub default_install_hook_types: Option<Vec<HookType>>,
    /// A mapping from language to the default `language_version`.
    pub default_language_version: Option<FxHashMap<Language, String>>,
    /// A configuration-wide default for the stages property of hooks.
    /// Default to all stages.
    pub default_stages: Option<Vec<Stage>>,
    /// Global file include pattern.
    pub files: Option<SerdeRegex>,
    /// Global file exclude pattern.
    pub exclude: Option<SerdeRegex>,
    /// Set to true to have prek stop running hooks after the first failure.
    /// Default is false.
    pub fail_fast: Option<bool>,
    /// The minimum version of prek required to run this configuration.
    #[serde(deserialize_with = "deserialize_minimum_version", default)]
    pub minimum_prek_version: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RepoLocation {
    Local,
    Meta,
    Remote(String),
}

impl FromStr for RepoLocation {
    type Err = url::ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "local" => Ok(RepoLocation::Local),
            "meta" => Ok(RepoLocation::Meta),
            _ => Ok(RepoLocation::Remote(s.to_string())),
        }
    }
}

impl<'de> Deserialize<'de> for RepoLocation {
    fn deserialize<D>(deserializer: D) -> Result<RepoLocation, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        RepoLocation::from_str(&s).map_err(serde::de::Error::custom)
    }
}

impl RepoLocation {
    pub fn as_str(&self) -> &str {
        match self {
            RepoLocation::Local => "local",
            RepoLocation::Meta => "meta",
            RepoLocation::Remote(url) => url.as_str(),
        }
    }
}

impl Display for RepoLocation {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Common hook options.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct HookOptions {
    /// Not documented in the official docs.
    pub alias: Option<String>,
    /// The pattern of files to run on.
    pub files: Option<SerdeRegex>,
    /// Exclude files that were matched by `files`.
    /// Default is `$^`, which matches nothing.
    pub exclude: Option<SerdeRegex>,
    /// List of file types to run on (AND).
    /// Default is `[file]`, which matches all files.
    #[serde(deserialize_with = "deserialize_and_validate_tags", default)]
    pub types: Option<Vec<String>>,
    /// List of file types to run on (OR).
    /// Default is `[]`.
    #[serde(deserialize_with = "deserialize_and_validate_tags", default)]
    pub types_or: Option<Vec<String>>,
    /// List of file types to exclude.
    /// Default is `[]`.
    #[serde(deserialize_with = "deserialize_and_validate_tags", default)]
    pub exclude_types: Option<Vec<String>>,
    /// Not documented in the official docs.
    pub additional_dependencies: Option<Vec<String>>,
    /// Additional arguments to pass to the hook.
    pub args: Option<Vec<String>>,
    /// This hook will run even if there are no matching files.
    /// Default is false.
    pub always_run: Option<bool>,
    /// If this hook fails, don't run any more hooks.
    /// Default is false.
    pub fail_fast: Option<bool>,
    /// Append filenames that would be checked to the hook entry as arguments.
    /// Default is true.
    pub pass_filenames: Option<bool>,
    /// A description of the hook. For metadata only.
    pub description: Option<String>,
    /// Run the hook on a specific version of the language.
    /// Default is `default`.
    /// See <https://pre-commit.com/#overriding-language-version>.
    pub language_version: Option<String>,
    /// Write the output of the hook to a file when the hook fails or verbose is enabled.
    pub log_file: Option<String>,
    /// This hook will execute using a single process instead of in parallel.
    /// Default is false.
    pub require_serial: Option<bool>,
    /// Select which git hook(s) to run for.
    /// Default all stages are selected.
    /// See <https://pre-commit.com/#confining-hooks-to-run-at-certain-stages>.
    pub stages: Option<Vec<Stage>>,
    /// Print the output of the hook even if it passes.
    /// Default is false.
    pub verbose: Option<bool>,
    /// The minimum version of prek required to run this hook.
    #[serde(deserialize_with = "deserialize_minimum_version", default)]
    pub minimum_prek_version: Option<String>,
}

impl HookOptions {
    pub fn update(&mut self, other: &Self) {
        macro_rules! update_if_some {
            ($($field:ident),* $(,)?) => {
                $(
                if other.$field.is_some() {
                    self.$field.clone_from(&other.$field);
                }
                )*
            };
        }

        update_if_some!(
            alias,
            files,
            exclude,
            types,
            types_or,
            exclude_types,
            additional_dependencies,
            args,
            always_run,
            fail_fast,
            pass_filenames,
            description,
            language_version,
            log_file,
            require_serial,
            stages,
            verbose,
            minimum_prek_version,
        );
    }
}

/// A remote hook in the configuration file.
///
/// All keys in manifest hook dict are valid in a config hook dict, but are optional.
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct RemoteHook {
    /// The id of the hook.
    pub id: String,
    /// Override the name of the hook.
    pub name: Option<String>,
    /// Override the entrypoint. Not documented in the official docs but works.
    pub entry: Option<String>,
    /// Override the language. Not documented in the official docs but works.
    pub language: Option<Language>,
    #[serde(flatten)]
    pub options: HookOptions,
}

/// A local hook in the configuration file.
///
/// It's the same as the manifest hook definition.
pub type LocalHook = ManifestHook;

#[derive(Debug, Copy, Clone, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum MetaHookID {
    CheckHooksApply,
    CheckUselessExcludes,
    Identity,
}

impl Display for MetaHookID {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let name = match self {
            MetaHookID::CheckHooksApply => "check-hooks-apply",
            MetaHookID::CheckUselessExcludes => "check-useless-excludes",
            MetaHookID::Identity => "identity",
        };
        f.write_str(name)
    }
}

impl FromStr for MetaHookID {
    type Err = ();

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "check-hooks-apply" => Ok(MetaHookID::CheckHooksApply),
            "check-useless-excludes" => Ok(MetaHookID::CheckUselessExcludes),
            "identity" => Ok(MetaHookID::Identity),
            _ => Err(()),
        }
    }
}

/// A meta hook predefined in pre-commit.
///
/// It's the same as the manifest hook definition but with only a few predefined id allowed.
#[derive(Debug, Clone)]
pub struct MetaHook(pub(crate) ManifestHook);

impl<'de> Deserialize<'de> for MetaHook {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let hook = RemoteHook::deserialize(deserializer)?;

        let id = MetaHookID::from_str(&hook.id)
            .map_err(|()| serde::de::Error::custom("Unknown meta hook id"))?;
        if hook.language.is_some_and(|l| l != Language::System) {
            return Err(serde::de::Error::custom(
                "language must be system for meta hook",
            ));
        }
        if hook.entry.is_some() {
            return Err(serde::de::Error::custom(
                "entry is not allowed for meta hook",
            ));
        }

        let mut defaults = match id {
            MetaHookID::CheckHooksApply => ManifestHook {
                id: MetaHookID::CheckHooksApply.to_string(),
                name: "Check hooks apply".to_string(),
                language: Language::System,
                entry: String::new(),
                options: HookOptions {
                    files: Some(
                        Regex::new(&format!(
                            "^{}|{}$",
                            regex::escape(CONFIG_FILE),
                            regex::escape(ALT_CONFIG_FILE)
                        ))
                        .map(SerdeRegex)
                        .unwrap(),
                    ),
                    ..Default::default()
                },
            },
            MetaHookID::CheckUselessExcludes => ManifestHook {
                id: MetaHookID::CheckUselessExcludes.to_string(),
                name: "Check useless excludes".to_string(),
                language: Language::System,
                entry: String::new(),
                options: HookOptions {
                    files: Some(
                        Regex::new(&format!(
                            "^{}|{}$",
                            regex::escape(CONFIG_FILE),
                            regex::escape(ALT_CONFIG_FILE)
                        ))
                        .map(SerdeRegex)
                        .unwrap(),
                    ),
                    ..Default::default()
                },
            },
            MetaHookID::Identity => ManifestHook {
                id: MetaHookID::Identity.to_string(),
                name: "identity".to_string(),
                language: Language::System,
                entry: String::new(),
                options: HookOptions {
                    verbose: Some(true),
                    ..Default::default()
                },
            },
        };

        defaults.options.update(&hook.options);

        Ok(MetaHook(defaults))
    }
}

impl From<MetaHook> for ManifestHook {
    fn from(hook: MetaHook) -> Self {
        hook.0
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct RemoteRepo {
    pub repo: String,
    pub rev: String,
    #[serde(skip)]
    pub hooks: Vec<RemoteHook>,
}

impl PartialEq for RemoteRepo {
    fn eq(&self, other: &Self) -> bool {
        self.repo == other.repo && self.rev == other.rev
    }
}

impl Eq for RemoteRepo {}

impl std::hash::Hash for RemoteRepo {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.repo.hash(state);
        self.rev.hash(state);
    }
}

impl Display for RemoteRepo {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}@{}", self.repo, self.rev)
    }
}

#[derive(Debug, Clone)]
pub struct LocalRepo {
    pub hooks: Vec<LocalHook>,
}

impl Display for LocalRepo {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("local")
    }
}

#[derive(Debug, Clone)]
pub struct MetaRepo {
    pub hooks: Vec<MetaHook>,
}

impl Display for MetaRepo {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("meta")
    }
}

#[derive(Debug, Clone)]
pub enum Repo {
    Remote(RemoteRepo),
    Local(LocalRepo),
    Meta(MetaRepo),
}

impl<'de> Deserialize<'de> for Repo {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(Deserialize)]
        struct RepoWire {
            repo: RepoLocation,
            #[serde(flatten)]
            rest: serde_yaml::Value,
        }

        let RepoWire { repo, rest } = RepoWire::deserialize(deserializer)?;

        match repo {
            RepoLocation::Remote(url) => {
                #[derive(Deserialize)]
                #[serde(deny_unknown_fields)]
                struct _RemoteRepo {
                    rev: String,
                    hooks: Vec<RemoteHook>,
                }
                let _RemoteRepo { rev, hooks } = _RemoteRepo::deserialize(rest)
                    .map_err(|e| serde::de::Error::custom(format!("Invalid remote repo: {e}")))?;

                Ok(Repo::Remote(RemoteRepo {
                    repo: url,
                    rev,
                    hooks,
                }))
            }
            RepoLocation::Local => {
                #[derive(Deserialize)]
                #[serde(deny_unknown_fields)]
                struct _LocalRepo {
                    hooks: Vec<LocalHook>,
                }
                let _LocalRepo { hooks } = _LocalRepo::deserialize(rest)
                    .map_err(|e| serde::de::Error::custom(format!("Invalid local repo: {e}")))?;
                Ok(Repo::Local(LocalRepo { hooks }))
            }
            RepoLocation::Meta => {
                #[derive(Deserialize)]
                #[serde(deny_unknown_fields)]
                struct _MetaRepo {
                    hooks: Vec<MetaHook>,
                }
                let _MetaRepo { hooks } = _MetaRepo::deserialize(rest)
                    .map_err(|e| serde::de::Error::custom(format!("Invalid meta repo: {e}")))?;
                Ok(Repo::Meta(MetaRepo { hooks }))
            }
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct ManifestHook {
    /// The id of the hook.
    pub id: String,
    /// The name of the hook.
    pub name: String,
    /// The command to run. It can contain arguments that will not be overridden.
    pub entry: String,
    /// The language of the hook. Tells prek how to install and run the hook.
    pub language: Language,
    #[serde(flatten)]
    pub options: HookOptions,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
#[serde(transparent)]
pub struct Manifest {
    pub hooks: Vec<ManifestHook>,
}

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Config file not found: {0}")]
    NotFound(String),

    #[error(transparent)]
    Io(#[from] std::io::Error),

    #[error("Failed to parse `{0}`")]
    Yaml(String, #[source] serde_yaml::Error),
}

/// Keys that prek does not use.
const EXPECTED_UNUSED: &[&str] = &["minimum_pre_commit_version", "ci"];

/// Read the configuration file from the given path.
pub fn read_config(path: &Path) -> Result<Config, Error> {
    let content = match fs_err::read_to_string(path) {
        Ok(content) => content,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            return Err(Error::NotFound(path.user_display().to_string()));
        }
        Err(e) => return Err(e.into()),
    };

    let mut yaml: Value = serde_yaml::from_str(&content)
        .map_err(|e| Error::Yaml(path.user_display().to_string(), e))?;

    yaml.apply_merge()
        .map_err(|e| Error::Yaml(path.user_display().to_string(), e))?;

    let mut unused = Vec::new();
    let config: Config = serde_ignored::deserialize(yaml, |path| {
        let key = path.to_string();
        if !EXPECTED_UNUSED.contains(&key.as_str()) {
            unused.push(key);
        }
    })
    .map_err(|e| Error::Yaml(path.user_display().to_string(), e))?;

    if !unused.is_empty() {
        warn_user!(
            "Ignored unexpected keys in `{}`: {}",
            path.display().cyan(),
            unused
                .into_iter()
                .map(|key| format!("`{}`", key.yellow()))
                .collect::<Vec<_>>()
                .join(", ")
        );
    }

    // Check for mutable revs and warn the user.
    let repos_has_mutable_rev = config
        .repos
        .iter()
        .filter_map(|repo| {
            if let Repo::Remote(repo) = repo {
                let rev = &repo.rev;
                // A rev is considered mutable if it doesn't contain a '.' (like a version)
                // and is not a hexadecimal string (like a commit SHA).
                if !rev.contains('.') && !looks_like_sha(rev) {
                    return Some(repo);
                }
            }
            None
        })
        .collect::<Vec<_>>();
    if !repos_has_mutable_rev.is_empty() {
        let msg = repos_has_mutable_rev
            .iter()
            .map(|repo| format!("{}: {}", repo.repo.cyan(), repo.rev.yellow()))
            .collect::<Vec<_>>()
            .join("\n");

        warn_user!(
            "{}",
            indoc::formatdoc! { r#"
            The following repos have mutable `rev` fields (moving tag / branch):
            {}
            Mutable references are never updated after first install and are not supported.
            See https://pre-commit.com/#using-the-latest-version-for-a-repository for more details.
            Hint: `prek autoupdate` often fixes this",
            "#,
            msg
            }
        );
    }

    Ok(config)
}

/// Read the manifest file from the given path.
pub fn read_manifest(path: &Path) -> Result<Manifest, Error> {
    let content = fs_err::read_to_string(path)?;
    let manifest = serde_yaml::from_str(&content)
        .map_err(|e| Error::Yaml(path.user_display().to_string(), e))?;
    Ok(manifest)
}

/// Check if a string looks like a git SHA
fn looks_like_sha(s: &str) -> bool {
    static SHA_RE: OnceLock<Regex> = OnceLock::new();
    let re = SHA_RE.get_or_init(|| Regex::new(r"^[a-fA-F0-9]+$").unwrap());
    re.is_match(s).unwrap_or(false)
}

/// Deserializes a vector of strings and validates that each is a known file type tag.
fn deserialize_and_validate_tags<'de, D>(deserializer: D) -> Result<Option<Vec<String>>, D::Error>
where
    D: Deserializer<'de>,
{
    let tags_opt: Option<Vec<String>> = Option::deserialize(deserializer)?;
    if let Some(tags) = &tags_opt {
        let all_tags = identify::all_tags();
        for tag in tags {
            if !all_tags.contains(tag.as_str()) {
                let msg = format!("Type tag \"{tag}\" is not recognized. Try upgrading prek");
                return Err(serde::de::Error::custom(msg));
            }
        }
    }
    Ok(tags_opt)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write as _;

    #[test]
    fn parse_repos() {
        // Local hook should not have `rev`
        let yaml = indoc::indoc! {r"
            repos:
              - repo: local
                hooks:
                  - id: cargo-fmt
                    name: cargo fmt
                    entry: cargo fmt --
                    language: system
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r#"
        Ok(
            Config {
                repos: [
                    Local(
                        LocalRepo {
                            hooks: [
                                ManifestHook {
                                    id: "cargo-fmt",
                                    name: "cargo fmt",
                                    entry: "cargo fmt --",
                                    language: System,
                                    options: HookOptions {
                                        alias: None,
                                        files: None,
                                        exclude: None,
                                        types: None,
                                        types_or: None,
                                        exclude_types: None,
                                        additional_dependencies: None,
                                        args: None,
                                        always_run: None,
                                        fail_fast: None,
                                        pass_filenames: None,
                                        description: None,
                                        language_version: None,
                                        log_file: None,
                                        require_serial: None,
                                        stages: None,
                                        verbose: None,
                                        minimum_prek_version: None,
                                    },
                                },
                            ],
                        },
                    ),
                ],
                default_install_hook_types: None,
                default_language_version: None,
                default_stages: None,
                files: None,
                exclude: None,
                fail_fast: None,
                minimum_prek_version: None,
            },
        )
        "#);

        let yaml = indoc::indoc! {r"
            repos:
              - repo: local
                rev: v1.0.0
                hooks:
                  - id: cargo-fmt
                    name: cargo fmt
                    types:
                      - rust
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid local repo: unknown field `rev`, expected `hooks`", line: 2, column: 3),
        )
        "###);

        // Remote hook should have `rev`.
        let yaml = indoc::indoc! {r"
            repos:
              - repo: https://github.com/crate-ci/typos
                rev: v1.0.0
                hooks:
                  - id: typos
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r#"
        Ok(
            Config {
                repos: [
                    Remote(
                        RemoteRepo {
                            repo: "https://github.com/crate-ci/typos",
                            rev: "v1.0.0",
                            hooks: [
                                RemoteHook {
                                    id: "typos",
                                    name: None,
                                    entry: None,
                                    language: None,
                                    options: HookOptions {
                                        alias: None,
                                        files: None,
                                        exclude: None,
                                        types: None,
                                        types_or: None,
                                        exclude_types: None,
                                        additional_dependencies: None,
                                        args: None,
                                        always_run: None,
                                        fail_fast: None,
                                        pass_filenames: None,
                                        description: None,
                                        language_version: None,
                                        log_file: None,
                                        require_serial: None,
                                        stages: None,
                                        verbose: None,
                                        minimum_prek_version: None,
                                    },
                                },
                            ],
                        },
                    ),
                ],
                default_install_hook_types: None,
                default_language_version: None,
                default_stages: None,
                files: None,
                exclude: None,
                fail_fast: None,
                minimum_prek_version: None,
            },
        )
        "#);

        let yaml = indoc::indoc! {r"
            repos:
              - repo: https://github.com/crate-ci/typos
                hooks:
                  - id: typos
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid remote repo: missing field `rev`", line: 2, column: 3),
        )
        "###);
    }

    #[test]
    fn parse_hooks() {
        // Remote hook only `id` is required.
        let yaml = indoc::indoc! { r"
            repos:
              - repo: https://github.com/crate-ci/typos
                rev: v1.0.0
                hooks:
                  - name: typos
                    alias: typo
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid remote repo: missing field `id`", line: 2, column: 3),
        )
        "###);

        // Local hook should have `id`, `name`, and `entry` and `language`.
        let yaml = indoc::indoc! { r"
            repos:
              - repo: local
                hooks:
                  - id: cargo-fmt
                    name: cargo fmt
                    entry: cargo fmt
                    types:
                      - rust
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid local repo: missing field `language`", line: 2, column: 3),
        )
        "###);

        let yaml = indoc::indoc! { r"
            repos:
              - repo: local
                hooks:
                  - id: cargo-fmt
                    name: cargo fmt
                    entry: cargo fmt
                    language: rust
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r#"
        Ok(
            Config {
                repos: [
                    Local(
                        LocalRepo {
                            hooks: [
                                ManifestHook {
                                    id: "cargo-fmt",
                                    name: "cargo fmt",
                                    entry: "cargo fmt",
                                    language: Rust,
                                    options: HookOptions {
                                        alias: None,
                                        files: None,
                                        exclude: None,
                                        types: None,
                                        types_or: None,
                                        exclude_types: None,
                                        additional_dependencies: None,
                                        args: None,
                                        always_run: None,
                                        fail_fast: None,
                                        pass_filenames: None,
                                        description: None,
                                        language_version: None,
                                        log_file: None,
                                        require_serial: None,
                                        stages: None,
                                        verbose: None,
                                        minimum_prek_version: None,
                                    },
                                },
                            ],
                        },
                    ),
                ],
                default_install_hook_types: None,
                default_language_version: None,
                default_stages: None,
                files: None,
                exclude: None,
                fail_fast: None,
                minimum_prek_version: None,
            },
        )
        "#);
    }

    #[test]
    fn meta_hooks() {
        // Invalid rev
        let yaml = indoc::indoc! { r"
            repos:
              - repo: meta
                rev: v1.0.0
                hooks:
                  - name: typos
                    alias: typo
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid meta repo: unknown field `rev`, expected `hooks`", line: 2, column: 3),
        )
        "###);

        // Invalid meta hook id
        let yaml = indoc::indoc! { r"
            repos:
              - repo: meta
                hooks:
                  - id: hello
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid meta repo: Unknown meta hook id", line: 2, column: 3),
        )
        "###);

        // Invalid language
        let yaml = indoc::indoc! { r"
            repos:
              - repo: meta
                hooks:
                  - id: check-hooks-apply
                    language: python
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid meta repo: language must be system for meta hook", line: 2, column: 3),
        )
        "###);

        // Invalid entry
        let yaml = indoc::indoc! { r"
            repos:
              - repo: meta
                hooks:
                  - id: check-hooks-apply
                    entry: echo hell world
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r###"
        Err(
            Error("repos: Invalid meta repo: entry is not allowed for meta hook", line: 2, column: 3),
        )
        "###);

        // Valid meta hook
        let yaml = indoc::indoc! { r"
            repos:
              - repo: meta
                hooks:
                  - id: check-hooks-apply
                  - id: check-useless-excludes
                  - id: identity
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r#"
        Ok(
            Config {
                repos: [
                    Meta(
                        MetaRepo {
                            hooks: [
                                MetaHook(
                                    ManifestHook {
                                        id: "check-hooks-apply",
                                        name: "Check hooks apply",
                                        entry: "",
                                        language: System,
                                        options: HookOptions {
                                            alias: None,
                                            files: Some(
                                                SerdeRegex(
                                                    "^\\.pre-commit-config\\.yaml|\\.pre-commit-config\\.yml$",
                                                ),
                                            ),
                                            exclude: None,
                                            types: None,
                                            types_or: None,
                                            exclude_types: None,
                                            additional_dependencies: None,
                                            args: None,
                                            always_run: None,
                                            fail_fast: None,
                                            pass_filenames: None,
                                            description: None,
                                            language_version: None,
                                            log_file: None,
                                            require_serial: None,
                                            stages: None,
                                            verbose: None,
                                            minimum_prek_version: None,
                                        },
                                    },
                                ),
                                MetaHook(
                                    ManifestHook {
                                        id: "check-useless-excludes",
                                        name: "Check useless excludes",
                                        entry: "",
                                        language: System,
                                        options: HookOptions {
                                            alias: None,
                                            files: Some(
                                                SerdeRegex(
                                                    "^\\.pre-commit-config\\.yaml|\\.pre-commit-config\\.yml$",
                                                ),
                                            ),
                                            exclude: None,
                                            types: None,
                                            types_or: None,
                                            exclude_types: None,
                                            additional_dependencies: None,
                                            args: None,
                                            always_run: None,
                                            fail_fast: None,
                                            pass_filenames: None,
                                            description: None,
                                            language_version: None,
                                            log_file: None,
                                            require_serial: None,
                                            stages: None,
                                            verbose: None,
                                            minimum_prek_version: None,
                                        },
                                    },
                                ),
                                MetaHook(
                                    ManifestHook {
                                        id: "identity",
                                        name: "identity",
                                        entry: "",
                                        language: System,
                                        options: HookOptions {
                                            alias: None,
                                            files: None,
                                            exclude: None,
                                            types: None,
                                            types_or: None,
                                            exclude_types: None,
                                            additional_dependencies: None,
                                            args: None,
                                            always_run: None,
                                            fail_fast: None,
                                            pass_filenames: None,
                                            description: None,
                                            language_version: None,
                                            log_file: None,
                                            require_serial: None,
                                            stages: None,
                                            verbose: Some(
                                                true,
                                            ),
                                            minimum_prek_version: None,
                                        },
                                    },
                                ),
                            ],
                        },
                    ),
                ],
                default_install_hook_types: None,
                default_language_version: None,
                default_stages: None,
                files: None,
                exclude: None,
                fail_fast: None,
                minimum_prek_version: None,
            },
        )
        "#);
    }

    #[test]
    fn language_version() {
        let yaml = indoc::indoc! { r"
            repos:
              - repo: local
                hooks:
                  - id: hook-1
                    name: hook 1
                    entry: echo hello world
                    language: system
                    language_version: default
                  - id: hook-2
                    name: hook 2
                    entry: echo hello world
                    language: system
                    language_version: system
                  - id: hook-3
                    name: hook 3
                    entry: echo hello world
                    language: system
                    language_version: '3.8'
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        insta::assert_debug_snapshot!(result, @r#"
        Ok(
            Config {
                repos: [
                    Local(
                        LocalRepo {
                            hooks: [
                                ManifestHook {
                                    id: "hook-1",
                                    name: "hook 1",
                                    entry: "echo hello world",
                                    language: System,
                                    options: HookOptions {
                                        alias: None,
                                        files: None,
                                        exclude: None,
                                        types: None,
                                        types_or: None,
                                        exclude_types: None,
                                        additional_dependencies: None,
                                        args: None,
                                        always_run: None,
                                        fail_fast: None,
                                        pass_filenames: None,
                                        description: None,
                                        language_version: Some(
                                            "default",
                                        ),
                                        log_file: None,
                                        require_serial: None,
                                        stages: None,
                                        verbose: None,
                                        minimum_prek_version: None,
                                    },
                                },
                                ManifestHook {
                                    id: "hook-2",
                                    name: "hook 2",
                                    entry: "echo hello world",
                                    language: System,
                                    options: HookOptions {
                                        alias: None,
                                        files: None,
                                        exclude: None,
                                        types: None,
                                        types_or: None,
                                        exclude_types: None,
                                        additional_dependencies: None,
                                        args: None,
                                        always_run: None,
                                        fail_fast: None,
                                        pass_filenames: None,
                                        description: None,
                                        language_version: Some(
                                            "system",
                                        ),
                                        log_file: None,
                                        require_serial: None,
                                        stages: None,
                                        verbose: None,
                                        minimum_prek_version: None,
                                    },
                                },
                                ManifestHook {
                                    id: "hook-3",
                                    name: "hook 3",
                                    entry: "echo hello world",
                                    language: System,
                                    options: HookOptions {
                                        alias: None,
                                        files: None,
                                        exclude: None,
                                        types: None,
                                        types_or: None,
                                        exclude_types: None,
                                        additional_dependencies: None,
                                        args: None,
                                        always_run: None,
                                        fail_fast: None,
                                        pass_filenames: None,
                                        description: None,
                                        language_version: Some(
                                            "3.8",
                                        ),
                                        log_file: None,
                                        require_serial: None,
                                        stages: None,
                                        verbose: None,
                                        minimum_prek_version: None,
                                    },
                                },
                            ],
                        },
                    ),
                ],
                default_install_hook_types: None,
                default_language_version: None,
                default_stages: None,
                files: None,
                exclude: None,
                fail_fast: None,
                minimum_prek_version: None,
            },
        )
        "#);
    }

    #[test]
    fn test_read_config() -> Result<()> {
        let config = read_config(Path::new("tests/fixtures/uv-pre-commit-config.yaml"))?;
        insta::assert_debug_snapshot!(config);
        Ok(())
    }

    #[test]
    fn test_read_manifest() -> Result<()> {
        let manifest = read_manifest(Path::new("tests/fixtures/uv-pre-commit-hooks.yaml"))?;
        insta::assert_debug_snapshot!(manifest);
        Ok(())
    }

    #[test]
    fn test_minimum_prek_version() {
        // Test that missing minimum_prek_version field doesn't cause an error
        let yaml = indoc::indoc! {r"
            repos:
              - repo: local
                hooks:
                  - id: test-hook
                    name: Test Hook
                    entry: echo test
                    language: system
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        assert!(result.is_ok());
        let config = result.unwrap();
        assert!(config.minimum_prek_version.is_none());

        // Test that empty minimum_prek_version field is treated as None
        let yaml = indoc::indoc! {r"
            repos:
              - repo: local
                hooks:
                  - id: test-hook
                    name: Test Hook
                    entry: echo test
                    language: system
            minimum_prek_version: ''
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        assert!(result.is_ok());
        let config = result.unwrap();
        assert!(config.minimum_prek_version.is_none());

        // Test that valid minimum_prek_version field works in top-level config
        let yaml = indoc::indoc! {r"
            repos:
              - repo: local
                hooks:
                  - id: test-hook
                    name: Test Hook
                    entry: echo test
                    language: system
            minimum_prek_version: '10.0.0'
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        assert!(result.is_err());

        // Test that valid minimum_prek_version field works in hook config
        let yaml = indoc::indoc! {r"
            repos:
              - repo: local
                hooks:
                  - id: test-hook
                    name: Test Hook
                    entry: echo test
                    language: system
                    minimum_prek_version: '10.0.0'
        "};
        let result = serde_yaml::from_str::<Config>(yaml);
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_type_tags() {
        // Valid tags should parse successfully
        let yaml_valid = r"
            repos:
              - repo: local
                hooks:
                  - id: my-hook
                    name: My Hook
                    entry: echo
                    language: system
                    types: [python, file]
                    types_or: [text, binary]
                    exclude_types: [symlink]
        ";
        let result = serde_yaml::from_str::<Config>(yaml_valid);
        assert!(result.is_ok(), "Should parse valid tags successfully");

        // Empty lists and missing keys should also be fine
        let yaml_empty = r"
            repos:
              - repo: local
                hooks:
                  - id: my-hook
                    name: My Hook
                    entry: echo
                    language: system
                    types: []
                    exclude_types: []
                    # types_or is missing, which is also valid
        ";
        let result_empty = serde_yaml::from_str::<Config>(yaml_empty);
        assert!(
            result_empty.is_ok(),
            "Should parse empty/missing tags successfully"
        );

        // Invalid tag in 'types' should fail
        let yaml_invalid_types = r"
            repos:
              - repo: local
                hooks:
                  - id: my-hook
                    name: My Hook
                    entry: echo
                    language: system
                    types: [pythoon] # Deliberate typo
        ";
        let result_invalid_types = serde_yaml::from_str::<Config>(yaml_invalid_types);
        assert!(result_invalid_types.is_err());

        assert!(
            result_invalid_types
                .unwrap_err()
                .to_string()
                .contains("Type tag \"pythoon\" is not recognized")
        );

        // Invalid tag in 'types_or' should fail
        let yaml_invalid_types_or = r"
            repos:
              - repo: local
                hooks:
                  - id: my-hook
                    name: My Hook
                    entry: echo
                    language: system
                    types_or: [invalidtag]
        ";
        let result_invalid_types_or = serde_yaml::from_str::<Config>(yaml_invalid_types_or);
        assert!(result_invalid_types_or.is_err());
        assert!(
            result_invalid_types_or
                .unwrap_err()
                .to_string()
                .contains("Type tag \"invalidtag\" is not recognized")
        );

        // Invalid tag in 'exclude_types' should fail
        let yaml_invalid_exclude_types = r"
            repos:
              - repo: local
                hooks:
                  - id: my-hook
                    name: My Hook
                    entry: echo
                    language: system
                    exclude_types: [not-a-real-tag]
        ";
        let result_invalid_exclude_types =
            serde_yaml::from_str::<Config>(yaml_invalid_exclude_types);
        assert!(result_invalid_exclude_types.is_err());
        assert!(
            result_invalid_exclude_types
                .unwrap_err()
                .to_string()
                .contains("Type tag \"not-a-real-tag\" is not recognized")
        );
    }

    #[test]
    fn read_config_with_merge_keys() -> Result<()> {
        let yaml = indoc::indoc! {r#"
            repos:
              - repo: local
                hooks:
                  - id: mypy-local
                    name: Local mypy
                    entry: python tools/pre_commit/mypy.py 0 "local"
                    <<: &mypy_common
                      language: python
                      types_or: [python, pyi]
                  - id: mypy-3.10
                    name: Mypy 3.10
                    entry: python tools/pre_commit/mypy.py 1 "3.10"
                    <<: *mypy_common
        "#};

        let mut file = tempfile::NamedTempFile::new()?;
        file.write_all(yaml.as_bytes())?;

        let config = read_config(file.path())?;
        insta::assert_debug_snapshot!(config, @r#"
        Config {
            repos: [
                Local(
                    LocalRepo {
                        hooks: [
                            ManifestHook {
                                id: "mypy-local",
                                name: "Local mypy",
                                entry: "python tools/pre_commit/mypy.py 0 \"local\"",
                                language: Python,
                                options: HookOptions {
                                    alias: None,
                                    files: None,
                                    exclude: None,
                                    types: None,
                                    types_or: Some(
                                        [
                                            "python",
                                            "pyi",
                                        ],
                                    ),
                                    exclude_types: None,
                                    additional_dependencies: None,
                                    args: None,
                                    always_run: None,
                                    fail_fast: None,
                                    pass_filenames: None,
                                    description: None,
                                    language_version: None,
                                    log_file: None,
                                    require_serial: None,
                                    stages: None,
                                    verbose: None,
                                    minimum_prek_version: None,
                                },
                            },
                            ManifestHook {
                                id: "mypy-3.10",
                                name: "Mypy 3.10",
                                entry: "python tools/pre_commit/mypy.py 1 \"3.10\"",
                                language: Python,
                                options: HookOptions {
                                    alias: None,
                                    files: None,
                                    exclude: None,
                                    types: None,
                                    types_or: Some(
                                        [
                                            "python",
                                            "pyi",
                                        ],
                                    ),
                                    exclude_types: None,
                                    additional_dependencies: None,
                                    args: None,
                                    always_run: None,
                                    fail_fast: None,
                                    pass_filenames: None,
                                    description: None,
                                    language_version: None,
                                    log_file: None,
                                    require_serial: None,
                                    stages: None,
                                    verbose: None,
                                    minimum_prek_version: None,
                                },
                            },
                        ],
                    },
                ),
            ],
            default_install_hook_types: None,
            default_language_version: None,
            default_stages: None,
            files: None,
            exclude: None,
            fail_fast: None,
            minimum_prek_version: None,
        }
        "#);

        Ok(())
    }
}
