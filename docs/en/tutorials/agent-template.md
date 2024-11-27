# Kagura AI Agent Template

You can create a new Kagura agent template using the `kagura create` command.

## Using PyPI (Recommended)
```bash
pip install kagura-ai
```

## Creating New Agent Template

1. Create project directory:
```bash
mkdir my-kagura-agent
cd my-kagura-agent
```

2. Initialize project with Kagura:
```bash
poetry init
# If you are using poetry
# poetry add kagura-ai
# or for development
# poetry add git+https://github.com/JFK/kagura-ai.git
```

3. Create agent template:
```bash
poetry run kagura create --name <agent_name> --description "<description>"
```
