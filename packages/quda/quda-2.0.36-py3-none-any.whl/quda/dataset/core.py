# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/8/27 10:47
# Description:

from __future__ import annotations

import lidb
from functools import partial
import polars.selectors as cs
import polars as pl
from typing import Callable
import logair
import ygo

def complete_data(fn, date, save_path,):
    logger = logair.get_logger("quda.dataset")
    try:
        data = fn(date=date)
        if data is None:
            # 保存数据的逻辑在fn中实现了
            return
        # 剔除以 `_` 开头的列
        data = data.filter(date=date).select(~cs.starts_with("_"))
        if not isinstance(data, (pl.DataFrame, pl.LazyFrame)):
            logger.error("Result of dataset.fn must be polars.DataFrame or polars.LazyFrame.")
            return
        if isinstance(data, pl.LazyFrame):
            data = data.collect()
        lidb.put(data, save_path, abs_path=True, partitions=["asset", "date"])
    except Exception as e:
        logger.error(f"Error when complete data for {date}")
        logger.warning(e)

class Dataset:

    def __init__(self,
                 fn: Callable[..., pl.DataFrame],
                 tb: str,
                 partitions: list[str] = None):
        """

        Parameters
        ----------
        fn: str
            数据集计算函数
        tb: str
            数据集保存表格
        partitions: list[str]
            分区
        """
        self.fn = fn
        self.fn_params_sig = ygo.fn_signature_params(fn)
        if partitions is not None:
            partitions = [k for k in partitions if (k != "date" and k != "asset")]
            partitions = [*partitions, "asset", "date"]
        else:
            partitions = ["asset", "date"]
        self.partitions = partitions
        self._type_asset = "asset" in self.fn_params_sig

        self.tb = tb
        self.save_path = lidb.tb_path(tb)
        fn_params = ygo.fn_params(self.fn)
        self.fn_params = {k: v for (k, v) in fn_params}
        self.constraints = dict()
        for k in self.partitions[:-2]:
            if k in self.fn_params:
                v = self.fn_params[k]
                self.constraints[k] = v
                self.save_path = self.save_path / f"{k}={v}"

    def is_empty(self, path) -> bool:
        return not any(path.rglob("*.parquet"))

    def __call__(self, *fn_args, **fn_kwargs):
        # self.fn =
        fn = partial(self.fn, *fn_args, **fn_kwargs)
        ds = Dataset(fn=fn, tb=self.tb, partitions=self.partitions)
        return ds

    def get_value(self, date, **constraints):
        """
        取值
        Parameters
        ----------
        date: str
            取值日期
        constraints: dict
            取值的过滤条件

        Returns
        -------

        """
        _constraints = {k: v for k, v in constraints.items() if k in self.partitions}
        _limits = {k: v for k, v in constraints.items() if k not in self.partitions}
        search_path = self.save_path
        for k, v in _constraints.items():
            search_path = search_path / f"{k}={v}"

        if not self.is_empty(search_path):
            lf = lidb.scan(search_path, abs_path=True).filter(date=date, **_limits)
            data = lf.collect()
            if not data.is_empty():
                return data
        fn = self.fn
        save_path = self.save_path

        if self._type_asset:
            if "asset" in _constraints:
                fn = ygo.delay(self.fn)(asset=_constraints["asset"])
        if len(self.constraints) < len(self.partitions) - 2:
            # 如果分区指定的字段没有在Dataset定义中指定，需要在get_value中指定
            params = dict()
            for k in self.partitions[:-2]:
                if k not in self.constraints:
                    v = constraints[k]
                    params[k] = v
                    save_path =save_path / f"{k}={v}"
            fn = ygo.delay(self.fn)(**params)
        complete_data(fn, date, save_path, )

        return lidb.scan(search_path, abs_path=True).filter(date=date, **_limits).collect()

    def get_history(self, dateList: list[str], **constraints):
        _constraints = {k: v for k, v in constraints.items() if k in self.partitions}
        search_path = self.save_path
        for k, v in _constraints.items():
            search_path = search_path / f"{k}={v}"
        if self.is_empty(search_path):
            # 需要补全全部数据
            missing_dates = dateList
        else:
            if not self._type_asset:
                _search_path = self.save_path
                for k, v in _constraints.items():
                    if k != "asset":
                        _search_path = _search_path / f"{k}={v}"
                    else:
                        _search_path = _search_path / "asset=000001"
                hive_info = lidb.parse_hive_partition_structure(_search_path)
            else:
                hive_info = lidb.parse_hive_partition_structure(search_path)
            exist_dates = hive_info["date"].to_list()
            missing_dates = set(dateList).difference(set(exist_dates))
            missing_dates = sorted(list(missing_dates))
        if missing_dates:
            fn = self.fn
            save_path = self.save_path

            if self._type_asset:
                if "asset" in _constraints:
                    fn = ygo.delay(self.fn)(asset=_constraints["asset"])

            if len(self.constraints) < len(self.partitions) - 2:
                # 如果分区指定的字段没有在Dataset定义中指定，需要在get_value中指定
                params = dict()
                for k in self.partitions[:-2]:
                    if k not in self.constraints:
                        v = constraints[k]
                        params[k] = v
                        save_path =save_path / f"{k}={v}"
                fn = ygo.delay(self.fn)(**params)

            with ygo.pool(n_jobs=5, backend="loky") as go:
                for date in missing_dates:
                    go.submit(complete_data, job_name=f"completing {self.save_path.relative_to(lidb.DB_PATH)}")(
                        fn=fn,
                        date=date,
                        save_path=save_path)
                go.do()
        data = lidb.scan(search_path, abs_path=True).filter(pl.col("date").is_in(dateList), **constraints)
        return data.sort("date").collect()