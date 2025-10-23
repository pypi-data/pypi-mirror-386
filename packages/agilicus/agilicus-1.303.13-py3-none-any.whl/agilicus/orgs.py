import dataclasses
import json
import operator
import sys

import requests

from typing import List, Union

from agilicus import agilicus_api
from agilicus import OpenApiException
from agilicus.agilicus_api import FeatureFlag
from agilicus.agilicus_api import OrganisationOwnerConfig

from . import context, response

from .input_helpers import get_org_from_input_or_ctx, update_if_not_none
from .output import output_if_console
from .output.table import (
    format_table,
    column,
)
from . import get_many_entries
from .input_helpers import strip_none
from . import pop_utils

from .licensing.licenses import apply_constraint_and_vars


def get_org_by_dictionary(ctx, org_id):
    if org_id:
        data = [get(ctx, org_id)]
    else:
        data = query(ctx, org_id)

    org_dict_by_id = {}
    org_dict_by_name = {}
    for org in data:
        if not org:
            continue
        org_dict_by_id[org["id"]] = org
        org_dict_by_name[org["organisation"]] = org
    return (org_dict_by_id, org_dict_by_name)


def query(ctx, org_id=None, created_since=None, page_size=None, name=None, **kwargs):
    token = context.get_token(ctx)

    org_id = get_org_from_input_or_ctx(ctx, org_id)

    params = {}
    update_if_not_none(params, kwargs)

    if org_id:
        params["org_id"] = org_id

    if name is not None:
        params["organisation"] = name

    apiclient = context.get_apiclient(ctx, token)
    if kwargs.get("page_at_id", None) is not None:
        resp = get_many_entries(
            apiclient.org_api.list_orgs,
            "orgs",
            page_size=page_size,
            maximum=kwargs.get("limit", None),
            **params,
        )
    else:
        resp = apiclient.org_api.list_orgs(**params).orgs
    if created_since is not None:
        resp = [org for org in resp if org.created and org.created >= created_since]
        resp = sorted(resp, key=operator.itemgetter("created"))
    return resp


def query_suborgs(ctx, org_id=None, **kwargs):
    token = context.get_token(ctx)
    if not org_id:
        org_id = context.get_org_id(ctx, token)

    headers = {}
    headers["Authorization"] = "Bearer {}".format(token)

    uri = f"/v1/orgs/{org_id}/orgs"
    resp = requests.get(
        context.get_api(ctx) + uri,
        headers=headers,
        verify=context.get_cacert(ctx),
    )
    response.validate(resp)
    return json.loads(resp.text)["orgs"]


def get_raw(ctx, org_id, **kwargs):
    org_id = get_org_from_input_or_ctx(ctx, org_id)
    apiclient = context.get_apiclient(ctx)
    org = apiclient.org_api.get_org(org_id=org_id, **kwargs)
    return org


def get(ctx, org_id, org=None, **kwargs):
    kwargs = strip_none(kwargs)
    org_id = get_org_from_input_or_ctx(ctx, org_id)
    try:
        return get_raw(ctx, org_id, **kwargs).to_dict()
    except OpenApiException as e:
        output_if_console(ctx, str(e))
        return None


def get_org_billing_account(ctx, org_id):
    apiclient = context.get_apiclient(ctx)
    org_id = get_org_from_input_or_ctx(ctx, org_id)
    account = apiclient.org_api.get_org_billing_account(org_id=org_id)
    return account


def create_portal_link(ctx, org_id, return_uri):
    apiclient = context.get_apiclient(ctx)
    org_id = get_org_from_input_or_ctx(ctx, org_id)
    link = agilicus_api.BillingPortalLink(return_uri=return_uri)
    return apiclient.org_api.create_billing_portal_link(
        org_id=org_id, billing_portal_link=link
    )


