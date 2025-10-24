
# flake8: noqa

# Import all APIs into this package.
# If you have many APIs here with many many models used in each API this may
# raise a `RecursionError`.
# In order to avoid this, import only the API that you directly need like:
#
#   from .api.application_services_api import ApplicationServicesApi
#
# or import this package, but before doing it, use:
#
#   import sys
#   sys.setrecursionlimit(n)

# Import APIs into API package:
from agilicus_api.api.application_services_api import ApplicationServicesApi
from agilicus_api.api.applications_api import ApplicationsApi
from agilicus_api.api.audits_api import AuditsApi
from agilicus_api.api.billing_api import BillingApi
from agilicus_api.api.catalogues_api import CataloguesApi
from agilicus_api.api.certificates_api import CertificatesApi
from agilicus_api.api.challenges_api import ChallengesApi
from agilicus_api.api.connectors_api import ConnectorsApi
from agilicus_api.api.credentials_api import CredentialsApi
from agilicus_api.api.diagnostics_api import DiagnosticsApi
from agilicus_api.api.features_api import FeaturesApi
from agilicus_api.api.files_api import FilesApi
from agilicus_api.api.groups_api import GroupsApi
from agilicus_api.api.hosts_api import HostsApi
from agilicus_api.api.issuers_api import IssuersApi
from agilicus_api.api.labels_api import LabelsApi
from agilicus_api.api.launchers_api import LaunchersApi
from agilicus_api.api.licensing_api import LicensingApi
from agilicus_api.api.lookups_api import LookupsApi
from agilicus_api.api.messages_api import MessagesApi
from agilicus_api.api.metrics_api import MetricsApi
from agilicus_api.api.organisations_api import OrganisationsApi
from agilicus_api.api.permissions_api import PermissionsApi
from agilicus_api.api.policy_api import PolicyApi
from agilicus_api.api.policy_templates_api import PolicyTemplatesApi
from agilicus_api.api.policy_config_api import PolicyConfigApi
from agilicus_api.api.regions_api import RegionsApi
from agilicus_api.api.resources_api import ResourcesApi
from agilicus_api.api.rules_api import RulesApi
from agilicus_api.api.tokens_api import TokensApi
from agilicus_api.api.trusted_certs_api import TrustedCertsApi
from agilicus_api.api.users_api import UsersApi
from agilicus_api.api.whoami_api import WhoamiApi
