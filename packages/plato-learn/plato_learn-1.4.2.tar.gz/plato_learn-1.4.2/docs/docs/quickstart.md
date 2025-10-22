# Quick Start

## Running Plato Directly Using `uv`

To start a federated learning training workload with only a configuration file, run `uv run [Python file] -c [configuration file] ...`. For example:

```bash
uv run plato.py -c configs/MNIST/fedavg_lenet5.toml
```

The following command-line parameters are supported:

- `-c`: the path to the configuration file to be used. The default is `config.toml` in the project's home directory.

- `-b`: the base path, to be used to contain all models, datasets, checkpoints, and results (defaults to `./runtime`).

- `-r`: resume a previously interrupted training session (only works correctly in synchronous training sessions).

- `--cpu`: use the CPU as the device only.

Datasets required by an example are downloaded automatically the first time it runs; subsequent executions reuse the cached copies stored under the chosen base path.

_Plato_ uses the TOML format for its configuration files to manage runtime configuration parameters. Example configuration files have been provided in the `configs/` directory.

In `examples/`, a number of federated learning algorithms have been included. To run them, just run the main Python program in each of the directories with a suitable configuration file. For example, to run the `basic` example located at `examples/basic/`, run the command:

```bash
uv run examples/basic/basic.py -c configs/MNIST/fedavg_lenet5.toml
```

## Using MLX as a Backend

Plato supports MLX as an alternative backend to PyTorch for Apple Silicon devices. To use MLX, first install the optional dependencies:

```bash
uv sync --extra mlx
```

Then configure your TOML file to use the MLX framework by setting `framework = "mlx"` in the relevant sections:

```toml
[trainer]
type = "mlx"
framework = "mlx"

[algorithm]
type = "mlx_fedavg"
framework = "mlx"

[parameters.model]
framework = "mlx"
```

A complete example configuration is available at `configs/MNIST/fedavg_lenet5_mlx.toml`. Run it with:

```bash
uv run plato.py -c configs/MNIST/fedavg_lenet5_mlx.toml
```

## Running Plato in a Docker Container

To build such a Docker image, use the provided `Dockerfile`:

```bash
docker build -t plato -f Dockerfile .
```

To run the docker image that was just built, use the command:

```bash
./dockerrun.sh
```

To remove all the containers after they are run, use the command:

```bash
docker rm $(docker ps -a -q)
```

To remove the `plato` Docker image, use the command:

```bash
docker rmi plato
```

The provided `Dockerfile` helps to build a Docker image running Ubuntu 24.04, with a virtual environment called `plato` pre-configured to run Plato.

## Running Plato in a Docker Container with GPU Support

First, the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) will need to be installed on the host machine. On Ubuntu 24.04, follow these steps:

1. Configure the production repository:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

2. Update the packages list from the repository:

```bash
sudo apt-get update
```

3. Install the NVIDIA Container Toolkit packages (where `1.17.8-1` is the latest version as of October 2025):

```bash
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.17.8-1
  sudo apt-get install -y \
      nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}
```

4. Configure the Docker runtime for GPU support:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
```

5. Restart Docker:

```bash
sudo systemctl restart docker
```

For more information about installing the NVIDIA Container Toolkit, refer to its [official documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

The following command can be used to verify that GPU access is available in Docker containers:

```bash
docker run --gpus all --rm nvidia/cuda:13.0.1-cudnn-devel-ubuntu24.04 nvidia-smi
```

This should output a table listing your GPUs, confirming that GPU access works.

The following command can be used to enter GPU-enabled Docker container with Plato built-in:

```bash
./dockerrun_gpu.sh
```

## Formatting the Code and Fixing Linter Errors

It is strongly recommended that new additions and revisions of the codebase conform to [Ruff](https://docs.astral.sh/ruff/)'s formatting and linter guidelines. To format the entire codebase automatically, run:

```bash
uvx ruff format
```

To fix all linter errors automatically, run:

```bash
uvx ruff check --fix
```
