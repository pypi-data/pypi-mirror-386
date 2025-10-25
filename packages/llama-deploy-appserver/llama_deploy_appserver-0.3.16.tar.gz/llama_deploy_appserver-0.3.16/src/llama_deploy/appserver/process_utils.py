import functools
import os
import platform
import subprocess
import sys
import threading
from typing import Callable, TextIO, cast


def run_process(
    cmd: list[str],
    *,
    cwd: os.PathLike | None = None,
    env: dict[str, str] | None = None,
    prefix: str | None = None,
    color_code: str = "36",
    line_transform: Callable[[str], str | None] | None = None,
    use_tty: bool | None = None,
) -> None:
    """Run a process and stream its output with optional TTY semantics.

    If use_tty is None, a PTY will be used only when the parent's stdout is a TTY
    and the platform supports PTYs. When a PTY is used, stdout/stderr are merged.
    """
    use_pty = _should_use_pty(use_tty)
    prefixer = _make_prefixer(prefix, color_code, line_transform)

    process, sources, cleanup = _spawn_process(cmd, cwd=cwd, env=env, use_pty=use_pty)
    threads: list[threading.Thread] = []
    try:
        cleanup()
        _log_command(cmd, prefixer)
        threads = _start_stream_threads(sources, prefixer)
        ret = process.wait()
        if ret != 0:
            raise subprocess.CalledProcessError(ret, cmd)
    finally:
        for t in threads:
            t.join()


def spawn_process(
    cmd: list[str],
    *,
    cwd: os.PathLike | None = None,
    env: dict[str, str] | None = None,
    prefix: str | None = None,
    color_code: str = "36",
    line_transform: Callable[[str], str | None] | None = None,
    use_tty: bool | None = None,
) -> subprocess.Popen:
    """Spawn a process and stream its output in background threads.

    Returns immediately with the Popen object. Streaming threads are daemons.
    """
    use_pty = _should_use_pty(use_tty)
    prefixer = _make_prefixer(prefix, color_code, line_transform)

    process, sources, cleanup = _spawn_process(cmd, cwd=cwd, env=env, use_pty=use_pty)
    cleanup()
    _log_command(cmd, prefixer)
    _start_stream_threads(sources, prefixer)
    return process


@functools.cache
def _use_color() -> bool:
    """Return True if ANSI colors should be emitted to stdout.

    Respects common environment variables and falls back to TTY detection.
    """
    force_color = os.environ.get("FORCE_COLOR")

    return sys.stdout.isatty() or force_color is not None and force_color != "0"


def _colored_prefix(prefix: str, color_code: str) -> str:
    return f"\x1b[{color_code}m{prefix}\x1b[0m " if _use_color() else f"{prefix} "


def _make_prefixer(
    prefix: str | None,
    color_code: str,
    line_transform: Callable[[str], str | None] | None = None,
) -> Callable[[str], str | None]:
    colored = _colored_prefix(prefix, color_code) if prefix else ""

    def _prefixer(line: str) -> str | None:
        transformed = line_transform(line) if line_transform else line
        if transformed is None:
            return None
        return f"{colored}{transformed}"

    return _prefixer


# Unified PTY/Pipe strategy helpers


def _should_use_pty(use_tty: bool | None) -> bool:
    if platform.system() == "Windows":
        return False
    if use_tty is None:
        return sys.stdout.isatty()
    return use_tty and sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def should_use_color() -> bool:
    return _should_use_pty(None)


def _spawn_process(
    cmd: list[str],
    *,
    cwd: os.PathLike | None,
    env: dict[str, str] | None,
    use_pty: bool,
) -> tuple[subprocess.Popen, list[tuple[int | TextIO, TextIO]], Callable[[], None]]:
    if use_pty:
        import pty

        master_fd, slave_fd = pty.openpty()
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=cwd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )

        def cleanup() -> None:
            try:
                os.close(slave_fd)
            except OSError:
                pass

        sources: list[tuple[int | TextIO, TextIO]] = [
            (master_fd, cast(TextIO, sys.stdout)),
        ]
        return process, sources, cleanup

    use_shell = False
    if platform.system() == "Windows":
        use_shell = True
    process = subprocess.Popen(
        cmd,
        env=env,
        cwd=cwd,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        shell=use_shell,
    )

    def cleanup() -> None:
        return None

    assert process.stdout is not None and process.stderr is not None
    sources = [
        (process.stdout, cast(TextIO, sys.stdout)),
        (process.stderr, cast(TextIO, sys.stderr)),
    ]
    return process, sources, cleanup


def _stream_source(
    source: int | TextIO,
    writer: TextIO,
    transform: Callable[[str], str | None] | None,
) -> None:
    if isinstance(source, int):
        try:
            with os.fdopen(
                source, "r", encoding="utf-8", errors="replace", buffering=1
            ) as f:
                for line in f:
                    out = transform(line) if transform else line
                    if out is not None:
                        try:
                            writer.write(out)
                            writer.flush()
                        except UnicodeEncodeError:
                            pass
        except OSError:
            # PTY EOF may raise EIO; ignore
            pass
    else:
        for line in iter(source.readline, ""):
            out = transform(line) if transform else line
            if out is None:
                continue
            writer.write(out)
            writer.flush()
        try:
            source.close()
        except Exception:
            pass


def _log_command(cmd: list[str], transform: Callable[[str], str | None] | None) -> None:
    cmd_str = "> " + " ".join(cmd)
    if transform:
        cmd_str = transform(cmd_str)
    sys.stderr.write(cmd_str + "\n")


def _start_stream_threads(
    sources: list[tuple[int | TextIO, TextIO]],
    transform: Callable[[str], str | None] | None,
) -> list[threading.Thread]:
    threads: list[threading.Thread] = []
    for src, dst in sources:
        t = threading.Thread(
            target=_stream_source, args=(src, dst, transform), daemon=True
        )
        t.start()
        threads.append(t)
    return threads
