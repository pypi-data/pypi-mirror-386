import logging  # noqa: INP001
import sqlite3

from .table import QolsysTable

LOGGER = logging.getLogger(__name__)


class QolsysTablePgmOutputs(QolsysTable):

    def __init__(self, db: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
        super().__init__(db, cursor)
        self._uri = "content://com.qolsys.qolsysprovider.PgmOutputsContentProvider/pgm_outputs"
        self._table = "pgm_outputs"
        self._abort_on_error = False
        self._implemented = False


        self._columns = [
            "_id",
        ]

        self._create_table()
