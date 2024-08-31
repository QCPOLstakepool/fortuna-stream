import os.path
import sqlite3
from fortuna_stream_sinks.FortunaBlock import FortunaBlock
from fortuna_stream_sinks.FortunaConversion import FortunaConversion
from fortuna_stream_sinks.Transaction import Transaction


class Database:
    def __init__(self, path):
        self.path = path

    def migrate(self):
        if not os.path.exists(self.path):
            self._create_database()

        version = self._get_version()

        if version < 1:
            self._migrate_to_v1()

    def insert_block(self, block: FortunaBlock) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("INSERT INTO transactions(hash, validity_from, validity_to) VALUES(?, ?, ?)",
                           (block.transaction.hash, block.transaction.validity_from, block.transaction.validity_to))
            cursor.execute("INSERT INTO blocks(number, miner, rewards, leading_zeroes, difficulty, transaction_hash, posted_on_x) VALUES(?, ?, ?, ?, ?, ?, 0)",
                           (block.number, block.miner, block.rewards, block.leading_zeroes, block.difficulty, block.transaction.hash))

            connection.commit()
        finally:
            self._close_connection(connection)

    def insert_v1_to_v2_conversion(self, conversion: FortunaConversion) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("INSERT INTO transactions(hash, validity_from, validity_to) VALUES(?, ?, ?)",
                           (conversion.transaction.hash, conversion.transaction.validity_from, conversion.transaction.validity_to))
            cursor.execute("INSERT INTO conversions(transaction_hash, address, amount, from_version, to_version, posted_on_x) VALUES(?, ?, ?, ?, ?, 0)",
                           (conversion.transaction.hash, conversion.address, conversion.amount, conversion.from_version, conversion.to_version))

            connection.commit()
        finally:
            self._close_connection(connection)

    def get_blocks_not_posted_on_x(self) -> list[FortunaBlock]:
        blocks: list[FortunaBlock] = []

        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT b.number, b.miner, b.rewards, b.leading_zeroes, b.difficulty, t.hash, t.validity_from, t.validity_to FROM blocks AS b JOIN transactions AS t ON b.transaction_hash = t.hash WHERE b.posted_on_x = 0 ORDER BY b.number DESC")
            rows = result.fetchall()

            for row in rows:
                blocks.append(FortunaBlock(
                    Transaction(
                        row[5],
                        row[6],
                        row[7]
                    ),
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4]
                ))
        finally:
            self._close_connection(connection)

        return blocks

    def set_blocks_posted_on_x(self, number: int) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("UPDATE blocks SET posted_on_x = 1 WHERE posted_on_x = 0 AND number <= ?", (number,))

            connection.commit()
        finally:
            self._close_connection(connection)

    def get_conversions_not_posted_on_x(self) -> list[FortunaConversion]:
        conversions: list[FortunaConversion] = []

        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT c.address, c.amount, c.from_version, c.to_version, t.hash, t.validity_from, t.validity_to FROM conversions AS c JOIN transactions AS t ON c.transaction_hash = t.hash WHERE c.posted_on_x = 0 ORDER BY c.rowid DESC")
            rows = result.fetchall()

            for row in rows:
                conversions.append(FortunaConversion(
                    Transaction(
                        row[4],
                        row[5],
                        row[6]
                    ),
                    row[0],
                    row[1],
                    row[2],
                    row[3]
                ))
        finally:
            self._close_connection(connection)

        return conversions

    def set_conversions_posted_on_x(self, transaction_hash: str) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("UPDATE conversions SET posted_on_x = 1 WHERE posted_on_x = 0 AND rowid <= (SELECT rowid FROM conversions WHERE transaction_hash = ?)", (transaction_hash,))

            connection.commit()
        finally:
            self._close_connection(connection)

    def _create_database(self) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("CREATE TABLE version(number INTEGER PRIMARY KEY)")
            cursor.execute("INSERT INTO version(number) VALUES(0)")

            connection.commit()
        finally:
            self._close_connection(connection)

    def _get_version(self) -> int:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT number FROM version")

            return result.fetchone()[0]
        finally:
            self._close_connection(connection)

    def _migrate_to_v1(self) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("UPDATE version SET number = 1")
            cursor.execute("CREATE TABLE transactions("
                           "hash TEXT PRIMARY_KEY, "
                           "validity_from INTEGER, "
                           "validity_to INTEGER)")
            cursor.execute("CREATE TABLE blocks("
                           "number INTEGER PRIMARY KEY, "
                           "miner TEXT, "
                           "rewards INTEGER, "
                           "leading_zeroes INTEGER, "
                           "difficulty INTEGER, "
                           "transaction_hash TEXT, "
                           "posted_on_x INTEGER, "
                           "FOREIGN KEY(transaction_hash) REFERENCES transactions(hash))")
            cursor.execute("CREATE TABLE conversions("
                           "transaction_hash TEXT PRIMARY KEY, "
                           "from_version INTEGER,"
                           "to_version INTEGER,"
                           "address TEXT,"
                           "amount INTEGER,"
                           "posted_on_x INTEGER, "
                           "FOREIGN KEY(transaction_hash) REFERENCES transactions(hash))")

            connection.commit()
        finally:
            self._close_connection(connection)

    def _open_connection(self):
        return sqlite3.connect(self.path)

    def _close_connection(self, connection) -> None:
        if connection is not None:
            connection.close()
