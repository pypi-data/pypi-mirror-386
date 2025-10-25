import os
from pathlib import Path

from dotenv import load_dotenv


class EnvPathsAccess:
    annotations: str
    annotations_plmarker: str
    predictions: str
    raw_docs: str

    def __getattr__(self, name):
        load_dotenv()
        name_in_env = f"PATH_{name.upper()}"
        value = os.environ.get(name_in_env)
        if value is None:
            raise AttributeError(
                f"Set {name_in_env} in .env file or as environment variable."
            )
        return Path(value)


paths = EnvPathsAccess()
