# Getting Started

In `examples/`, we included a wide variety of examples that showed how federated learning algorithms in the research literature can be implemented using Plato by customizing the `client`, `server`, `algorithm`, and `trainer` classes.

### Dataset Preparation

When you run an example for the first time, Plato downloads the required datasets automatically before training begins. Depending on the dataset size and your connection speed, the first round may take a little longer while the assets are prepared.

Plato uses [uv](https://docs.astral.sh/uv/) for hierarchical dependency management. Example-specific packages are defined in local `pyproject.toml` files rather than in the top-level directory.

To run an example with its dependencies, you need to run `uv sync` first in the top-level directory, navigate to the directory containing the example, and then use `uv run` to run the example.

!!! tip "Note"
    To make sure that all dependencies are properly loaded, always run `uv run` from within the directory containing the example.

Plato supports both Linux with NVIDIA GPUs and macOS with M1/M2/M4/M4 GPUs. It will automatically detect and use these GPUs when they are present.

---

## Algorithms Using Plato

- [Server Aggregation Algorithms](algorithms/1.%20Server%20Aggregation%20Algorithms.md)

- [Secure Aggregation with Homomorphic Encryption](algorithms/2.%20Secure%20Aggregation%20with%20Homomorphic%20Encryption.md)

- [Asynchronous Federated Learning Algorithms](algorithms/3.%20Asynchronous%20Federated%20Learning%20Algorithms.md)

- [Federated Unlearning](algorithms/4.%20Federated%20Unlearning.md)

- [Algorithms with Customized Client Training Loops](algorithms/5.%20Algorithms%20with%20Customized%20Client%20Training%20Loops.md)

- [Client Selection Algorithms](algorithms/6.%20Client%20Selection%20Algorithms.md)

- [Split Learning Algorithms](algorithms/7.%20Split%20Learning%20Algorithms.md)

- [Personalized Federated Learning Algorithms](algorithms/8.%20Personalized%20Federated%20Learning%20Algorithms.md)

- [Personalized Federated Learning Algorithms based on Self-Supervised Learning](algorithms/9.%20Personalized%20Federated%20Learning%20Algorithms%20based%20on%20Self-Supervised%20Learning.md)

- [Algorithms based on Neural Architecture Search and Model Search](algorithms/10.%20Algorithms%20based%20on%20Neural%20Architecture%20Search%20and%20Model%20Search.md)

- [Three-layer Federated Learning Algorithms](algorithms/11.%20Three-layer%20Federated%20Learning%20Algorithms.md)

- [Poisoning Detection Algorithms](algorithms/12.%20Poisoning%20Detection%20Algorithms.md)

- [Model Pruning Algorithms](algorithms/13.%20Model%20Pruning%20Algorithms.md)

## Case Studies

- [Federated LoRA Fine-Tuning](case-studies/1.%20LoRA.md)

- [Composable Trainer API](case-studies/2.%20Composable%20Trainer.md)
