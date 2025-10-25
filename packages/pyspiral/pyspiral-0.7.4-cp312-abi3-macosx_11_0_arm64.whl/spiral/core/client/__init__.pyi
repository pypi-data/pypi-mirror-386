from typing import Any, Literal

import pyarrow as pa
from spiral.api.types import DatasetName, IndexName, ProjectId, RootUri, TableName
from spiral.core.authn import Authn
from spiral.core.table import ColumnGroupState, KeyRange, KeySpaceState, Scan, ScanState, Snapshot, Table, Transaction
from spiral.core.table.spec import ColumnGroup, Schema
from spiral.expressions import Expr

class Spiral:
    """A client for Spiral database"""
    def __init__(
        self,
        api_url: str | None = None,
        spfs_url: str | None = None,
        authn: Authn | None = None,
    ):
        """Initialize the Spiral client."""
        ...
    def authn(self) -> Authn:
        """Get the current authentication context."""
        ...

    def scan(
        self,
        projection: Expr,
        filter: Expr | None = None,
        asof: int | None = None,
    ) -> Scan:
        """Construct a table scan."""
        ...

    def load_scan(self, scan_state: ScanState) -> Scan:
        """Load a scan from a serialized scan state."""
        ...

    def transaction(self, table: Table, format: str | None = None, retries: int | None = 3) -> Transaction:
        """Being a table transaction."""
        ...

    def search(
        self,
        top_k: int,
        rank_by: Expr,
        *,
        filters: Expr | None = None,
        freshness_window_s: int | None = None,
    ) -> pa.RecordBatchReader:
        """Search an index.

        Searching an index returns a stream of record batches that match table's key schema + float score column.
        """
        ...

    def table(self, table_id: str) -> Table:
        """Get a table."""
        ...

    def create_table(
        self,
        project_id: ProjectId,
        dataset: DatasetName,
        table: TableName,
        key_schema: Schema,
        *,
        root_uri: RootUri | None = None,
        exist_ok: bool = False,
    ) -> Table:
        """Create a new table in the specified project."""
        ...

    def text_index(self, index_id: str) -> TextIndex:
        """Get a text index."""
        ...

    def create_text_index(
        self,
        project_id: ProjectId,
        name: IndexName,
        projection: Expr,
        filter: Expr | None = None,
        *,
        root_uri: RootUri | None = None,
        exist_ok: bool = False,
    ) -> TextIndex:
        """Create a new index in the specified project."""
        ...

    def key_space_index(self, index_id: str) -> KeySpaceIndex:
        """Get a key space index."""
        ...

    def create_key_space_index(
        self,
        project_id: ProjectId,
        name: IndexName,
        granularity: int,
        projection: Expr,
        filter: Expr | None = None,
        *,
        root_uri: RootUri | None = None,
        exist_ok: bool = False,
    ) -> KeySpaceIndex:
        """Create a new key space index in the specified project."""
        ...

    def internal(self, *, format: str | None = None) -> Internal:
        """Internal client APIs. It can change without notice."""
        ...

class TextIndex:
    id: str

class KeySpaceIndex:
    id: str
    table_id: str
    granularity: int
    projection: Expr
    filter: Expr
    asof: int

class Shard:
    """A shard representing a partition of data.

    Attributes:
        key_range: The key range for this shard.
        cardinality: The number of rows in this shard, if known.
    """

    key_range: KeyRange
    cardinality: int | None

    def __init__(self, key_range: KeyRange, cardinality: int | None): ...
    def __getnewargs__(self) -> tuple[KeyRange, int | None]: ...

class ShuffleConfig:
    """Configuration for within-shard sample shuffling.

    This controls how samples are shuffled within a buffer, separate from
    which shards to read (which is specified as a parameter to the scan).

    Attributes:
        buffer_size: Size of the buffer pool for shuffling samples.
        seed: Random seed for reproducibility. If None, uses OS randomness.
        max_batch_size: Maximum batch size for output chunks. If None,
            defaults to max(1, buffer_size / 16).
    """

    buffer_size: int
    seed: int | None
    max_batch_size: int | None

    def __init__(
        self,
        buffer_size: int,
        *,
        seed: int | None = None,
        max_batch_size: int | None = None,
    ): ...

class Internal:
    def flush_wal(self, table: Table, *, keep_latest_s: int | None = None) -> None:
        """
        Flush the write-ahead log of the table.
        """
        ...
    def compact_key_space(
        self,
        *,
        table: Table,
        mode: Literal["plan", "read", "write"] | None = None,
        partition_bytes_min: int | None = None,
    ):
        """
        Compact the key space of the table.
        """
        ...
    def compact_column_group(
        self,
        table: Table,
        column_group: ColumnGroup,
        *,
        mode: Literal["plan", "read", "write"] | None = None,
        partition_bytes_min: int | None = None,
    ):
        """
        Compact a column group in the table.
        """
        ...
    def update_text_index(self, index: TextIndex, snapshot: Snapshot) -> None:
        """
        Index table changes up to the given snapshot.
        """
        ...
    def update_key_space_index(self, index: KeySpaceIndex, snapshot: Snapshot) -> None:
        """
        Index table changes up to the given snapshot.
        """
        ...
    def key_space_state(self, snapshot: Snapshot) -> KeySpaceState:
        """
        The key space state for the table.
        """
        ...
    def column_group_state(
        self, snapshot: Snapshot, key_space_state: KeySpaceState, column_group: ColumnGroup
    ) -> ColumnGroupState:
        """
        The state the column group of the table.
        """
        ...
    def column_groups_states(self, snapshot: Snapshot, key_space_state: KeySpaceState) -> list[ColumnGroupState]:
        """
        The state of each column group of the table.
        """
        ...
    def compute_shards(self, index: KeySpaceIndex) -> list[Shard]:
        """
        Compute the scan shards from a key space index.
        """
        ...
    def prepare_shard(
        self,
        output_path: str,
        scan: Scan,
        shard: Shard,
        row_block_size: int = 8192,
    ) -> None:
        """
        Prepare a shard locally. Used for `SpiralStream` integration with `streaming` which requires on-disk shards.
        """
        ...
    def metrics(self) -> dict[str, Any]: ...

def flush_telemetry() -> None:
    """Flush telemetry data to the configured exporter."""
    ...
