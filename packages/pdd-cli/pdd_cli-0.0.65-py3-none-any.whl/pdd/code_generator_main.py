import os
import re
import asyncio
import json
import pathlib
import shlex
import subprocess
import requests
import tempfile
import sys
from typing import Optional, Tuple, Dict, Any, List

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Relative imports for PDD package structure
from . import DEFAULT_STRENGTH, DEFAULT_TIME, EXTRACTION_STRENGTH # Assuming these are in __init__.py
from .construct_paths import construct_paths
from .preprocess import preprocess as pdd_preprocess
from .code_generator import code_generator as local_code_generator_func
from .incremental_code_generator import incremental_code_generator as incremental_code_generator_func
from .get_jwt_token import get_jwt_token, AuthError, NetworkError, TokenError, UserCancelledError, RateLimitError
from .python_env_detector import detect_host_python_executable

# Environment variable names for Firebase/GitHub auth
FIREBASE_API_KEY_ENV_VAR = "NEXT_PUBLIC_FIREBASE_API_KEY" 
GITHUB_CLIENT_ID_ENV_VAR = "GITHUB_CLIENT_ID"
PDD_APP_NAME = "PDD Code Generator"

# Cloud function URL
CLOUD_GENERATE_URL = "https://us-central1-prompt-driven-development.cloudfunctions.net/generateCode"
CLOUD_REQUEST_TIMEOUT = 400  # seconds

console = Console()

