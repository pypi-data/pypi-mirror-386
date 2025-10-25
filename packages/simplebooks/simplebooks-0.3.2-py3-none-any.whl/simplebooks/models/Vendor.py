from sqloquent import SqlModel
import packify


_None = packify.pack(None)


class Vendor(SqlModel):
    connection_info: str = ''
    table: str = 'vendors'
    id_column: str = 'id'
    columns: tuple[str] = ('id', 'name', 'code', 'details')
    id: str
    name: str
    code: str|None
    details: str|None

    # override automatic property
    @property
    def details(self) -> packify.SerializableType:
        """A packify.SerializableType stored in the database as a blob."""
        return packify.unpack(self.data.get('details', None) or _None)
    @details.setter
    def details(self, val: packify.SerializableType):
        if isinstance(val, packify.SerializableType):
            self.data['details'] = packify.pack(val)
