#  Copyright (c) 2025 by EOPF Sample Service team and contributors
#  Permissions are hereby granted under the terms of the Apache 2.0 License:
#  https://opensource.org/license/apache-2-0.

from unittest import TestCase

import xarray as xr

from integration.helpers import assert_dataset_is_chunked
from xarray_eopf.utils import timeit

ol1efr_url = (
    "https://objects.eodc.eu/e05ab01a9d56408d82ac32d69a5aae2a:202508-s03olcefr/19/"
    "products/cpm_v256/S3B_OL_1_EFR____20250819T074058_20250819T074358_"
    "20250819T092155_0179_110_106_3420_ESA_O_NR_004.zarr"
)

ol1err_url = (
    "https://objects.eodc.eu/e05ab01a9d56408d82ac32d69a5aae2a:202510-s03olcerr-global/"
    "19/products/cpm_v256/S3A_OL_1_ERR____20251019T145533_20251019T153950_"
    "20251019T165332_2657_131_353______PS1_O_NR_004.zarr"
)

ol2lfr_url = (
    "https://objects.eodc.eu/e05ab01a9d56408d82ac32d69a5aae2a:202510-s03olclfr-"
    "global/15/products/cpm_v256/S3A_OL_2_LFR____20251015T050206_20251015T050506_"
    "20251015T070316_0179_131_290_2340_PS1_O_NR_003.zarr"
)
sl1rbt_url = (
    "https://objects.eodc.eu/e05ab01a9d56408d82ac32d69a5aae2a:202510-s03slsrbt-global/"
    "16/products/cpm_v256/S3B_SL_1_RBT____20251016T072510_20251016T072810_"
    "20251016T092049_0179_112_163_2700_ESA_O_NR_004.zarr"
)
sl2lst_url = (
    "https://objects.eodc.eu/e05ab01a9d56408d82ac32d69a5aae2a:202510-s03slslst-eu/16/"
    "products/cpm_v256/S3B_SL_2_LST____20251016T215803_20251016T220103_"
    "20251017T004323_0179_112_172_0540_ESA_O_NR_004.zarr"
)

allowed_open_time = 5  # seconds


