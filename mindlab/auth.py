from pathlib import Path
from typing import Dict, Optional, Tuple

from google.auth import default, load_credentials_from_file
from google.auth.credentials import Credentials
from xdg import xdg_config_home

from mindlab.pyproject import MINDLAB_CONFIG


class Auth:  # pylint: disable=too-few-public-methods
    def __init__(self, organization: Optional[str] = None):
        self.organization = (
            organization if organization is not None else MINDLAB_CONFIG.get('organization')
        )

    def organization_id(self, organization: Optional[str] = None) -> str:
        """
        Return the canonical organization ID.
        """
        organization = organization or self.organization
        if not organization:
            raise ValueError('You must provide an organization')
        return organization.replace('.', '-')


class GCPAuth(Auth):
    def __init__(self, organization: Optional[str] = None, project: Optional[str] = None):
        """
        Google Cloud Platform authentication.
        """
        super().__init__(organization=organization)
        self.project = project if project is not None else MINDLAB_CONFIG.get('project')
        self._gcloud_config = xdg_config_home() / 'gcloud'
        self._credentials: Dict[Tuple[str, str], Credentials] = {}

    def clear_cache(self) -> None:
        self._credentials = {}

    def project_id(self, organization_id: str, project: Optional[str] = None) -> str:
        """
        Return the canonical project ID.
        """
        project = project or self.project
        if not project:
            raise ValueError('You must provide a project')
        return f'{project}-{organization_id}'

    def ids(
        self, organization: Optional[str] = None, project: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Return a tuple of organization ID and project ID.
        """
        organization_id = self.organization_id(organization)
        return organization_id, self.project_id(organization_id, project)

    def organization_credentials_path(self, organization_id: str) -> Optional[Path]:
        """
        Return the path to the organization credentials or None if it does not exist.
        """
        credentials_path = self._gcloud_config / f'credentials/{organization_id}.json'
        return credentials_path if credentials_path.exists() else None

    def credentials(
        self, organization: Optional[str] = None, project: Optional[str] = None,
    ) -> Tuple[Credentials, str]:
        """
        Return a tuple of credentials and project ID.
        """
        organization_id, project_id = self.ids(organization, project)

        if credentials := self._credentials.get((organization_id, project_id)):
            return credentials, project_id

        if org_creds := self.organization_credentials_path(organization_id):
            credentials = load_credentials_from_file(org_creds, quota_project_id=project_id)[0]
        else:
            # Note: we cannot specify the quota project ID here for some weird reason
            # (see https://github.com/google-github-actions/auth/issues/250)
            credentials = default()[0]

        self._credentials[(organization_id, project_id)] = credentials
        return credentials, project_id


class AWSAuth(Auth):  # pylint: disable=too-few-public-methods
    """
    Amazon Web Services authentication.
    """
