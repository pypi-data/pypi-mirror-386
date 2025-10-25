import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from colorama import Fore, Style, init

from lupin_logger.constants import ATTR_COLORS, LOG_COLORS, NOTICE_LEVEL

# Initialize colorama
init(autoreset=True)

logging.addLevelName(NOTICE_LEVEL, "NOTICE")


def format_attr_console(attr: Dict[str, Any]) -> str:
    """Format attributes with colors for console output."""
    formatted_attr = []
    for key, value in attr.items():
        if isinstance(value, datetime):
            # Format lisible console (HH:MM:SS YYYY-MM-DD)
            colored_value = f"{Fore.CYAN + Style.BRIGHT}{value.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}"
        else:
            for _type, color in ATTR_COLORS.items():
                if isinstance(value, _type):
                    colored_value = f"{color}{value}{Style.RESET_ALL}"
                    break
            else:
                colored_value = f"{Fore.WHITE + Style.BRIGHT}{value}{Style.RESET_ALL}"

        formatted_attr.append(f"{key}={colored_value}")
    return " | ".join(formatted_attr)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for file logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record as a JSON string for file logging."""
        log_entry: Dict[str, Any] = {
            "tm": datetime.now().astimezone().isoformat(),
            "app": getattr(record, "app", "UnknownApp"),
            "origin": "lupin",
            "lvl": record.levelname.lower(),
            "msg": record.getMessage(),
            "loc": f"{record.pathname}:{record.lineno}",
        }

        if hasattr(record, "attr") and record.attr:
            log_entry["attr"] = {
                k: str(v) if isinstance(v, Path) else v for k, v in record.attr.items()
            }

        return json.dumps(log_entry, ensure_ascii=False, cls=CustomJsonEncoder)


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.astimezone().isoformat()
        return super().default(obj)


class ConsoleFormatter(logging.Formatter):
    """Custom formatter for console output with colors."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record for console display with colors."""
        log_color = LOG_COLORS.get(record.levelname, Fore.WHITE)
        timestamp = datetime.now().strftime("%H:%M:%S.3%f")[:-3]  # Format HH:MM:SS.mmm
        log_msg = (
            f"{timestamp} - {log_color}{Style.BRIGHT}{record.levelname}{Style.RESET_ALL}:"
            + f" {log_color}{record.getMessage()}"
        )

        if hasattr(record, "attr") and record.attr:
            log_msg += f" {Fore.RESET}{format_attr_console(record.attr)}"

        return log_msg


class CustomLogger(logging.Logger):
    """Custom logger with JSON formatting for files and colored console output."""

    def __init__(
        self,
        name: str,
        app: str,
        log_directory: Optional[str] = None,
        level: int = logging.DEBUG,
    ) -> None:
        """
        Initializes the logger.

        :param name: Logger name.
        :param app: Application name for log identification.
        :param log_directory: Directory where logs will be stored.
            Defaults to 'C:/Users/<USERNAME>/LupinDentalData/logs/'.
        :param level: Logging level (default: DEBUG).
        """
        super().__init__(name, level)
        self.app_name = app  # Stocke l'application pour l'ajouter dans les logs

        # Définit le répertoire de logs basé sur le home directory
        user_directory = Path.home()
        default_log_dir = user_directory / "LupinDentalData" / "logs"
        default_server_dir = Path("/logs")

        if log_directory and Path(log_directory).exists():
            base_log_dir = Path(log_directory).resolve()
        elif default_server_dir.exists():
            base_log_dir = default_server_dir
        else:
            base_log_dir = default_log_dir

        # Créer le sous-dossier basé sur la date du jour
        today_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H-%M-%S")
        daily_log_dir = base_log_dir / today_date
        daily_log_dir.mkdir(
            parents=True, exist_ok=True
        )  # Crée les dossiers si nécessaire

        # Définir le chemin du fichier log
        log_filename = f"{today_date}_{current_time}_{name}.lupinlog.jsonl"
        log_file_path = daily_log_dir / log_filename

        # Création du handler pour le fichier log
        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        self.addHandler(file_handler)

        # Création du handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ConsoleFormatter())
        self.addHandler(console_handler)
        self.info(
            "Logger generated.",
            {"name": name, "app": app, "base_log_dir": base_log_dir},
        )

    def _log_with_attr(
        self, level: int, msg: str, attr: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Internal method to log messages with automatic `app` and `attr`.

        :param level: Logging level.
        :param msg: Log message.
        :param attr: Additional attributes.
        """
        extra = {"app": self.app_name}

        # 🔧 Patch : si attr n’est pas un dict, on l’emballe dans un dict {"value": attr}
        if attr is not None and not isinstance(attr, dict):
            attr = {"value": attr}

        if attr:
            extra["attr"] = attr

        self.log(level, msg, extra=extra, stacklevel=3)
        # Overriding standard logging methods to inject `app` and `attr`

    def info(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        self._log_with_attr(logging.INFO, msg, attr)

    def debug(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        self._log_with_attr(logging.DEBUG, msg, attr)

    def warning(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        self._log_with_attr(logging.WARNING, msg, attr)

    def error(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        self._log_with_attr(logging.ERROR, msg, attr)

    def critical(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        self._log_with_attr(logging.CRITICAL, msg, attr)

    def notice(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        self._log_with_attr(25, msg, attr)  # Level 25 for NOTICE

    def exception(self, msg: str, attr: Optional[Dict[str, Any]] = None) -> None:
        """
        Logs an exception with traceback automatically added to `attr`.

        :param msg: Log message.
        :param attr: Additional attributes (optional).
        """
        if attr is None:
            attr = {}

        # Add traceback details
        attr["traceback"] = traceback.format_exc()

        self._log_with_attr(logging.ERROR, msg, attr)

    def log_attr(self, level: int, msg: str, attr: Optional[dict] = None) -> None:
        """
        Logs a message with attributes and ensures `app` is included.

        :param level: Log level.
        :param msg: Log message.
        :param attr: Additional attributes (default: None).
        """
        extra = {"app": self.app_name, "attr": attr if attr else {}}
        self.log(level, msg, extra=extra)


def get_logger(
    name: str = "default", app: str = "default", log_directory: Optional[str] = None
) -> CustomLogger:
    """
    Creates and returns a configured logger.

    :param name: Logger name.
    :param log_directory: Custom log directory (optional).
    :return: Configured CustomLogger instance.
    """
    return CustomLogger(name, app=app, log_directory=log_directory)
