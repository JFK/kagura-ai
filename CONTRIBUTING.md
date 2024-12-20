# Contribution Guidelines

Thank you for your interest in contributing to **Kagura AI**! This project thrives on collaboration, and we are excited to have you involved. Below, you will find a comprehensive guide to help you contribute effectively.

---

## Purpose and Vision of Kagura AI

Kagura AI is inspired by the traditional Japanese art form Kagura (神楽), symbolizing harmony, connection, and respect. Just as Kagura integrates music, dance, and rituals, Kagura AI seeks to harmonize technology, data, and multi-agent systems. The project aims to:

- Build collaborative, ethical, and sustainable AI systems.
- Bridge the gap between cutting-edge AI technology and the values of humanity and nature.
- Foster innovation while honoring timeless principles of balance and respect.

By contributing to Kagura AI, you are helping to create a framework that combines technological advancement with social and environmental responsibility.

---

## How to Create an Issue

When creating an issue, please use the appropriate template:

- [Bug Report](https://github.com/JFK/kagura-ai/issues/new?template=bug_report.md): Report a bug in the project.
- [Feature Request](https://github.com/JFK/kagura-ai/issues/new?template=feature_request.md): Suggest a new feature or enhancement.
- [Task](https://github.com/JFK/kagura-ai/issues/new?template=task.md): Propose or track a specific task.
- [Documentation Improvement](https://github.com/JFK/kagura-ai/issues/new?template=documentation_improvement.md): Suggest improvements for the documentation.
- [Question](https://github.com/JFK/kagura-ai/issues/new?template=question.md): Ask a question about the project.

For beginners, check out the [Good First Issues](https://github.com/JFK/kagura-ai/issues?q=is%3Aopen+is%3Aissue+label%3A"good+first+issue") to get started.

---

## How to Contribute

1. **Check or Create an Issue**
   - Look for existing issues in the [Issues](https://github.com/JFK/kagura-ai/issues) section.
   - If none match your proposed contribution, create a new issue to describe it.

2. **Fork and Clone the Repository**
   - Fork this repository and clone it locally:
     ```bash
     git clone https://github.com/your-username/kagura-ai.git
     cd kagura-ai
     make sync
     ```

3. **Create a New Branch**
   - Create a branch for your changes:
     ```bash
     git checkout -b feature/your-feature-name
     ```

4. **Make Changes**
   - Edit the code, and verify your changes by running tests locally:
     ```bash
     make test
     ```

5. **Commit and Push**
   - Write clear commit messages:
     ```bash
     git add .
     git commit -m "Add feature: your-feature-name"
     git push origin feature/your-feature-name
     ```

6. **Submit a Pull Request**
   - Go to the [Pull Requests](https://github.com/JFK/kagura-ai/pulls) section and create a new PR.
   - Provide a detailed description of your changes and their purpose.

---

## Continuous Integration

GitHub Actions automatically checks contributions to ensure high-quality code. These checks include:

- **Code Formatting**: Ensures adherence to the project's style guidelines.
- **Unit Tests**: Verifies the correctness of the changes.
- **Coverage Reports**: Evaluates the code coverage to maintain high reliability.

Please ensure all tests pass locally before submitting a PR.

---

## Coding Standards

- **Style Guide**:
  - Follow [PEP 8](https://peps.python.org/pep-0008/).
    ```bash
    make ruff
    ```

- **Type Checking**:
  - Run `pyright` to check for type correctness:
    ```bash
    make right
    ```

---

## Testing

- Add unit tests for any new functionality.
- Run tests and check code coverage:
  ```bash
  make test
  ```

---

## Documentation

- Update `README.md` or the `docs/` directory for any changes in functionality or APIs.

### MkDocs Documentation

This document explains how Kagura AI uses MkDocs for documentation.

### Running the Local Server

To preview the documentation locally, use the following command:

```bash
uv run mkdocs serve
```

- [MkDocs Official Documentation](https://www.mkdocs.org/)
- [MkDocs Material Theme](https://squidfunk.github.io/mkdocs-material/)

---

## Pull Request Reviews

- Project maintainers will review your PR and provide feedback.
- Be prepared to address comments or suggestions to finalize your contribution.

---

## Frequently Asked Questions

### Why are tests required?
Tests ensure the stability and reliability of the codebase and help detect issues early.

### What types of issues should I create?
Feel free to report bugs, suggest new features, or propose documentation improvements.

---

## Additional Resources

- [Code of Conduct](./CODE_OF_CONDUCT.md): Learn about the behavior we expect in our community.
- [Contribution Guide](./CONTRIBUTING.md): This document.
- [Issues](https://github.com/JFK/kagura-ai/issues): Find existing issues to contribute to.

---

We deeply value your contributions and the time you invest in improving Kagura AI. Together, let’s create an innovative, ethical, and impactful AI framework. 😊
