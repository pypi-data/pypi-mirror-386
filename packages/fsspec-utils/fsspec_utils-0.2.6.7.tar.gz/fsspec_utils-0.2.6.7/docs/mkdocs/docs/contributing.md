# Contributing to fsspec-utils

We welcome contributions to `fsspec-utils`! Your help makes this project better. This guide outlines how you can contribute, from reporting issues to submitting pull requests.

## How to Contribute

### Reporting Issues

If you encounter any bugs, unexpected behavior, or have suggestions for new features, please open an issue on our [GitHub Issues page](https://github.com/fsspec/fsspec-utils/issues).

When reporting an issue, please include:
- A clear and concise description of the problem.
- Steps to reproduce the behavior.
- Expected behavior.
- Screenshots or error messages if applicable.
- Your `fsspec-utils` version and Python environment details.

### Submitting Pull Requests

We gladly accept pull requests for bug fixes, new features, and improvements. To submit a pull request:

1.  **Fork the Repository**: Start by forking the `fsspec-utils` repository on GitHub.
2.  **Clone Your Fork**: Clone your forked repository to your local machine.
    ```bash
    git clone https://github.com/your-username/fsspec-utils.git
    cd fsspec-utils
    ```
3.  **Create a New Branch**: Create a new branch for your changes.
    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b bugfix/issue-description
    ```
4.  **Make Your Changes**: Implement your bug fix or feature.
5.  **Write Tests**: Ensure your changes are covered by appropriate unit tests.
6.  **Run Tests**: Verify all tests pass before submitting.
    ```bash
    uv run pytest
    ```
7.  **Format Code**: Ensure your code adheres to the project's style guidelines. The project uses `ruff` for linting and formatting.
    ```bash
    uv run ruff check . --fix
    uv run ruff format .
    ```
8.  **Commit Your Changes**: Write clear and concise commit messages.
    ```bash
    git commit -m "feat: Add new awesome feature"
    ```
9.  **Push to Your Fork**: Push your branch to your forked repository.
    ```bash
    git push origin feature/your-feature-name
    ```
10. **Open a Pull Request**: Go to the original `fsspec-utils` repository on GitHub and open a pull request from your new branch. Provide a detailed description of your changes.

## Development Setup

To set up your development environment, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/fsspec/fsspec-utils.git
    cd fsspec-utils
    ```
2.  **Install `uv`**:
    `fsspec-utils` uses `uv` for dependency management and running commands. If you don't have `uv` installed, you can install it via `pip`:
    ```bash
    pip install uv
    ```
3.  **Install Development Dependencies**:
    The project uses `uv` to manage dependencies. Install the `dev` dependency group which includes tools for testing, linting, and documentation generation.
    ```bash
    uv pip install -e ".[dev]"
    ```
    This command installs the project in editable mode (`-e`) and includes all development-related dependencies specified in `pyproject.toml` under the `[project.optional-dependencies] dev` section.

## Best Practices for Contributions

-   **Code Style**: Adhere to the existing code style. We use `ruff` for linting and formatting.
-   **Testing**: All new features and bug fixes should be accompanied by relevant unit tests.
-   **Documentation**: If your changes introduce new features or modify existing behavior, please update the documentation accordingly.
-   **Commit Messages**: Write descriptive commit messages that explain the purpose of your changes.
-   **Atomic Commits**: Try to keep your commits focused on a single logical change.
-   **Branch Naming**: Use clear and concise branch names (e.g., `feature/new-feature`, `bugfix/fix-issue-123`).