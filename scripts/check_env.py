#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def load_env_file(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if (val.startswith("\"") and val.endswith("\"")) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        env[key] = val
    return env


def main(argv: list[str]) -> int:
    env = load_env_file(ENV_PATH)
    # Overlay real environment (docker-compose may override)
    env = {**env, **os.environ}

    required = [
        "DJANGO_SETTINGS_MODULE",
        "SECRET_KEY",
        "DEBUG",
        "ALLOWED_HOSTS",
        # DB required by entrypoint wait + Django
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_DATABASE",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        # Celery/Redis
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
    ]

    # Require superuser vars only if CREATE_SUPERUSER=1
    if str(env.get("CREATE_SUPERUSER", "0")).lower() in {"1", "true", "yes", "on"}:
        required += [
            "DJANGO_SU_EMAIL",
            "DJANGO_SU_PASSWORD",
        ]

    missing = [k for k in required if not env.get(k)]

    warnings = []
    sk = env.get("SECRET_KEY", "")
    if sk in {"your-secret-key-here", "dev-secret", "dev-only-secret-key-change-me"} or len(sk) < 32:
        warnings.append("SECRET_KEY appears weak or placeholder; generate a strong key.")

    # IA local (Ollama) opcional pero recomendada para procesar descriptores
    if str(env.get("AI_PROVIDER", "ollama")).lower() == "ollama":
        if not env.get("OLLAMA_BASE_URL"):
            warnings.append("OLLAMA_BASE_URL not set; defaulting to http://host.docker.internal:11434.")
        if not env.get("OLLAMA_MODEL"):
            warnings.append("OLLAMA_MODEL not set; defaulting to phi3:mini.")
        if not env.get("AI_SCHEMA_VERSION"):
            warnings.append("AI_SCHEMA_VERSION not set; defaulting to v1.")

    if missing:
        print("Missing required variables in .env or environment:")
        for k in missing:
            print(f" - {k}")
        if warnings:
            print()
            print("Warnings:")
            for w in warnings:
                print(f" - {w}")
        return 1
    else:
        print("All required variables are present.")
        if warnings:
            print("Warnings:")
            for w in warnings:
                print(f" - {w}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

