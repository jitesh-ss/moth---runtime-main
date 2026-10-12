"""Allow ``python -m moth_launcher`` to use the neutral launcher."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
