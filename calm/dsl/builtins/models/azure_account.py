import sys

from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER, PROVIDER_RESOURCE
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class AzureAccountSpecType(AccountSpecType):
    __schema_name__ = "AzureAccountSpec"
    __openapi_type__ = "azure_account_spec"

    __provider_type__ = PROVIDER.AZURE
    __resource_type__ = PROVIDER_RESOURCE.AZURE.VM

    def compile(cls):
        """returns the compiled payload for azure account spec"""

        cdict = super().compile()
        client_key = cdict.pop("client_key", None)
        cdict["client_key"] = {
            "attrs": {"is_secret_modified": True},
            "value": client_key,
        }

        # TODO remove from here
        if cdict["cloud_environment"] not in [
            "PublicCloud",
            "GermanCloud",
            "ChinaCloud",
            "USGovernmentCloud",
        ]:
            LOG.error(
                "Invalid cloud environment '{}' given.".format(
                    cdict["cloud_environment"]
                )
            )
            sys.exit(-1)

        return cdict


class AzureAccountSpecValidator(PropertyValidator, openapi_type="azure_account_spec"):
    __default__ = None
    __kind__ = AzureAccountSpecType


def azure_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AzureAccountSpecType(name, bases, kwargs)


AzureAccountSpec = azure_account_spec()