def update(  # noqa: max-complexity: 19
    ctx,
    org_id,
    auto_create=None,
    issuer=None,
    issuer_id=None,
    contact_id=None,
    subdomain=None,
    external_id=None,
    trust_on_first_use_duration=None,
    admin_state=None,
    name_slug=None,
    organisation=None,
    shard=None,
    disable_user_requests=None,
    cluster=None,
    ruleset_bundle_id=None,
    point_of_presence_id=None,
    region_id=None,
):
    token = context.get_token(ctx)

    headers = {}
    headers["Authorization"] = "Bearer {}".format(token)
    headers["content-type"] = "application/json"

    data = get(ctx, org_id)

    if "created" in data:
        del data["created"]
    if "updated" in data:
        del data["updated"]

    # incase there is no assigned issue yet to this org, don't
    # assume its there.
    data.pop("issuer", None)

    if "sub_organisations" in data:
        del data["sub_organisations"]

    if "sub_orgs" in data:
        del data["sub_orgs"]

    if auto_create is not None:
        data["auto_create"] = auto_create

    if contact_id:
        data["contact_id"] = contact_id

    if subdomain:
        data["subdomain"] = subdomain

    if external_id:
        data["external_id"] = external_id

    if issuer is not None:
        data["issuer"] = issuer

    if issuer_id is not None:
        data["issuer_id"] = issuer_id

    if trust_on_first_use_duration is not None:
        data["trust_on_first_use_duration"] = trust_on_first_use_duration

    if admin_state is not None:
        data["admin_state"] = admin_state

    if name_slug is not None:
        data["name_slug"] = name_slug

    if organisation is not None:
        data["organisation"] = organisation

    if shard is not None:
        data["shard"] = shard

    if cluster is not None:
        data["cluster"] = cluster

    if ruleset_bundle_id is not None:
        data["ruleset_bundle_id"] = ruleset_bundle_id

    if point_of_presence_id is not None:
        data["point_of_presence_id"] = point_of_presence_id

    if region_id is not None:
        data["region_id"] = region_id

    for i in list(data):
        if data[i] is None:
            del data[i]

    if disable_user_requests is not None:
        ownerConfig = OrganisationOwnerConfig(
            disable_user_requests=disable_user_requests
        )
        data["owner_config"] = ownerConfig.to_dict()

    uri = "/v1/orgs/{}".format(org_id)
    resp = requests.put(
        context.get_api(ctx) + uri,
        headers=headers,
        data=json.dumps(data),
        verify=context.get_cacert(ctx),
    )
    response.validate(resp)
    return resp.text


def add(ctx, **kwargs):
    apiclient = context.get_apiclient(ctx)
    kwargs = strip_none(kwargs)
    org = agilicus_api.Organisation(**kwargs)
    try:
        return apiclient.org_api.create_org(org).to_dict()
    except agilicus_api.ApiException as e:
        if e.status == 409:
            print(f"error creating org reason: {e.reason}", file=sys.stderr)
            org = _get_org_by_name_helper(apiclient, kwargs.get("organisation", ""))
            if not org:
                return json.loads(e.body)
            return org
        else:
            raise


def _get_org_by_name_helper(apiclient, organisation):
    params = {}
    params["organisation"] = organisation
    orgs = apiclient.org_api.list_orgs(**params)["orgs"]
    for org in orgs:
        if org.organisation == organisation:
            return {"id": org.id}
    return {}


def add_suborg(
    ctx, organisation, contact_id=None, auto_create=True, subdomain=None, org_id=None
):
    token = context.get_token(ctx)

    headers = {}
    headers["Authorization"] = "Bearer {}".format(token)
    headers["content-type"] = "application/json"

    data = {}
    data["organisation"] = organisation
    if contact_id:
        data["contact_id"] = contact_id
    if subdomain:
        data["subdomain"] = subdomain
    data["auto_create"] = auto_create

    org_id = org_id or context.get_org_id(ctx, token)
    uri = f"/v1/orgs/{org_id}/orgs"
    resp = requests.post(
        context.get_api(ctx) + uri,
        headers=headers,
        data=json.dumps(data),
        verify=context.get_cacert(ctx),
    )
    response.validate(resp)
    return json.loads(resp.text)


def delete_suborg(ctx, suborg_id):
    token = context.get_token(ctx)

    headers = {}
    headers["Authorization"] = "Bearer {}".format(token)
    headers["content-type"] = "application/json"

    uri = "/v1/orgs/{}/orgs/{}".format(context.get_org_id(ctx, token), suborg_id)
    resp = requests.delete(
        context.get_api(ctx) + uri,
        headers=headers,
        verify=context.get_cacert(ctx),
    )
    response.validate(resp)


