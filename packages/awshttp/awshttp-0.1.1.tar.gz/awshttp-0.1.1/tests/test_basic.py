"""Basic tests for awshttp."""

import awshttp


def test_import():
    """Test that the module can be imported."""
    assert awshttp.__version__ == '0.1.0'


def test_exports():
    """Test that all expected functions are exported."""
    expected = [
        'request', 'get', 'post', 'put', 'delete', 'patch',
        'with_retry', 'post_json', 'put_json'
    ]
    for func in expected:
        assert hasattr(awshttp, func)
