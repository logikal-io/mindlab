from pathlib import Path

from pytest import raises
from pytest_mock import MockerFixture

from mindlab.auth import Auth, GCPAuth


def test_organization_error() -> None:
    with raises(ValueError, match='You must provide an organization'):
        Auth(organization='').organization_id()


def test_gcp_credentials(mocker: MockerFixture) -> None:
    org_creds_path = mocker.patch('mindlab.auth.GCPAuth.organization_credentials_path')
    mocker.patch('mindlab.auth.load_credentials_from_file', return_value=['from_file', None])
    mocker.patch('mindlab.auth.default', return_value=['default', None])

    config = {'organization': 'test-organization', 'project': 'test-project'}
    auth = GCPAuth(**config)
    expected_project_id = f'{config["project"]}-{config["organization"]}'

    # With organizational credentials
    org_creds_path.return_value = Path('org_creds')
    assert auth.credentials() == ('from_file', expected_project_id)

    # From cache
    org_creds_path.return_value = None
    assert auth.credentials() == ('from_file', expected_project_id)

    # With default credentials
    auth.clear_cache()
    assert auth.credentials() == ('default', expected_project_id)


def test_gcp_credentials_errors() -> None:
    with raises(ValueError, match='You must provide a project'):
        GCPAuth(project='').credentials(organization='test')
