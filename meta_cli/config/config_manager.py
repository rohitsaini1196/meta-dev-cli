import os
import stat
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

CONFIG_DIR = Path.home() / ".meta-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config(BaseModel):
    access_token: Optional[str] = None
    default_app_id: Optional[str] = None
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None


class ConfigError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None):
        import meta_cli.config.config_manager as _mod
        self.config_path = config_path if config_path is not None else _mod.CONFIG_FILE

    def load(self) -> Config:
        if not self.config_path.exists():
            return Config()
        try:
            return Config.model_validate_json(self.config_path.read_text())
        except Exception:
            return Config()

    def save(self, config: Config) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_suffix(".tmp")
        tmp_path.write_text(config.model_dump_json(indent=2))
        tmp_path.replace(self.config_path)
        os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)

    def update(self, **kwargs) -> Config:
        config = self.load()
        updated = config.model_copy(update=kwargs)
        self.save(updated)
        return updated

    def require_token(self) -> str:
        config = self.load()
        if not config.access_token:
            raise ConfigError(
                "No access token found.",
                hint="Run: meta login",
            )
        return config.access_token

    def require_app_id(self) -> str:
        config = self.load()
        if not config.default_app_id:
            raise ConfigError(
                "No default app selected.",
                hint="Run: meta apps use <app-id>",
            )
        return config.default_app_id

    def require_waba_id(self) -> str:
        config = self.load()
        if not config.waba_id:
            raise ConfigError(
                "No WhatsApp Business Account ID configured.",
                hint=(
                    "Find your WABA ID:\n"
                    "  1. Go to https://developers.facebook.com/apps\n"
                    "  2. Select your app → WhatsApp → API Setup\n"
                    "  3. Copy the 'WhatsApp Business Account ID' shown at the top\n\n"
                    "Then run: meta wa setup --waba-id <id> --phone-number-id <id>"
                ),
            )
        return config.waba_id

    def require_phone_number_id(self) -> str:
        config = self.load()
        if not config.phone_number_id:
            raise ConfigError(
                "No sender phone number ID configured.",
                hint=(
                    "Find your Phone Number ID:\n"
                    "  1. Go to https://developers.facebook.com/apps\n"
                    "  2. Select your app → WhatsApp → API Setup\n"
                    "  3. Copy the 'Phone number ID' listed under 'Send and receive messages'\n\n"
                    "Then run: meta wa setup --waba-id <id> --phone-number-id <id>"
                ),
            )
        return config.phone_number_id
