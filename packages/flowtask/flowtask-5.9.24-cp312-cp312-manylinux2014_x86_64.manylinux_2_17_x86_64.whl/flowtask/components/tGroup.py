import asyncio
from collections.abc import Callable
import pandas as pd
import numpy as np
from ..exceptions import ComponentError, ConfigError
from .flow import FlowComponent


class tGroup(FlowComponent):
    """
    tGroup

        Overview

            The tGroup class is a component for performing a group-by operation on a DataFrame using specified columns.
            It returns unique combinations of the specified group-by columns, allowing data aggregation and summarization.

        .. table:: Properties
        :widths: auto

            +----------------+----------+-----------+---------------------------------------------------------------+
            | Name           | Required | Summary                                                                   |
            +----------------+----------+-----------+---------------------------------------------------------------+
            | group_by       |   Yes    | List of columns to group by.                                              |
            +----------------+----------+-----------+---------------------------------------------------------------+
            | columns        |   No     | List of columns to retain in the result DataFrame. If None,               |
            |                |          | all columns in `group_by` are returned.                                   |
            +----------------+----------+-----------+---------------------------------------------------------------+
            | agg            |   No     | List of aggregation functions to apply to the grouped data.               |
            |                |          | Each aggregation should be a dictionary with the column name,             |
            |                | aggregation function, and an optional alias.                                         |
            +----------------+----------+-----------+---------------------------------------------------------------+
        Returns

            This component returns a DataFrame with unique rows based on the specified `group_by` columns. If `columns`
            is defined, only those columns are included in the result. The component provides debugging information on
            column data types if enabled, and any errors during grouping are logged and raised as exceptions.

        Example:

        ```
        - tGroup:
            group_by:
            - store_id
            - formatted_address
            - state_code
            - latitude
            - longitude
            - store_name
            - city
        ```

        - Aggregation Example:
        ```
        - tGroup:
            group_by:
            - store_id
            - formatted_address
            - state_code
            - latitude
            - longitude
            - store_name
            - city
            agg:
                - store_id: distinct
                alias: unique_store_ids
                - latitude: mean
                alias: avg_latitude
                - longitude: mean
                alias: avg_longitude
                - state_code: count
        ```
    """  # noqa

    condition = ""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        """Init Method."""
        self._columns: list = kwargs.pop("group_by", None)
        self.aggregations: list = kwargs.pop("agg", [])
        if not self._columns:
            raise ConfigError(
                "tGroup require a list of Columns for Group By => **group_by**"
            )
        if not isinstance(self._columns, list):
            raise ConfigError("Group By must be a list of columns")
        if not all(isinstance(col, str) for col in self._columns):
            raise ConfigError("All group_by columns must be strings")
        super(tGroup, self).__init__(loop=loop, job=job, stat=stat, **kwargs)

    async def start(self, **kwargs):
        # Si lo que llega no es un DataFrame de Pandas se cancela la tarea
        if self.previous:
            self.data = self.input
        else:
            raise ComponentError("Data Not Found")
        if not isinstance(self.data, pd.DataFrame):
            raise ComponentError("Incompatible Pandas Dataframe")
        return True

    async def close(self):
        pass

    async def run(self):
        self._result = None
        try:
            hashable_columns = [
                col for col in self._columns
                if not self.data[col].apply(lambda x: isinstance(x, list)).any()
            ]
            if self.aggregations:
                agg_dict = {}
                for agg in self.aggregations:
                    agg = agg.copy()
                    # agg is a dictionary as:
                    # - store_id: distinct
                    #   alias: unique_store_ids
                    # get key, value of first element on dictionary:
                    if not isinstance(agg, dict):
                        raise ConfigError(
                            f"Aggregation must be a dict with column and agg function, got {agg} instead"
                        )
                    col, func = next(iter(agg.items()))
                    fn = func.lower()
                    agg.pop(col)
                    alias = agg.pop("alias", f"{col}_{fn}")
                    args = agg
                    if fn == "count":
                        agg_dict[alias] = (col, 'count')
                    elif fn == "sum":
                        agg_dict[alias] = (col, 'sum', args)
                    elif fn == "mean":
                        agg_dict[alias] = (col, 'mean', args)
                    elif fn == "median":
                        agg_dict[alias] = (col, 'median', args)
                    elif fn == "min":
                        agg_dict[alias] = (col, 'min', args)
                    elif fn == "max":
                        agg_dict[alias] = (col, 'max', args)
                    elif fn == "std":
                        agg_dict[alias] = (col, 'std', args)
                    elif fn == "var":
                        agg_dict[alias] = (col, 'var', args)
                    elif fn == "first":
                        agg_dict[alias] = (col, 'first', args)
                    elif fn == "last":
                        agg_dict[alias] = (col, 'last', args)
                    elif fn == "unique":
                        agg_dict[alias] = (col, 'unique', args)
                    elif fn == "nunique":
                        agg_dict[alias] = (col, 'nunique', args)
                    elif fn == "mode":
                        agg_dict[alias] = (col, 'mode', args)
                    elif fn == "quantile":
                        agg_dict[alias] = (col, 'quantile', args)
                    elif fn == "skew":
                        agg_dict[alias] = (col, 'skew', args)
                    elif fn == "kurt":
                        agg_dict[alias] = (col, 'kurt', args)
                    elif fn == "mad":
                        agg_dict[alias] = (col, 'mad', args)
                    elif fn == "sem":
                        agg_dict[alias] = (col, 'sem', args)
                    elif fn == "pct_change":
                        agg_dict[alias] = (col, 'pct_change', args)
                    elif fn == "diff":
                        agg_dict[alias] = (col, 'diff', args)
                    elif fn == "cumsum":
                        agg_dict[alias] = (col, 'cumsum', args)
                    elif fn == "cumprod":
                        agg_dict[alias] = (col, 'cumprod', args)
                    elif fn == "cummax":
                        agg_dict[alias] = (col, 'cummax', args)
                    elif fn == "cummin":
                        agg_dict[alias] = (col, 'cummin', args)
                    elif fn == "distinct":
                        agg_dict[alias] = (col, pd.Series.nunique)
                    elif fn == 'count_nulls':
                        agg_dict[alias] = (col, lambda x: x.isnull().sum())
                    elif fn == 'count_not_nulls':
                        agg_dict[alias] = (col, lambda x: x.notnull().sum())
                    elif fn == 'count_unique':
                        agg_dict[alias] = (col, lambda x: x.nunique())
                    elif fn == 'count_distinct':
                        agg_dict[alias] = (col, lambda x: x.unique().size)
                    elif fn == 'count_zeros':
                        agg_dict[alias] = (col, lambda x: (x == 0).sum())
                    elif hasattr(np, fn):
                        agg_dict[col] = (col, fn, args)
                    elif fn == 'apply':
                        if 'function' not in agg:
                            raise ConfigError(
                                "Function must be specified for apply"
                            )
                        func = agg['function']
                        if callable(func):
                            agg_dict[alias] = (col, func)
                        else:
                            raise ConfigError(
                                f"Function {func} must be callable"
                            )
                    else:
                        raise ConfigError(f"Unsupported aggregation function: {fn}")
                # Perform group by with aggregation
                try:
                    df = self.data.groupby(hashable_columns).agg(**agg_dict).reset_index()
                except KeyError as err:
                    raise ConfigError(
                        f"Invalid columns for aggregation: {err}"
                    ) from err
                except Exception as err:
                    raise ComponentError(
                        f"Error during aggregation: {err}"
                    ) from err
            else:
                # Perform group by without aggregation, avoiding unhashable types
                # Get unique elements
                df = self.data[hashable_columns].drop_duplicates().reset_index(drop=True)
        except Exception as err:
            raise ComponentError(f"Generic Error on Data: error: {err}") from err
        if hasattr(self, "columns"):
            # returning only a subset of data
            df = df[self.columns]
        if self._debug is True:
            print("::: Printing Column Information === ")
            print("Grouped: ", df)
            for column, t in df.dtypes.items():
                print(column, "->", t, "->", df[column].iloc[0])
        self._result = df
        return self._result
