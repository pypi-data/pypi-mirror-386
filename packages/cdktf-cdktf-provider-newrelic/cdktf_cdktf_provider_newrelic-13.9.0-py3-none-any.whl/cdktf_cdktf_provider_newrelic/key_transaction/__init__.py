r'''
# `newrelic_key_transaction`

Refer to the Terraform Registry for docs: [`newrelic_key_transaction`](https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction).
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


class KeyTransaction(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-newrelic.keyTransaction.KeyTransaction",
):
    '''Represents a {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction newrelic_key_transaction}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        apdex_index: jsii.Number,
        application_guid: builtins.str,
        browser_apdex_target: jsii.Number,
        metric_name: builtins.str,
        name: builtins.str,
        id: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction newrelic_key_transaction} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param apdex_index: The acceptable amount of the time spent in the backend before customers get frustrated (Apdex target). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#apdex_index KeyTransaction#apdex_index}
        :param application_guid: The GUID of the application. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#application_guid KeyTransaction#application_guid}
        :param browser_apdex_target: The acceptable amount of time for rendering a page in a browser before customers get frustrated (browser Apdex target). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#browser_apdex_target KeyTransaction#browser_apdex_target}
        :param metric_name: The name of the metric underlying this key transaction. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#metric_name KeyTransaction#metric_name}
        :param name: The name of the key transaction. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#name KeyTransaction#name}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#id KeyTransaction#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8db08007b4c99dfe3a2ed7b8f233b818a475a2624b6f3282a7e631234269c0de)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = KeyTransactionConfig(
            apdex_index=apdex_index,
            application_guid=application_guid,
            browser_apdex_target=browser_apdex_target,
            metric_name=metric_name,
            name=name,
            id=id,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id_, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a KeyTransaction resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the KeyTransaction to import.
        :param import_from_id: The id of the existing KeyTransaction that should be imported. Refer to the {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the KeyTransaction to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ce954a66d86c27a9b00e75c131aee940545803e397a24465d74e5f827f787d6f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

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
    @jsii.member(jsii_name="domain")
    def domain(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "domain"))

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @builtins.property
    @jsii.member(jsii_name="apdexIndexInput")
    def apdex_index_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "apdexIndexInput"))

    @builtins.property
    @jsii.member(jsii_name="applicationGuidInput")
    def application_guid_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "applicationGuidInput"))

    @builtins.property
    @jsii.member(jsii_name="browserApdexTargetInput")
    def browser_apdex_target_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "browserApdexTargetInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="metricNameInput")
    def metric_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "metricNameInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="apdexIndex")
    def apdex_index(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "apdexIndex"))

    @apdex_index.setter
    def apdex_index(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b7af85a6b826b71fb214ebb89f2ede9d0442c22729f41a6e09a432163f5c137f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "apdexIndex", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="applicationGuid")
    def application_guid(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "applicationGuid"))

    @application_guid.setter
    def application_guid(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0e8fb77e7c27b4264491040fd2dde0158f417da3d08d439d71d0a460c791a6d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "applicationGuid", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="browserApdexTarget")
    def browser_apdex_target(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "browserApdexTarget"))

    @browser_apdex_target.setter
    def browser_apdex_target(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e5104930bb44251b86ad46024cd8d8a8cb046133a4e1194268bcede118612dd1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "browserApdexTarget", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__33df1e79b7d6f9353a198894a6132871883a5a4cee606e551cfbb97faf23e22c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="metricName")
    def metric_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "metricName"))

    @metric_name.setter
    def metric_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__11ef6623d9da4f791c960736348cb21e20b88f49213ec169f46e7808bf007b7e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "metricName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aaea65f16fd385ca5c1746205c5bf566d814918499995b7bdf04e9ebb0a49810)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-newrelic.keyTransaction.KeyTransactionConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "apdex_index": "apdexIndex",
        "application_guid": "applicationGuid",
        "browser_apdex_target": "browserApdexTarget",
        "metric_name": "metricName",
        "name": "name",
        "id": "id",
    },
)
class KeyTransactionConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        apdex_index: jsii.Number,
        application_guid: builtins.str,
        browser_apdex_target: jsii.Number,
        metric_name: builtins.str,
        name: builtins.str,
        id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param apdex_index: The acceptable amount of the time spent in the backend before customers get frustrated (Apdex target). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#apdex_index KeyTransaction#apdex_index}
        :param application_guid: The GUID of the application. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#application_guid KeyTransaction#application_guid}
        :param browser_apdex_target: The acceptable amount of time for rendering a page in a browser before customers get frustrated (browser Apdex target). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#browser_apdex_target KeyTransaction#browser_apdex_target}
        :param metric_name: The name of the metric underlying this key transaction. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#metric_name KeyTransaction#metric_name}
        :param name: The name of the key transaction. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#name KeyTransaction#name}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#id KeyTransaction#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__96a16c69949077f0dfdc8c98833f8200ad76715cc69bd4b0ce1d772e23cf8734)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument apdex_index", value=apdex_index, expected_type=type_hints["apdex_index"])
            check_type(argname="argument application_guid", value=application_guid, expected_type=type_hints["application_guid"])
            check_type(argname="argument browser_apdex_target", value=browser_apdex_target, expected_type=type_hints["browser_apdex_target"])
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "apdex_index": apdex_index,
            "application_guid": application_guid,
            "browser_apdex_target": browser_apdex_target,
            "metric_name": metric_name,
            "name": name,
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
        if id is not None:
            self._values["id"] = id

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
    def apdex_index(self) -> jsii.Number:
        '''The acceptable amount of the time spent in the backend before customers get frustrated (Apdex target).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#apdex_index KeyTransaction#apdex_index}
        '''
        result = self._values.get("apdex_index")
        assert result is not None, "Required property 'apdex_index' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def application_guid(self) -> builtins.str:
        '''The GUID of the application.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#application_guid KeyTransaction#application_guid}
        '''
        result = self._values.get("application_guid")
        assert result is not None, "Required property 'application_guid' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def browser_apdex_target(self) -> jsii.Number:
        '''The acceptable amount of time for rendering a page in a browser before customers get frustrated (browser Apdex target).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#browser_apdex_target KeyTransaction#browser_apdex_target}
        '''
        result = self._values.get("browser_apdex_target")
        assert result is not None, "Required property 'browser_apdex_target' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def metric_name(self) -> builtins.str:
        '''The name of the metric underlying this key transaction.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#metric_name KeyTransaction#metric_name}
        '''
        result = self._values.get("metric_name")
        assert result is not None, "Required property 'metric_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the key transaction.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#name KeyTransaction#name}
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/newrelic/newrelic/3.73.0/docs/resources/key_transaction#id KeyTransaction#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "KeyTransactionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "KeyTransaction",
    "KeyTransactionConfig",
]

