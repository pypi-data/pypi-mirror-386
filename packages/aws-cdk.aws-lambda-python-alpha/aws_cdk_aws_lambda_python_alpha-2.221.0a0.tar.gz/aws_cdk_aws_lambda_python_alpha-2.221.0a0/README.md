# Amazon Lambda Python Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

This library provides constructs for Python Lambda functions.

To use this module, you will need to have Docker installed.

## Python Function

Define a `PythonFunction`:

```python
python.PythonFunction(self, "MyFunction",
    entry="/path/to/my/function",  # required
    runtime=Runtime.PYTHON_3_8,  # required
    index="my_index.py",  # optional, defaults to 'index.py'
    handler="my_exported_func"
)
```

All other properties of `lambda.Function` are supported, see also the [AWS Lambda construct library](https://github.com/aws/aws-cdk/tree/main/packages/aws-cdk-lib/aws-lambda).

## Python Layer

You may create a python-based lambda layer with `PythonLayerVersion`. If `PythonLayerVersion` detects a `requirements.txt`
or `Pipfile` or `poetry.lock` with the associated `pyproject.toml` at the entry path, then `PythonLayerVersion` will include the dependencies inline with your code in the
layer.

Define a `PythonLayerVersion`:

```python
python.PythonLayerVersion(self, "MyLayer",
    entry="/path/to/my/layer"
)
```

A layer can also be used as a part of a `PythonFunction`:

```python
python.PythonFunction(self, "MyFunction",
    entry="/path/to/my/function",
    runtime=Runtime.PYTHON_3_8,
    layers=[
        python.PythonLayerVersion(self, "MyLayer",
            entry="/path/to/my/layer"
        )
    ]
)
```

## Packaging

If `requirements.txt`, `Pipfile`, `uv.lock` or `poetry.lock` exists at the entry path, the construct will handle installing all required modules in a [Lambda compatible Docker container](https://gallery.ecr.aws/sam/build-python3.13) according to the `runtime` and with the Docker platform based on the target architecture of the Lambda function.

Python bundles are only recreated and published when a file in a source directory has changed.
Therefore (and as a general best-practice), it is highly recommended to commit a lockfile with a
list of all transitive dependencies and their exact versions. This will ensure that when any dependency version is updated, the bundle asset is recreated and uploaded.

To that end, we recommend using [`pipenv`], [`uv`] or [`poetry`] which have lockfile support.

* [`pipenv`](https://pipenv-fork.readthedocs.io/en/latest/basics.html#example-pipfile-lock)
* [`poetry`](https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control)
* [`uv`](https://docs.astral.sh/uv/concepts/projects/sync/#exporting-the-lockfile)

Packaging is executed using the `Packaging` class, which:

1. Infers the packaging type based on the files present.
2. If it sees a `Pipfile`, `uv.lock` or a `poetry.lock` file, it exports it to a compatible `requirements.txt` file with credentials (if they're available in the source files or in the bundling container).
3. Installs dependencies using `pip` or `uv`.
4. Copies the dependencies into an asset that is bundled for the Lambda package.

**Lambda with a requirements.txt**

```plaintext
.
├── lambda_function.py # exports a function named 'handler'
├── requirements.txt # has to be present at the entry path
```

**Lambda with a Pipfile**

```plaintext
.
├── lambda_function.py # exports a function named 'handler'
├── Pipfile # has to be present at the entry path
├── Pipfile.lock # your lock file
```

**Lambda with a poetry.lock**

```plaintext
.
├── lambda_function.py # exports a function named 'handler'
├── pyproject.toml # your poetry project definition
├── poetry.lock # your poetry lock file has to be present at the entry path
```

**Lambda with a uv.lock**

Reference: https://docs.astral.sh/uv/concepts/projects/layout/

```plaintext
.
├── lambda_function.py # exports a function named 'handler'
├── pyproject.toml # your poetry project definition
├── uv.lock # your uv lock file has to be present at the entry path
├── .python-version # this file is ignored, python version is configured via Runtime
```

**Excluding source files**

You can exclude files from being copied using the optional bundling string array parameter `assetExcludes`:

```python
python.PythonFunction(self, "function",
    entry="/path/to/poetry-function",
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        # translates to `rsync --exclude='.venv'`
        asset_excludes=[".venv"]
    )
)
```

**Including hashes**

You can include hashes in `poetry` using the optional boolean parameter `poetryIncludeHashes`:

```python
python.PythonFunction(self, "function",
    entry="/path/to/poetry-function",
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        poetry_include_hashes=True
    )
)
```

**Excluding URLs**

You can exclude URLs in `poetry` using the optional boolean parameter `poetryWithoutUrls`:

```python
python.PythonFunction(self, "function",
    entry="/path/to/poetry-function",
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        poetry_without_urls=True
    )
)
```

## Custom Bundling

Custom bundling can be performed by passing in additional build arguments that point to index URLs to private repos, or by using an entirely custom Docker images for bundling dependencies. The build args currently supported are:

* `PIP_INDEX_URL`
* `PIP_EXTRA_INDEX_URL`
* `HTTPS_PROXY`

Additional build args for bundling that refer to PyPI indexes can be specified as:

```python
entry = "/path/to/function"
image = DockerImage.from_build(entry)

python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        build_args={"PIP_INDEX_URL": "https://your.index.url/simple/", "PIP_EXTRA_INDEX_URL": "https://your.extra-index.url/simple/"}
    )
)
```

If using a custom Docker image for bundling, the dependencies are installed with `pip`, `pipenv` or `poetry` by using the `Packaging` class. A different bundling Docker image that is in the same directory as the function can be specified as:

```python
entry = "/path/to/function"
image = DockerImage.from_build(entry)

python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(image=image)
)
```

You can set additional Docker options to configure the build environment:

```python
entry = "/path/to/function"

python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        network="host",
        security_opt="no-new-privileges",
        user="user:group",
        volumes_from=["777f7dc92da7"],
        volumes=[DockerVolume(host_path="/host-path", container_path="/container-path")]
    )
)
```

## Custom Bundling with Code Artifact

To use a Code Artifact PyPI repo, the `PIP_INDEX_URL` for bundling the function can be customized (requires AWS CLI in the build environment):

```python
from child_process import exec_sync


entry = "/path/to/function"
image = DockerImage.from_build(entry)

domain = "my-domain"
domain_owner = "111122223333"
repo_name = "my_repo"
region = "us-east-1"
code_artifact_auth_token = exec_sync(f"aws codeartifact get-authorization-token --domain {domain} --domain-owner {domainOwner} --query authorizationToken --output text").to_string().trim()

index_url = f"https://aws:{codeArtifactAuthToken}@{domain}-{domainOwner}.d.codeartifact.{region}.amazonaws.com/pypi/{repoName}/simple/"

python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        environment={"PIP_INDEX_URL": index_url}
    )
)
```

The index URL or the token are only used during bundling and thus not included in the final asset. Setting only environment variable for `PIP_INDEX_URL` or `PIP_EXTRA_INDEX_URL` should work for accessing private Python repositories with `pip`, `pipenv` and `poetry` based dependencies.

If you also want to use the Code Artifact repo for building the base Docker image for bundling, use `buildArgs`. However, note that setting custom build args for bundling will force the base bundling image to be rebuilt every time (i.e. skip the Docker cache). Build args can be customized as:

```python
from child_process import exec_sync


entry = "/path/to/function"
image = DockerImage.from_build(entry)

domain = "my-domain"
domain_owner = "111122223333"
repo_name = "my_repo"
region = "us-east-1"
code_artifact_auth_token = exec_sync(f"aws codeartifact get-authorization-token --domain {domain} --domain-owner {domainOwner} --query authorizationToken --output text").to_string().trim()

index_url = f"https://aws:{codeArtifactAuthToken}@{domain}-{domainOwner}.d.codeartifact.{region}.amazonaws.com/pypi/{repoName}/simple/"

python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        build_args={"PIP_INDEX_URL": index_url}
    )
)
```

## Command hooks

It is  possible to run additional commands by specifying the `commandHooks` prop:

```python
entry = "/path/to/function"
python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        command_hooks={
            # run tests
            def before_bundling(self, input_dir):
                return ["pytest"],
            def after_bundling(self, input_dir):
                return ["pylint"]
        }
    )
)
```

The following hooks are available:

* `beforeBundling`: runs before all bundling commands
* `afterBundling`: runs after all bundling commands

They all receive the directory containing the dependencies file (`inputDir`) and the
directory where the bundled asset will be output (`outputDir`). They must return
an array of commands to run. Commands are chained with `&&`.

The commands will run in the environment in which bundling occurs: inside the
container for Docker bundling or on the host OS for local bundling.

## Docker based bundling in complex Docker configurations

By default the input and output of Docker based bundling is handled via bind mounts.
In situations where this does not work, like Docker-in-Docker setups or when using a remote Docker socket, you can configure an alternative, but slower, variant that also works in these situations.

```python
entry = "/path/to/function"

python.PythonFunction(self, "function",
    entry=entry,
    runtime=Runtime.PYTHON_3_8,
    bundling=python.BundlingOptions(
        bundling_file_access=BundlingFileAccess.VOLUME_COPY
    )
)
```

## Troubleshooting

### Containerfile: no such file or directory

If you are on a Mac, using [Finch](https://github.com/runfinch/finch) instead of Docker, and see an error
like this:

```txt
lstat /private/var/folders/zx/d5wln9n10sn0tcj1v9798f1c0000gr/T/jsii-kernel-9VYgrO/node_modules/@aws-cdk/aws-lambda-python-alpha/lib/Containerfile: no such file or directory
```

That is a sign that your temporary directory has not been mapped into the Finch VM. Add the following to `~/.finch/finch.yaml`:

```yaml
additional_directories:
  - path: /private/var/folders/
  - path: /var/folders/
```

Then restart the Finch VM by running `finch vm stop && finch vm start`.
