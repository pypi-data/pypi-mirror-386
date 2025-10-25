import pytest

from rustybt.errors import UnsupportedDataType
from rustybt.pipeline import CustomClassifier, CustomFactor, CustomFilter
from rustybt.pipeline.dtypes import (
    CLASSIFIER_DTYPES,
    FACTOR_DTYPES,
    FILTER_DTYPES,
)
from rustybt.pipeline.sentinels import NotSpecified
from rustybt.testing import parameter_space
from rustybt.testing.fixtures import ZiplineTestCase
from rustybt.utils.numpy_utils import bool_dtype, int64_dtype

missing_values = {
    int64_dtype: -1,
    bool_dtype: False,
}


class DtypeTestCase(ZiplineTestCase):
    def correct_dtype(cls, dtypes):
        @parameter_space(dtype_=dtypes)
        def test(self, dtype_):
            class Correct(cls):
                missing_value = missing_values.get(dtype_, NotSpecified)
                inputs = []
                window_length = 1
                dtype = dtype_

            # construct an instance to make sure the valid dtype checks out
            assert Correct().dtype, dtype_

        return test

    def incorrect_dtype(cls, dtypes, hint):
        @parameter_space(dtype_=dtypes)
        def test(self, dtype_):
            with pytest.raises(UnsupportedDataType) as excinfo:

                class Incorrect(cls):
                    missing_value = missing_values.get(dtype_, NotSpecified)
                    inputs = []
                    window_length = 1
                    dtype = dtype_

                # the dtype is only checked at instantiating time, not class
                # construction time
                Incorrect()

            assert hint in str(excinfo.value)
            assert str(dtype_) in str(excinfo.value)

        return test

    test_custom_classifier_correct_dtypes = correct_dtype(
        CustomClassifier,
        CLASSIFIER_DTYPES,
    )
    test_custom_classifier_factor_dtypes = incorrect_dtype(
        CustomClassifier,
        FACTOR_DTYPES - CLASSIFIER_DTYPES,
        "CustomFactor",
    )
    test_custom_classifier_filter_dtypes = incorrect_dtype(
        CustomClassifier,
        FILTER_DTYPES - CLASSIFIER_DTYPES,
        "CustomFilter",
    )

    test_custom_factor_correct_dtypes = correct_dtype(
        CustomFactor,
        FACTOR_DTYPES,
    )
    test_custom_factor_classifier_dtypes = incorrect_dtype(
        CustomFactor,
        CLASSIFIER_DTYPES - FACTOR_DTYPES,
        "CustomClassifier",
    )
    test_custom_factor_filter_dtypes = incorrect_dtype(
        CustomFactor,
        FILTER_DTYPES - FACTOR_DTYPES,
        "CustomFilter",
    )

    test_custom_filter_correct_dtypes = correct_dtype(
        CustomFilter,
        FILTER_DTYPES,
    )
    test_custom_filter_classifier_dtypes = incorrect_dtype(
        CustomFilter,
        CLASSIFIER_DTYPES - FILTER_DTYPES,
        "CustomClassifier",
    )

    # This test is special because int64 is in both the ``FACTOR_DTYPES``
    # and ``CLASSIFIER_DTYPES`` set. We check the dtype sets in alphabetical
    # order so we will suggest a classifier for int64 instead of a factor
    # even though both are valid. You probably wanted a classifier if you have
    # int64 anyway.
    test_custom_filter_factor_dtypes = incorrect_dtype(
        CustomFilter,
        FACTOR_DTYPES - FILTER_DTYPES - CLASSIFIER_DTYPES,
        "CustomFactor",
    )
