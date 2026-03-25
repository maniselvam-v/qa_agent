# Auto-generated conftest — add shared fixtures here
import pytest
import os

def pytest_configure(config):
    config.addinivalue_line('markers', 'positive: positive test cases')
    config.addinivalue_line('markers', 'negative: negative test cases')
    config.addinivalue_line('markers', 'edge: edge case tests')
    config.addinivalue_line('markers', 'api: API tests')
    config.addinivalue_line('markers', 'ui: UI tests')
    config.addinivalue_line('markers', 'etl: ETL tests')
    config.addinivalue_line('markers', 'performance: performance tests')
