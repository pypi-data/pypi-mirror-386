from dataclasses import dataclass
from typing import Optional

from _qwak_proto.qwak.feature_store.sources.batch_pb2 import (
    BatchSource as ProtoBatchSource,
    JdbcSource as ProtoJdbcSource,
    PostgresqlSource as ProtoPostgresqlSource,
)
from _qwak_proto.qwak.feature_store.sources.data_source_pb2 import (
    DataSourceSpec as ProtoDataSourceSpec,
)
from qwak.feature_store.data_sources.batch._jdbc import JdbcSource


@dataclass
class PostgresSource(JdbcSource):
    def _to_proto(self, artifact_url: Optional[str] = None):
        return ProtoDataSourceSpec(
            data_source_repository_name=self.repository,
            batch_source=ProtoBatchSource(
                name=self.name,
                description=self.description,
                date_created_column=self.date_created_column,
                jdbcSource=ProtoJdbcSource(
                    url=self.url,
                    username_secret_name=self.username_secret_name,
                    password_secret_name=self.password_secret_name,
                    db_table=self.db_table,
                    query=self.query,
                    postgresqlSource=ProtoPostgresqlSource(),
                ),
            ),
        )

    @classmethod
    def _from_proto(cls, proto):
        postgresql = proto.jdbcSource
        return cls(
            name=proto.name,
            date_created_column=proto.date_created_column,
            description=proto.description,
            url=postgresql.url,
            username_secret_name=postgresql.username_secret_name,
            password_secret_name=postgresql.password_secret_name,
            db_table=postgresql.db_table,
            query=postgresql.query,
        )
