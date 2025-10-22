# Copyright 1999-2025 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import pandas as pd

from ...serialization.serializables import BoolField, StringField
from ..operators import DataFrameOperatorMixin
from .core import DataFrameSortOperator


class DataFrameRank(DataFrameSortOperator, DataFrameOperatorMixin):
    method = StringField("method", default=None)
    numeric_only = BoolField("numeric_only", default=None)
    pct = BoolField("pct", default=False)

    @property
    def na_option(self):
        return self.na_position

    def __call__(self, df_obj):
        params = df_obj.params
        if df_obj.ndim == 2:  # dataframe
            if self.numeric_only:
                sel_df = df_obj.select_dtypes(include=[np.number])
                cols = sel_df.dtypes.index
            else:
                cols = df_obj.dtypes.index
            params["dtypes"] = pd.Series([np.dtype(float)] * len(cols), index=cols)
            return self.new_dataframe([df_obj], **params)
        else:
            params["dtypes"] = np.dtype(float)
            return self.new_series([df_obj], **params)


def rank(
    df,
    axis=0,
    method="average",
    numeric_only=False,
    na_option="keep",
    ascending=True,
    pct=False,
):
    """
    Compute numerical data ranks (1 through n) along axis.

    By default, equal values are assigned a rank that is the average of the
    ranks of those values.

    Parameters
    ----------
    axis : {0 or 'index', 1 or 'columns'}, default 0
        Index to direct ranking.
    method : {'average', 'min', 'max', 'first', 'dense'}, default 'average'
        How to rank the group of records that have the same value (i.e. ties):

        * average: average rank of the group
        * min: lowest rank in the group
        * max: highest rank in the group
        * first: ranks assigned in order they appear in the array
        * dense: like 'min', but rank always increases by 1 between groups.

    numeric_only : bool, optional
        For DataFrame objects, rank only numeric columns if set to True.
    na_option : {'keep', 'top', 'bottom'}, default 'keep'
        How to rank NaN values:

        * keep: assign NaN rank to NaN values
        * top: assign lowest rank to NaN values
        * bottom: assign highest rank to NaN values

    ascending : bool, default True
        Whether or not the elements should be ranked in ascending order.
    pct : bool, default False
        Whether or not to display the returned rankings in percentile
        form.

    Returns
    -------
    same type as caller
        Return a Series or DataFrame with data ranks as values.

    See Also
    --------
    core.groupby.GroupBy.rank : Rank of values within each group.

    Examples
    --------
    >>> import maxframe.tensor as mt
    >>> import maxframe.dataframe as md
    >>> df = md.DataFrame(data={'Animal': ['cat', 'penguin', 'dog',
    ...                                    'spider', 'snake'],
    ...                         'Number_legs': [4, 2, 4, 8, mt.nan]})
    >>> df.execute()
        Animal  Number_legs
    0      cat          4.0
    1  penguin          2.0
    2      dog          4.0
    3   spider          8.0
    4    snake          NaN

    The following example shows how the method behaves with the above
    parameters:

    * default_rank: this is the default behaviour obtained without using
      any parameter.
    * max_rank: setting ``method = 'max'`` the records that have the
      same values are ranked using the highest rank (e.g.: since 'cat'
      and 'dog' are both in the 2nd and 3rd position, rank 3 is assigned.)
    * NA_bottom: choosing ``na_option = 'bottom'``, if there are records
      with NaN values they are placed at the bottom of the ranking.
    * pct_rank: when setting ``pct = True``, the ranking is expressed as
      percentile rank.

    >>> df['default_rank'] = df['Number_legs'].rank()
    >>> df['max_rank'] = df['Number_legs'].rank(method='max')
    >>> df['NA_bottom'] = df['Number_legs'].rank(na_option='bottom')
    >>> df['pct_rank'] = df['Number_legs'].rank(pct=True)
    >>> df.execute()
        Animal  Number_legs  default_rank  max_rank  NA_bottom  pct_rank
    0      cat          4.0           2.5       3.0        2.5     0.625
    1  penguin          2.0           1.0       1.0        1.0     0.250
    2      dog          4.0           2.5       3.0        2.5     0.625
    3   spider          8.0           4.0       4.0        4.0     1.000
    4    snake          NaN           NaN       NaN        5.0       NaN
    """
    op = DataFrameRank(
        axis=axis,
        method=method,
        numeric_only=numeric_only,
        na_position=na_option,
        ascending=ascending,
        pct=pct,
    )
    return op(df)
