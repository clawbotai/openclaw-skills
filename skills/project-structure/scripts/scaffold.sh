#!/usr/bin/env bash
# scaffold.sh — Create a new project from templates
# Usage: bash scaffold.sh <type> <name> [target-dir]
# Types: skill, node-app, python-app, ml-project, fullstack

set -euo pipefail


# --- Auto-injected by master-docs/inject-help.sh ---
show_help() {
    cat <<'ENDHELP'
NAME
    scaffold — scaffold.sh — Create a new project from templates Usage: bash scaffold.sh <type> <name> [target-dir] Types: skill, node-app, python-app, ml-project, fullstack

SYNOPSIS
    scaffold.sh [OPTIONS]

DESCRIPTION
    scaffold.sh — Create a new project from templates Usage: bash scaffold.sh <type> <name> [target-dir] Types: skill, node-app, python-app, ml-project, fullstack

OPTIONS
    -h, --help    Show this help message and exit

EXIT STATUS
    0   Success
    1   Error
ENDHELP
}

# Parse --help / -h flags
for arg in "$@"; do
    case "$arg" in
        -h|--help) show_help; exit 0 ;;
    esac
done
# --- End auto-injected help ---
TYPE="${1:-}"
NAME="${2:-}"
TARGET_DIR="${3:-.}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/../templates"

if [ -z "$TYPE" ] || [ -z "$NAME" ]; then
  echo "Usage: bash scaffold.sh <type> <name> [target-dir]"
  echo ""
  echo "Types:"
  echo "  skill        OpenClaw skill"
  echo "  node-app     Node.js/TypeScript application"
  echo "  python-app   Python application"
  echo "  go-app       Go application"
  echo "  ml-project   ML/AI project"
  echo "  fullstack    Full-stack web application"
  exit 1
fi

PROJECT_DIR="$TARGET_DIR/$NAME"

if [ -d "$PROJECT_DIR" ]; then
  echo "Error: $PROJECT_DIR already exists"
  exit 1
fi

echo "Creating $TYPE project: $NAME"
echo "Location: $PROJECT_DIR"
echo ""

mkdir -p "$PROJECT_DIR"

# --- Helper functions ---
create_file() {
  local path="$1"
  local content="$2"
  mkdir -p "$(dirname "$PROJECT_DIR/$path")"
  echo "$content" > "$PROJECT_DIR/$path"
}

create_gitignore_node() {
  cat > "$PROJECT_DIR/.gitignore" << 'EOF'
node_modules/
dist/
build/
.env
*.log
.DS_Store
coverage/
.turbo/
EOF
}

create_gitignore_python() {
  cat > "$PROJECT_DIR/.gitignore" << 'EOF'
__pycache__/
*.py[cod]
.venv/
venv/
.env
dist/
build/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
EOF
}

# --- Scaffold by type ---
case "$TYPE" in
  skill)
    SLUG="$NAME"
    create_file "SKILL.md" "# ${NAME}

> One-line description of what this skill does.

## Overview

Detailed explanation.

## Usage

How to use this skill.

## Examples

Concrete examples here.

## References

- Link to relevant docs
"

    cat > "$PROJECT_DIR/_meta.json" << EOF
{
  "slug": "$SLUG",
  "version": "0.1.0",
  "name": "$NAME",
  "description": "TODO: describe this skill",
  "tags": []
}
EOF

    mkdir -p "$PROJECT_DIR/scripts"
    mkdir -p "$PROJECT_DIR/references"
    echo "Created skill: $NAME"
    ;;

  node-app)
    mkdir -p "$PROJECT_DIR/src" "$PROJECT_DIR/tests" "$PROJECT_DIR/scripts" "$PROJECT_DIR/config"

    cat > "$PROJECT_DIR/package.json" << EOF
{
  "name": "$NAME",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "vitest"
  }
}
EOF

    cat > "$PROJECT_DIR/tsconfig.json" << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
EOF

    create_file "src/index.ts" "console.log('Hello from $NAME');"
    create_file ".env.example" "# Environment variables\n# NODE_ENV=development\n# PORT=3000"
    create_gitignore_node

    cat > "$PROJECT_DIR/README.md" << EOF
