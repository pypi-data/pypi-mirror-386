use std::borrow::Cow;
use std::ffi::OsStr;
#[cfg(feature = "macchina")]
use std::fs;
use std::io::{Write as _};
#[cfg(windows)]
use std::io::{self};
use std::path::PathBuf;
use std::process::Command;
use std::sync::OnceLock;
use std::{env, fmt};

use aho_corasick::AhoCorasick;
use anyhow::{Context as _, Result};
use indexmap::IndexMap;
use itertools::Itertools as _;
#[cfg(windows)]
use anyhow::anyhow;
#[cfg(windows)]
use crate::utils::find_file;
#[cfg(windows)]
use std::path::Path;
#[cfg(windows)]
use normpath::PathExt as _;
#[cfg(windows)]
use same_file::is_same_file;
use serde::{Deserialize, Serialize};
use strum::AsRefStr;
#[cfg(feature = "macchina")]
use toml_edit::{value, DocumentMut, Item, Table};
use tracing::debug;
use unicode_segmentation::UnicodeSegmentation as _;
use which::which;
use crate::ascii::{RawAsciiArt, RecoloredAsciiArt};
use crate::color_util::{printc, NeofetchAsciiIndexedColor, PresetIndexedColor};
use crate::distros::Distro;
use crate::types::{AnsiMode, Backend};
use crate::utils::{find_in_path, get_cache_path, input, process_command_status};

pub const TEST_ASCII: &str = r####################"
### |\___/| ###
### )     ( ###
## =\     /= ##
#### )===( ####
### /     \ ###
### |     | ###
## / {txt} \ ##
## \       / ##
_/\_\_   _/_/\_
|##|  ( (  |##|
|##|   ) ) |##|
|##|  (_(  |##|
"####################;

pub const NEOFETCH_COLOR_PATTERNS: [&str; 6] =
    ["${c1}", "${c2}", "${c3}", "${c4}", "${c5}", "${c6}"];
pub static NEOFETCH_COLORS_AC: OnceLock<AhoCorasick> = OnceLock::new();
pub const NEOFETCH_SCRIPT: &str = include_str!(concat!(env!("OUT_DIR"), "/neofetch"));

#[derive(Clone, Eq, PartialEq, Debug, AsRefStr, Deserialize, Serialize)]
#[serde(tag = "mode")]
#[serde(rename_all = "lowercase")]
#[strum(serialize_all = "lowercase")]
pub enum ColorAlignment {
    Horizontal,
    Vertical,
    Custom {
        #[serde(rename = "custom_colors")]
        #[serde(deserialize_with = "crate::utils::index_map_serde::deserialize")]
        colors: IndexMap<NeofetchAsciiIndexedColor, PresetIndexedColor>,
    },
}

/// Asks the user to provide an input among a list of options.
pub fn literal_input<'a, S1, S2>(
    prompt: S1,
    options: &'a [S2],
    default: &str,
    show_options: bool,
    color_mode: AnsiMode,
) -> Result<&'a str>
where
    S1: AsRef<str>,
    S2: AsRef<str>,
{
    let prompt = prompt.as_ref();

    if show_options {
        let options_text = options
            .iter()
            .map(|o| {
                let o = o.as_ref();

                if o == default {
                    format!("&l&n{o}&L&N")
                } else {
                    o.to_owned()
                }
            })
            .collect::<Vec<_>>()
            .join("|");
        printc(format!("{prompt} ({options_text})"), color_mode)
            .context("failed to print input prompt")?;
    } else {
        printc(format!("{prompt} (default: {default})"), color_mode)
            .context("failed to print input prompt")?;
    }

    loop {
        let selection = input(Some("> ")).context("failed to read input")?;
        let selection = if selection.is_empty() {
            default.to_owned()
        } else {
            selection.to_lowercase()
        };

        if let Some(selected) = find_selection(&selection, options) {
            println!();

            return Ok(selected);
        } else {
            let options_text = options.iter().map(AsRef::as_ref).join("|");
            println!("Invalid selection! {selection} is not one of {options_text}");
        }
    }

    fn find_selection<'a, S>(sel: &str, options: &'a [S]) -> Option<&'a str>
    where
        S: AsRef<str>,
    {
        if sel.is_empty() {
            return None;
        }

        // Find exact match
        if let Some(selected) = options.iter().find(|&o| o.as_ref().to_lowercase() == sel) {
            return Some(selected.as_ref());
        }

        // Find starting abbreviation
        if let Some(selected) = options
            .iter()
            .find(|&o| o.as_ref().to_lowercase().starts_with(sel))
        {
            return Some(selected.as_ref());
        }

        None
    }
}

