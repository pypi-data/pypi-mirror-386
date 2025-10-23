r'''
# `upcloud_loadbalancer_static_backend_member`

Refer to the Terraform Registry for docs: [`upcloud_loadbalancer_static_backend_member`](https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member).
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


class LoadbalancerStaticBackendMember(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-upcloud.loadbalancerStaticBackendMember.LoadbalancerStaticBackendMember",
):
    '''Represents a {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member upcloud_loadbalancer_static_backend_member}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        backend: builtins.str,
        max_sessions: jsii.Number,
        name: builtins.str,
        weight: jsii.Number,
        enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ip: typing.Optional[builtins.str] = None,
        port: typing.Optional[jsii.Number] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member upcloud_loadbalancer_static_backend_member} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param backend: ID of the load balancer backend to which the member is connected. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#backend LoadbalancerStaticBackendMember#backend}
        :param max_sessions: Maximum number of sessions before queueing. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#max_sessions LoadbalancerStaticBackendMember#max_sessions}
        :param name: The name of the member. Must be unique within within the load balancer backend. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#name LoadbalancerStaticBackendMember#name}
        :param weight: Weight of the member. The higher the weight, the more traffic the member receives. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#weight LoadbalancerStaticBackendMember#weight}
        :param enabled: Indicates if the member is enabled. Disabled members are excluded from load balancing. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#enabled LoadbalancerStaticBackendMember#enabled}
        :param ip: Optional fallback IP address in case of failure on DNS resolving. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#ip LoadbalancerStaticBackendMember#ip}
        :param port: Server port. Port is optional and can be specified in DNS SRV record. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#port LoadbalancerStaticBackendMember#port}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0093c421ecfc42e8e6dd6bf51f82ca5c5c98fde120c10799c3749e9640eabbee)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = LoadbalancerStaticBackendMemberConfig(
            backend=backend,
            max_sessions=max_sessions,
            name=name,
            weight=weight,
            enabled=enabled,
            ip=ip,
            port=port,
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
        '''Generates CDKTF code for importing a LoadbalancerStaticBackendMember resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the LoadbalancerStaticBackendMember to import.
        :param import_from_id: The id of the existing LoadbalancerStaticBackendMember that should be imported. Refer to the {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the LoadbalancerStaticBackendMember to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5cdc62ba614f1912735788517ff09703118b30c0c50c8ed7d0e5c37e85d65c16)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetEnabled")
    def reset_enabled(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEnabled", []))

    @jsii.member(jsii_name="resetIp")
    def reset_ip(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIp", []))

    @jsii.member(jsii_name="resetPort")
    def reset_port(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPort", []))

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
    @jsii.member(jsii_name="backendInput")
    def backend_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "backendInput"))

    @builtins.property
    @jsii.member(jsii_name="enabledInput")
    def enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enabledInput"))

    @builtins.property
    @jsii.member(jsii_name="ipInput")
    def ip_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "ipInput"))

    @builtins.property
    @jsii.member(jsii_name="maxSessionsInput")
    def max_sessions_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxSessionsInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="portInput")
    def port_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "portInput"))

    @builtins.property
    @jsii.member(jsii_name="weightInput")
    def weight_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "weightInput"))

    @builtins.property
    @jsii.member(jsii_name="backend")
    def backend(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "backend"))

    @backend.setter
    def backend(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6a85befa123f0977604415bd7084fef660039bf490b62e67440df5e3b31519a0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "backend", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="enabled")
    def enabled(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "enabled"))

    @enabled.setter
    def enabled(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b814a2af3c03084c6098926c658cd82f86a9cf909a5b9e85c63c0279bfe985d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "enabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ip")
    def ip(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "ip"))

    @ip.setter
    def ip(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c37b73f2180c6b8f47a18e7e2214cde8b42b9ddb0fc1e533e0f703003996887)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ip", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxSessions")
    def max_sessions(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxSessions"))

    @max_sessions.setter
    def max_sessions(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__01d0370daa78a462eb2494d898af4d7a95a510bfffe5256413a933acb9571e8e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxSessions", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7048e0599376667732eafe50e62926cc664a5daa98d66935b5d0b035622e56de)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="port")
    def port(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "port"))

    @port.setter
    def port(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__25279ab57e45832c2d6e76b00763463d4e5c66544c473a0b143bcbb6bafa9691)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "port", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="weight")
    def weight(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "weight"))

    @weight.setter
    def weight(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d69200f071818b66916b76ed762fa220ace74773e8af2948103bef4a65889525)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "weight", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-upcloud.loadbalancerStaticBackendMember.LoadbalancerStaticBackendMemberConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "backend": "backend",
        "max_sessions": "maxSessions",
        "name": "name",
        "weight": "weight",
        "enabled": "enabled",
        "ip": "ip",
        "port": "port",
    },
)
class LoadbalancerStaticBackendMemberConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        backend: builtins.str,
        max_sessions: jsii.Number,
        name: builtins.str,
        weight: jsii.Number,
        enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ip: typing.Optional[builtins.str] = None,
        port: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param backend: ID of the load balancer backend to which the member is connected. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#backend LoadbalancerStaticBackendMember#backend}
        :param max_sessions: Maximum number of sessions before queueing. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#max_sessions LoadbalancerStaticBackendMember#max_sessions}
        :param name: The name of the member. Must be unique within within the load balancer backend. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#name LoadbalancerStaticBackendMember#name}
        :param weight: Weight of the member. The higher the weight, the more traffic the member receives. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#weight LoadbalancerStaticBackendMember#weight}
        :param enabled: Indicates if the member is enabled. Disabled members are excluded from load balancing. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#enabled LoadbalancerStaticBackendMember#enabled}
        :param ip: Optional fallback IP address in case of failure on DNS resolving. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#ip LoadbalancerStaticBackendMember#ip}
        :param port: Server port. Port is optional and can be specified in DNS SRV record. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#port LoadbalancerStaticBackendMember#port}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7fd91b91af980180e27c74a1ffa9d5ee54648adb15fb81bf7f115e7ad236d8f)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument backend", value=backend, expected_type=type_hints["backend"])
            check_type(argname="argument max_sessions", value=max_sessions, expected_type=type_hints["max_sessions"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument weight", value=weight, expected_type=type_hints["weight"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument ip", value=ip, expected_type=type_hints["ip"])
            check_type(argname="argument port", value=port, expected_type=type_hints["port"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "backend": backend,
            "max_sessions": max_sessions,
            "name": name,
            "weight": weight,
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
        if enabled is not None:
            self._values["enabled"] = enabled
        if ip is not None:
            self._values["ip"] = ip
        if port is not None:
            self._values["port"] = port

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
    def backend(self) -> builtins.str:
        '''ID of the load balancer backend to which the member is connected.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#backend LoadbalancerStaticBackendMember#backend}
        '''
        result = self._values.get("backend")
        assert result is not None, "Required property 'backend' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def max_sessions(self) -> jsii.Number:
        '''Maximum number of sessions before queueing.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#max_sessions LoadbalancerStaticBackendMember#max_sessions}
        '''
        result = self._values.get("max_sessions")
        assert result is not None, "Required property 'max_sessions' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the member. Must be unique within within the load balancer backend.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#name LoadbalancerStaticBackendMember#name}
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def weight(self) -> jsii.Number:
        '''Weight of the member. The higher the weight, the more traffic the member receives.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#weight LoadbalancerStaticBackendMember#weight}
        '''
        result = self._values.get("weight")
        assert result is not None, "Required property 'weight' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def enabled(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Indicates if the member is enabled. Disabled members are excluded from load balancing.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#enabled LoadbalancerStaticBackendMember#enabled}
        '''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def ip(self) -> typing.Optional[builtins.str]:
        '''Optional fallback IP address in case of failure on DNS resolving.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#ip LoadbalancerStaticBackendMember#ip}
        '''
        result = self._values.get("ip")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def port(self) -> typing.Optional[jsii.Number]:
        '''Server port. Port is optional and can be specified in DNS SRV record.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/upcloudltd/upcloud/5.29.1/docs/resources/loadbalancer_static_backend_member#port LoadbalancerStaticBackendMember#port}
        '''
        result = self._values.get("port")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LoadbalancerStaticBackendMemberConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LoadbalancerStaticBackendMember",
    "LoadbalancerStaticBackendMemberConfig",
]