def delete(ctx, org_id):
    token = context.get_token(ctx)

    headers = {}
    headers["Authorization"] = "Bearer {}".format(token)
    headers["content-type"] = "application/json"

    uri = "/v1/orgs/{}".format(org_id)
    resp = requests.delete(
        context.get_api(ctx) + uri,
        headers=headers,
        verify=context.get_cacert(ctx),
    )
    response.validate(resp)
    return json.loads(resp.text)


def get_system_options(ctx, org_id=None):
    token = context.get_token(ctx)
    if not org_id:
        org_id = context.get_org_id(ctx, token)

    apiclient = context.get_apiclient_from_ctx(ctx)
    return apiclient.org_api.get_system_options(org_id)


def replace_system_options(
    ctx,
    org_id,
    allowed_domains,
    license_constraints,
    constraint_vars,
    replace_constraints,
    replace_vars,
):
    apiclient = context.get_apiclient(ctx)
    system_options = get_system_options(ctx, org_id)

    if allowed_domains is not None:
        system_options.allowed_domains = allowed_domains

    apply_constraint_and_vars(
        system_options,
        license_constraints,
        constraint_vars,
        replace_constraints,
        replace_vars,
    )

    return apiclient.org_api.replace_system_options(
        org_id=org_id, organisation_system_options=system_options
    ).to_dict()


def find_feature(features, feature_name):
    for feature in features:
        if feature.feature == feature_name:
            return feature

    return None


def set_feature(ctx, feature, enabled, setting="", **kwargs):
    apiclient = context.get_apiclient(ctx)
    org_id = get_org_from_input_or_ctx(ctx, **kwargs)
    org = get_raw(ctx, org_id)
    features = org.feature_flags or []
    feature_obj = find_feature(features, feature)

    if not feature_obj:
        feature_obj = FeatureFlag(feature=feature, enabled=enabled, setting=setting)
    else:
        # not the most efficient but simple enough.
        features.remove(feature_obj)

    feature_obj.enabled = enabled
    feature_obj.setting = setting

    features.append(feature_obj)

    org.feature_flags = features

    apiclient.org_api.replace_org(org_id=org.id, organisation=org)
    return get_raw(ctx, org_id).to_dict()


def remove_feature(ctx, feature, **kwargs):
    apiclient = context.get_apiclient(ctx)
    org_id = get_org_from_input_or_ctx(ctx, **kwargs)
    org = get_raw(ctx, org_id)
    features = org.feature_flags or []
    feature_obj = find_feature(features, feature)
    if not feature_obj:
        return org.to_dict()

    features.remove(feature_obj)

    org.feature_flags = features

    apiclient.org_api.replace_org(org_id=org.id, organisation=org)
    return get_raw(ctx, org_id).to_dict()


@dataclasses.dataclass
class OrgBillingInfo:
    org_id: str
    org_name: str
    status: str
    account_id: Union[str, None]
    customer_id: Union[str, None]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def format_org_billing_info_as_text(ctx, info: List[OrgBillingInfo]):
    columns = [
        column("org_id"),
        column("org_name"),
        column("status"),
        column("account_id"),
        column("customer_id"),
    ]

    return format_table(ctx, info, columns)


def _org_to_billing_info(org, customer_id=None):
    return OrgBillingInfo(
        org_id=org.id,
        org_name=org.organisation,
        status=org.admin_state,
        account_id=org.billing_account_id,
        customer_id=customer_id,
    )


def query_no_billing(ctx, **kwargs):
    token = context.get_token(ctx)
    params = {}
    update_if_not_none(params, kwargs)
    # Search for orgs without a billing account id
    params["billing_account_id"] = ""

    apiclient = context.get_apiclient(ctx, token)
    orgs = apiclient.org_api.list_orgs(**params)["orgs"]
    info: List[OrgBillingInfo] = []
    for org in orgs:
        info.append(_org_to_billing_info(org))

    info.extend(_get_billing_accounts_missing_stripe(ctx))
    return format_org_billing_info_as_text(ctx, info)


