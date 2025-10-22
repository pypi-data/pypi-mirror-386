r'''
# `datadog_integration_aws_event_bridge`

Refer to the Terraform Registry for docs: [`datadog_integration_aws_event_bridge`](https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge).
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from .._jsii import *

import cdktf as _cdktf_9a9027ec
import constructs as _constructs_77d1e7e8


class IntegrationAwsEventBridge(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-datadog.integrationAwsEventBridge.IntegrationAwsEventBridge",
):
    '''Represents a {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge datadog_integration_aws_event_bridge}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        account_id: builtins.str,
        event_generator_name: builtins.str,
        region: builtins.str,
        create_event_bus: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge datadog_integration_aws_event_bridge} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param account_id: Your AWS Account ID without dashes. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#account_id IntegrationAwsEventBridge#account_id}
        :param event_generator_name: The given part of the event source name, which is then combined with an assigned suffix to form the full name. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#event_generator_name IntegrationAwsEventBridge#event_generator_name}
        :param region: The event source's `AWS region <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#region IntegrationAwsEventBridge#region}
        :param create_event_bus: True if Datadog should create the event bus in addition to the event source. Requires the ``events:CreateEventBus`` permission. Defaults to ``true``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#create_event_bus IntegrationAwsEventBridge#create_event_bus}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__74f20009a8810195f37ac00abfcce88c444452ad68259804278607c8b67c87ea)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = IntegrationAwsEventBridgeConfig(
            account_id=account_id,
            event_generator_name=event_generator_name,
            region=region,
            create_event_bus=create_event_bus,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a IntegrationAwsEventBridge resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the IntegrationAwsEventBridge to import.
        :param import_from_id: The id of the existing IntegrationAwsEventBridge that should be imported. Refer to the {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the IntegrationAwsEventBridge to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f7481c50a1bbae7e557678c40c2c04dc8fe4b82d1752d28b73388e42ab31548d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetCreateEventBus")
    def reset_create_event_bus(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreateEventBus", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="accountIdInput")
    def account_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "accountIdInput"))

    @builtins.property
    @jsii.member(jsii_name="createEventBusInput")
    def create_event_bus_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "createEventBusInput"))

    @builtins.property
    @jsii.member(jsii_name="eventGeneratorNameInput")
    def event_generator_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "eventGeneratorNameInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="accountId")
    def account_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "accountId"))

    @account_id.setter
    def account_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a5109afd28073a262f38baa86f8c500091db5c6c655aed854b4a3651523987a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "accountId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="createEventBus")
    def create_event_bus(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "createEventBus"))

    @create_event_bus.setter
    def create_event_bus(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e8ca995d315bebda21a31ad319c2d7da4281e15c9380b32c7d69c8edab6a17ae)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "createEventBus", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="eventGeneratorName")
    def event_generator_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "eventGeneratorName"))

    @event_generator_name.setter
    def event_generator_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bfdb7098c028ddbf10923ac727f66fde13bd4f506c048d177520915b2cf14e56)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "eventGeneratorName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @region.setter
    def region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be06684697aebbc3454b4611256872534da550323f302e5bc4a723990d28ab91)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "region", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-datadog.integrationAwsEventBridge.IntegrationAwsEventBridgeConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "account_id": "accountId",
        "event_generator_name": "eventGeneratorName",
        "region": "region",
        "create_event_bus": "createEventBus",
    },
)
class IntegrationAwsEventBridgeConfig(_cdktf_9a9027ec.TerraformMetaArguments):
    def __init__(
        self,
        *,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
        account_id: builtins.str,
        event_generator_name: builtins.str,
        region: builtins.str,
        create_event_bus: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param account_id: Your AWS Account ID without dashes. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#account_id IntegrationAwsEventBridge#account_id}
        :param event_generator_name: The given part of the event source name, which is then combined with an assigned suffix to form the full name. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#event_generator_name IntegrationAwsEventBridge#event_generator_name}
        :param region: The event source's `AWS region <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#region IntegrationAwsEventBridge#region}
        :param create_event_bus: True if Datadog should create the event bus in addition to the event source. Requires the ``events:CreateEventBus`` permission. Defaults to ``true``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#create_event_bus IntegrationAwsEventBridge#create_event_bus}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d27292c2c947778198abd48f5f640795cf406e78a2fe22d66c818ab97bba89ae)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument account_id", value=account_id, expected_type=type_hints["account_id"])
            check_type(argname="argument event_generator_name", value=event_generator_name, expected_type=type_hints["event_generator_name"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument create_event_bus", value=create_event_bus, expected_type=type_hints["create_event_bus"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "account_id": account_id,
            "event_generator_name": event_generator_name,
            "region": region,
        }
        if connection is not None:
            self._values["connection"] = connection
        if count is not None:
            self._values["count"] = count
        if depends_on is not None:
            self._values["depends_on"] = depends_on
        if for_each is not None:
            self._values["for_each"] = for_each
        if lifecycle is not None:
            self._values["lifecycle"] = lifecycle
        if provider is not None:
            self._values["provider"] = provider
        if provisioners is not None:
            self._values["provisioners"] = provisioners
        if create_event_bus is not None:
            self._values["create_event_bus"] = create_event_bus

    @builtins.property
    def connection(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("connection")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]], result)

    @builtins.property
    def count(
        self,
    ) -> typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("count")
        return typing.cast(typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]], result)

    @builtins.property
    def depends_on(
        self,
    ) -> typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("depends_on")
        return typing.cast(typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]], result)

    @builtins.property
    def for_each(self) -> typing.Optional[_cdktf_9a9027ec.ITerraformIterator]:
        '''
        :stability: experimental
        '''
        result = self._values.get("for_each")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.ITerraformIterator], result)

    @builtins.property
    def lifecycle(self) -> typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle]:
        '''
        :stability: experimental
        '''
        result = self._values.get("lifecycle")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle], result)

    @builtins.property
    def provider(self) -> typing.Optional[_cdktf_9a9027ec.TerraformProvider]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provider")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformProvider], result)

    @builtins.property
    def provisioners(
        self,
    ) -> typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provisioners")
        return typing.cast(typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]], result)

    @builtins.property
    def account_id(self) -> builtins.str:
        '''Your AWS Account ID without dashes.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#account_id IntegrationAwsEventBridge#account_id}
        '''
        result = self._values.get("account_id")
        assert result is not None, "Required property 'account_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def event_generator_name(self) -> builtins.str:
        '''The given part of the event source name, which is then combined with an assigned suffix to form the full name.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#event_generator_name IntegrationAwsEventBridge#event_generator_name}
        '''
        result = self._values.get("event_generator_name")
        assert result is not None, "Required property 'event_generator_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def region(self) -> builtins.str:
        '''The event source's `AWS region <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#region IntegrationAwsEventBridge#region}
        '''
        result = self._values.get("region")
        assert result is not None, "Required property 'region' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def create_event_bus(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''True if Datadog should create the event bus in addition to the event source.

        Requires the ``events:CreateEventBus`` permission. Defaults to ``true``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/datadog/datadog/3.77.0/docs/resources/integration_aws_event_bridge#create_event_bus IntegrationAwsEventBridge#create_event_bus}
        '''
        result = self._values.get("create_event_bus")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IntegrationAwsEventBridgeConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "IntegrationAwsEventBridge",
    "IntegrationAwsEventBridgeConfig",
]

publication.publish()

def _typecheckingstub__74f20009a8810195f37ac00abfcce88c444452ad68259804278607c8b67c87ea(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account_id: builtins.str,
    event_generator_name: builtins.str,
    region: builtins.str,
    create_event_bus: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f7481c50a1bbae7e557678c40c2c04dc8fe4b82d1752d28b73388e42ab31548d(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a5109afd28073a262f38baa86f8c500091db5c6c655aed854b4a3651523987a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e8ca995d315bebda21a31ad319c2d7da4281e15c9380b32c7d69c8edab6a17ae(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bfdb7098c028ddbf10923ac727f66fde13bd4f506c048d177520915b2cf14e56(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be06684697aebbc3454b4611256872534da550323f302e5bc4a723990d28ab91(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d27292c2c947778198abd48f5f640795cf406e78a2fe22d66c818ab97bba89ae(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    account_id: builtins.str,
    event_generator_name: builtins.str,
    region: builtins.str,
    create_event_bus: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass
