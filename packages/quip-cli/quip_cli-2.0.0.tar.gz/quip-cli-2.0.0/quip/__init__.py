from colorama import Fore, Style, init
import warnings
import click
import os
import yaml

init()
warnings.filterwarnings("ignore", category=SyntaxWarning, message=r"invalid escape sequence.*")

__version__ = "2.0.0"

# Environment variable to control quiet mode
QUIET_ENV_VAR = "QUIP_QUIET"

# Global quiet mode flag
_quiet_mode = False

def set_quiet_mode(quiet):
    """Set global quiet mode."""
    global _quiet_mode
    _quiet_mode = quiet

def is_quiet_mode():
    """Check if quiet mode is enabled."""
    return _quiet_mode


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def _find_config_file(config_path=None):
    if config_path and os.path.exists(config_path):
        return config_path
    current_path = os.path.join(os.getcwd(), ".uip_config.yml")
    if os.path.exists(current_path):
        return current_path
    home_path = os.path.join(os.path.expanduser("~"), ".uip_config.yml")
    if os.path.exists(home_path):
        return home_path
    return None


def _config_quiet_value(config_path=None):
    config_file = _find_config_file(config_path)
    if not config_file:
        return None
    try:
        with open(config_file) as handle:
            data = yaml.safe_load(handle) or {}
    except Exception:
        return None
    defaults = data.get("defaults")
    if isinstance(defaults, dict):
        return _to_bool(defaults.get("quiet"))
    return None


def resolve_quiet_mode(cli_quiet=False, config_path=None):
    if cli_quiet:
        return True
    env_value = _to_bool(os.environ.get(QUIET_ENV_VAR))
    if env_value is not None:
        return env_value
    config_value = _config_quiet_value(config_path)
    if config_value is not None:
        return config_value
    return False

def cprint(text, color, end='\n', style='Normal'):
    if len(str(text).strip()) == 0: return
    fore = getattr(Fore, color.upper())
    style = getattr(Style, style.upper())
    print('{0}{1}{2}{3}'.format(fore, style, text, Style.RESET_ALL), end=end)

def color_text(text, color, style='Normal'):
    fore = getattr(Fore, color.upper())
    style = getattr(Style, style.upper())
    return '{0}{1}{2}{3}'.format(fore, style, text, Style.RESET_ALL)

def yes_or_no(question, default=None, color=None):
    # If quiet mode is enabled, use default
    if _quiet_mode:
        if default is not None:
            if color is not None:
                cprint(f"{question} [quiet mode: using default={default}]", color)
            else:
                print(f"{question} [quiet mode: using default={default}]")
            return default
        else:
            # If no default in quiet mode, assume False for safety
            if color is not None:
                cprint(f"{question} [quiet mode: using default=False]", color)
            else:
                print(f"{question} [quiet mode: using default=False]")
            return False
    
    if default == True:
        options = "(Y/n)"
    elif default == False:
        options = "(y/N)"
    else:
        options = "(y/n)"
        default = None

    if color is not None:
        prompt = color_text(question + options + ": ", color)
    else:
        prompt = question + options + ": "
    while True:
        answer = input(prompt).lower().strip()
        
        if len(answer) == 0 and default is not None:
            return default
        elif answer[0] in  ["y", "yes"]:
            return True
        elif answer[0] in  ["n", "no"]:
            return False

def choose_one(values, title=None, default=None, sort=True):
    # Quiet mode should NOT suppress this prompt; always ask user
    default_index = 1
    answer = None
    values = sorted(values, key=lambda d: d[0])

    if title is not None:
        cprint(title, "magenta")
        cprint("=" * len(title), "magenta")
    len_values = len(values)
    for index, value in enumerate(values, start=1):
        if default is not None and value[0] == default:
            print(f"({index}) {value[0]} [default]")
            default_index = index
        else:
            print(f"({index}) {value[0]}")

    ask = True
    while ask:
        if default is None:
            message = f"Choose one (1-{len_values}) : "
        else:
            message = f"Choose one (1-{len_values}) [{default_index}]: "
        
        answer = input(message).lower().strip()
        if len(answer) == 0 and default is not None:
            answer = default_index
        else:
            answer = int(answer)
        if answer < 1 or answer > len_values:
            cprint(f"answer must be between 1 and {len_values}", "red")
        else:
            ask = False
    
    return values[answer-1]


# --- Output helpers for QUIP 2.0 banners ---
def _version_major_minor():
    parts = str(__version__).split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else str(__version__)


def print_banner_compact(command=None, project=None, template=None, config=None, quiet=None, debug=None):
    """Print a compact one-line banner emphasizing QUIP 2.0."""
    mm = _version_major_minor()
    bits = [f"[QUIP {mm}]"]
    if command:
        bits.append(f"command={command}")
    if project:
        bits.append(f"project={project}")
    if template is not None:
        bits.append(f"template={str(bool(template)).lower()}")
    if config:
        bits.append(f"config={config}")
    if quiet is not None:
        bits.append(f"quiet={'on' if quiet else 'off'}")
    if debug is not None:
        bits.append(f"debug={'on' if debug else 'off'}")
    line = " 200 ".join(bits).replace("\u0019", "|")  # safe separator
    cprint(line, "cyan")


def print_ascii_art_quip2():
    """Print a large ASCII art for QUIP 2.0 for prominent commands."""
    art = [
        "  ____  _   _ ___ ____  ",
        " / __ \u005c| | | |_ _|  _ \ ",
        "| |  | | |_| | | | |_) |",
        "| |  | |  _  | | |  _ < ",
        "| |__| | | | | | | |_) |",
        " \u005c___\u005c_\_| |_|___|____/  2.0",
    ]
    for line in art:
        cprint(line.replace("\u0019", "|"), "magenta")


# New helpers with clean formatting for 2.0
def print_banner2(command=None, project=None, template=None, config=None, quiet=None, debug=None):
    mm = ".".join(str(__version__).split(".")[:2])
    parts = [f"[QUIP {mm}]"]
    if command:
        parts.append(f"command={command}")
    if project:
        parts.append(f"project={project}")
    if template is not None:
        parts.append(f"template={str(bool(template)).lower()}")
    if config:
        parts.append(f"config={config}")
    if quiet is not None:
        parts.append(f"quiet={'on' if quiet else 'off'}")
    if debug is not None:
        parts.append(f"debug={'on' if debug else 'off'}")
    cprint(" • ".join(parts), "cyan")


def print_ascii_art2():
    
    art = [
        r'!                                               ',
        r'!                                               ',
        r'!     .d88888b.  888     888 8888888 8888888b.  ',
        r'!    d88P" "Y88b 888     888   888   888   Y88b ',
        r'!    888     888 888     888   888   888    888 ',
        r'!    888     888 888     888   888   888   d88P ',
        r'!    888     888 888     888   888   8888888P   ',
        r'!    888 Y8b 888 888     888   888   888        ',
        r'!    Y88b.Y8b88P Y88b. .d88P   888   888        ',
        r'!     "Y888888"   "Y88888P"  8888888 888        ',
        r'!           Y8b                                 ',
        r'!                                               ',
        f'!                  V.{__version__}                        '
    ]
    for line in art:
        cprint(line, "magenta")