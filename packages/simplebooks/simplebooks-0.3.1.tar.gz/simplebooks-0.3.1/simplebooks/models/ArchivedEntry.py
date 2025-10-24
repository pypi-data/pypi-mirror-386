from __future__ import annotations
from sqloquent import SqlModel, RelatedModel, RelatedCollection, QueryBuilderProtocol
from .EntryType import EntryType
import packify


class ArchivedEntry(SqlModel):
    connection_info: str = ''
    table: str = 'archived_entries'
    id_column: str = 'id'
    columns: tuple[str] = ('id', 'type', 'amount', 'nonce', 'account_id', 'details')
    id: str
    type: str
    amount: int
    nonce: bytes
    account_id: str
    details: bytes
    account: RelatedModel
    transactions: RelatedCollection

    def __hash__(self) -> int:
        data = self.encode_value(self._encode(self.data))
        return hash(bytes(data, 'utf-8'))

    # override automatic properties
    @property
    def type(self) -> EntryType:
        """The EntryType of the Entry."""
        return EntryType(self.data['type'])
    @type.setter
    def type(self, val: EntryType):
        if type(val) is not EntryType:
            return
        self.data['type'] = val.value

    @property
    def details(self) -> packify.SerializableType:
        """A packify.SerializableType stored in the database as a blob."""
        return packify.unpack(self.data.get('details', b'n\x00\x00\x00\x00'))
    @details.setter
    def details(self, val: packify.SerializableType):
        self.data['details'] = packify.pack(val)

    @staticmethod
    def _encode(data: dict|None) -> dict|None:
        if type(data) is not dict:
            return data
        if type(data.get('type', None)) is EntryType:
            data['type'] = data['type'].value
        if type(data.get('details', {})) is not bytes:
            data['details'] = packify.pack(data.get('details', None))
        return data

    @staticmethod
    def _parse(data: dict|None) -> dict|None:
        if type(data) is dict and type(data['amount']) is str:
            data['amount'] = int(data['amount'])
        return data

    @classmethod
    def insert(cls, data: dict) -> ArchivedEntry | None:
        """Ensure data is encoded before inserting."""
        result = super().insert(cls._encode(data))
        return result

    @classmethod
    def insert_many(cls, items: list[dict]) -> int:
        """Ensure data is encoded before inserting."""
        items = [cls._encode(data) for data in list]
        return super().insert_many(items)

    @classmethod
    def query(cls, conditions: dict = None) -> QueryBuilderProtocol:
        """Ensure conditions are encoded properly before querying."""
        return super().query(cls._encode(conditions))
