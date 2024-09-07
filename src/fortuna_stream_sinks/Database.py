import os.path
import sqlite3
from fortuna_stream_sinks.FortunaBlock import FortunaBlock
from fortuna_stream_sinks.FortunaConversion import FortunaConversion
from fortuna_stream_sinks.FortunaDifficultyChange import FortunaDifficultyChange
from fortuna_stream_sinks.Transaction import Transaction


class Database:
    def __init__(self, path):
        self.path = path

    def migrate(self) -> None:
        if not os.path.exists(self.path):
            self._create_database()

        version = self._get_version()

        if version < 1:
            self._migrate_to_v1()

        if version < 2:
            self._migrate_to_v2()

    def get_block(self, number: int) -> FortunaBlock | None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT b.number, b.miner, b.rewards, b.leading_zeroes, b.difficulty, t.hash, t.validity_from, t.validity_to, t.version, t.raw_json FROM blocks AS b JOIN transactions AS t ON b.transaction_hash = t.hash WHERE b.number = ?", (number,))
            row = result.fetchone()

            if row is None:
                return None

            return FortunaBlock(
                Transaction(
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9]
                ),
                row[0],
                row[1],
                row[2],
                row[3],
                row[4]
            )
        finally:
            self._close_connection(connection)

    def insert_transaction(self, transaction: Transaction) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("INSERT OR REPLACE INTO transactions(hash, validity_from, validity_to, version, raw_json) VALUES(?, ?, ?, ?, ?)",
                           (transaction.hash, transaction.validity_from, transaction.validity_to, transaction.version, transaction.raw_json))

            connection.commit()
        finally:
            self._close_connection(connection)

    def insert_block(self, block: FortunaBlock) -> None:
        transaction = block.transaction
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("INSERT OR REPLACE INTO transactions(hash, validity_from, validity_to, version, raw_json) VALUES(?, ?, ?, ?, ?)",
                           (transaction.hash, transaction.validity_from, transaction.validity_to, transaction.version, transaction.raw_json))
            cursor.execute("INSERT OR REPLACE INTO blocks(number, miner, rewards, leading_zeroes, difficulty, transaction_hash, queued) VALUES(?, ?, ?, ?, ?, ?, 1)",
                           (block.number, block.miner, block.rewards, block.leading_zeroes, block.difficulty, transaction.hash))

            connection.commit()
        finally:
            self._close_connection(connection)

    def insert_difficulty_change(self, block_number: int) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("INSERT OR REPLACE INTO difficulty_changes(block_number, queued) VALUES(?, 1)", (block_number,))

            connection.commit()
        finally:
            self._close_connection(connection)

    def insert_v1_to_v2_conversion(self, conversion: FortunaConversion) -> None:
        transaction = conversion.transaction
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("INSERT OR REPLACE INTO transactions(hash, validity_from, validity_to, version, raw_json) VALUES(?, ?, ?, ?, ?)",
                           (transaction.hash, transaction.validity_from, transaction.validity_to, transaction.version, transaction.raw_json))
            cursor.execute("INSERT OR REPLACE INTO conversions(transaction_hash, address, amount, from_version, to_version, queued) VALUES(?, ?, ?, ?, ?, 1)",
                           (transaction.hash, conversion.address, conversion.amount, conversion.from_version, conversion.to_version))

            connection.commit()
        finally:
            self._close_connection(connection)

    def get_blocks_queued(self) -> list[FortunaBlock]:
        blocks: list[FortunaBlock] = []

        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT b.number, b.miner, b.rewards, b.leading_zeroes, b.difficulty, t.hash, t.validity_from, t.validity_to, t.version, t.raw_json FROM blocks AS b JOIN transactions AS t ON b.transaction_hash = t.hash WHERE b.queued = 1 ORDER BY b.number DESC")
            rows = result.fetchall()

            for row in rows:
                blocks.append(FortunaBlock(
                    Transaction(
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        row[9]
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

    def set_blocks_queued_off(self, number: int) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("UPDATE blocks SET queued = 0 WHERE queued = 1 AND number <= ?", (number,))

            connection.commit()
        finally:
            self._close_connection(connection)

    def get_conversions_queued(self) -> list[FortunaConversion]:
        conversions: list[FortunaConversion] = []

        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT c.address, c.amount, c.from_version, c.to_version, t.hash, t.validity_from, t.validity_to, t.version, t.raw_json FROM conversions AS c JOIN transactions AS t ON c.transaction_hash = t.hash WHERE c.queued = 1 ORDER BY c.rowid DESC")
            rows = result.fetchall()

            for row in rows:
                conversions.append(FortunaConversion(
                    Transaction(
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8]
                    ),
                    row[0],
                    row[1],
                    row[2],
                    row[3]
                ))
        finally:
            self._close_connection(connection)

        return conversions

    def set_conversions_queued_off(self, transaction_hash: str) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("UPDATE conversions SET queued = 0 WHERE queued = 1 AND rowid <= (SELECT rowid FROM conversions WHERE transaction_hash = ?)", (transaction_hash,))

            connection.commit()
        finally:
            self._close_connection(connection)

    def get_difficulty_changes_queued(self) -> list[FortunaDifficultyChange]:
        difficulty_changes: list[FortunaDifficultyChange] = []

        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            result = cursor.execute("SELECT b.number, b.leading_zeroes, b.difficulty FROM difficulty_changes AS dc JOIN blocks AS b ON b.number = dc.block_number WHERE dc.queued = 1 ORDER BY dc.rowid DESC")
            rows = result.fetchall()

            for row in rows:
                difficulty_changes.append(FortunaDifficultyChange(
                    row[0],
                    row[1],
                    row[2]
                ))
        finally:
            self._close_connection(connection)

        return difficulty_changes

    def set_difficulty_changes_queued_off(self, block_number: int) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("UPDATE difficulty_changes SET queued = 0 WHERE queued = 1 AND block_number <= ?", (block_number,))

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
                           "validity_to INTEGER,"
                           "version INTEGER,"
                           "raw_json TEXT)")
            cursor.execute("CREATE TABLE blocks("
                           "number INTEGER PRIMARY KEY, "
                           "miner TEXT, "
                           "rewards INTEGER, "
                           "leading_zeroes INTEGER, "
                           "difficulty INTEGER, "
                           "transaction_hash TEXT, "
                           "queued INTEGER, "
                           "FOREIGN KEY(transaction_hash) REFERENCES transactions(hash))")
            cursor.execute("CREATE TABLE difficulty_changes("
                           "block_number INTEGER PRIMARY KEY, "
                           "FOREIGN KEY(block_number) REFERENCES blocks(number))")
            cursor.execute("CREATE TABLE conversions("
                           "transaction_hash TEXT PRIMARY KEY, "
                           "from_version INTEGER,"
                           "to_version INTEGER,"
                           "address TEXT,"
                           "amount INTEGER,"
                           "queued INTEGER, "
                           "FOREIGN KEY(transaction_hash) REFERENCES transactions(hash))")

            connection.commit()
        finally:
            self._close_connection(connection)

    def _migrate_to_v2(self) -> None:
        connection = None

        try:
            connection = self._open_connection()

            cursor = connection.cursor()
            cursor.execute("ALTER TABLE difficulty_changes ADD COLUMN queued INTEGER")
            cursor.execute("UPDATE difficulty_changes SET queued = 0")
            cursor.execute("UPDATE version SET number = 2")

            connection.commit()
        finally:
            self._close_connection(connection)

    def _open_connection(self):
        return sqlite3.connect(self.path)

    def _close_connection(self, connection) -> None:
        if connection is not None:
            connection.close()