/// Add the PyPI pacakge path to the PATH environment variable (for this local process only).
/// This is done so that `which` can find the commands inside the PyPI package.
pub fn add_pkg_path() -> Result<()> {
    // Get PATH
    let pv = &env::var_os("PATH").context("`PATH` env var is not set or invalid")?;
    let mut path = env::split_paths(pv).collect::<Vec<_>>();
    let exe = env::current_exe().context("failed to get path of current running executable")?;
    let base = exe.parent().unwrap();

    // Add from bin: ../git, ../fastfetch, ../scripts
    let to_add = ["git", "fastfetch", "scripts", "fastfetch/usr/bin"];
    if let Some(parent) = base.parent() {
        path.extend(to_add.iter().map(|d| parent.join(d)));
    }

    // Add from cwd: ./hyfetch/git, ./hyfetch/fastfetch, ./hyfetch/scripts
    path.extend(to_add.iter().map(|d| PathBuf::from("hyfetch").join(d)));

    // Set PATH
    env::set_var("PATH", env::join_paths(path).context("failed to join paths")?);
    debug!("Added PyPI package path to PATH, PATH={}", env::var("PATH")?);

    Ok(())
}

/// Gets the absolute path of the [neofetch] command.
///
/// [neofetch]: https://github.com/hykilpikonna/hyfetch#running-updated-original-neofetch
pub fn neofetch_path() -> Result<PathBuf> {
    if let Ok(p) = which("neowofetch") {
        return Ok(p);
    }

    // Instead of doing that, let's write the neofetch script to a temp file
    let f: PathBuf = get_cache_path().context("Failed to get cache path")?.join("nf_script.sh");
    let mut file = fs::File::create(&f).context("Failed to create neofetch script file")?;
    file.write_all(NEOFETCH_SCRIPT.as_bytes())
        .context("Failed to write neofetch script to file")?;

    Ok(f)
}

/// Gets the absolute path of the [macchina] command.
///
/// [macchina]: https://github.com/Macchina-CLI/macchina
#[cfg(feature = "macchina")]
pub fn macchina_path() -> Result<Option<PathBuf>> {
    let macchina_path = {
        #[cfg(not(windows))]
        {
            find_in_path("macchina").context("failed to check existence of `macchina` in `PATH`")?
        }
        #[cfg(windows)]
        {
            find_in_path("macchina.exe")
                .context("failed to check existence of `macchina.exe` in `PATH`")?
        }
    };

    // Fall back to `macchina.exe` in directory of current executable
    #[cfg(windows)]
    let macchina_path = macchina_path.map_or_else(
        || {
            let current_exe_path: PathBuf = env::current_exe()
                .and_then(|p| p.normalize().map(|p| p.into()))
                .context("failed to get path of current running executable")?;
            let current_exe_dir_path = current_exe_path
                .parent()
                .expect("parent should not be `None`");
            let macchina_path = current_exe_dir_path.join("macchina.exe");
            find_file(&macchina_path)
                .with_context(|| format!("failed to check existence of file {macchina_path:?}"))
        },
        |path| Ok(Some(path)),
    )?;

    Ok(macchina_path)
}

