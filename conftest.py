import logging


def pytest_configure() -> None:
    logging.getLogger('botocore').setLevel(logging.INFO)  # DEBUG is too verbose
