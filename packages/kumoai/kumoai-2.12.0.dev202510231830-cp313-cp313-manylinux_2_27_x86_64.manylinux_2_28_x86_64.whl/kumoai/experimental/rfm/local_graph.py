import contextlib
import io
import warnings
from collections import defaultdict
from importlib.util import find_spec
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import pandas as pd
from kumoapi.graph import ColumnKey, ColumnKeyGroup, GraphDefinition
from kumoapi.table import TableDefinition
from kumoapi.typing import Stype
from typing_extensions import Self

from kumoai import in_notebook
from kumoai.experimental.rfm import LocalTable
from kumoai.graph import Edge

if TYPE_CHECKING:
    import graphviz


class LocalGraph:
    r"""A graph of :class:`LocalTable` objects, akin to relationships between
    tables in a relational database.

    Creating a graph is the final step of data definition; after a
    :class:`LocalGraph` is created, you can use it to initialize the
    Kumo Relational Foundation Model (:class:`KumoRFM`).

    .. code-block:: python

        >>> # doctest: +SKIP
        >>> import pandas as pd
        >>> import kumoai.experimental.rfm as rfm

        >>> # Load data frames into memory:
        >>> df1 = pd.DataFrame(...)
        >>> df2 = pd.DataFrame(...)
        >>> df3 = pd.DataFrame(...)

        >>> # Define tables from data frames:
        >>> table1 = rfm.LocalTable(name="table1", data=df1)
        >>> table2 = rfm.LocalTable(name="table2", data=df2)
        >>> table3 = rfm.LocalTable(name="table3", data=df3)

        >>> # Create a graph from a dictionary of tables:
        >>> graph = rfm.LocalGraph({
        ...     "table1": table1,
        ...     "table2": table2,
        ...     "table3": table3,
        ... })

        >>> # Infer table metadata:
        >>> graph.infer_metadata()

        >>> # Infer links/edges:
        >>> graph.infer_links()

        >>> # Inspect table metadata:
        >>> for table in graph.tables.values():
        ...     table.print_metadata()

        >>> # Visualize graph (if graphviz is installed):
        >>> graph.visualize()

        >>> # Add/Remove edges between tables:
        >>> graph.link(src_table="table1", fkey="id1", dst_table="table2")
        >>> graph.unlink(src_table="table1", fkey="id1", dst_table="table2")

        >>> # Validate graph:
        >>> graph.validate()
    """

    # Constructors ############################################################

    def __init__(
        self,
        tables: List[LocalTable],
        edges: Optional[List[Edge]] = None,
    ) -> None:

        self._tables: Dict[str, LocalTable] = {}
        self._edges: List[Edge] = []

        for table in tables:
            self.add_table(table)

        for edge in (edges or []):
            _edge = Edge._cast(edge)
            assert _edge is not None
            self.link(*_edge)

    @classmethod
    def from_data(
        cls,
        df_dict: Dict[str, pd.DataFrame],
        edges: Optional[List[Edge]] = None,
        infer_metadata: bool = True,
        verbose: bool = True,
    ) -> Self:
        r"""Creates a :class:`LocalGraph` from a dictionary of
        :class:`pandas.DataFrame` objects.

        Automatically infers table metadata and links.

        .. code-block:: python

            >>> # doctest: +SKIP
            >>> import pandas as pd
            >>> import kumoai.experimental.rfm as rfm

            >>> # Load data frames into memory:
            >>> df1 = pd.DataFrame(...)
            >>> df2 = pd.DataFrame(...)
            >>> df3 = pd.DataFrame(...)

            >>> # Create a graph from a dictionary of data frames:
            >>> graph = rfm.LocalGraph.from_data({
            ...     "table1": df1,
            ...     "table2": df2,
            ...     "table3": df3,
            ... })

            >>> # Inspect table metadata:
            >>> for table in graph.tables.values():
            ...     table.print_metadata()

            >>> # Visualize graph (if graphviz is installed):
            >>> graph.visualize()

        Args:
            df_dict: A dictionary of data frames, where the keys are the names
                of the tables and the values hold table data.
            infer_metadata: Whether to infer metadata for all tables in the
                graph.
            edges: An optional list of :class:`~kumoai.graph.Edge` objects to
                add to the graph. If not provided, edges will be automatically
                inferred from the data.
            verbose: Whether to print verbose output.

        Note:
            This method will automatically infer metadata and links for the
            graph.

        Example:
            >>> # doctest: +SKIP
            >>> import kumoai.experimental.rfm as rfm
            >>> df1 = pd.DataFrame(...)
            >>> df2 = pd.DataFrame(...)
            >>> df3 = pd.DataFrame(...)
            >>> graph = rfm.LocalGraph.from_data(data={
            ...     "table1": df1,
            ...     "table2": df2,
            ...     "table3": df3,
            ... })
            >>> graph.validate()
        """
        tables = [LocalTable(df, name) for name, df in df_dict.items()]

        graph = cls(tables, edges=edges or [])

        if infer_metadata:
            graph.infer_metadata(verbose)

            if edges is None:
                graph.infer_links(verbose)

        return graph

    # Tables ##############################################################

    def has_table(self, name: str) -> bool:
        r"""Returns ``True`` if the graph has a table with name ``name``;
        ``False`` otherwise.
        """
        return name in self.tables

    def table(self, name: str) -> LocalTable:
        r"""Returns the table with name ``name`` in the graph.

        Raises:
            KeyError: If ``name`` is not present in the graph.
        """
        if not self.has_table(name):
            raise KeyError(f"Table '{name}' not found in graph")
        return self.tables[name]

    @property
    def tables(self) -> Dict[str, LocalTable]:
        r"""Returns the dictionary of table objects."""
        return self._tables

    def add_table(self, table: LocalTable) -> Self:
        r"""Adds a table to the graph.

        Args:
            table: The table to add.

        Raises:
            KeyError: If a table with the same name already exists in the
                graph.
        """
        if table.name in self._tables:
            raise KeyError(f"Cannot add table with name '{table.name}' to "
                           f"this graph; table names must be globally unique.")

        self._tables[table.name] = table

        return self

    def remove_table(self, name: str) -> Self:
        r"""Removes a table with ``name`` from the graph.

        Args:
            name: The table to remove.

        Raises:
            KeyError: If no such table is present in the graph.
        """
        if not self.has_table(name):
            raise KeyError(f"Table '{name}' not found in the graph")

        del self._tables[name]

        self._edges = [
            edge for edge in self._edges
            if edge.src_table != name and edge.dst_table != name
        ]

        return self

    @property
    def metadata(self) -> pd.DataFrame:
        r"""Returns a :class:`pandas.DataFrame` object containing metadata
        information about the tables in this graph.

        The returned dataframe has columns ``name``, ``primary_key``,
        ``time_column``, and ``end_time_column``, which provide an aggregate
        view of the properties of the tables of this graph.

        Example:
            >>> # doctest: +SKIP
            >>> import kumoai.experimental.rfm as rfm
            >>> graph = rfm.LocalGraph(tables=...).infer_metadata()
            >>> graph.metadata  # doctest: +SKIP
                name   primary_key  time_column  end_time_column
            0   users      user_id            -                -
        """
        tables = list(self.tables.values())

        return pd.DataFrame({
            'name':
            pd.Series(dtype=str, data=[t.name for t in tables]),
            'primary_key':
            pd.Series(dtype=str, data=[t._primary_key or '-' for t in tables]),
            'time_column':
            pd.Series(dtype=str, data=[t._time_column or '-' for t in tables]),
            'end_time_column':
            pd.Series(
                dtype=str,
                data=[t._end_time_column or '-' for t in tables],
            ),
        })

    def print_metadata(self) -> None:
        r"""Prints the :meth:`~LocalGraph.metadata` of the graph."""
        if in_notebook():
            from IPython.display import Markdown, display
            display(Markdown('### 🗂️ Graph Metadata'))
            df = self.metadata
            try:
                if hasattr(df.style, 'hide'):
                    display(df.style.hide(axis='index'))  # pandas=2
                else:
                    display(df.style.hide_index())  # pandas<1.3
            except ImportError:
                print(df.to_string(index=False))  # missing jinja2
        else:
            print("🗂️ Graph Metadata:")
            print(self.metadata.to_string(index=False))

    def infer_metadata(self, verbose: bool = True) -> Self:
        r"""Infers metadata for all tables in the graph.

        Args:
            verbose: Whether to print verbose output.

        Note:
            For more information, please see
            :meth:`kumoai.experimental.rfm.LocalTable.infer_metadata`.
        """
        for table in self.tables.values():
            table.infer_metadata(verbose=False)

        if verbose:
            self.print_metadata()

        return self

    # Edges ###################################################################

    @property
    def edges(self) -> List[Edge]:
        r"""Returns the edges of the graph."""
        return self._edges

    def print_links(self) -> None:
        r"""Prints the :meth:`~LocalGraph.edges` of the graph."""
        edges = [(edge.dst_table, self[edge.dst_table]._primary_key,
                  edge.src_table, edge.fkey) for edge in self.edges]
        edges = sorted(edges)

        if in_notebook():
            from IPython.display import Markdown, display
            display(Markdown('### 🕸️ Graph Links (FK ↔️ PK)'))
            if len(edges) > 0:
                display(
                    Markdown('\n'.join([
                        f'- `{edge[2]}.{edge[3]}` ↔️ `{edge[0]}.{edge[1]}`'
                        for edge in edges
                    ])))
            else:
                display(Markdown('*No links registered*'))
        else:
            print("🕸️ Graph Links (FK ↔️ PK):")
            if len(edges) > 0:
                print('\n'.join([
                    f'• {edge[2]}.{edge[3]} ↔️ {edge[0]}.{edge[1]}'
                    for edge in edges
                ]))
            else:
                print('No links registered')

    def link(
        self,
        src_table: Union[str, LocalTable],
        fkey: str,
        dst_table: Union[str, LocalTable],
    ) -> Self:
        r"""Links two tables (``src_table`` and ``dst_table``) from the foreign
        key ``fkey`` in the source table to the primary key in the destination
        table.

        The link is treated as bidirectional.

        Args:
            src_table: The name of the source table of the edge. This table
                must have a foreign key with name :obj:`fkey` that links to the
                primary key in the destination table.
            fkey: The name of the foreign key in the source table.
            dst_table: The name of the destination table of the edge. This
                table must have a primary key that links to the source table's
                foreign key.

        Raises:
            ValueError: if the edge is already present in the graph, if the
                source table does not exist in the graph, if the destination
                table does not exist in the graph, if the source key does not
                exist in the source table.
        """
        if isinstance(src_table, LocalTable):
            src_table = src_table.name
        assert isinstance(src_table, str)

        if isinstance(dst_table, LocalTable):
            dst_table = dst_table.name
        assert isinstance(dst_table, str)

        edge = Edge(src_table, fkey, dst_table)

        if edge in self.edges:
            raise ValueError(f"{edge} already exists in the graph")

        if not self.has_table(src_table):
            raise ValueError(f"Source table '{src_table}' does not exist in "
                             f"the graph")

        if not self.has_table(dst_table):
            raise ValueError(f"Destination table '{dst_table}' does not exist "
                             f"in the graph")

        if not self[src_table].has_column(fkey):
            raise ValueError(f"Source key '{fkey}' does not exist as a column "
                             f"in source table '{src_table}'")

        if not Stype.ID.supports_dtype(self[src_table][fkey].dtype):
            raise ValueError(f"Cannot use '{fkey}' in source table "
                             f"'{src_table}' as a foreign key due to its "
                             f"incompatible data type. Foreign keys must have "
                             f"data type 'int', 'float' or 'string' "
                             f"(got '{self[src_table][fkey].dtype}')")

        self._edges.append(edge)

        return self

    def unlink(
        self,
        src_table: Union[str, LocalTable],
        fkey: str,
        dst_table: Union[str, LocalTable],
    ) -> Self:
        r"""Removes an :class:`~kumoai.graph.Edge` from the graph.

        Args:
            src_table: The name of the source table of the edge.
            fkey: The name of the foreign key in the source table.
            dst_table: The name of the destination table of the edge.

        Raises:
            ValueError: if the edge is not present in the graph.
        """
        if isinstance(src_table, LocalTable):
            src_table = src_table.name
        assert isinstance(src_table, str)

        if isinstance(dst_table, LocalTable):
            dst_table = dst_table.name
        assert isinstance(dst_table, str)

        edge = Edge(src_table, fkey, dst_table)

        if edge not in self.edges:
            raise ValueError(f"{edge} is not present in the graph")

        self._edges.remove(edge)

        return self

    def infer_links(self, verbose: bool = True) -> Self:
        r"""Infers links for the tables and adds them as edges to the graph.

        Args:
            verbose: Whether to print verbose output.

        Note:
            This function expects graph edges to be undefined upfront.
        """
        if len(self.edges) > 0:
            warnings.warn("Cannot infer links if graph edges already exist")
            return self

        # A list of primary key candidates (+score) for every column:
        candidate_dict: dict[
            tuple[str, str],
            list[tuple[str, float]],
        ] = defaultdict(list)

        for dst_table in self.tables.values():
            dst_key = dst_table.primary_key

            if dst_key is None:
                continue

            assert dst_key.dtype is not None
            dst_number = dst_key.dtype.is_int() or dst_key.dtype.is_float()
            dst_string = dst_key.dtype.is_string()

            dst_table_name = dst_table.name.lower()
            dst_key_name = dst_key.name.lower()

            for src_table in self.tables.values():
                src_table_name = src_table.name.lower()

                for src_key in src_table.columns:
                    if src_key == src_table.primary_key:
                        continue  # Cannot link to primary key.

                    src_number = (src_key.dtype.is_int()
                                  or src_key.dtype.is_float())
                    src_string = src_key.dtype.is_string()

                    if src_number != dst_number or src_string != dst_string:
                        continue  # Non-compatible data types.

                    src_key_name = src_key.name.lower()

                    score = 0.0

                    # Name similarity:
                    if src_key_name == dst_key_name:
                        score += 7.0
                    elif (dst_key_name != 'id'
                          and src_key_name.endswith(dst_key_name)):
                        score += 4.0
                    elif src_key_name.endswith(  # e.g., user.id -> user_id
                            f'{dst_table_name}_{dst_key_name}'):
                        score += 4.0
                    elif src_key_name.endswith(  # e.g., user.id -> userid
                            f'{dst_table_name}{dst_key_name}'):
                        score += 4.0
                    elif (dst_table_name.endswith('s') and
                          src_key_name.endswith(  # e.g., users.id -> user_id
                              f'{dst_table_name[:-1]}_{dst_key_name}')):
                        score += 4.0
                    elif (dst_table_name.endswith('s') and
                          src_key_name.endswith(  # e.g., users.id -> userid
                              f'{dst_table_name[:-1]}{dst_key_name}')):
                        score += 4.0
                    elif src_key_name.endswith(dst_table_name):
                        score += 4.0  # e.g., users -> users
                    elif (dst_table_name.endswith('s')  # e.g., users -> user
                          and src_key_name.endswith(dst_table_name[:-1])):
                        score += 4.0
                    elif ((src_key_name == 'parentid'
                           or src_key_name == 'parent_id')
                          and src_table_name == dst_table_name):
                        score += 2.0

                    # `rel-bench` hard-coding :(
                    elif (src_table.name == 'posts'
                          and src_key.name == 'AcceptedAnswerId'
                          and dst_table.name == 'posts'):
                        score += 2.0
                    elif (src_table.name == 'user_friends'
                          and src_key.name == 'friend'
                          and dst_table.name == 'users'):
                        score += 3.0

                    # For non-exact matching, at least one additional
                    # requirement needs to be met.

                    # Exact data type compatibility:
                    if src_key.stype == Stype.ID:
                        score += 2.0

                    if src_key.dtype == dst_key.dtype:
                        score += 1.0

                    # Cardinality ratio:
                    if len(src_table._data) > len(dst_table._data):
                        score += 1.0

                    if score < 5.0:
                        continue

                    candidate_dict[(
                        src_table.name,
                        src_key.name,
                    )].append((
                        dst_table.name,
                        score,
                    ))

        for (src_table_name, src_key_name), scores in candidate_dict.items():
            scores.sort(key=lambda x: x[-1], reverse=True)

            if len(scores) > 1 and scores[0][1] == scores[1][1]:
                continue  # Cannot uniquely infer link.

            dst_table_name = scores[0][0]
            self.link(src_table_name, src_key_name, dst_table_name)

        if verbose:
            self.print_links()

        return self

    # Metadata ################################################################

    def validate(self) -> Self:
        r"""Validates the graph to ensure that all relevant metadata is
        specified for its tables and edges.

        Concretely, validation ensures that edges properly link foreign keys to
        primary keys between valid tables.
        It additionally ensures that primary and foreign keys between tables
        in an :class:`~kumoai.graph.Edge` are of the same data type.

        Raises:
            ValueError: if validation fails.
        """
        if len(self.tables) == 0:
            raise ValueError("At least one table needs to be added to the "
                             "graph")

        for edge in self.edges:
            src_table, fkey, dst_table = edge

            src_key = self[src_table][fkey]
            dst_key = self[dst_table].primary_key

            # Check that the destination table defines a primary key:
            if dst_key is None:
                raise ValueError(f"Edge {edge} is invalid since table "
                                 f"'{dst_table}' does not have a primary key. "
                                 f"Add either a primary key or remove the "
                                 f"link before proceeding.")

            # Ensure that foreign key is not a primary key:
            src_pkey = self[src_table].primary_key
            if src_pkey is not None and src_pkey.name == fkey:
                raise ValueError(f"Cannot treat the primary key of table "
                                 f"'{src_table}' as a foreign key. Remove "
                                 f"either the primary key or the link before "
                                 f"before proceeding.")

            # Check that fkey/pkey have valid and consistent data types:
            assert src_key.dtype is not None
            src_number = src_key.dtype.is_int() or src_key.dtype.is_float()
            src_string = src_key.dtype.is_string()
            assert dst_key.dtype is not None
            dst_number = dst_key.dtype.is_int() or dst_key.dtype.is_float()
            dst_string = dst_key.dtype.is_string()

            if not src_number and not src_string:
                raise ValueError(f"{edge} is invalid as foreign key must be a "
                                 f"number or string (got '{src_key.dtype}'")

            if src_number != dst_number or src_string != dst_string:
                raise ValueError(f"{edge} is invalid as foreign key "
                                 f"'{fkey}' and primary key '{dst_key.name}' "
                                 f"have incompatible data types (got "
                                 f"fkey.dtype '{src_key.dtype}' and "
                                 f"pkey.dtype '{dst_key.dtype}')")

        return self

    # Visualization ###########################################################

    def visualize(
        self,
        path: Optional[Union[str, io.BytesIO]] = None,
        show_columns: bool = True,
    ) -> 'graphviz.Graph':
        r"""Visualizes the tables and edges in this graph using the
        :class:`graphviz` library.

        Args:
            path: A path to write the produced image to. If ``None``, the image
                will not be written to disk.
            show_columns: Whether to show all columns of every table in the
                graph. If ``False``, will only show the primary key, foreign
                key(s), and time column of each table.

        Returns:
            A ``graphviz.Graph`` instance representing the visualized graph.
        """
        def has_graphviz_executables() -> bool:
            import graphviz
            try:
                graphviz.Digraph().pipe()
            except graphviz.backend.ExecutableNotFound:
                return False

            return True

        # Check basic dependency:
        if not find_spec('graphviz'):
            raise ModuleNotFoundError("The 'graphviz' package is required for "
                                      "visualization")
        elif not has_graphviz_executables():
            raise RuntimeError("Could not visualize graph as 'graphviz' "
                               "executables are not installed. These "
                               "dependencies are required in addition to the "
                               "'graphviz' Python package. Please install "
                               "them as described at "
                               "https://graphviz.org/download/.")
        else:
            import graphviz

        format: Optional[str] = None
        if isinstance(path, str):
            format = path.split('.')[-1]
        elif isinstance(path, io.BytesIO):
            format = 'svg'
        graph = graphviz.Graph(format=format)

        def left_align(keys: List[str]) -> str:
            if len(keys) == 0:
                return ""
            return '\\l'.join(keys) + '\\l'

        fkeys_dict: Dict[str, List[str]] = defaultdict(list)
        for src_table_name, fkey_name, _ in self.edges:
            fkeys_dict[src_table_name].append(fkey_name)

        for table_name, table in self.tables.items():
            keys = []
            if primary_key := table.primary_key:
                keys += [f'{primary_key.name}: PK ({primary_key.dtype})']
            keys += [
                f'{fkey_name}: FK ({self[table_name][fkey_name].dtype})'
                for fkey_name in fkeys_dict[table_name]
            ]
            if time_column := table.time_column:
                keys += [f'{time_column.name}: Time ({time_column.dtype})']
            if end_time_column := table.end_time_column:
                keys += [
                    f'{end_time_column.name}: '
                    f'End Time ({end_time_column.dtype})'
                ]
            key_repr = left_align(keys)

            columns = []
            if show_columns:
                columns += [
                    f'{column.name}: {column.stype} ({column.dtype})'
                    for column in table.columns
                    if column.name not in fkeys_dict[table_name] and
                    column.name != table._primary_key and column.name != table.
                    _time_column and column.name != table._end_time_column
                ]
            column_repr = left_align(columns)

            if len(keys) > 0 and len(columns) > 0:
                label = f'{{{table_name}|{key_repr}|{column_repr}}}'
            elif len(keys) > 0:
                label = f'{{{table_name}|{key_repr}}}'
            elif len(columns) > 0:
                label = f'{{{table_name}|{column_repr}}}'
            else:
                label = f'{{{table_name}}}'

            graph.node(table_name, shape='record', label=label)

        for src_table_name, fkey_name, dst_table_name in self.edges:
            if self[dst_table_name]._primary_key is None:
                continue  # Invalid edge.

            pkey_name = self[dst_table_name]._primary_key

            if fkey_name != pkey_name:
                label = f' {fkey_name}\n< >\n{pkey_name} '
            else:
                label = f' {fkey_name} '

            graph.edge(
                src_table_name,
                dst_table_name,
                label=label,
                headlabel='1',
                taillabel='*',
                minlen='2',
                fontsize='11pt',
                labeldistance='1.5',
            )

        if isinstance(path, str):
            path = '.'.join(path.split('.')[:-1])
            graph.render(path, cleanup=True)
        elif isinstance(path, io.BytesIO):
            path.write(graph.pipe())
        elif in_notebook():
            from IPython.display import display
            display(graph)
        else:
            try:
                stderr_buffer = io.StringIO()
                with contextlib.redirect_stderr(stderr_buffer):
                    graph.view(cleanup=True)
                if stderr_buffer.getvalue():
                    warnings.warn("Could not visualize graph since your "
                                  "system does not know how to open or "
                                  "display PDF files from the command line. "
                                  "Please specify 'visualize(path=...)' and "
                                  "open the generated file yourself.")
            except Exception as e:
                warnings.warn(f"Could not visualize graph due to an "
                              f"unexpected error in 'graphviz'. Error: {e}")

        return graph

    # Helpers #################################################################

    def _to_api_graph_definition(self) -> GraphDefinition:
        tables: Dict[str, TableDefinition] = {}
        col_groups: List[ColumnKeyGroup] = []
        for table_name, table in self.tables.items():
            tables[table_name] = table._to_api_table_definition()
            if table.primary_key is None:
                continue
            keys = [ColumnKey(table_name, table.primary_key.name)]
            for edge in self.edges:
                if edge.dst_table == table_name:
                    keys.append(ColumnKey(edge.src_table, edge.fkey))
            keys = sorted(
                list(set(keys)),
                key=lambda x: f'{x.table_name}.{x.col_name}',
            )
            if len(keys) > 1:
                col_groups.append(ColumnKeyGroup(keys))
        return GraphDefinition(tables, col_groups)

    # Class properties ########################################################

    def __hash__(self) -> int:
        return hash((tuple(self.edges), tuple(sorted(self.tables.keys()))))

    def __contains__(self, name: str) -> bool:
        return self.has_table(name)

    def __getitem__(self, name: str) -> LocalTable:
        return self.table(name)

    def __delitem__(self, name: str) -> None:
        self.remove_table(name)

    def __repr__(self) -> str:
        tables = '\n'.join(f'    {table},' for table in self.tables)
        tables = f'[\n{tables}\n  ]' if len(tables) > 0 else '[]'
        edges = '\n'.join(
            f'    {edge.src_table}.{edge.fkey}'
            f' ⇔ {edge.dst_table}.{self[edge.dst_table]._primary_key},'
            for edge in self.edges)
        edges = f'[\n{edges}\n  ]' if len(edges) > 0 else '[]'
        return (f'{self.__class__.__name__}(\n'
                f'  tables={tables},\n'
                f'  edges={edges},\n'
                f')')
