from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UserDefinedType


class Geography(UserDefinedType):
    cache_ok = True

    def __init__(self, geometry_type: str, srid: int = 4326) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **kw) -> str:
        return f"geography({self.geometry_type},{self.srid})"


@compiles(Geography, "sqlite")
def compile_geography_sqlite(type_: Geography, compiler, **kw) -> str:
    return "TEXT"


@compiles(Geography, "postgresql")
def compile_geography_postgresql(type_: Geography, compiler, **kw) -> str:
    return type_.get_col_spec()
