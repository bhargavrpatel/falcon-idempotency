import pytest

import falcon_idempotency


def test_mock_function():
    assert falcon_idempotency.mock_function(1, 2) == 3