def _get_billing_accounts_missing_stripe(ctx):
    try:
        import stripe
    except ModuleNotFoundError:
        output_if_console(ctx, "Not fetching orgs with misconfigured billing accounts.")
        output_if_console(ctx, "Add the 'billing' option to the install to gain access")
        return []

    stripe.api_key = context.get_stripe_key(ctx)
    if not stripe.api_key:
        output_if_console(ctx, "Not fetching orgs with misconfigured billing accounts.")
        output_if_console(ctx, "Configure BILLING_API_KEY.")
        return []

    try:
        customer_list = stripe.Customer.list()
        customers = {customer.id for customer in customer_list}

    except Exception as exc:
        if context.output_console(ctx):
            print(f"Failed to fetch billing service customers: {str(exc)}")
            return []
        raise

    apiclient = context.get_apiclient(ctx)
    billing = apiclient.billing_api.list_billing_accounts()["billing_accounts"]
    missing = []
    for account in billing:
        if account.spec.customer_id in customers:
            continue
        for org in account.status.orgs:
            missing.append(_org_to_billing_info(org, account.spec.customer_id))

    return missing


def list_domains(ctx, org_id=None, **kwargs):
    token = context.get_token(ctx)
    if not org_id:
        org_id = context.get_org_id(ctx, token)

    headers = {}
    headers["Authorization"] = "Bearer {}".format(token)

    uri = f"/v1/orgs/{org_id}/domains"
    resp = requests.get(
        context.get_api(ctx) + uri,
        headers=headers,
        verify=context.get_cacert(ctx),
    )
    response.validate(resp)
    return json.loads(resp.text)["domains"]


def reconcile_sub_org_issuer(ctx, sub_org_id, own_issuer, org_id=None, **kwargs):
    apiclient = context.get_apiclient(ctx)
    org_id = get_org_from_input_or_ctx(ctx, org_id=org_id)

    req = agilicus_api.ReconcileSubOrgIssuerRequest(own_issuer=own_issuer)
    return apiclient.org_api.reconcile_sub_org_issuer(
        org_id=org_id, sub_org_id=sub_org_id, reconcile_sub_org_issuer_request=req
    )


def reconcile_org_policy(ctx, all_orgs, org_id, limit, **kwargs):
    apiclient = context.get_apiclient(ctx)
    body = agilicus_api.ReconcileOrgDefaultPolicyRequest()
    org_id = get_org_from_input_or_ctx(ctx, org_id=org_id)
    if not all_orgs:
        body.org_id = org_id
    body.limit = limit

    return apiclient.org_api.create_reconcile_org_default_policy(body)


def format_reconcile_org_policy_results(ctx, results):
    columns = [
        column("org_id"),
        column("ruleset_bundle_id"),
        column("failure"),
    ]
    return format_table(ctx, results.modified, columns)


POP_TAGS_FEATURE_NAME = "pop_tags"


def list_org_pops(ctx, **kwargs):
    org_id = get_org_from_input_or_ctx(ctx, **kwargs)
    org = get_raw(ctx, org_id)
    features = org.feature_flags or []
    feature_obj = find_feature(features, POP_TAGS_FEATURE_NAME)

    if not feature_obj:
        feature_obj = FeatureFlag(feature=POP_TAGS_FEATURE_NAME, enabled=False)
    return pop_utils.make_feature_pop_result(feature_obj)


def _update_pop_setting(ctx, pop, setting_updater: callable, **kwargs):
    apiclient = context.get_apiclient(ctx)
    org_id = get_org_from_input_or_ctx(ctx, **kwargs)
    org = get_raw(ctx, org_id)
    features = org.feature_flags or []
    feature_obj = find_feature(features, POP_TAGS_FEATURE_NAME)

    if not feature_obj:
        feature_obj = FeatureFlag(feature=POP_TAGS_FEATURE_NAME, enabled=False)
        features.append(feature_obj)

    feature_obj.setting = setting_updater(feature_obj.setting, pop)
    feature_obj.enabled = True
    org.feature_flags = features
    apiclient.org_api.replace_org(org_id=org.id, organisation=org)
    return pop_utils.make_feature_pop_result(feature_obj)


def add_org_pop(ctx, pop, **kwargs):
    return _update_pop_setting(ctx, pop, pop_utils.add_pop_to_str, **kwargs)


def remove_org_pop(ctx, pop, **kwargs):
    return _update_pop_setting(ctx, pop, pop_utils.remove_pop_from_str, **kwargs)


def fixup(ctx, org_id, **kwargs):
    apiclient = context.get_apiclient(ctx)
    kwargs = strip_none(kwargs)
    org_fixup = agilicus_api.OrgFixup(org_id=org_id, **kwargs)
    return apiclient.org_api.org_fixup(org_id, org_fixup).to_dict()