publication.publish()

def _typecheckingstub__0093c421ecfc42e8e6dd6bf51f82ca5c5c98fde120c10799c3749e9640eabbee(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    backend: builtins.str,
    max_sessions: jsii.Number,
    name: builtins.str,
    weight: jsii.Number,
    enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ip: typing.Optional[builtins.str] = None,
    port: typing.Optional[jsii.Number] = None,
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

def _typecheckingstub__5cdc62ba614f1912735788517ff09703118b30c0c50c8ed7d0e5c37e85d65c16(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6a85befa123f0977604415bd7084fef660039bf490b62e67440df5e3b31519a0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b814a2af3c03084c6098926c658cd82f86a9cf909a5b9e85c63c0279bfe985d(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c37b73f2180c6b8f47a18e7e2214cde8b42b9ddb0fc1e533e0f703003996887(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__01d0370daa78a462eb2494d898af4d7a95a510bfffe5256413a933acb9571e8e(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7048e0599376667732eafe50e62926cc664a5daa98d66935b5d0b035622e56de(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__25279ab57e45832c2d6e76b00763463d4e5c66544c473a0b143bcbb6bafa9691(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d69200f071818b66916b76ed762fa220ace74773e8af2948103bef4a65889525(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7fd91b91af980180e27c74a1ffa9d5ee54648adb15fb81bf7f115e7ad236d8f(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    backend: builtins.str,
    max_sessions: jsii.Number,
    name: builtins.str,
    weight: jsii.Number,
    enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ip: typing.Optional[builtins.str] = None,
    port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass
