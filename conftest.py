import logging


def pytest_configure() -> None:
    logging.getLogger('py4j').setLevel(logging.INFO)  # DEBUG is too verbose