publication.publish()

def _typecheckingstub__8db08007b4c99dfe3a2ed7b8f233b818a475a2624b6f3282a7e631234269c0de(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    apdex_index: jsii.Number,
    application_guid: builtins.str,
    browser_apdex_target: jsii.Number,
    metric_name: builtins.str,
    name: builtins.str,
    id: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__ce954a66d86c27a9b00e75c131aee940545803e397a24465d74e5f827f787d6f(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b7af85a6b826b71fb214ebb89f2ede9d0442c22729f41a6e09a432163f5c137f(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0e8fb77e7c27b4264491040fd2dde0158f417da3d08d439d71d0a460c791a6d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e5104930bb44251b86ad46024cd8d8a8cb046133a4e1194268bcede118612dd1(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__33df1e79b7d6f9353a198894a6132871883a5a4cee606e551cfbb97faf23e22c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__11ef6623d9da4f791c960736348cb21e20b88f49213ec169f46e7808bf007b7e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aaea65f16fd385ca5c1746205c5bf566d814918499995b7bdf04e9ebb0a49810(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__96a16c69949077f0dfdc8c98833f8200ad76715cc69bd4b0ce1d772e23cf8734(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    apdex_index: jsii.Number,
    application_guid: builtins.str,
    browser_apdex_target: jsii.Number,
    metric_name: builtins.str,
    name: builtins.str,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
