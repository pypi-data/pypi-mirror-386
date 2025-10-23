import platform
import re

import nox

py = ["3.9", "3.14", "3.14t", "pypy3.11"]
if platform.system() != "Windows":
    py.append("graalpy3.12")


@nox.session(python=py, venv_backend="uv")
def test(session: nox.Session) -> None:
    if isinstance(session.python, str) and re.match(r"^3\.\d+t?$", session.python):
        session.install(".[test,test-extra]")
    else:
        session.install(".[test]")
    session.run("pytest", "-v", *session.posargs)
