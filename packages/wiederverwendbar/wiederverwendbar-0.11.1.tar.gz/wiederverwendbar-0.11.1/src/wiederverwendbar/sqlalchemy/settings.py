from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional, Union

from wiederverwendbar.pydantic.printable_settings import PrintableSettings, Field


class SqlalchemySettings(PrintableSettings):
    db_file: Optional[Path] = Field(default=None,
                                    title="Database File",
                                    description="File to connect to database")
    db_host: Union[IPv4Address, str, None] = Field(default=None,
                                                   title="Database Host",
                                                   description="Host to connect to database")

    db_port: Optional[int] = Field(default=None,
                                   title="Database Port",
                                   ge=0,
                                   le=65535,
                                   description="Port to connect to database")
    db_protocol: str = Field(default="sqlite",
                             title="Database Protocol",
                             description="Protocol to connect to database")
    db_name: Optional[str] = Field(default=None,
                                   title="Database Name",
                                   description="Name of the database")
    db_username: Optional[str] = Field(default=None,
                                       title="Database User",
                                       description="User to connect to database")
    db_password: Optional[str] = Field(None,
                                       title="Database Password",
                                       description="Password to connect to database",
                                       secret=True)
    db_echo: bool = Field(default=False,
                          title="Database echo.",
                          description="Echo SQL queries to console")
    db_test_on_startup: bool = Field(default=True,
                                 title="Test Database on Startup",
                                 description="Test database connection on startup")
    db_sqlite_check_if_file_exist: bool = Field(default=True,
                                                title="Database SQLite Check If File Exist",
                                                description="Check if file exists in SQLite")
    db_sqlite_handle_foreign_keys: bool = Field(default=True,
                                                title="Database SQLite Handle Foreign Keys",
                                                description="Handle foreign keys in SQLite")