/// Gets the distro ascii of the current distro. Or if distro is specified, get
/// the specific distro's ascii art instead.
#[tracing::instrument(level = "debug")]
pub fn get_distro_ascii<S>(distro: Option<S>, backend: Backend) -> Result<RawAsciiArt>
where
    S: AsRef<str> + fmt::Debug,
{
    let distro: Cow<_> = if let Some(distro) = distro.as_ref() {
        distro.as_ref().into()
    } else {
        get_distro_name(backend)
            .context("failed to get distro name")?
            .into()
    };
    debug!(%distro, "distro name");

    // Try new codegen-based detection method
    if let Some(distro) = Distro::detect(&distro) {
        let asc = distro.ascii_art().to_owned();
        let fg = ascii_foreground(&distro);

        return Ok(RawAsciiArt { asc, fg });
    }

    debug!(%distro, "could not find a match for distro; falling back to neofetch");

    // Old detection method that calls neofetch
    let asc = run_neofetch_command_piped(&["print_ascii", "--ascii_distro", distro.as_ref()])
        .context("failed to get ascii art from neofetch")?;

    // Unescape backslashes here because backslashes are escaped in neofetch for
    // printf
    let asc = asc.replace(r"\\", r"\");

    Ok(RawAsciiArt {
        asc,
        fg: Vec::new(),
    })
}

#[tracing::instrument(level = "debug", skip(asc), fields(asc.w = asc.w, asc.h = asc.h))]
pub fn run(asc: RecoloredAsciiArt, backend: Backend, args: Option<&Vec<String>>) -> Result<()> {
    let asc = asc.lines.join("\n");

    match backend {
        Backend::Neofetch => run_neofetch(asc, args).context("failed to run neofetch")?,
        Backend::Fastfetch => run_fastfetch(asc, args).context("failed to run fastfetch")?,
        #[cfg(feature = "macchina")]
        Backend::Macchina => run_macchina(asc, args).context("failed to run macchina")?,
    }

    Ok(())
}

/// Gets distro ascii width and height, ignoring color code.
pub fn ascii_size<S>(asc: S) -> Result<(u16, u16)>
where
    S: AsRef<str>,
{
    let asc = asc.as_ref();

    if asc.is_empty() {
        return Ok((0, 0));
    }

    let asc = {
        let ac =
            NEOFETCH_COLORS_AC.get_or_init(|| AhoCorasick::new(NEOFETCH_COLOR_PATTERNS).unwrap());
        const N: usize = NEOFETCH_COLOR_PATTERNS.len();
        const REPLACEMENTS: [&str; N] = [""; N];
        ac.replace_all(asc, &REPLACEMENTS)
    };

    if asc.is_empty() {
        return Ok((0, 0));
    }

    let width = asc.lines()
        .map(|line| line.graphemes(true).count()).max()
        .expect("line iterator should not be empty");
    let width: u16 = width.try_into().context("ascii art width should fit in u16")?;
    let height: u16 = asc.lines().count().try_into().context("ascii art height should fit in u16")?;
    Ok((width, height))
}

/// Gets the absolute path of the bash command.
#[cfg(windows)]
fn bash_path() -> Result<PathBuf> {
    // Find `bash.exe` in `PATH`, but exclude the known bad paths
    if let Some(bash_path) = find_in_path("bash.exe").context("bash.exe not found")? {
        // Check if it's not MSYS bash https://stackoverflow.com/a/58418686/1529493
        if !bash_path.ends_with(r"Git\usr\bin\bash.exe") {
            // Check if it's not WSL bash
            // See https://github.com/hykilpikonna/hyfetch/issues/233
            let windir = env::var_os("windir").context("`windir` environ not found")?;
            match is_same_file(&bash_path, Path::new(&windir).join(r"System32\bash.exe")) {
                Ok(false) => return Ok(bash_path),
                Err(err) if err.kind() == io::ErrorKind::NotFound => return Ok(bash_path),
                _ => {}
            }
        }
    }

    if let Some(bash_path) = find_in_path("git.exe").context("failed to find `git.exe` in `PATH`")? {
        if bash_path.ends_with(r"Git\cmd\git.exe") {
            let pth = bash_path.parent().unwrap().parent().unwrap().join(r"bin\bash.exe");
            if pth.is_file() {
                return Ok(pth);
            }
        }
    }

    Err(anyhow!("bash.exe not found"))
}

/// Runs neofetch command, returning the piped stdout output.
fn run_neofetch_command_piped<S>(args: &[S]) -> Result<String>
where
    S: AsRef<OsStr> + fmt::Debug,
{
    let mut command = make_neofetch_command(args)?;

    let output = command
        .output()
        .context("failed to execute neofetch as child process")?;
    debug!(?output, "neofetch output");
    process_command_status(&output.status).context("neofetch command exited with error")?;

    let out = String::from_utf8(output.stdout)
        .context("failed to process neofetch output as it contains invalid UTF-8")?
        .trim()
        .to_owned();
    Ok(out)
}

fn make_neofetch_command<S>(args: &[S]) -> Result<Command>
where
    S: AsRef<OsStr>,
{
    // Find neofetch script
    let neofetch_path = neofetch_path().context("neofetch command not found")?;

    debug!(?neofetch_path, "neofetch path");

    #[cfg(not(windows))]
    {
        let mut command = Command::new("bash");
        command.arg(neofetch_path);
        command.args(args);
        Ok(command)
    }
    #[cfg(windows)]
    {
        let bash_path = bash_path().context("failed to get bash path")?;
        let mut command = Command::new(bash_path);
        command.arg(neofetch_path);
        command.args(args);
        Ok(command)
    }
}

/// Runs fastfetch command, returning the piped stdout output.
fn run_fastfetch_command_piped<S>(args: &[S]) -> Result<String>
where
    S: AsRef<OsStr> + fmt::Debug,
{
    let mut command = make_fastfetch_command(args)?;

    let output = command
        .output()
        .context("failed to execute fastfetch as child process")?;
    debug!(?output, "fastfetch output");
    process_command_status(&output.status).context("fastfetch command exited with error")?;

    let out = String::from_utf8(output.stdout)
        .context("failed to process fastfetch output as it contains invalid UTF-8")?
        .trim()
        .to_owned();
    Ok(out)
}

pub fn fastfetch_path() -> Result<PathBuf> {
    which("fastfetch").context("fastfetch command not found")
}

fn make_fastfetch_command<S>(args: &[S]) -> Result<Command>
where
    S: AsRef<OsStr>,
{
    // Find fastfetch executable
    let ff_path = fastfetch_path()?;
    debug!(?ff_path, "fastfetch path");

    let mut command = Command::new(ff_path);
    command.env("FFTS_IGNORE_PARENT", "1");
    command.args(args);
    Ok(command)
}

/// Runs macchina command, returning the piped stdout output.
#[cfg(feature = "macchina")]
fn run_macchina_command_piped<S>(args: &[S]) -> Result<String>
where
    S: AsRef<OsStr> + fmt::Debug,
{
    let mut command = make_macchina_command(args)?;

    let output = command
        .output()
        .context("failed to execute macchina as child process")?;
    debug!(?output, "macchina output");
    process_command_status(&output.status).context("macchina command exited with error")?;

    let out = String::from_utf8(output.stdout)
        .context("failed to process macchina output as it contains invalid UTF-8")?
        .trim()
        .to_owned();
    Ok(out)
}

#[cfg(feature = "macchina")]
fn make_macchina_command<S>(args: &[S]) -> Result<Command>
where
    S: AsRef<OsStr>,
{
    // Find macchina executable
    let macchina_path = macchina_path()
        .context("failed to get macchina path")?
        .context("macchina command not found")?;

    debug!(?macchina_path, "macchina path");

    let mut command = Command::new(macchina_path);
    command.args(args);
    Ok(command)
}

#[tracing::instrument(level = "debug")]
pub fn get_distro_name(backend: Backend) -> Result<String> {
    match backend {
        Backend::Neofetch => run_neofetch_command_piped(&["ascii_distro_name"])
            .context("failed to get distro name from neofetch"),
        Backend::Fastfetch => Ok(run_fastfetch_command_piped(&["--logo", "none", "-c", "none", "-s", "OS",])
            .context("failed to get distro name from fastfetch")?.replace("OS: ", "")),
        #[cfg(feature = "macchina")]
        Backend::Macchina => {
            // Write ascii art to temp file
            let asc_file_path = {
                let mut temp_file = tempfile::Builder::new()
                    .suffix("ascii.txt")
                    .tempfile()
                    .context("failed to create temp file for ascii art")?;
                temp_file
                    .write_all(b"\t\n\t\n")
                    .context("failed to write ascii art to temp file")?;
                temp_file.into_temp_path()
            };

            // Write macchina theme to temp file
            let theme_file_path = {
                let project_dirs = directories::ProjectDirs::from("", "", "macchina")
                    .context("failed to get base dirs")?;
                let themes_path = project_dirs.config_dir().join("themes");
                fs::create_dir_all(&themes_path).with_context(|| {
                    format!("failed to create macchina themes dir {themes_path:?}")
                })?;
                let mut temp_file = tempfile::Builder::new()
                    .suffix("theme.toml")
                    .tempfile_in(themes_path)
                    .context("failed to create temp file for macchina theme")?;
                let theme_doc = {
                    let mut doc = DocumentMut::new();
                    doc["spacing"] = value(0);
                    doc["padding"] = value(0);
                    // See https://github.com/Macchina-CLI/macchina/issues/319
                    // doc["hide_ascii"] = value(true);
                    doc["separator"] = value("");
                    doc["custom_ascii"] = Item::Table(Table::from_iter([(
                        "path",
                        &*asc_file_path.to_string_lossy(),
                    )]));
                    doc["keys"] = Item::Table(Table::from_iter([("os", ""), ("distro", "")]));
                    doc
                };
                debug!(%theme_doc, "macchina theme");
                temp_file
                    .write_all(theme_doc.to_string().as_bytes())
                    .context("failed to write macchina theme to temp file")?;
                temp_file.into_temp_path()
            };

            let args: [&OsStr; 4] = [
                "--show".as_ref(),
                if cfg!(target_os = "linux") {
                    "distribution"
                } else {
                    "operating-system"
                }
                .as_ref(),
                "--theme".as_ref(),
                theme_file_path
                    .file_stem()
                    .expect("file name should not be `None`"),
            ];
            run_macchina_command_piped(&args[..])
                .map(|s| {
                    anstream::adapter::strip_str(&s)
                        .to_string()
                        .trim()
                        .to_owned()
                })
                .context("failed to get distro name from macchina")
        },
    }
}

/// Runs neofetch with custom ascii art.
#[tracing::instrument(level = "debug", skip(asc))]
fn run_neofetch(asc: String, args: Option<&Vec<String>>) -> Result<()> {
    // Escape backslashes here because backslashes are escaped in neofetch for
    // printf
    let asc = asc.replace('\\', r"\\");

    // Write ascii art to temp file
    let asc_file_path = {
        let mut temp_file = tempfile::Builder::new()
            .suffix("ascii.txt")
            .tempfile()
            .context("failed to create temp file for ascii art")?;
        temp_file
            .write_all(asc.as_bytes())
            .context("failed to write ascii art to temp file")?;
        temp_file.into_temp_path()
    };

    // Call neofetch
    let args = {
        let mut v: Vec<Cow<OsStr>> = vec![
            OsStr::new("--ascii").into(),
            OsStr::new("--source").into(),
            OsStr::new(&asc_file_path).into(),
            OsStr::new("--ascii_colors").into(),
        ];
        if let Some(args) = args {
            v.extend(args.iter().map(|arg| OsStr::new(arg).into()));
        }
        v
    };
    let mut command = make_neofetch_command(&args[..])?;

    debug!(?command, "neofetch command");

    let status = command
        .status()
        .context("failed to execute neofetch command as child process")?;
    process_command_status(&status).context("neofetch command exited with error")?;

    Ok(())
}

/// Runs fastfetch with custom ascii art.
#[tracing::instrument(level = "debug", skip(asc))]
fn run_fastfetch(asc: String, args: Option<&Vec<String>>) -> Result<()> {
    // Write ascii art to temp file
    let asc_file_path = {
        let mut temp_file = tempfile::Builder::new()
            .suffix("ascii.txt")
            .tempfile()
            .context("failed to create temp file for ascii art")?;
        temp_file
            .write_all(asc.as_bytes())
            .context("failed to write ascii art to temp file")?;
        temp_file.into_temp_path()
    };

    // Call fastfetch
    let args = {
        let mut v: Vec<Cow<OsStr>> = vec![
            OsStr::new("--file-raw").into(),
            OsStr::new(&asc_file_path).into(),
        ];
        if let Some(args) = args {
            v.extend(args.iter().map(|arg| OsStr::new(arg).into()));
        }
        v
    };
    let mut command = make_fastfetch_command(&args[..])?;

    debug!(?command, "fastfetch command");

    let status = command
        .status()
        .context("failed to execute fastfetch command as child process")?;
    process_command_status(&status).context("fastfetch command exited with error")?;

    Ok(())
}

/// Runs macchina with custom ascii art.
#[cfg(feature = "macchina")]
#[tracing::instrument(level = "debug", skip(asc))]
fn run_macchina(asc: String, args: Option<&Vec<String>>) -> Result<()> {
    // Write ascii art to temp file
    let asc_file_path = {
        let mut temp_file = tempfile::Builder::new()
            .suffix("ascii.txt")
            .tempfile()
            .context("failed to create temp file for ascii art")?;
        temp_file
            .write_all(asc.as_bytes())
            .context("failed to write ascii art to temp file")?;
        temp_file.into_temp_path()
    };

    // Write macchina theme to temp file
    let theme_file_path = {
        let project_dirs = directories::ProjectDirs::from("", "", "macchina")
            .context("failed to get base dirs")?;
        let themes_path = project_dirs.config_dir().join("themes");
        fs::create_dir_all(&themes_path)
            .with_context(|| format!("failed to create macchina themes dir {themes_path:?}"))?;
        let mut temp_file = tempfile::Builder::new()
            .suffix("theme.toml")
            .tempfile_in(themes_path)
            .context("failed to create temp file for macchina theme")?;
        let theme_doc = {
            let mut doc = DocumentMut::new();
            doc["custom_ascii"] = Item::Table(Table::from_iter([(
                "path",
                &*asc_file_path.to_string_lossy(),
            )]));
            doc
        };
        debug!(%theme_doc, "macchina theme");
        temp_file
            .write_all(theme_doc.to_string().as_bytes())
            .context("failed to write macchina theme to temp file")?;
        temp_file.into_temp_path()
    };

    let args = {
        let mut v: Vec<Cow<OsStr>> = vec![
            OsStr::new("--theme").into(),
            theme_file_path
                .file_stem()
                .expect("file name should not be `None`")
                .into(),
        ];
        if let Some(args) = args {
            v.extend(args.iter().map(|arg| OsStr::new(arg).into()));
        }
        v
    };
    let mut command = make_macchina_command(&args[..])?;

    debug!(?command, "macchina command");

    let status = command
        .status()
        .context("failed to execute macchina command as child process")?;
    process_command_status(&status).context("macchina command exited with error")?;

    Ok(())
}

/// Gets the color indices that should be considered as foreground, for a
/// particular distro's ascii art.
fn ascii_foreground(distro: &Distro) -> Vec<NeofetchAsciiIndexedColor> {
    let fg: Vec<u8> = match distro {
        Distro::Anarchy => vec![2],
        Distro::Android => vec![2],
        Distro::Antergos => vec![1],
        Distro::ArchStrike => vec![2],
        Distro::Arkane => vec![1],
        Distro::Asahi => vec![5],
        Distro::Astra_Linux => vec![2],
        Distro::BlackArch => vec![3],
        Distro::CelOS => vec![3],
        Distro::Chapeau => vec![2],
        Distro::Chrom => vec![5],
        Distro::Clear_Linux_OS => vec![2],
        Distro::Container_Linux_by_CoreOS => vec![3],
        Distro::CRUX => vec![3],
        Distro::EuroLinux => vec![2],
        Distro::eweOS => vec![3],
        Distro::Fedora => vec![2],
        Distro::Fedora_Sericea => vec![2],
        Distro::Fedora_Silverblue => vec![2],
        Distro::GalliumOS => vec![2],
        Distro::Gentoo => vec![1],
        Distro::HarDClanZ => vec![2],
        Distro::Kibojoe => vec![3],
        Distro::KrassOS => vec![2],
        Distro::Kubuntu => vec![2],
        Distro::Linux => vec![1],
        Distro::LinuxFromScratch => vec![1, 3],
        Distro::Lubuntu => vec![2],
        Distro::openEuler => vec![2],
        Distro::orchid => vec![1],
        Distro::Panwah => vec![1],
        Distro::Peppermint => vec![2],
        Distro::PNM_Linux => vec![2],
        Distro::Pop__OS => vec![2],
        Distro::Reborn_OS => vec![1],
        Distro::SalentOS => vec![4],
        Distro::Septor => vec![2],
        Distro::Ubuntu_Cinnamon => vec![2],
        Distro::Ubuntu_Kylin => vec![2],
        Distro::Ubuntu_MATE => vec![2],
        Distro::Ubuntu_old => vec![2],
        Distro::Ubuntu_Studio => vec![2],
        Distro::Ubuntu_Sway => vec![2],
        Distro::Ultramarine_Linux => vec![2],
        Distro::Univention => vec![2],
        Distro::uwuntu => vec![2],
        Distro::Vanilla => vec![2],
        Distro::VNux => vec![3, 5],
        Distro::Void => vec![2],
        Distro::Xray_OS => vec![2, 3],
        Distro::Xubuntu => vec![2],
        _ => Vec::new(),
    };

    fg.into_iter()
        .map(|fore| {
            fore.try_into()
                .expect("`fore` should be a valid neofetch color index")
        })
        .collect()
}
