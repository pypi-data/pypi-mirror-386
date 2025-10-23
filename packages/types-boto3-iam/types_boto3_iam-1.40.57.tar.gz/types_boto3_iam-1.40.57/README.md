<a id="types-boto3-iam"></a>

# types-boto3-iam

[![PyPI - types-boto3-iam](https://img.shields.io/pypi/v/types-boto3-iam.svg?color=blue)](https://pypi.org/project/types-boto3-iam/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/types-boto3-iam.svg?color=blue)](https://pypi.org/project/types-boto3-iam/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/types_boto3_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/types-boto3-iam)](https://pypistats.org/packages/types-boto3-iam)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 IAM 1.40.57](https://pypi.org/project/boto3/)
compatible with [VSCode](https://code.visualstudio.com/),
[PyCharm](https://www.jetbrains.com/pycharm/),
[Emacs](https://www.gnu.org/software/emacs/),
[Sublime Text](https://www.sublimetext.com/),
[mypy](https://github.com/python/mypy),
[pyright](https://github.com/microsoft/pyright) and other tools.

Generated with
[mypy-boto3-builder 8.11.0](https://github.com/youtype/mypy_boto3_builder).

More information can be found on
[types-boto3](https://pypi.org/project/types-boto3/) page and in
[types-boto3-iam docs](https://youtype.github.io/types_boto3_docs/types_boto3_iam/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [types-boto3-iam](#types-boto3-iam)
  - [How to install](#how-to-install)
    - [Generate locally (recommended)](<#generate-locally-(recommended)>)
    - [VSCode extension](#vscode-extension)
    - [From PyPI with pip](#from-pypi-with-pip)
  - [How to uninstall](#how-to-uninstall)
  - [Usage](#usage)
    - [VSCode](#vscode)
    - [PyCharm](#pycharm)
    - [Emacs](#emacs)
    - [Sublime Text](#sublime-text)
    - [Other IDEs](#other-ides)
    - [mypy](#mypy)
    - [pyright](#pyright)
    - [Pylint compatibility](#pylint-compatibility)
  - [Explicit type annotations](#explicit-type-annotations)
    - [Client annotations](#client-annotations)
    - [Paginators annotations](#paginators-annotations)
    - [Waiters annotations](#waiters-annotations)
    - [Service Resource annotations](#service-resource-annotations)
    - [Other resources annotations](#other-resources-annotations)
    - [Collections annotations](#collections-annotations)
    - [Literals](#literals)
    - [Type definitions](#type-definitions)
  - [How it works](#how-it-works)
  - [What's new](#what's-new)
    - [Implemented features](#implemented-features)
    - [Latest changes](#latest-changes)
  - [Versioning](#versioning)
  - [Thank you](#thank-you)
  - [Documentation](#documentation)
  - [Support and contributing](#support-and-contributing)

<a id="how-to-install"></a>

## How to install

<a id="generate-locally-(recommended)"></a>

### Generate locally (recommended)

You can generate type annotations for `boto3` package locally with
`mypy-boto3-builder`. Use
[uv](https://docs.astral.sh/uv/getting-started/installation/) for build
isolation.

1. Run mypy-boto3-builder in your package root directory:
   `uvx --with 'boto3==1.40.57' mypy-boto3-builder`
2. Select `boto3` AWS SDK.
3. Add `IAM` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `IAM`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `types-boto3` for `IAM` service.

```bash
# install with boto3 type annotations
python -m pip install 'types-boto3[iam]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'types-boto3-lite[iam]'

# standalone installation
python -m pip install types-boto3-iam
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y types-boto3-iam
```

<a id="usage"></a>

## Usage

<a id="vscode"></a>

### VSCode

- Install
  [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- Install
  [Pylance extension](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- Set `Pylance` as your Python Language Server
- Install `types-boto3[iam]` in your environment:

```bash
python -m pip install 'types-boto3[iam]'
```

Both type checking and code completion should now work. No explicit type
annotations required, write your `boto3` code as usual.

<a id="pycharm"></a>

### PyCharm

> ⚠️ Due to slow PyCharm performance on `Literal` overloads (issue
> [PY-40997](https://youtrack.jetbrains.com/issue/PY-40997)), it is recommended
> to use [types-boto3-lite](https://pypi.org/project/types-boto3-lite/) until
> the issue is resolved.

> ⚠️ If you experience slow performance and high CPU usage, try to disable
> `PyCharm` type checker and use [mypy](https://github.com/python/mypy) or
> [pyright](https://github.com/microsoft/pyright) instead.

> ⚠️ To continue using `PyCharm` type checker, you can try to replace
> `types-boto3` with
> [types-boto3-lite](https://pypi.org/project/types-boto3-lite/):

```bash
pip uninstall types-boto3
pip install types-boto3-lite
```

Install `types-boto3[iam]` in your environment:

```bash
python -m pip install 'types-boto3[iam]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `types-boto3` with services you use in your environment:

```bash
python -m pip install 'types-boto3[iam]'
```

- Install [use-package](https://github.com/jwiegley/use-package),
  [lsp](https://github.com/emacs-lsp/lsp-mode/),
  [company](https://github.com/company-mode/company-mode) and
  [flycheck](https://github.com/flycheck/flycheck) packages
- Install [lsp-pyright](https://github.com/emacs-lsp/lsp-pyright) package

```elisp
(use-package lsp-pyright
  :ensure t
  :hook (python-mode . (lambda ()
                          (require 'lsp-pyright)
                          (lsp)))  ; or lsp-deferred
  :init (when (executable-find "python3")
          (setq lsp-pyright-python-executable-cmd "python3"))
  )
```

- Make sure emacs uses the environment where you have installed `types-boto3`

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="sublime-text"></a>

### Sublime Text

- Install `types-boto3[iam]` with services you use in your environment:

```bash
python -m pip install 'types-boto3[iam]'
```

- Install [LSP-pyright](https://github.com/sublimelsp/LSP-pyright) package

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="other-ides"></a>

### Other IDEs

Not tested, but as long as your IDE supports `mypy` or `pyright`, everything
should work.

<a id="mypy"></a>

### mypy

- Install `mypy`: `python -m pip install mypy`
- Install `types-boto3[iam]` in your environment:

```bash
python -m pip install 'types-boto3[iam]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `types-boto3[iam]` in your environment:

```bash
python -m pip install 'types-boto3[iam]'
```

Optionally, you can install `types-boto3` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`types-boto3-iam` dependency in production. However, there is an issue in
`pylint` that it complains about undefined variables. To fix it, set all types
to `object` in non-`TYPE_CHECKING` mode.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_boto3_ec2 import EC2Client, EC2ServiceResource
    from types_boto3_ec2.waiters import BundleTaskCompleteWaiter
    from types_boto3_ec2.paginators import DescribeVolumesPaginator
else:
    EC2Client = object
    EC2ServiceResource = object
    BundleTaskCompleteWaiter = object
    DescribeVolumesPaginator = object

...
```

<a id="explicit-type-annotations"></a>

## Explicit type annotations

<a id="client-annotations"></a>

### Client annotations

`IAMClient` provides annotations for `boto3.client("iam")`.

```python
from boto3.session import Session

from types_boto3_iam import IAMClient

client: IAMClient = Session().client("iam")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`types_boto3_iam.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from types_boto3_iam import IAMClient
from types_boto3_iam.paginator import (
    GetAccountAuthorizationDetailsPaginator,
    GetGroupPaginator,
    ListAccessKeysPaginator,
    ListAccountAliasesPaginator,
    ListAttachedGroupPoliciesPaginator,
    ListAttachedRolePoliciesPaginator,
    ListAttachedUserPoliciesPaginator,
    ListEntitiesForPolicyPaginator,
    ListGroupPoliciesPaginator,
    ListGroupsForUserPaginator,
    ListGroupsPaginator,
    ListInstanceProfileTagsPaginator,
    ListInstanceProfilesForRolePaginator,
    ListInstanceProfilesPaginator,
    ListMFADeviceTagsPaginator,
    ListMFADevicesPaginator,
    ListOpenIDConnectProviderTagsPaginator,
    ListPoliciesPaginator,
    ListPolicyTagsPaginator,
    ListPolicyVersionsPaginator,
    ListRolePoliciesPaginator,
    ListRoleTagsPaginator,
    ListRolesPaginator,
    ListSAMLProviderTagsPaginator,
    ListSSHPublicKeysPaginator,
    ListServerCertificateTagsPaginator,
    ListServerCertificatesPaginator,
    ListSigningCertificatesPaginator,
    ListUserPoliciesPaginator,
    ListUserTagsPaginator,
    ListUsersPaginator,
    ListVirtualMFADevicesPaginator,
    SimulateCustomPolicyPaginator,
    SimulatePrincipalPolicyPaginator,
)

client: IAMClient = Session().client("iam")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
get_account_authorization_details_paginator: GetAccountAuthorizationDetailsPaginator = (
    client.get_paginator("get_account_authorization_details")
)
get_group_paginator: GetGroupPaginator = client.get_paginator("get_group")
list_access_keys_paginator: ListAccessKeysPaginator = client.get_paginator("list_access_keys")
list_account_aliases_paginator: ListAccountAliasesPaginator = client.get_paginator(
    "list_account_aliases"
)
list_attached_group_policies_paginator: ListAttachedGroupPoliciesPaginator = client.get_paginator(
    "list_attached_group_policies"
)
list_attached_role_policies_paginator: ListAttachedRolePoliciesPaginator = client.get_paginator(
    "list_attached_role_policies"
)
list_attached_user_policies_paginator: ListAttachedUserPoliciesPaginator = client.get_paginator(
    "list_attached_user_policies"
)
list_entities_for_policy_paginator: ListEntitiesForPolicyPaginator = client.get_paginator(
    "list_entities_for_policy"
)
list_group_policies_paginator: ListGroupPoliciesPaginator = client.get_paginator(
    "list_group_policies"
)
list_groups_for_user_paginator: ListGroupsForUserPaginator = client.get_paginator(
    "list_groups_for_user"
)
list_groups_paginator: ListGroupsPaginator = client.get_paginator("list_groups")
list_instance_profile_tags_paginator: ListInstanceProfileTagsPaginator = client.get_paginator(
    "list_instance_profile_tags"
)
list_instance_profiles_for_role_paginator: ListInstanceProfilesForRolePaginator = (
    client.get_paginator("list_instance_profiles_for_role")
)
list_instance_profiles_paginator: ListInstanceProfilesPaginator = client.get_paginator(
    "list_instance_profiles"
)
list_mfa_device_tags_paginator: ListMFADeviceTagsPaginator = client.get_paginator(
    "list_mfa_device_tags"
)
list_mfa_devices_paginator: ListMFADevicesPaginator = client.get_paginator("list_mfa_devices")
list_open_id_connect_provider_tags_paginator: ListOpenIDConnectProviderTagsPaginator = (
    client.get_paginator("list_open_id_connect_provider_tags")
)
list_policies_paginator: ListPoliciesPaginator = client.get_paginator("list_policies")
list_policy_tags_paginator: ListPolicyTagsPaginator = client.get_paginator("list_policy_tags")
list_policy_versions_paginator: ListPolicyVersionsPaginator = client.get_paginator(
    "list_policy_versions"
)
list_role_policies_paginator: ListRolePoliciesPaginator = client.get_paginator("list_role_policies")
list_role_tags_paginator: ListRoleTagsPaginator = client.get_paginator("list_role_tags")
list_roles_paginator: ListRolesPaginator = client.get_paginator("list_roles")
list_saml_provider_tags_paginator: ListSAMLProviderTagsPaginator = client.get_paginator(
    "list_saml_provider_tags"
)
list_ssh_public_keys_paginator: ListSSHPublicKeysPaginator = client.get_paginator(
    "list_ssh_public_keys"
)
list_server_certificate_tags_paginator: ListServerCertificateTagsPaginator = client.get_paginator(
    "list_server_certificate_tags"
)
list_server_certificates_paginator: ListServerCertificatesPaginator = client.get_paginator(
    "list_server_certificates"
)
list_signing_certificates_paginator: ListSigningCertificatesPaginator = client.get_paginator(
    "list_signing_certificates"
)
list_user_policies_paginator: ListUserPoliciesPaginator = client.get_paginator("list_user_policies")
list_user_tags_paginator: ListUserTagsPaginator = client.get_paginator("list_user_tags")
list_users_paginator: ListUsersPaginator = client.get_paginator("list_users")
list_virtual_mfa_devices_paginator: ListVirtualMFADevicesPaginator = client.get_paginator(
    "list_virtual_mfa_devices"
)
simulate_custom_policy_paginator: SimulateCustomPolicyPaginator = client.get_paginator(
    "simulate_custom_policy"
)
simulate_principal_policy_paginator: SimulatePrincipalPolicyPaginator = client.get_paginator(
    "simulate_principal_policy"
)
```

<a id="waiters-annotations"></a>

### Waiters annotations

`types_boto3_iam.waiter` module contains type annotations for all waiters.

```python
from boto3.session import Session

from types_boto3_iam import IAMClient
from types_boto3_iam.waiter import (
    InstanceProfileExistsWaiter,
    PolicyExistsWaiter,
    RoleExistsWaiter,
    UserExistsWaiter,
)

client: IAMClient = Session().client("iam")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
instance_profile_exists_waiter: InstanceProfileExistsWaiter = client.get_waiter(
    "instance_profile_exists"
)
policy_exists_waiter: PolicyExistsWaiter = client.get_waiter("policy_exists")
role_exists_waiter: RoleExistsWaiter = client.get_waiter("role_exists")
user_exists_waiter: UserExistsWaiter = client.get_waiter("user_exists")
```

<a id="service-resource-annotations"></a>

### Service Resource annotations

`IAMServiceResource` provides annotations for `boto3.resource("iam")`.

```python
from boto3.session import Session

from types_boto3_iam import IAMServiceResource

resource: IAMServiceResource = Session().resource("iam")

# now resource usage is checked by mypy and IDE should provide code completion
```

<a id="other-resources-annotations"></a>

### Other resources annotations

`types_boto3_iam.service_resource` module contains type annotations for all
resources.

```python
from boto3.session import Session

from types_boto3_iam import IAMServiceResource
from types_boto3_iam.service_resource import (
    AccessKey,
    AccessKeyPair,
    AccountPasswordPolicy,
    AccountSummary,
    AssumeRolePolicy,
    CurrentUser,
    Group,
    GroupPolicy,
    InstanceProfile,
    LoginProfile,
    MfaDevice,
    Policy,
    PolicyVersion,
    Role,
    RolePolicy,
    SamlProvider,
    ServerCertificate,
    SigningCertificate,
    User,
    UserPolicy,
    VirtualMfaDevice,
)

resource: IAMServiceResource = Session().resource("iam")

# Explicit type annotations are optional here
# Type should be correctly discovered by mypy and IDEs
my_access_key: AccessKey = resource.AccessKey(...)
my_access_key_pair: AccessKeyPair = resource.AccessKeyPair(...)
my_account_password_policy: AccountPasswordPolicy = resource.AccountPasswordPolicy(...)
my_account_summary: AccountSummary = resource.AccountSummary(...)
my_assume_role_policy: AssumeRolePolicy = resource.AssumeRolePolicy(...)
my_current_user: CurrentUser = resource.CurrentUser(...)
my_group: Group = resource.Group(...)
my_group_policy: GroupPolicy = resource.GroupPolicy(...)
my_instance_profile: InstanceProfile = resource.InstanceProfile(...)
my_login_profile: LoginProfile = resource.LoginProfile(...)
my_mfa_device: MfaDevice = resource.MfaDevice(...)
my_policy: Policy = resource.Policy(...)
my_policy_version: PolicyVersion = resource.PolicyVersion(...)
my_role: Role = resource.Role(...)
my_role_policy: RolePolicy = resource.RolePolicy(...)
my_saml_provider: SamlProvider = resource.SamlProvider(...)
my_server_certificate: ServerCertificate = resource.ServerCertificate(...)
my_signing_certificate: SigningCertificate = resource.SigningCertificate(...)
my_user: User = resource.User(...)
my_user_policy: UserPolicy = resource.UserPolicy(...)
my_virtual_mfa_device: VirtualMfaDevice = resource.VirtualMfaDevice(...)
```

<a id="collections-annotations"></a>

### Collections annotations

`types_boto3_iam.service_resource` module contains type annotations for all
`IAMServiceResource` collections.

```python
from boto3.session import Session

from types_boto3_iam import IAMServiceResource
from types_boto3_iam.service_resource import (
    ServiceResourceGroupsCollection,
    ServiceResourceInstanceProfilesCollection,
    ServiceResourcePoliciesCollection,
    ServiceResourceRolesCollection,
    ServiceResourceSamlProvidersCollection,
    ServiceResourceServerCertificatesCollection,
    ServiceResourceUsersCollection,
    ServiceResourceVirtualMfaDevicesCollection,
)

resource: IAMServiceResource = Session().resource("iam")

# Explicit type annotations are optional here
# Type should be correctly discovered by mypy and IDEs
groups: iam_resources.ServiceResourceGroupsCollection = resource.groups
instance_profiles: iam_resources.ServiceResourceInstanceProfilesCollection = (
    resource.instance_profiles
)
policies: iam_resources.ServiceResourcePoliciesCollection = resource.policies
roles: iam_resources.ServiceResourceRolesCollection = resource.roles
saml_providers: iam_resources.ServiceResourceSamlProvidersCollection = resource.saml_providers
server_certificates: iam_resources.ServiceResourceServerCertificatesCollection = (
    resource.server_certificates
)
users: iam_resources.ServiceResourceUsersCollection = resource.users
virtual_mfa_devices: iam_resources.ServiceResourceVirtualMfaDevicesCollection = (
    resource.virtual_mfa_devices
)
```

<a id="literals"></a>

### Literals

`types_boto3_iam.literals` module contains literals extracted from shapes that
can be used in user code for type checking.

Full list of `IAM` Literals can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_iam/literals/).

```python
from types_boto3_iam.literals import AccessAdvisorUsageGranularityTypeType


def check_value(value: AccessAdvisorUsageGranularityTypeType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`types_boto3_iam.type_defs` module contains structures and shapes assembled to
typed dictionaries and unions for additional type checking.

Full list of `IAM` TypeDefs can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_iam/type_defs/).

```python
# TypedDict usage example
from types_boto3_iam.type_defs import AccessDetailTypeDef


def get_value() -> AccessDetailTypeDef:
    return {
        "ServiceName": ...,
    }
```

<a id="how-it-works"></a>

## How it works

Fully automated
[mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder) carefully
generates type annotations for each service, patiently waiting for `boto3`
updates. It delivers drop-in type annotations for you and makes sure that:

- All available `boto3` services are covered.
- Each public class and method of every `boto3` service gets valid type
  annotations extracted from `botocore` schemas.
- Type annotations include up-to-date documentation.
- Link to documentation is provided for every method.
- Code is processed by [ruff](https://docs.astral.sh/ruff/) for readability.

<a id="what's-new"></a>

## What's new

<a id="implemented-features"></a>

### Implemented features

- Fully type annotated `boto3`, `botocore`, `aiobotocore` and `aioboto3`
  libraries
- `mypy`, `pyright`, `VSCode`, `PyCharm`, `Sublime Text` and `Emacs`
  compatibility
- `Client`, `ServiceResource`, `Resource`, `Waiter` `Paginator` type
  annotations for each service
- Generated `TypeDefs` for each service
- Generated `Literals` for each service
- Auto discovery of types for `boto3.client` and `boto3.resource` calls
- Auto discovery of types for `session.client` and `session.resource` calls
- Auto discovery of types for `client.get_waiter` and `client.get_paginator`
  calls
- Auto discovery of types for `ServiceResource` and `Resource` collections
- Auto discovery of types for `aiobotocore.Session.create_client` calls

<a id="latest-changes"></a>

### Latest changes

Builder changelog can be found in
[Releases](https://github.com/youtype/mypy_boto3_builder/releases).

<a id="versioning"></a>

## Versioning

`types-boto3-iam` version is the same as related `boto3` version and follows
[Python Packaging version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/).

<a id="thank-you"></a>

## Thank you

- [Allie Fitter](https://github.com/alliefitter) for
  [boto3-type-annotations](https://pypi.org/project/boto3-type-annotations/),
  this package is based on top of his work
- [black](https://github.com/psf/black) developers for an awesome formatting
  tool
- [Timothy Edmund Crosley](https://github.com/timothycrosley) for
  [isort](https://github.com/PyCQA/isort) and how flexible it is
- [mypy](https://github.com/python/mypy) developers for doing all dirty work
  for us
- [pyright](https://github.com/microsoft/pyright) team for the new era of typed
  Python

<a id="documentation"></a>

## Documentation

All services type annotations can be found in
[boto3 docs](https://youtype.github.io/types_boto3_docs/types_boto3_iam/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
