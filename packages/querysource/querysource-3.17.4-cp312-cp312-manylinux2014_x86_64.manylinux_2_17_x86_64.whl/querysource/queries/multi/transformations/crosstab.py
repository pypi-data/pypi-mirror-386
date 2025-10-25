from typing import Union
import pandas as pd
from ....exceptions import (
    DriverError,
    QueryException
)
from .abstract import AbstractTransform


class crosstab(AbstractTransform):
    def __init__(self, data: Union[dict, pd.DataFrame], **kwargs) -> None:
        self.reset_index: bool = kwargs.pop('reset_index', True)
        self._type = kwargs.pop('type', 'crosstab')
        super(crosstab, self).__init__(data, **kwargs)
        if not hasattr(self, 'index'):
            raise DriverError(
                "Crosstab Transform: Missing Index on definition"
            )
        if not hasattr(self, 'columns'):
            raise DriverError(
                "Crosstab Transform: Missing Columns on definition"
            )

    async def run(self):
        await self.start()
        args = {
            ## "normalize": 'columns',
            ## "dropna": False
        }
        if not hasattr(self, 'values'):
            self.values = None
        if hasattr(self, 'aggregate'):
            args['aggfunc'] = self.aggregate
            args['values'] = [self.data[i] for i in self.values]  # pylint: disable=E1133
        if hasattr(self, 'totals'):
            tname = self.totals['name']
            args['margins'] = True
            args['margins_name'] = tname
        try:
            if self._type == 'crosstab':
                df = pd.crosstab(
                    index=[self.data[i] for i in self.index],
                    columns=[self.data[i] for i in self.columns],
                    **args
                )
            elif self._type == 'pivot':
                args = {}
                if hasattr(self, 'aggregate'):
                    aggfunc = self.aggregate
                else:
                    aggfunc = 'first'
                df = pd.pivot_table(
                    self.data,
                    index=self.index,
                    columns=self.columns,
                    aggfunc=aggfunc,
                    values=self.values,
                    **args
                )
            if self.reset_index is True:
                df.reset_index(inplace=True)
            self.colum_info(df)
            return df
        except (ValueError, KeyError) as err:
            raise QueryException(
                f'Crosstab Error: {err!s}'
            ) from err
        except Exception as err:
            raise QueryException(
                f"Unknown error {err!s}"
            ) from err
