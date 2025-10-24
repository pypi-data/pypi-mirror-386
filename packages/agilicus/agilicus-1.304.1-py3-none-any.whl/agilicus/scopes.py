import dataclasses
from typing import List


@dataclasses.dataclass
class AgilicusScopes:
    applications: List[str]
    audits: List[str]
    catalogues: List[str]
    challenges: List[str]
    diagnostics: List[str]
    files: List[str]
    issuers: List[str]
    messages: List[str]
    metrics: List[str]
    orgs: List[str]
    sysgroups: List[str]
    traffic_tokens: List[str]
    users: List[str]
    permissions: List[str]

    def to_list(self):
        scopes = []
        for endpoint, scope_list in self.__dict__.items():
            # Translate _ to - since we're representing these as python vars
            endpoint_name = endpoint.replace("_", "-")
            for scope in scope_list:
                scopes.append(f"urn:agilicus:api:{endpoint_name}:{scope}")

        return list(set(scopes))


MULTI_ORG_SCOPE = "urn:agilicus:token_payload:multiorg:true"

# Please keep this list in sync with the one in
# portal/src/app/core/services/auth-service.service.ts
DEFAULT_SCOPES = ["urn:agilicus:api:*?", "urn:agilicus:api:rabbitmq?"]

ADMIN_SCOPES = ["urn:agilicus:api:*:creator?", "urn:agilicus:api:rabbitmq?"]

DEFAULT_SCOPES_MULTI = [
    "urn:agilicus:api:*?",
    "urn:agilicus:api:rabbitmq?",
    MULTI_ORG_SCOPE,
]


def get_default_scopes():
    return DEFAULT_SCOPES


def get_admin_scopes():
    return ADMIN_SCOPES
