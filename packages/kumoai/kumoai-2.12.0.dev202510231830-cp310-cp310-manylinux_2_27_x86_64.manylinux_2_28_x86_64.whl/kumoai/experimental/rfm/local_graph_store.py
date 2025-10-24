import warnings
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from kumoapi.rfm.context import Subgraph
from kumoapi.typing import Stype

from kumoai.experimental.rfm import LocalGraph
from kumoai.experimental.rfm.utils import normalize_text
from kumoai.utils import InteractiveProgressLogger, ProgressLogger

try:
    import torch
    WITH_TORCH = True
except ImportError:
    WITH_TORCH = False


class LocalGraphStore:
    def __init__(
        self,
        graph: LocalGraph,
        preprocess: bool = False,
        verbose: Union[bool, ProgressLogger] = True,
    ) -> None:

        if not isinstance(verbose, ProgressLogger):
            verbose = InteractiveProgressLogger(
                "Materializing graph",
                verbose=verbose,
            )

        with verbose as logger:
            self.df_dict, self.mask_dict = self.sanitize(graph, preprocess)
            self.stype_dict = self.get_stype_dict(graph)
            logger.log("Sanitized input data")

            self.pkey_name_dict, self.pkey_map_dict = self.get_pkey_data(graph)
            num_pkeys = sum(t.has_primary_key() for t in graph.tables.values())
            if num_pkeys > 1:
                logger.log(f"Collected primary keys from {num_pkeys} tables")
            else:
                logger.log(f"Collected primary key from {num_pkeys} table")

            (
                self.time_column_dict,
                self.end_time_column_dict,
                self.time_dict,
                self.min_time,
                self.max_time,
            ) = self.get_time_data(graph)
            if self.max_time != pd.Timestamp.min:
                logger.log(f"Identified temporal graph from "
                           f"{self.min_time.date()} to {self.max_time.date()}")
            else:
                logger.log("Identified static graph without timestamps")

            self.row_dict, self.colptr_dict = self.get_csc(graph)
            num_nodes = sum(len(df) for df in self.df_dict.values())
            num_edges = sum(len(row) for row in self.row_dict.values())
            logger.log(f"Created graph with {num_nodes:,} nodes and "
                       f"{num_edges:,} edges")

    @property
    def node_types(self) -> List[str]:
        return list(self.df_dict.keys())

    @property
    def edge_types(self) -> List[Tuple[str, str, str]]:
        return list(self.row_dict.keys())

    def get_node_id(self, table_name: str, pkey: pd.Series) -> np.ndarray:
        r"""Returns the node ID given primary keys.

        Args:
            table_name: The table name.
            pkey: The primary keys to receive node IDs for.
        """
        if table_name not in self.df_dict.keys():
            raise KeyError(f"Table '{table_name}' does not exist")

        if table_name not in self.pkey_map_dict.keys():
            raise ValueError(f"Table '{table_name}' does not have a primary "
                             f"key")

        if len(pkey) == 0:
            raise KeyError(f"No primary keys passed for table '{table_name}'")

        pkey_map = self.pkey_map_dict[table_name]

        try:
            pkey = pkey.astype(type(pkey_map.index[0]))
        except ValueError as e:
            raise ValueError(f"Could not cast primary keys "
                             f"{pkey.tolist()} to the expected data "
                             f"type '{pkey_map.index.dtype}'") from e

        try:
            return pkey_map.loc[pkey]['arange'].to_numpy()
        except KeyError as e:
            missing = ~np.isin(pkey, pkey_map.index)
            raise KeyError(f"The primary keys {pkey[missing].tolist()} do "
                           f"not exist in the '{table_name}' table") from e

    def sanitize(
        self,
        graph: LocalGraph,
        preprocess: bool = False,
    ) -> Tuple[Dict[str, pd.DataFrame], Dict[str, np.ndarray]]:
        r"""Sanitizes raw data according to table schema definition:

        In particular, it:
        * converts timestamp data to `pd.Datetime`
        * drops timezone information from timestamps
        * drops duplicate primary keys
        * removes rows with missing primary keys or time values

        If ``preprocess`` is set to ``True``, it will additionally pre-process
        data for faster model processing. In particular, it:
        * tokenizes any text column that is not a foreign key
        """
        df_dict: Dict[str, pd.DataFrame] = {
            table_name: table._data.copy(deep=False).reset_index(drop=True)
            for table_name, table in graph.tables.items()
        }

        foreign_keys = {(edge.src_table, edge.fkey) for edge in graph.edges}

        mask_dict: Dict[str, np.ndarray] = {}
        for table in graph.tables.values():
            for col in table.columns:
                if col.stype == Stype.timestamp:
                    ser = df_dict[table.name][col.name]
                    if not pd.api.types.is_datetime64_any_dtype(ser):
                        with warnings.catch_warnings():
                            warnings.filterwarnings(
                                'ignore',
                                message='Could not infer format',
                            )
                            ser = pd.to_datetime(ser, errors='coerce')
                        df_dict[table.name][col.name] = ser
                    if isinstance(ser.dtype, pd.DatetimeTZDtype):
                        ser = ser.dt.tz_localize(None)
                        df_dict[table.name][col.name] = ser

                # Normalize text in advance (but exclude foreign keys):
                if (preprocess and col.stype == Stype.text
                        and (table.name, col.name) not in foreign_keys):
                    ser = df_dict[table.name][col.name]
                    df_dict[table.name][col.name] = normalize_text(ser)

            mask: Optional[np.ndarray] = None
            if table._time_column is not None:
                ser = df_dict[table.name][table._time_column]
                mask = ser.notna().to_numpy()

            if table._primary_key is not None:
                ser = df_dict[table.name][table._primary_key]
                _mask = (~ser.duplicated().to_numpy()) & ser.notna().to_numpy()
                mask = _mask if mask is None else (_mask & mask)

            if mask is not None and not mask.all():
                mask_dict[table.name] = mask

        return df_dict, mask_dict

    def get_stype_dict(self, graph: LocalGraph) -> Dict[str, Dict[str, Stype]]:
        stype_dict: Dict[str, Dict[str, Stype]] = {}
        foreign_keys = {(edge.src_table, edge.fkey) for edge in graph.edges}
        for table in graph.tables.values():
            stype_dict[table.name] = {}
            for column in table.columns:
                if column == table.primary_key:
                    continue
                if (table.name, column.name) in foreign_keys:
                    continue
                stype_dict[table.name][column.name] = column.stype
        return stype_dict

    def get_pkey_data(
        self,
        graph: LocalGraph,
    ) -> Tuple[
            Dict[str, str],
            Dict[str, pd.DataFrame],
    ]:
        pkey_name_dict: Dict[str, str] = {}
        pkey_map_dict: Dict[str, pd.DataFrame] = {}

        for table in graph.tables.values():
            if table._primary_key is None:
                continue

            pkey_name_dict[table.name] = table._primary_key
            pkey = self.df_dict[table.name][table._primary_key]
            pkey_map = pd.DataFrame(
                dict(arange=range(len(pkey))),
                index=pkey,
            )
            if table.name in self.mask_dict:
                pkey_map = pkey_map[self.mask_dict[table.name]]

            if len(pkey_map) == 0:
                error_msg = f"Found no valid rows in table '{table.name}'. "
                if table.has_time_column():
                    error_msg += ("Please make sure that there exists valid "
                                  "non-N/A primary key and time column pairs "
                                  "in this table.")
                else:
                    error_msg += ("Please make sure that there exists valid "
                                  "non-N/A primary keys in this table.")
                raise ValueError(error_msg)

            pkey_map_dict[table.name] = pkey_map

        return pkey_name_dict, pkey_map_dict

    def get_time_data(
        self,
        graph: LocalGraph,
    ) -> Tuple[
            Dict[str, str],
            Dict[str, str],
            Dict[str, np.ndarray],
            pd.Timestamp,
            pd.Timestamp,
    ]:
        time_column_dict: Dict[str, str] = {}
        end_time_column_dict: Dict[str, str] = {}
        time_dict: Dict[str, np.ndarray] = {}
        min_time = pd.Timestamp.max
        max_time = pd.Timestamp.min
        for table in graph.tables.values():
            if table._end_time_column is not None:
                end_time_column_dict[table.name] = table._end_time_column

            if table._time_column is None:
                continue

            time = self.df_dict[table.name][table._time_column]
            time_dict[table.name] = time.astype('datetime64[ns]').astype(
                int).to_numpy() // 1000**3
            time_column_dict[table.name] = table._time_column

            if table.name in self.mask_dict.keys():
                time = time[self.mask_dict[table.name]]
            if len(time) > 0:
                min_time = min(min_time, time.min())
                max_time = max(max_time, time.max())

        return (
            time_column_dict,
            end_time_column_dict,
            time_dict,
            min_time,
            max_time,
        )

    def get_csc(
        self,
        graph: LocalGraph,
    ) -> Tuple[
            Dict[Tuple[str, str, str], np.ndarray],
            Dict[Tuple[str, str, str], np.ndarray],
    ]:
        # A mapping from raw primary keys to node indices (0 to N-1):
        map_dict: Dict[str, pd.CategoricalDtype] = {}
        # A dictionary to manage offsets of node indices for invalid rows:
        offset_dict: Dict[str, np.ndarray] = {}
        for table_name in set(edge.dst_table for edge in graph.edges):
            ser = self.df_dict[table_name][graph[table_name]._primary_key]
            if table_name in self.mask_dict.keys():
                mask = self.mask_dict[table_name]
                ser = ser[mask]
                offset_dict[table_name] = np.cumsum(~mask)[mask]
            map_dict[table_name] = pd.CategoricalDtype(ser, ordered=True)

        # Build CSC graph representation:
        row_dict: Dict[Tuple[str, str, str], np.ndarray] = {}
        colptr_dict: Dict[Tuple[str, str, str], np.ndarray] = {}
        for src_table, fkey, dst_table in graph.edges:
            src_df = self.df_dict[src_table]
            dst_df = self.df_dict[dst_table]

            src = np.arange(len(src_df))
            dst = src_df[fkey].astype(map_dict[dst_table]).cat.codes.to_numpy()
            dst = dst.astype(int)
            mask = dst >= 0
            if dst_table in offset_dict.keys():
                dst = dst + offset_dict[dst_table][dst]
            if src_table in self.mask_dict.keys():
                mask &= self.mask_dict[src_table]
            src, dst = src[mask], dst[mask]

            # Sort by destination/column (and time within neighborhoods):
            # `lexsort` is expensive (especially in numpy) so avoid it if
            # possible by grouping `time` and `node_id` together:
            if src_table in self.time_dict:
                src_time = self.time_dict[src_table][src]
                min_time = int(src_time.min())
                max_time = int(src_time.max())
                offset = (max_time - min_time) + 1
                if offset * len(dst_df) <= np.iinfo(np.int64).max:
                    index = dst * offset + (src_time - min_time)
                    perm = _argsort(index)
                else:  # Safe route to avoid `int64` overflow:
                    perm = _lexsort([src_time, dst])
            else:
                perm = _argsort(dst)

            row, col = src[perm], dst[perm]

            # Convert into compressed representation:
            colcount = np.bincount(col, minlength=len(dst_df))
            colptr = np.empty(len(colcount) + 1, dtype=colcount.dtype)
            colptr[0] = 0
            np.cumsum(colcount, out=colptr[1:])
            edge_type = (src_table, fkey, dst_table)
            row_dict[edge_type] = row
            colptr_dict[edge_type] = colptr

            # Reverse connection - no sort and no time handling needed since
            # the reverse mapping is 1-to-many.
            row, col = dst, src
            colcount = np.bincount(col, minlength=len(src_df))
            colptr = np.empty(len(colcount) + 1, dtype=colcount.dtype)
            colptr[0] = 0
            np.cumsum(colcount, out=colptr[1:])
            edge_type = Subgraph.rev_edge_type(edge_type)
            row_dict[edge_type] = row
            colptr_dict[edge_type] = colptr

        return row_dict, colptr_dict


def _argsort(input: np.ndarray) -> np.ndarray:
    if not WITH_TORCH:
        return np.argsort(input)
    return torch.from_numpy(input).argsort().numpy()


def _lexsort(inputs: List[np.ndarray]) -> np.ndarray:
    assert len(inputs) >= 1

    if not WITH_TORCH:
        return np.lexsort(inputs)

    try:
        out = torch.from_numpy(inputs[0]).argsort(stable=True)
    except Exception:
        return np.lexsort(inputs)  # PyTorch<1.9 without `stable` support.

    for input in inputs[1:]:
        index = torch.from_numpy(input)[out]
        index = index.argsort(stable=True)
        out = out[index]

    return out.numpy()