# $NAME

## Setup

\`\`\`bash
npm install
npm run dev
\`\`\`

## Scripts

- \`npm run dev\` — Development with hot reload
- \`npm run build\` — Production build
- \`npm test\` — Run tests
EOF
    echo "Created Node.js app: $NAME"
    ;;

  python-app)
    PACKAGE_NAME="${NAME//-/_}"
    mkdir -p "$PROJECT_DIR/src/$PACKAGE_NAME" "$PROJECT_DIR/tests" "$PROJECT_DIR/scripts" "$PROJECT_DIR/docs"

    cat > "$PROJECT_DIR/pyproject.toml" << EOF
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "$NAME"
version = "0.1.0"
description = "TODO: describe this project"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF

    create_file "src/$PACKAGE_NAME/__init__.py" ""
    create_file "src/$PACKAGE_NAME/main.py" "def main():\n    print('Hello from $NAME')\n\nif __name__ == '__main__':\n    main()"
    create_file "tests/__init__.py" ""
    create_file "tests/test_main.py" "from ${PACKAGE_NAME}.main import main\n\ndef test_main():\n    main()  # smoke test"
    create_file ".env.example" "# Environment variables"
    create_gitignore_python

    cat > "$PROJECT_DIR/README.md" << EOF
# $NAME

## Setup

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
\`\`\`

## Usage

\`\`\`bash
python -m ${PACKAGE_NAME}.main
\`\`\`

## Tests

\`\`\`bash
pytest
\`\`\`
EOF
    echo "Created Python app: $NAME"
    ;;

  ml-project)
    PACKAGE_NAME="${NAME//-/_}"
    mkdir -p "$PROJECT_DIR/src/$PACKAGE_NAME"/{data,models,features}
    mkdir -p "$PROJECT_DIR/"{tests,notebooks,data/{raw,processed},models,configs,scripts}

    cat > "$PROJECT_DIR/pyproject.toml" << EOF
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "$NAME"
version = "0.1.0"
description = "TODO: describe this ML project"
requires-python = ">=3.11"
dependencies = ["numpy", "pandas", "scikit-learn"]

[project.optional-dependencies]
dev = ["pytest", "ruff", "jupyter", "mypy"]

[tool.ruff]
line-length = 100
EOF

    create_file "src/$PACKAGE_NAME/__init__.py" ""
    create_file "src/$PACKAGE_NAME/train.py" "\"\"\"Training entry point.\"\"\"\n\ndef train():\n    print('Training $NAME')\n\nif __name__ == '__main__':\n    train()"
    create_file "src/$PACKAGE_NAME/predict.py" "\"\"\"Inference entry point.\"\"\"\n\ndef predict(input_data):\n    pass"
    create_file "src/$PACKAGE_NAME/evaluate.py" "\"\"\"Model evaluation.\"\"\"\n\ndef evaluate():\n    pass"
    create_file "src/$PACKAGE_NAME/data/loaders.py" "\"\"\"Data loading utilities.\"\"\""
    create_file "src/$PACKAGE_NAME/data/__init__.py" ""
    create_file "src/$PACKAGE_NAME/models/__init__.py" ""
    create_file "src/$PACKAGE_NAME/features/__init__.py" ""
    create_file "data/README.md" "# Data\n\nDescribe data sources, schema, and how to obtain data.\n\n## Raw\nOriginal immutable data.\n\n## Processed\nCleaned and transformed data."
    create_file "configs/experiment.yaml" "# Experiment configuration\nmodel:\n  type: baseline\n  params: {}\n\ntraining:\n  epochs: 10\n  batch_size: 32\n  learning_rate: 0.001"
    create_file "tests/__init__.py" ""
    create_gitignore_python
    # Append ML-specific ignores
    cat >> "$PROJECT_DIR/.gitignore" << 'EOF'
data/raw/
data/processed/
models/*.pkl
models/*.pt
models/*.h5
notebooks/.ipynb_checkpoints/
EOF

    cat > "$PROJECT_DIR/README.md" << EOF
# $NAME

## Setup

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
\`\`\`

## Training

\`\`\`bash
python -m ${PACKAGE_NAME}.train
\`\`\`

## Evaluation

\`\`\`bash
python -m ${PACKAGE_NAME}.evaluate
\`\`\`
EOF
    echo "Created ML project: $NAME"
    ;;

  go-app)
    MODULE_NAME="github.com/user/$NAME"
    mkdir -p "$PROJECT_DIR/cmd/$NAME" "$PROJECT_DIR/internal"/{handler,service,model} "$PROJECT_DIR/pkg" "$PROJECT_DIR/api" "$PROJECT_DIR/scripts" "$PROJECT_DIR/docs"

    cat > "$PROJECT_DIR/go.mod" << EOF
module $MODULE_NAME

go 1.22
EOF

    create_file "cmd/$NAME/main.go" "package main

import \"fmt\"

func main() {
	fmt.Println(\"Hello from $NAME\")
}"

    create_file "internal/handler/.gitkeep" ""
    create_file "internal/service/.gitkeep" ""
    create_file "internal/model/.gitkeep" ""

    cat > "$PROJECT_DIR/.gitignore" << 'EOF'
bin/
dist/
*.exe
*.test
*.out
.env
.DS_Store
vendor/
EOF

    cat > "$PROJECT_DIR/README.md" << EOF
# $NAME

## Setup

\`\`\`bash
go mod tidy
go run ./cmd/$NAME
\`\`\`

## Build

\`\`\`bash
go build -o bin/$NAME ./cmd/$NAME
\`\`\`

## Test

\`\`\`bash
go test ./...
\`\`\`
EOF
    echo "Created Go app: $NAME"
    ;;

  fullstack)
    mkdir -p "$PROJECT_DIR/apps/web/src" "$PROJECT_DIR/apps/api/src" "$PROJECT_DIR/packages/shared/src" "$PROJECT_DIR/scripts" "$PROJECT_DIR/infra/docker" "$PROJECT_DIR/docs"

    cat > "$PROJECT_DIR/package.json" << EOF
{
  "name": "$NAME",
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "scripts": {
    "dev": "npm run dev --workspaces",
    "build": "npm run build --workspaces",
    "test": "npm test --workspaces"
  }
}
EOF

    cat > "$PROJECT_DIR/apps/web/package.json" << EOF
{
  "name": "@$NAME/web",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "echo 'TODO: configure framework'",
    "build": "echo 'TODO: configure build'"
  }
}
EOF

    cat > "$PROJECT_DIR/apps/api/package.json" << EOF
{
  "name": "@$NAME/api",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc"
  }
}
EOF

    cat > "$PROJECT_DIR/packages/shared/package.json" << EOF
{
  "name": "@$NAME/shared",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc"
  }
}
EOF

    create_file "apps/web/src/index.ts" "// Web frontend entry"
    create_file "apps/api/src/index.ts" "console.log('API server starting');"
    create_file "packages/shared/src/index.ts" "// Shared utilities"
    create_file "infra/docker/Dockerfile" "FROM node:20-alpine\nWORKDIR /app\nCOPY . .\nRUN npm install\nCMD [\"npm\", \"start\"]"
    create_file ".env.example" "# Environment variables\n# DATABASE_URL=\n# API_PORT=3001"
    create_gitignore_node

    cat > "$PROJECT_DIR/README.md" << EOF
# $NAME

Full-stack application.

## Structure

- \`apps/web/\` — Frontend
- \`apps/api/\` — Backend API
- \`packages/shared/\` — Shared code
- \`infra/\` — Infrastructure

## Setup

\`\`\`bash
npm install
npm run dev
\`\`\`
EOF
    echo "Created fullstack project: $NAME"
    ;;

  *)
    echo "Unknown type: $TYPE"
    echo "Valid types: skill, node-app, python-app, ml-project, fullstack"
    exit 1
    ;;
esac

echo ""
echo "✓ Project scaffolded at: $PROJECT_DIR"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_DIR"
[ "$TYPE" != "skill" ] && echo "  git init"
echo "  # Start building!"
