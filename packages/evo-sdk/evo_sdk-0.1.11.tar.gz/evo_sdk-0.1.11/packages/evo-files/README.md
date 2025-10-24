<p align="center"><a href="https://seequent.com" target="_blank"><picture><source media="(prefers-color-scheme: dark)" srcset="https://developer.seequent.com/img/seequent-logo-dark.svg" alt="Seequent logo" width="400" /><img src="https://developer.seequent.com/img/seequent-logo.svg" alt="Seequent logo" width="400" /></picture></a></p>
<p align="center">
    <a href="https://pypi.org/project/evo-files/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/evo-files" /></a>
    <a href="https://github.com/SeequentEvo/evo-python-sdk/actions/workflows/run-all-tests.yaml"><img src="https://github.com/SeequentEvo/evo-python-sdk/actions/workflows/run-all-tests.yaml/badge.svg" alt="" /></a>
</p>
<p align="center">
    <a href="https://developer.seequent.com/" target="_blank">Seequent Developer Portal</a>
    &bull; <a href="https://community.seequent.com/group/19-evo" target="_blank">Seequent Community</a>
    &bull; <a href="https://seequent.com" target="_blank">Seequent website</a>
</p>

# Evo File API Client

The File API provides the ability to manage files of any type or size, associated with your Evo workspace.
Enable your product with Evo connected workflows by integrating with the Seequent Evo File API. Most file
formats and sizes are accepted.

## Pre-requisites

* Python ^3.10
* An [application registered in Bentley](https://developer.bentley.com/register/?product=seequent-evo)

## Installation

```shell
pip install evo-files 
```

## Usage

To get up and running quickly with the Evo File SDK, start by configuring your
[environment and API connector](https://github.com/SeequentEvo/evo-python-sdk/blob/main/packages/evo-sdk-common/docs/quickstart.md).

You can then use the `FileAPIClient` to perform operations, for example:

```python
from evo.files import FileAPIClient

file_client = FileAPIClient(environment, connector)
files = await file_client.list_files()
```

For some interactive Jupyter notebook examples, see the [examples folder](docs/examples).

## Contributing

For instructions on contributing to the development of this library, please refer to the [evo-python-sdk documentation](https://github.com/seequentevo/evo-python-sdk).

## License

The Python SDK for Evo is open source and licensed under the [Apache 2.0 license.](./LICENSE.md).

Copyright © 2025 Bentley Systems, Incorporated.

Licensed under the Apache License, Version 2.0 (the "License").
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