class Sentinel3NativeTest(TestCase):
    def test_open_datatree_sen3_ol1efr(self):
        self._test_open_datatree_sen3(
            ol1efr_url, 11, "measurements", {"columns": 4865, "rows": 4091}, 21
        )

    def test_open_dataset_sen3_ol1efr(self):
        self._test_open_dataset_sen3(
            ol1efr_url,
            "measurements_oa21_radiance",
            {"measurements_columns": 4865, "measurements_rows": 4091},
            63,
        )

    def test_open_dataset_sen3_ol1efr_subgroup(self):
        self._test_open_dataset_sen3_subgroup(
            ol1efr_url,
            "oa21_radiance",
            "measurements",
            {"columns": 4865, "rows": 4091},
            21,
        )

    def test_open_datatree_sen3_ol1err(self):
        self._test_open_datatree_sen3(
            ol1err_url, 8, "measurements", {"columns": 1217, "rows": 15098}, 21
        )

    def test_open_dataset_sen3_ol1err(self):
        self._test_open_dataset_sen3(
            ol1err_url,
            "measurements_oa21_radiance",
            {"measurements_columns": 1217, "measurements_rows": 15098},
            59,
        )

    def test_open_dataset_sen3_ol1err_subgroup(self):
        self._test_open_dataset_sen3_subgroup(
            ol1err_url,
            "oa21_radiance",
            "measurements",
            {"columns": 1217, "rows": 15098},
            21,
        )

    def test_open_datatree_sen3_ol2lfr(self):
        self._test_open_datatree_sen3(
            ol2lfr_url, 9, "measurements", {"columns": 4865, "rows": 4091}, 5
        )

    def test_open_dataset_sen3_ol2lfr(self):
        self._test_open_dataset_sen3(
            ol2lfr_url,
            "measurements_otci",
            {"measurements_columns": 4865, "measurements_rows": 4091},
            28,
        )

    def test_open_dataset_sen3_ol2lfr_subgroup(self):
        self._test_open_dataset_sen3_subgroup(
            ol2lfr_url, "otci", "measurements", {"columns": 4865, "rows": 4091}, 5
        )

    def test_open_datatree_sen3_sl1rbt(self):
        self._test_open_datatree_sen3(
            sl1rbt_url,
            97,
            "measurements/bnadir",
            {"columns": 3000, "rows": 2400},
            5,
        )

    def test_open_dataset_sen3_sl1rbt(self):
        self._test_open_dataset_sen3(
            sl1rbt_url,
            "measurements_bnadir_s4_radiance_bn",
            {"measurements_bnadir_columns": 3000, "measurements_bnadir_rows": 2400},
            739,
        )

    def test_open_dataset_sen3_sl1rbt_subgroup(self):
        self._test_open_dataset_sen3_subgroup(
            sl1rbt_url,
            "s4_radiance_bn",
            "measurements/bnadir",
            {"columns": 3000, "rows": 2400},
            5,
        )

    def test_open_datatree_sen3_sl2lst(self):
        self._test_open_datatree_sen3(
            sl2lst_url,
            13,
            "measurements",
            {"columns": 1500, "rows": 1200},
            1,
        )

    def test_open_dataset_sen3_sl2lst(self):
        self._test_open_dataset_sen3(
            sl2lst_url,
            "measurements_lst",
            {"measurements_columns": 1500, "measurements_rows": 1200},
            58,
        )

    def test_open_dataset_sen3_sl2lst_subgroup(self):
        self._test_open_dataset_sen3_subgroup(
            sl2lst_url,
            "lst",
            "measurements",
            {"columns": 1500, "rows": 1200},
            1,
        )

    def _test_open_datatree_sen3(
        self,
        url: str,
        num_groups: int,
        subgroup: str,
        ds_sizes: dict,
        num_data_vars: int,
    ):
        with timeit("open " + url) as result:
            # noinspection PyTypeChecker
            dt = xr.open_datatree(url, engine="eopf-zarr", op_mode="native", chunks={})
        self.assertTrue(result.time_delta < allowed_open_time)
        self.assertEqual(num_groups, len(dt.groups))
        self.assertIn(
            f"/{subgroup}",
            dt.groups,
        )
        ds = dt[subgroup].ds
        self.assertEqual(ds_sizes, ds.sizes)
        self.assertEqual(num_data_vars, len(ds.data_vars))
        assert_dataset_is_chunked(self, ds, verbose=False)

    def _test_open_dataset_sen3(
        self, url: str, name_data_var: str, ds_sizes: dict, num_data_vars: int
    ):
        with timeit("open " + url) as result:
            # noinspection PyTypeChecker
            ds = xr.open_dataset(url, engine="eopf-zarr", op_mode="native", chunks={})
        self.assertTrue(result.time_delta < allowed_open_time)
        self.assertEqual(num_data_vars, len(ds.data_vars))
        self.assertIn(name_data_var, ds.data_vars)
        self.assertEqual(
            ds_sizes,
            ds[name_data_var].sizes,
        )
        assert_dataset_is_chunked(self, ds, verbose=False)

    def _test_open_dataset_sen3_subgroup(
        self,
        url: str,
        name_data_var: str,
        subgroup: str,
        ds_sizes: dict,
        num_data_vars: int,
    ):
        with timeit("open " + f"{url}/{subgroup}") as result:
            # noinspection PyTypeChecker
            ds = xr.open_dataset(
                f"{url}/{subgroup}",
                engine="eopf-zarr",
                op_mode="native",
                chunks={},
            )
        self.assertTrue(result.time_delta < allowed_open_time)
        self.assertEqual(num_data_vars, len(ds.data_vars))
        self.assertIn(name_data_var, ds.data_vars)
        self.assertEqual(ds_sizes, ds.sizes)
        assert_dataset_is_chunked(self, ds, verbose=False)
