"""Tiny terminal UI helpers (stdlib only): colors, text input and option selection."""

import os
import sys

try:  # Gives input() line editing + history (arrow keys) on Linux/macOS.
    import readline  # noqa: F401
except ImportError:  # pragma: no cover - Windows
    pass

_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
_INTERACTIVE = sys.stdin.isatty() and sys.stdout.isatty()


def style(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes, e.g. style("hi", "1", "36") -> bold cyan."""
    if not _COLOR:
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


def bold(t: str) -> str:
    return style(t, "1")


def dim(t: str) -> str:
    return style(t, "2")


def cyan(t: str) -> str:
    return style(t, "36")


def green(t: str) -> str:
    return style(t, "32")


def yellow(t: str) -> str:
    return style(t, "33")


def red(t: str) -> str:
    return style(t, "31")


def ask(prompt: str) -> str:
    """Read a line of text. A trailing backslash continues input on the next line.

    Raises EOFError / KeyboardInterrupt so callers can decide how to exit.
    """
    lines = []
    line = input(prompt)
    while line.endswith("\\"):
        lines.append(line[:-1])
        line = input(dim("... "))
    lines.append(line)
    return "\n".join(lines).strip()


def confirm(question: str, default: bool = True) -> bool:
    """Yes/no question."""
    choice = select(question, ["Yes", "No"], default=0 if default else 1)
    return choice == "Yes"


def select(title: str, options: list, default: int = 0):
    """Let the user pick one option. Returns the chosen option, or None if cancelled.

    Uses arrow keys (↑/↓ or j/k, Enter to pick, Esc/q to cancel) in a real terminal,
    and falls back to a numbered prompt otherwise.
    """
    if not options:
        return None
    if _INTERACTIVE and os.name == "posix":
        return _select_arrows(title, options, default)
    return _select_numbered(title, options)


def _select_numbered(title: str, options: list):
    print(bold(title))
    for i, opt in enumerate(options, 1):
        print(f"  {cyan(str(i))}. {opt}")
    while True:
        try:
            raw = input(dim("Choose a number (blank to cancel): ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(red("Invalid choice."))


def _read_key() -> str:
    """Read one keypress (handles arrow-key escape sequences)."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1).decode(errors="ignore")
        if ch == "\x1b":
            # Arrow keys send ESC [ A/B; a lone ESC means "cancel".
            import select as _sel

            if _sel.select([fd], [], [], 0.05)[0]:
                ch += os.read(fd, 2).decode(errors="ignore")
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _select_arrows(title: str, options: list, default: int):
    idx = max(0, min(default, len(options) - 1))
    hint = dim("(↑/↓ to move, Enter to select, Esc to cancel)")
    print(f"{bold(title)} {hint}")

    def render(first: bool) -> None:
        if not first:
            sys.stdout.write(f"\033[{len(options)}A")  # move cursor back up
        for i, opt in enumerate(options):
            line = f"{cyan('❯')} {bold(str(opt))}" if i == idx else f"  {opt}"
            sys.stdout.write(f"\r\033[2K{line}\n")
        sys.stdout.flush()

    sys.stdout.write("\033[?25l")  # hide cursor
    try:
        render(True)
        while True:
            key = _read_key()
            if key in ("\x1b[A", "k"):
                idx = (idx - 1) % len(options)
            elif key in ("\x1b[B", "j"):
                idx = (idx + 1) % len(options)
            elif key.isdigit() and 1 <= int(key) <= len(options):
                idx = int(key) - 1
            elif key in ("\r", "\n"):
                return options[idx]
            elif key in ("\x1b", "q", "\x03", "\x04"):  # Esc, q, Ctrl-C, Ctrl-D
                return None
            render(False)
    finally:
        sys.stdout.write("\033[?25h")  # show cursor
        sys.stdout.flush()