# --- Git Helper Functions ---
def _run_git_command(command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Runs a git command and returns (return_code, stdout, stderr)."""
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False, cwd=cwd, encoding='utf-8')
        return process.returncode, process.stdout.strip(), process.stderr.strip()
    except FileNotFoundError:
        return -1, "", "Git command not found. Ensure git is installed and in your PATH."
    except Exception as e:
        return -2, "", f"Error running git command {' '.join(command)}: {e}"

def is_git_repository(path: Optional[str] = None) -> bool:
    """Checks if the given path (or current dir) is a git repository."""
    start_path = pathlib.Path(path).resolve() if path else pathlib.Path.cwd()
    # Check for .git in current or any parent directory
    current_path = start_path
    while True:
        if (current_path / ".git").is_dir():
            # Verify it's the root of the work tree or inside it
            returncode, stdout, _ = _run_git_command(["git", "rev-parse", "--is-inside-work-tree"], cwd=str(start_path))
            return returncode == 0 and stdout == "true"
        parent = current_path.parent
        if parent == current_path: # Reached root directory
            break
        current_path = parent
    return False


def _expand_vars(text: str, vars_map: Optional[Dict[str, str]]) -> str:
    """Replace $KEY and ${KEY} in text when KEY exists in vars_map. Leave others unchanged."""
    if not text or not vars_map:
        return text

    def repl_braced(m: re.Match) -> str:
        key = m.group(1)
        return vars_map.get(key, m.group(0))

    def repl_simple(m: re.Match) -> str:
        key = m.group(1)
        return vars_map.get(key, m.group(0))

    # Replace ${KEY} first, then $KEY
    text = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl_braced, text)
    text = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", repl_simple, text)
    return text


def _parse_front_matter(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Parse YAML front matter at the start of a prompt and return (meta, body)."""
    try:
        if not text.startswith("---\n"):
            return None, text
        end_idx = text.find("\n---", 4)
        if end_idx == -1:
            return None, text
        fm_body = text[4:end_idx]
        rest = text[end_idx + len("\n---"):]
        if rest.startswith("\n"):
            rest = rest[1:]
        import yaml as _yaml
        meta = _yaml.safe_load(fm_body) or {}
        if not isinstance(meta, dict):
            meta = {}
        return meta, rest
    except Exception:
        return None, text


def get_git_content_at_ref(file_path: str, git_ref: str = "HEAD") -> Optional[str]:
    """Gets the content of the file as it was at the specified git_ref."""
    abs_file_path = pathlib.Path(file_path).resolve()
    if not is_git_repository(str(abs_file_path.parent)):
        return None
    
    returncode_rev, git_root_str, stderr_rev = _run_git_command(["git", "rev-parse", "--show-toplevel"], cwd=str(abs_file_path.parent))
    if returncode_rev != 0:
        # console.print(f"[yellow]Git (rev-parse) warning for {file_path}: {stderr_rev}[/yellow]")
        return None
    
    git_root = pathlib.Path(git_root_str)
    try:
        relative_path = abs_file_path.relative_to(git_root)
    except ValueError:
        # console.print(f"[yellow]File {file_path} is not under git root {git_root}.[/yellow]")
        return None

    returncode, stdout, stderr = _run_git_command(["git", "show", f"{git_ref}:{relative_path.as_posix()}"], cwd=str(git_root))
    if returncode == 0:
        return stdout
    else:
        # File might not exist at that ref, or other git error.
        # if "does not exist" not in stderr and "exists on disk, but not in" not in stderr and console.is_terminal: # Be less noisy for common cases
        #     console.print(f"[yellow]Git (show) warning for {file_path} at {git_ref}: {stderr}[/yellow]")
        return None

def get_file_git_status(file_path: str) -> str:
    """Gets the git status of a single file (e.g., ' M', '??', 'A '). Empty if clean."""
    abs_file_path = pathlib.Path(file_path).resolve()
    if not is_git_repository(str(abs_file_path.parent)) or not abs_file_path.exists():
        return ""
    returncode, stdout, _ = _run_git_command(["git", "status", "--porcelain", str(abs_file_path)], cwd=str(abs_file_path.parent))
    if returncode == 0:
        # stdout might be " M path/to/file" or "?? path/to/file"
        # We only want the status codes part
        status_part = stdout.split(str(abs_file_path.name))[0].strip() if str(abs_file_path.name) in stdout else stdout.strip()
        return status_part
    return ""

def git_add_files(file_paths: List[str], verbose: bool = False) -> bool:
    """Stages the given files using 'git add'."""
    if not file_paths:
        return True
    
    # Resolve paths and ensure they are absolute for git command
    abs_paths = [str(pathlib.Path(fp).resolve()) for fp in file_paths]
    
    # Determine common parent directory to run git command from, or git root
    # For simplicity, assume they are in the same repo and run from one of their parents
    if not is_git_repository(str(pathlib.Path(abs_paths[0]).parent)):
        if verbose:
            console.print(f"[yellow]Cannot stage files: {abs_paths[0]} is not in a git repository.[/yellow]")
        return False
        
    returncode, _, stderr = _run_git_command(["git", "add"] + abs_paths, cwd=str(pathlib.Path(abs_paths[0]).parent))
    if returncode == 0:
        if verbose:
            console.print(f"Successfully staged: [cyan]{', '.join(abs_paths)}[/cyan]")
        return True
    else:
        console.print(f"[red]Error staging files with git:[/red] {stderr}")
        return False
# --- End Git Helper Functions ---


def code_generator_main(
    ctx: click.Context,
    prompt_file: str,
    output: Optional[str],
    original_prompt_file_path: Optional[str],
    force_incremental_flag: bool,
    env_vars: Optional[Dict[str, str]] = None,
) -> Tuple[str, bool, float, str]:
    """
    CLI wrapper for generating code from prompts. Handles full and incremental generation,
    local vs. cloud execution, and output.
    """
    cli_params = ctx.obj or {}
    is_local_execution_preferred = cli_params.get('local', False)
    strength = cli_params.get('strength', DEFAULT_STRENGTH)
    temperature = cli_params.get('temperature', 0.0)
    time_budget = cli_params.get('time', DEFAULT_TIME)
    verbose = cli_params.get('verbose', False)
    force_overwrite = cli_params.get('force', False)
    quiet = cli_params.get('quiet', False)

    generated_code_content: Optional[str] = None
    was_incremental_operation = False
    total_cost = 0.0
    model_name = "unknown"

    input_file_paths_dict: Dict[str, str] = {"prompt_file": prompt_file}
    if original_prompt_file_path:
        input_file_paths_dict["original_prompt_file"] = original_prompt_file_path
    
    command_options: Dict[str, Any] = {"output": output}

    try:
        resolved_config, input_strings, output_file_paths, language = construct_paths(
            input_file_paths=input_file_paths_dict,
            force=force_overwrite,
            quiet=quiet,
            command="generate",
            command_options=command_options,
            context_override=ctx.obj.get('context')
        )
        prompt_content = input_strings["prompt_file"]
        # Phase-2 templates: parse front matter metadata
        fm_meta, body = _parse_front_matter(prompt_content)
        if fm_meta:
            prompt_content = body
        # Determine final output path: if user passed a directory, use resolved file path
        resolved_output = output_file_paths.get("output")
        if output is None:
            output_path = resolved_output
        else:
            try:
                is_dir_hint = output.endswith(os.path.sep) or output.endswith("/")
            except Exception:
                is_dir_hint = False
            if is_dir_hint or os.path.isdir(output):
                output_path = resolved_output
            else:
                output_path = output

    except FileNotFoundError as e:
        console.print(f"[red]Error: Input file not found: {e.filename}[/red]")
        return "", False, 0.0, "error"
    except Exception as e:
        console.print(f"[red]Error during path construction: {e}[/red]")
        return "", False, 0.0, "error"

    can_attempt_incremental = False
    existing_code_content: Optional[str] = None
    original_prompt_content_for_incremental: Optional[str] = None

    # Merge -e vars with front-matter defaults; validate required
    if env_vars is None:
        env_vars = {}
    if fm_meta and isinstance(fm_meta.get("variables"), dict):
        for k, spec in (fm_meta["variables"].items()):
            if isinstance(spec, dict):
                if k not in env_vars and "default" in spec:
                    env_vars[k] = str(spec["default"])
            # if scalar default allowed, ignore for now
        missing = [k for k, spec in fm_meta["variables"].items() if isinstance(spec, dict) and spec.get("required") and k not in env_vars]
        if missing:
            console.print(f"[error]Missing required variables: {', '.join(missing)}")
            return "", False, 0.0, "error"

    # Execute optional discovery from front matter to populate env_vars without overriding explicit -e values
    def _run_discovery(discover_cfg: Dict[str, Any]) -> Dict[str, str]:
        results: Dict[str, str] = {}
        try:
            if not discover_cfg:
                return results
            enabled = discover_cfg.get("enabled", False)
            if not enabled:
                return results
            root = discover_cfg.get("root", ".")
            patterns = discover_cfg.get("patterns", []) or []
            exclude = discover_cfg.get("exclude", []) or []
            max_per = int(discover_cfg.get("max_per_pattern", 0) or 0)
            max_total = int(discover_cfg.get("max_total", 0) or 0)
            root_path = pathlib.Path(root).resolve()
            seen: List[str] = []
            def _match_one(patterns_list: List[str]) -> List[str]:
                matches: List[str] = []
                for pat in patterns_list:
                    globbed = list(root_path.rglob(pat))
                    for p in globbed:
                        if any(p.match(ex) for ex in exclude):
                            continue
                        sp = str(p.resolve())
                        if sp not in matches:
                            matches.append(sp)
                    if max_per and len(matches) >= max_per:
                        matches = matches[:max_per]
                        break
                return matches
            # If a mapping 'set' is provided, compute per-variable results
            set_map = discover_cfg.get("set") or {}
            if isinstance(set_map, dict) and set_map:
                for var_name, spec in set_map.items():
                    if var_name in env_vars:
                        continue  # don't override explicit -e
                    v_patterns = spec.get("patterns", []) if isinstance(spec, dict) else []
                    v_exclude = spec.get("exclude", []) if isinstance(spec, dict) else []
                    save_exclude = exclude
                    try:
                        if v_exclude:
                            exclude = v_exclude
                        matches = _match_one(v_patterns or patterns)
                    finally:
                        exclude = save_exclude
                    if matches:
                        results[var_name] = ",".join(matches)
                        seen.extend(matches)
            # Fallback: populate SCAN_FILES and SCAN metadata
            if not results:
                files = _match_one(patterns)
                if max_total and len(files) > max_total:
                    files = files[:max_total]
                if files:
                    results["SCAN_FILES"] = ",".join(files)
            # Always set root/patterns helpers
            if root:
                results.setdefault("SCAN_ROOT", str(root_path))
            if patterns:
                results.setdefault("SCAN_PATTERNS", ",".join(patterns))
        except Exception as e:
            if verbose and not quiet:
                console.print(f"[yellow]Discovery skipped due to error: {e}[/yellow]")
        return results

    if fm_meta and isinstance(fm_meta.get("discover"), dict):
        discovered = _run_discovery(fm_meta.get("discover") or {})
        for k, v in discovered.items():
            if k not in env_vars:
                env_vars[k] = v

    # Expand variables in output path if provided
    if output_path:
        output_path = _expand_vars(output_path, env_vars)

    # Honor front-matter output when CLI did not pass --output
    if output is None and fm_meta and isinstance(fm_meta.get("output"), str):
        try:
            meta_out = _expand_vars(fm_meta["output"], env_vars)
            if meta_out:
                output_path = str(pathlib.Path(meta_out).resolve())
        except Exception:
            pass

    # Honor front-matter language if provided (overrides detection for both local and cloud)
    if fm_meta and isinstance(fm_meta.get("language"), str) and fm_meta.get("language"):
        language = fm_meta.get("language")

    if output_path and pathlib.Path(output_path).exists():
        try:
            existing_code_content = pathlib.Path(output_path).read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read existing output file {output_path}: {e}[/yellow]")
            existing_code_content = None

        if existing_code_content is not None:
            if "original_prompt_file" in input_strings:
                original_prompt_content_for_incremental = input_strings["original_prompt_file"]
                can_attempt_incremental = True
                if verbose:
                    console.print(f"Using specified original prompt: [cyan]{original_prompt_file_path}[/cyan]")
            elif is_git_repository(str(pathlib.Path(prompt_file).parent)):
                # prompt_content is the current on-disk version
                head_prompt_content = get_git_content_at_ref(prompt_file, git_ref="HEAD")

                if head_prompt_content is not None:
                    # Compare on-disk content (prompt_content) with HEAD content
                    if prompt_content.strip() != head_prompt_content.strip():
                        # Uncommitted changes exist. Original is HEAD, new is on-disk.
                        original_prompt_content_for_incremental = head_prompt_content
                        can_attempt_incremental = True
                        if verbose:
                            console.print(f"On-disk [cyan]{prompt_file}[/cyan] has uncommitted changes. Using HEAD version as original prompt.")
                    else:
                        # On-disk is identical to HEAD. Search for a prior *different* version.
                        if verbose:
                            console.print(f"On-disk [cyan]{prompt_file}[/cyan] matches HEAD. Searching for a prior *different* version as original prompt.")

                        new_prompt_candidate = head_prompt_content # This is also prompt_content (on-disk)
                        found_different_prior = False
                        
                        git_root_path_obj: Optional[pathlib.Path] = None
                        prompt_file_rel_to_root_str: Optional[str] = None

                        try:
                            abs_prompt_file_path = pathlib.Path(prompt_file).resolve()
                            temp_git_root_rc, temp_git_root_str, temp_git_root_stderr = _run_git_command(
                                ["git", "rev-parse", "--show-toplevel"], 
                                cwd=str(abs_prompt_file_path.parent)
                            )
                            if temp_git_root_rc == 0:
                                git_root_path_obj = pathlib.Path(temp_git_root_str)
                                prompt_file_rel_to_root_str = abs_prompt_file_path.relative_to(git_root_path_obj).as_posix()
                            elif verbose:
                                console.print(f"[yellow]Git (rev-parse) failed for {prompt_file}: {temp_git_root_stderr}. Cannot search history for prior different version.[/yellow]")
                        
                        except ValueError: # If file is not under git root
                             if verbose:
                                console.print(f"[yellow]File {prompt_file} not under a detected git root. Cannot search history.[/yellow]")
                        except Exception as e_git_setup:
                            if verbose:
                                console.print(f"[yellow]Error setting up git info for {prompt_file}: {e_git_setup}. Cannot search history.[/yellow]")

                        if git_root_path_obj and prompt_file_rel_to_root_str:
                            MAX_COMMITS_TO_SEARCH = 10  # How far back to look
                            log_cmd = ["git", "log", f"--pretty=format:%H", f"-n{MAX_COMMITS_TO_SEARCH}", "--", prompt_file_rel_to_root_str]
                            
                            log_rc, log_stdout, log_stderr = _run_git_command(log_cmd, cwd=str(git_root_path_obj))

                            if log_rc == 0 and log_stdout.strip():
                                shas = log_stdout.strip().split('\\n')
                                if verbose:
                                     console.print(f"Found {len(shas)} commits for [cyan]{prompt_file_rel_to_root_str}[/cyan] in recent history (up to {MAX_COMMITS_TO_SEARCH}).")

                                if len(shas) > 1: # Need at least one commit before the one matching head_prompt_content
                                    for prior_sha in shas[1:]: # Iterate starting from the commit *before* HEAD's version of the file
                                        if verbose:
                                            console.print(f"  Checking commit {prior_sha[:7]} for content of [cyan]{prompt_file}[/cyan]...")
                                        
                                        # get_git_content_at_ref uses the original prompt_file path, 
                                        # which it resolves internally relative to the git root.
                                        prior_content = get_git_content_at_ref(prompt_file, prior_sha) 
                                        
                                        if prior_content is not None:
                                            if prior_content.strip() != new_prompt_candidate.strip():
                                                original_prompt_content_for_incremental = prior_content
                                                can_attempt_incremental = True
                                                found_different_prior = True
                                                if verbose:
                                                    console.print(f"    [green]Found prior different version at commit {prior_sha[:7]}. Using as original prompt.[/green]")
                                                break 
                                            elif verbose:
                                                 console.print(f"    Content at {prior_sha[:7]} is identical to current HEAD. Skipping.")
                                        elif verbose:
                                            console.print(f"    Could not retrieve content for [cyan]{prompt_file}[/cyan] at commit {prior_sha[:7]}.")
                                else: 
                                    if verbose:
                                        console.print(f"  File [cyan]{prompt_file_rel_to_root_str}[/cyan] has less than 2 versions in recent history at this path.")
                            elif verbose:
                                console.print(f"[yellow]Git (log) failed for {prompt_file_rel_to_root_str} or no history found: {log_stderr}[/yellow]")
                        
                        if not found_different_prior:
                            original_prompt_content_for_incremental = new_prompt_candidate 
                            can_attempt_incremental = True 
                            if verbose:
                                console.print(
                                    f"[yellow]Warning: Could not find a prior *different* version of {prompt_file} "
                                    f"within the last {MAX_COMMITS_TO_SEARCH if git_root_path_obj else 'N/A'} relevant commits. "
                                    f"Using current HEAD version as original (prompts will be identical).[/yellow]"
                                )
                else:
                    # File not in HEAD, cannot determine git-based original prompt.
                    if verbose:
                        console.print(f"[yellow]Warning: Could not find committed version of {prompt_file} in git (HEAD) for incremental generation.[/yellow]")
            
            if force_incremental_flag and existing_code_content:
                if not (original_prompt_content_for_incremental or "original_prompt_file" in input_strings): # Check if original prompt is actually available
                     console.print(
                        "[yellow]Warning: --incremental flag used, but original prompt could not be determined. "
                        "Falling back to full generation.[/yellow]"
                    )
                else:
                    can_attempt_incremental = True 
    
    if force_incremental_flag and (not output_path or not pathlib.Path(output_path).exists()):
        console.print(
            "[yellow]Warning: --incremental flag used, but output file does not exist or path not specified. "
            "Performing full generation.[/yellow]"
        )
        can_attempt_incremental = False

    try:
        # Determine template-driven switches
        llm_enabled: bool = True
        post_process_script: Optional[str] = None
        prompt_body_for_script: str = prompt_content
        # Allow environment override for LLM toggle when front matter omits it
        env_llm_raw = None
        try:
            if env_vars and 'llm' in env_vars:
                env_llm_raw = str(env_vars.get('llm'))
            elif os.environ.get('llm') is not None:
                env_llm_raw = os.environ.get('llm')
            elif os.environ.get('LLM') is not None:
                env_llm_raw = os.environ.get('LLM')
        except Exception:
            env_llm_raw = None
        if fm_meta and isinstance(fm_meta, dict):
            try:
                if 'llm' in fm_meta:
                    llm_enabled = bool(fm_meta.get('llm', True))
                elif env_llm_raw is not None:
                    llm_str = str(env_llm_raw).strip().lower()
                    if llm_str in {"0", "false", "no", "off"}:
                        llm_enabled = False
                    else:
                        llm_enabled = llm_str in {"1", "true", "yes", "on"}
            except Exception:
                llm_enabled = True
        elif env_llm_raw is not None:
            try:
                llm_str = str(env_llm_raw).strip().lower()
                if llm_str in {"0", "false", "no", "off"}:
                    llm_enabled = False
                else:
                    llm_enabled = llm_str in {"1", "true", "yes", "on"}
            except Exception:
                llm_enabled = True
        
        if verbose:
            console.print(f"[blue]LLM enabled:[/blue] {llm_enabled}")
        
        # Resolve post-process script from env/CLI override, then front matter, then sensible default per template
        try:
            post_process_script = None
            script_override = None
            if env_vars:
                script_override = env_vars.get('POST_PROCESS_PYTHON') or env_vars.get('post_process_python')
            if not script_override:
                script_override = os.environ.get('POST_PROCESS_PYTHON') or os.environ.get('post_process_python')
            if script_override and str(script_override).strip():
                expanded = _expand_vars(str(script_override), env_vars)
                pkg_dir = pathlib.Path(__file__).parent.resolve()
                repo_root = pathlib.Path.cwd().resolve()
                repo_pdd_dir = (repo_root / 'pdd').resolve()
                candidate = pathlib.Path(expanded)
                if not candidate.is_absolute():
                    # 1) As provided, relative to CWD
                    as_is = (repo_root / candidate)
                    # 2) Under repo pdd/
                    under_repo_pdd = (repo_pdd_dir / candidate.name) if not as_is.exists() else as_is
                    # 3) Under installed package dir
                    under_pkg = (pkg_dir / candidate.name) if not as_is.exists() and not under_repo_pdd.exists() else as_is
                    if as_is.exists():
                        candidate = as_is
                    elif under_repo_pdd.exists():
                        candidate = under_repo_pdd
                    elif under_pkg.exists():
                        candidate = under_pkg
                    else:
                        candidate = as_is  # will fail later with not found
                post_process_script = str(candidate.resolve())
            elif fm_meta and isinstance(fm_meta, dict):
                raw_script = fm_meta.get('post_process_python')
                if isinstance(raw_script, str) and raw_script.strip():
                    # Expand variables like $VAR and ${VAR}
                    expanded = _expand_vars(raw_script, env_vars)
                    pkg_dir = pathlib.Path(__file__).parent.resolve()
                    repo_root = pathlib.Path.cwd().resolve()
                    repo_pdd_dir = (repo_root / 'pdd').resolve()
                    candidate = pathlib.Path(expanded)
                    if not candidate.is_absolute():
                        as_is = (repo_root / candidate)
                        under_repo_pdd = (repo_pdd_dir / candidate.name) if not as_is.exists() else as_is
                        under_pkg = (pkg_dir / candidate.name) if not as_is.exists() and not under_repo_pdd.exists() else as_is
                        if as_is.exists():
                            candidate = as_is
                        elif under_repo_pdd.exists():
                            candidate = under_repo_pdd
                        elif under_pkg.exists():
                            candidate = under_pkg
                        else:
                            candidate = as_is
                    post_process_script = str(candidate.resolve())
            # Fallback default: for architecture template, use built-in render_mermaid.py
            if not post_process_script:
                try:
                    prompt_str = str(prompt_file)
                    looks_like_arch_template = (
                        (isinstance(prompt_file, str) and (
                            prompt_str.endswith("architecture/architecture_json.prompt") or
                            prompt_str.endswith("architecture/architecture_json") or
                            "architecture_json.prompt" in prompt_str or
                            "architecture/architecture_json" in prompt_str
                        ))
                    )
                    looks_like_arch_output = (
                        bool(output_path) and pathlib.Path(str(output_path)).name == 'architecture.json'
                    )
                    if looks_like_arch_template or looks_like_arch_output:
                        pkg_dir = pathlib.Path(__file__).parent
                        repo_pdd_dir = pathlib.Path.cwd() / 'pdd'
                        if (pkg_dir / 'render_mermaid.py').exists():
                            post_process_script = str((pkg_dir / 'render_mermaid.py').resolve())
                        elif (repo_pdd_dir / 'render_mermaid.py').exists():
                            post_process_script = str((repo_pdd_dir / 'render_mermaid.py').resolve())
                except Exception:
                    post_process_script = None
            if verbose:
                console.print(f"[blue]Post-process script resolved to:[/blue] {post_process_script if post_process_script else 'None'}")
        except Exception:
            post_process_script = None
        # If LLM is disabled but no post-process script is provided, surface a helpful error
        if not llm_enabled and not post_process_script:
            console.print("[red]Error: llm: false requires 'post_process_python' to be specified in front matter.[/red]")
            return "", was_incremental_operation, total_cost, "error"
        if llm_enabled and can_attempt_incremental and existing_code_content is not None and original_prompt_content_for_incremental is not None:
            if verbose:
                console.print(Panel("Attempting incremental code generation...", title="[blue]Mode[/blue]", expand=False))

            if is_git_repository(str(pathlib.Path(prompt_file).parent)):
                files_to_stage_for_rollback: List[str] = []
                paths_to_check = [pathlib.Path(prompt_file).resolve()]
                if output_path and pathlib.Path(output_path).exists():
                    paths_to_check.append(pathlib.Path(output_path).resolve())

                for p_to_check in paths_to_check:
                    if not p_to_check.exists(): continue
                    
                    is_untracked = get_file_git_status(str(p_to_check)).startswith("??")
                    # Check if different from HEAD or untracked
                    is_different_from_head_rc = 1 if is_untracked else _run_git_command(["git", "diff", "--quiet", "HEAD", "--", str(p_to_check)], cwd=str(p_to_check.parent))[0]
                    
                    if is_different_from_head_rc != 0: # Different from HEAD or untracked
                        files_to_stage_for_rollback.append(str(p_to_check))
                
                if files_to_stage_for_rollback:
                    git_add_files(files_to_stage_for_rollback, verbose=verbose)
            
            # Preprocess both prompts: expand includes, substitute vars, then double
            orig_proc = pdd_preprocess(original_prompt_content_for_incremental, recursive=True, double_curly_brackets=False)
            orig_proc = _expand_vars(orig_proc, env_vars)
            orig_proc = pdd_preprocess(orig_proc, recursive=False, double_curly_brackets=True)

            new_proc = pdd_preprocess(prompt_content, recursive=True, double_curly_brackets=False)
            new_proc = _expand_vars(new_proc, env_vars)
            new_proc = pdd_preprocess(new_proc, recursive=False, double_curly_brackets=True)

            generated_code_content, was_incremental_operation, total_cost, model_name = incremental_code_generator_func(
                original_prompt=orig_proc,
                new_prompt=new_proc,
                existing_code=existing_code_content,
                language=language,
                strength=strength,
                temperature=temperature,
                time=time_budget,
                force_incremental=force_incremental_flag,
                verbose=verbose,
                preprocess_prompt=False
            )

            if not was_incremental_operation:
                if verbose:
                    console.print(Panel("Incremental generator suggested full regeneration. Falling back.", title="[yellow]Fallback[/yellow]", expand=False))
            elif verbose:
                console.print(Panel(f"Incremental update successful. Model: {model_name}, Cost: ${total_cost:.6f}", title="[green]Incremental Success[/green]", expand=False))

        if llm_enabled and not was_incremental_operation: # Full generation path
            if verbose:
                console.print(Panel("Performing full code generation...", title="[blue]Mode[/blue]", expand=False))
            
            current_execution_is_local = is_local_execution_preferred
            
            if not current_execution_is_local:
                if verbose: console.print("Attempting cloud code generation...")
                # Expand includes, substitute vars, then double
                processed_prompt_for_cloud = pdd_preprocess(prompt_content, recursive=True, double_curly_brackets=False, exclude_keys=[])
                processed_prompt_for_cloud = _expand_vars(processed_prompt_for_cloud, env_vars)
                processed_prompt_for_cloud = pdd_preprocess(processed_prompt_for_cloud, recursive=False, double_curly_brackets=True, exclude_keys=[])
                if verbose: console.print(Panel(Text(processed_prompt_for_cloud, overflow="fold"), title="[cyan]Preprocessed Prompt for Cloud[/cyan]", expand=False))
                
                jwt_token: Optional[str] = None
                try:
                    firebase_api_key_val = os.environ.get(FIREBASE_API_KEY_ENV_VAR)
                    github_client_id_val = os.environ.get(GITHUB_CLIENT_ID_ENV_VAR)

                    if not firebase_api_key_val: raise AuthError(f"{FIREBASE_API_KEY_ENV_VAR} not set.")
                    if not github_client_id_val: raise AuthError(f"{GITHUB_CLIENT_ID_ENV_VAR} not set.")

                    jwt_token = asyncio.run(get_jwt_token(
                        firebase_api_key=firebase_api_key_val,
                        github_client_id=github_client_id_val,
                        app_name=PDD_APP_NAME
                    ))
                except (AuthError, NetworkError, TokenError, UserCancelledError, RateLimitError) as e:
                    console.print(f"[yellow]Cloud authentication/token error: {e}. Falling back to local execution.[/yellow]")
                    current_execution_is_local = True
                except Exception as e:
                    console.print(f"[yellow]Unexpected error during cloud authentication: {e}. Falling back to local execution.[/yellow]")
                    current_execution_is_local = True

                if jwt_token and not current_execution_is_local:
                    payload = {"promptContent": processed_prompt_for_cloud, "language": language, "strength": strength, "temperature": temperature, "verbose": verbose}
                    headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}
                    try:
                        response = requests.post(CLOUD_GENERATE_URL, json=payload, headers=headers, timeout=CLOUD_REQUEST_TIMEOUT)
                        response.raise_for_status()
                        
                        response_data = response.json()
                        generated_code_content = response_data.get("generatedCode")
                        total_cost = float(response_data.get("totalCost", 0.0))
                        model_name = response_data.get("modelName", "cloud_model")

                        if generated_code_content is None:
                            console.print("[yellow]Cloud execution returned no code. Falling back to local.[/yellow]")
                            current_execution_is_local = True
                        elif verbose:
                             console.print(Panel(f"Cloud generation successful. Model: {model_name}, Cost: ${total_cost:.6f}", title="[green]Cloud Success[/green]", expand=False))
                    except requests.exceptions.Timeout:
                        console.print(f"[yellow]Cloud execution timed out ({CLOUD_REQUEST_TIMEOUT}s). Falling back to local.[/yellow]")
                        current_execution_is_local = True
                    except requests.exceptions.HTTPError as e:
                        err_content = e.response.text[:200] if e.response else "No response content"
                        console.print(f"[yellow]Cloud HTTP error ({e.response.status_code}): {err_content}. Falling back to local.[/yellow]")
                        current_execution_is_local = True
                    except requests.exceptions.RequestException as e:
                        console.print(f"[yellow]Cloud network error: {e}. Falling back to local.[/yellow]")
                        current_execution_is_local = True
                    except json.JSONDecodeError:
                        console.print("[yellow]Cloud returned invalid JSON. Falling back to local.[/yellow]")
                        current_execution_is_local = True
            
            if current_execution_is_local:
                if verbose: console.print("Executing code generator locally...")
                # Expand includes, substitute vars, then double; pass to local generator with preprocess_prompt=False
                local_prompt = pdd_preprocess(prompt_content, recursive=True, double_curly_brackets=False, exclude_keys=[])
                local_prompt = _expand_vars(local_prompt, env_vars)
                local_prompt = pdd_preprocess(local_prompt, recursive=False, double_curly_brackets=True, exclude_keys=[])
                # Language already resolved (front matter overrides detection if present)
                gen_language = language
                generated_code_content, total_cost, model_name = local_code_generator_func(
                    prompt=local_prompt,
                    language=gen_language,
                    strength=strength,
                    temperature=temperature,
                    time=time_budget,
                    verbose=verbose,
                    preprocess_prompt=False
                )
                was_incremental_operation = False
                if verbose:
                    console.print(Panel(f"Full generation successful. Model: {model_name}, Cost: ${total_cost:.6f}", title="[green]Local Success[/green]", expand=False))

        # Optional post-process Python hook (runs after LLM when enabled, or standalone when LLM is disabled)
        if post_process_script:
            try:
                python_executable = detect_host_python_executable()
                # Choose stdin for the script: LLM output if available and enabled, else prompt body
                stdin_payload = generated_code_content if (llm_enabled and generated_code_content is not None) else prompt_body_for_script
                env = os.environ.copy()
                env['PDD_LANGUAGE'] = str(language or '')
                env['PDD_OUTPUT_PATH'] = str(output_path or '')
                env['PDD_PROMPT_FILE'] = str(pathlib.Path(prompt_file).resolve())
                env['PDD_LLM'] = '1' if llm_enabled else '0'
                try:
                    env['PDD_ENV_VARS'] = json.dumps(env_vars or {})
                except Exception:
                    env['PDD_ENV_VARS'] = '{}'
                # If front matter provides args, run in argv mode with a temp input file
                fm_args = None
                try:
                    # Env/CLI override for args (comma-separated or JSON list)
                    raw_args_env = None
                    if env_vars:
                        raw_args_env = env_vars.get('POST_PROCESS_ARGS') or env_vars.get('post_process_args')
                    if not raw_args_env:
                        raw_args_env = os.environ.get('POST_PROCESS_ARGS') or os.environ.get('post_process_args')
                    if raw_args_env:
                        s = str(raw_args_env).strip()
                        parsed_list = None
                        if s.startswith('[') and s.endswith(']'):
                            try:
                                parsed = json.loads(s)
                                if isinstance(parsed, list):
                                    parsed_list = [str(a) for a in parsed]
                            except Exception:
                                parsed_list = None
                        if parsed_list is None:
                            if ',' in s:
                                parsed_list = [part.strip() for part in s.split(',') if part.strip()]
                            else:
                                parsed_list = [part for part in s.split() if part]
                        fm_args = parsed_list or None
                    if fm_args is None:
                        raw_args = fm_meta.get('post_process_args') if isinstance(fm_meta, dict) else None
                        if isinstance(raw_args, list):
                            fm_args = [str(a) for a in raw_args]
                except Exception:
                    fm_args = None
                proc = None
                temp_input_path = None
                try:
                    if fm_args is None:
                        # Provide sensible default args for architecture template with render_mermaid.py
                        try:
                            if post_process_script and pathlib.Path(post_process_script).name == 'render_mermaid.py':
                                if isinstance(prompt_file, str) and prompt_file.endswith('architecture/architecture_json.prompt'):
                                    fm_args = ["{INPUT_FILE}", "{APP_NAME}", "{OUTPUT_HTML}"]
                        except Exception:
                            pass
                    if fm_args:
                        # When LLM is disabled, use the existing output file instead of creating a temp file
                        if not llm_enabled and output_path and pathlib.Path(output_path).exists():
                            temp_input_path = str(pathlib.Path(output_path).resolve())
                            env['PDD_POSTPROCESS_INPUT_FILE'] = temp_input_path
                        else:
                            # Write payload to a temp file for scripts expecting a file path input
                            suffix = '.json' if (isinstance(language, str) and str(language).lower().strip() == 'json') or (output_path and str(output_path).lower().endswith('.json')) else '.txt'
                            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix, encoding='utf-8') as tf:
                                tf.write(stdin_payload or '')
                                temp_input_path = tf.name
                            env['PDD_POSTPROCESS_INPUT_FILE'] = temp_input_path
                        # Compute placeholder values
                        app_name_val = (env_vars or {}).get('APP_NAME') if env_vars else None
                        if not app_name_val:
                            app_name_val = 'System Architecture'
                        output_html_default = None
                        if output_path and str(output_path).lower().endswith('.json'):
                            output_html_default = str(pathlib.Path(output_path).with_name(f"{pathlib.Path(output_path).stem}_diagram.html").resolve())
                        placeholder_map = {
                            'INPUT_FILE': temp_input_path or '',
                            'OUTPUT': str(output_path or ''),
                            'PROMPT_FILE': str(pathlib.Path(prompt_file).resolve()),
                            'APP_NAME': str(app_name_val),
                            'OUTPUT_HTML': str(output_html_default or ''),
                        }
                        def _subst_arg(arg: str) -> str:
                            # First expand $VARS using existing helper, then {TOKENS}
                            expanded = _expand_vars(arg, env_vars)
                            for key, val in placeholder_map.items():
                                expanded = expanded.replace('{' + key + '}', val)
                            return expanded
                        args_list = [_subst_arg(a) for a in fm_args]
                        if verbose:
                            console.print(Panel(f"Post-process hook (argv)\nScript: {post_process_script}\nArgs: {args_list}", title="[blue]Post-process[/blue]", expand=False))
                        proc = subprocess.run(
                            [python_executable, post_process_script] + args_list,
                            text=True,
                            capture_output=True,
                            timeout=300,
                            cwd=str(pathlib.Path(post_process_script).parent),
                            env=env
                        )
                    else:
                        # Run the script with stdin payload, capture stdout as final content
                        if verbose:
                            console.print(Panel(f"Post-process hook (stdin)\nScript: {post_process_script}", title="[blue]Post-process[/blue]", expand=False))
                        proc = subprocess.run(
                            [python_executable, post_process_script],
                            input=stdin_payload or '',
                            text=True,
                            capture_output=True,
                            timeout=300,
                            cwd=str(pathlib.Path(post_process_script).parent),
                            env=env
                        )
                finally:
                    if temp_input_path:
                        try:
                            # Only delete temp files, not the actual output file when llm=false
                            if llm_enabled or not (output_path and pathlib.Path(output_path).exists() and temp_input_path == str(pathlib.Path(output_path).resolve())):
                                os.unlink(temp_input_path)
                        except Exception:
                            pass
                if proc and proc.returncode == 0:
                    if verbose:
                        console.print(Panel(f"Post-process success (rc=0)\nstdout: {proc.stdout[:150]}\nstderr: {proc.stderr[:150]}", title="[green]Post-process[/green]", expand=False))
                    # Do not modify generated_code_content to preserve architecture.json
                else:
                    rc = getattr(proc, 'returncode', 'N/A')
                    err = getattr(proc, 'stderr', '')
                    console.print(f"[yellow]Post-process failed (rc={rc}). Stderr:\n{err[:500]}[/yellow]")
            except FileNotFoundError:
                console.print(f"[yellow]Post-process script not found: {post_process_script}. Skipping.[/yellow]")
            except FileNotFoundError:
                console.print(f"[yellow]Post-process script not found: {post_process_script}. Skipping.[/yellow]")
            except subprocess.TimeoutExpired:
                console.print("[yellow]Post-process script timed out. Skipping.[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Post-process script error: {e}. Skipping.[/yellow]")
        if generated_code_content is not None:
            # Optional output_schema JSON validation before writing (only when LLM ran)
            if llm_enabled:
                try:
                    if fm_meta and isinstance(fm_meta.get("output_schema"), dict):
                        is_json_output = False
                        if isinstance(language, str) and str(language).lower().strip() == "json":
                            is_json_output = True
                        elif output_path and str(output_path).endswith(".json"):
                            is_json_output = True
                        if is_json_output:
                            parsed = json.loads(generated_code_content)
                            try:
                                import jsonschema  # type: ignore
                                jsonschema.validate(instance=parsed, schema=fm_meta.get("output_schema"))
                            except ModuleNotFoundError:
                                if verbose and not quiet:
                                    console.print("[yellow]jsonschema not installed; skipping schema validation.[/yellow]")
                            except Exception as ve:
                                raise click.UsageError(f"Generated JSON does not match output_schema: {ve}")
                except json.JSONDecodeError as jde:
                    raise click.UsageError(f"Generated output is not valid JSON: {jde}")

            if output_path:
                p_output = pathlib.Path(output_path)
                p_output.parent.mkdir(parents=True, exist_ok=True)
                p_output.write_text(generated_code_content, encoding="utf-8")
                if verbose or not quiet:
                    console.print(f"Generated code saved to: [green]{p_output.resolve()}[/green]")
                # Safety net: ensure architecture HTML is generated post-write if applicable
                try:
                    # Prefer resolved script if available; else default for architecture outputs
                    script_path2 = post_process_script
                    if not script_path2:
                        looks_like_arch_output2 = pathlib.Path(str(p_output)).name == 'architecture.json'
                        if looks_like_arch_output2:
                            pkg_dir2 = pathlib.Path(__file__).parent
                            repo_pdd_dir2 = pathlib.Path.cwd() / 'pdd'
                            if (pkg_dir2 / 'render_mermaid.py').exists():
                                script_path2 = str((pkg_dir2 / 'render_mermaid.py').resolve())
                            elif (repo_pdd_dir2 / 'render_mermaid.py').exists():
                                script_path2 = str((repo_pdd_dir2 / 'render_mermaid.py').resolve())
                    if script_path2 and pathlib.Path(script_path2).exists():
                        app_name2 = os.environ.get('APP_NAME') or (env_vars or {}).get('APP_NAME') or 'System Architecture'
                        out_html2 = os.environ.get('POST_PROCESS_OUTPUT') or str(p_output.with_name(f"{p_output.stem}_diagram.html").resolve())
                        # Only run if HTML not present yet
                        if not pathlib.Path(out_html2).exists():
                            try:
                                py_exec2 = detect_host_python_executable()
                            except Exception:
                                py_exec2 = sys.executable
                            if verbose:
                                console.print(Panel(f"Safety net post-process\nScript: {script_path2}\nArgs: {[str(p_output.resolve()), app_name2, out_html2]}", title="[blue]Post-process[/blue]", expand=False))
                            sp2 = subprocess.run([py_exec2, script_path2, str(p_output.resolve()), app_name2, out_html2],
                                                 capture_output=True, text=True, cwd=str(pathlib.Path(script_path2).parent))
                            if sp2.returncode == 0 and not quiet:
                                print(f"✅ Generated: {out_html2}")
                            elif verbose:
                                console.print(f"[yellow]Safety net failed (rc={sp2.returncode}). stderr:\n{sp2.stderr[:300]}[/yellow]")
                except Exception:
                    pass
                # Post-step now runs regardless of LLM value via the general post-process hook above.
            elif not quiet:
                # No destination resolved; surface the generated code directly to the console.
                console.print(Panel(Text(generated_code_content, overflow="fold"), title="[cyan]Generated Code[/cyan]", expand=False))
                console.print("[yellow]No output path resolved; skipping file write and stdout print.[/yellow]")
        else:
            # If LLM was disabled and post-process ran, that's a success (no error)
            if not llm_enabled and post_process_script:
                if verbose or not quiet:
                    console.print("[green]Post-process completed successfully (LLM was disabled).[/green]")
            else:
                console.print("[red]Error: Code generation failed. No code was produced.[/red]")
                return "", was_incremental_operation, total_cost, model_name or "error"

    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
        import traceback
        if verbose: console.print(traceback.format_exc())
        return "", was_incremental_operation, total_cost, "error"
        
    return generated_code_content or "", was_incremental_operation, total_cost, model_name
