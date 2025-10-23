from enum import Enum

class SQLiteForeignKey(Enum):
    """
    Enumeration for representing the state of foreign key constraints in SQLite.
    Attributes:
        ON (str): Enables foreign key constraint enforcement.
        OFF (str): Disables foreign key constraint enforcement.
    """

    ON = "ON"       # Enables foreign key constraint enforcement
    OFF = "OFF"     # Disables foreign key constraint enforcement