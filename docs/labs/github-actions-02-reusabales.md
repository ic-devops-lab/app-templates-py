# Lab: Github Actions CI: 02 Reusable workflows and actions

## Architectural differences

GitHub Actions provides several mechanisms for CI/CD reuse.

|         Mechanism          |      Reusable workflow      |        Composite action        | Workflow template |
| -------------------------- | --------------------------- | ------------------------------ | ----------------- |
| Invoked at                 | Job level                   | Step level                     | Repository setup |
| Contains multiple jobs     | Yes                         | No                             | Yes |
| Selects runners            | Yes                         | No                             | Yes |
| Defines job dependencies   | Yes                         | No                             | Yes |
| Accepts inputs             | Yes                         | Yes                            | Not as a runtime interface |
| Supports secrets interface | Yes                         | No dedicated secrets interface | Standard workflow syntax |
| Centralized updates        | Yes, depending on reference | Yes, depending on reference    | No |
| Primary purpose            | Pipeline orchestration      | Reusable execution steps       | Initial workflow scaffolding |

---

## Target architecture

Workflow layer:
```text
Consumer workflow
      ↓
Workflow call
      ↓
Reusable workflow
      ↓
Return to consumer
      ↓
Consumer workflow
```
The consumer repository controls when the pipeline executes. The centralized repository controls how it executes.

Job layer:
```text
job:
  ...
  Composite action "PyProject Setup"
    - Checkout
    - Set up uv
    - Install project dependencies
  ...
```
The repeated sequence of Checkout → Set up uv → Install dependencies is an ideal candidate for our first composite action

---

## Prepare the centralized repository

Target directory structure:
```text
github-actions-shared-workflows/
├── .github/
│   └── workflows/
│       ├── python-ci.yml
│       └── secrets-demo.yml
├── actions/
│   └── python-setup/
│       └── action.yml
├── docs/
├── README.md
└── .gitignore
```

An important GitHub limitation: reusable workflows must reside directly in `.github/workflows/`. Nested directories are not supported.

If the repository is private, configure:

Settings → Actions → General → Access

Allow other repositories within your organization to consume its workflows, subject to GitHub's repository visibility rules.

For this lab, it's recommended keeping both repositories private while using persistent self-hosted runners.

---

## Implement the composite action

[reusable composite action file at centralized repository](https://github.com/ic-devops-lab/github-actions-shared-workflows/blob/main/actions/pyproject-setup/action.yml)

```yaml
# actions/pyproject-setup/action.yml
name: Python Project Setup
description: Checkout source code, configure uv and install dependencies

inputs:
  python-version:
    description: Python version to use
    required: false
    default: "3.13"

  install-dependencies:
    description: Whether to install project dependencies
    required: false
    default: "true"

  enable-cache:
    description: Whether to enable uv dependency caching
    required: false
    default: "false"

runs:
  using: composite

  steps:
    - name: Checkout
      uses: actions/checkout@v7
      with:
        persist-credentials: false

    - name: Set up uv
      uses: astral-sh/setup-uv@v7
      with:
        python-version: ${{ inputs.python-version }}
        enable-cache: ${{ inputs.enable-cache }}

    - name: Install dependencies
      if: ${{ inputs.install-dependencies == 'true' }}
      shell: bash
      run: uv sync --locked --all-extras
```

Configurable inputs
|        Input         |                         Purpose                         |
| -------------------- | ------------------------------------------------------- |
| python-version       | Support different Python versions                       |
| install-dependencies | Avoid unnecessary dependency installation in build jobs |
| enable-cache         | Allow caching without enabling it by default            |

Caching is disabled initially because of billing concerns. We will explore it separately later.

`persist-credentials: false` added because our CI jobs do not need to push anything back to the repository.

Things to notice:
- Composite actions do not use `on: workflow_call.`
- They use `runs.using: composite`.
- Inputs do not have a type property.
- Input values are treated as strings, including boolean-like values.
- Every run step must explicitly specify its shell.
- There is no `runs-on` configuration because the action executes on the calling job's runner.

---

## Implement the reusable workflow

[reusable workflow file at centralized repository](https://github.com/ic-devops-lab/github-actions-shared-workflows/blob/main/.github/workflows/python-ci.yaml)

```yaml
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-version:
        type: string
        required: false
        default: "3.13"

      runner-group:
        type: string
        required: false
        default: devops-lab-runners

      runner-label:
        type: string
        required: false
        default: docker

      run-quality-checks:
        type: boolean
        default: true

      run-tests:
        type: boolean
        default: true

      build-package:
        type: boolean
        default: true

      artifact-retention-days:
        type: number
        default: 3

    outputs:
      build-id:
        description: Generated build identifier
        value: ${{ jobs.build.outputs.build-id }}

permissions:
  contents: read

jobs:
  quality:
    name: Code quality
    if: ${{ inputs.run-quality-checks }}

    runs-on:
      group: ${{ inputs.runner-group }}
      labels: ${{ inputs.runner-label }}

    timeout-minutes: 10

    steps:
      - name: Prepare Python environment
        uses: ic-devops-lab/github-actions-shared-workflows/actions/pyproject-setup@main
        with:
          python-version: ${{ inputs.python-version }}

      - name: Ruff lint
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

      - name: Type check
        run: uv run mypy src

  tests:
    name: Unit tests
    if: ${{ inputs.run-tests }}

    runs-on:
      group: ${{ inputs.runner-group }}
      labels: ${{ inputs.runner-label }}

    timeout-minutes: 15

    steps:
      - name: Prepare Python environment
        uses: ic-devops-lab/github-actions-shared-workflows/actions/pyproject-setup@main
        with:
          python-version: ${{ inputs.python-version }}

      - name: Run tests
        run: uv run pytest

  build:
    name: Build package

    needs:
      - quality
      - tests

    if: >-
      ${{
        !cancelled() &&
        inputs.build-package &&
        (
          needs.quality.result == 'success' ||
          needs.quality.result == 'skipped'
        ) &&
        (
          needs.tests.result == 'success' ||
          needs.tests.result == 'skipped'
        )
      }}

    runs-on:
      group: ${{ inputs.runner-group }}
      labels: ${{ inputs.runner-label }}

    timeout-minutes: 10

    outputs:
      build-id: ${{ steps.metadata.outputs.build-id }}

    steps:
      - name: Prepare Python environment
        uses: ic-devops-lab/github-actions-shared-workflows/actions/pyproject-setup@main
        with:
          python-version: ${{ inputs.python-version }}
          install-dependencies: "false"

      - name: Generate build metadata
        id: metadata
        shell: bash
        run: |
          BUILD_ID="${GITHUB_SHA::7}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
          echo "build-id=$BUILD_ID" >> "$GITHUB_OUTPUT"

      - name: Build package
        run: uv build

      - name: Upload package
        uses: actions/upload-artifact@v4
        with:
          name: python-package-${{ steps.metadata.outputs.build-id }}
          path: dist/
          retention-days: ${{ inputs.artifact-retention-days }}
          if-no-files-found: error

```

---

### Important cross-repository nuance

You might be tempted to reference the composite action like this:
```yaml
uses: ./actions/python-setup
```

However, this will not work in our cross-repository architecture unless we separately make the shared repository available in the runner workspace.

A reusable workflow executes in the caller repository's context.

|                                 Reference                                 |              Resolution              |
| ------------------------------------------------------------------------- | ------------------------------------ |
| `./actions/python-setup`                                                  | Relative to the runner workspace     |
| `actions/checkout@v4`                                                     | External action repository           |
| `ic-devops-lab/github-actions-shared-workflows/actions/python-setup@main` | Explicit shared repository reference |

Therefore, we need the fully qualified reference in our reusable workflow.

---

### Important detail — Conditional job dependencies

Why the `build` job has a relatively complicated if expression?

Normally, if a job listed in needs is skipped or fails, dependent jobs are also skipped unless their condition explicitly allows execution.

Since we want quality checks and tests to be independently configurable, we need to handle skipped dependencies.

Conditions in the workflow:
- Run quality checks?
- Run tests?
- Build package?

---

## Implement the consumer workflow

[workflow file](../../.github/workflows/gha-lab-ci-v3.yml)

The caller job has neither `runs-on` nor `steps`.

A reusable workflow invocation is itself a job-level construct. The actual jobs and runner requirements are defined inside the called workflow.

Notice the boolean expressions. Using `inputs.run-tests || true would incorrectly override an explicitly supplied false value.

When `actions/checkout` executes inside the reusable workflow, it checks out the caller repository, not the repository containing the reusable workflow.

Self-hosted runner executes centralized instructions against consumer source code.

Similarly, runner access and the `GITHUB_TOKEN` are evaluated in the caller's context.

---

## Secrets propagation

1. [reusable workflow file at centralized repository](https://github.com/ic-devops-lab/github-actions-shared-workflows/blob/main/.github/workflows/secrets-demo.yml): a minimal reusable workflow to explore secret handling.

2. Create a dummy repository secret named `LAB_DEMO_TOKEN` in the consumer repository.

Github repository → Setting → Secrets and variables → Actions → Repository secrets → New repository secret

3. [secret demo workflow in the current repository](../../.github/workflows/secrets-demo.yml)

**Some key points**:
- Secrets are not automatically passed to reusable workflows.
- In nested workflows, secrets must be passed at each level.
- Token permissions can be maintained or reduced by called workflows, but not elevated beyond the caller's effective permissions.
- Environment secrets have special behavior and cannot be passed through `workflow_call` as an environment configuration.
- Secret masking in logs is not a security boundary.

---

## Workflow versioning

So far, we have referenced the centralized workflow using @main.

This is convenient during development but undesirable for production consumers.

Create the first release in the centralized repository:
```bash
git tag -a v1.0.0 -m "Initial reusable Python CI workflow"
git push origin v1.0.0

git tag v1
git push origin v1
```

Then modify the consumer:
```yaml
jobs:
  ci:
    uses: ic-devops-lab/github-actions-shared-workflows/.github/workflows/python-ci.yml@v1
```

**Versioning strategies**

|  Reference  |     Mutable     |       Recommended use        |
| ----------- | --------------- | ---------------------------- |
| @main       | Yes             | Development                  |
| @v1         | Yes             | Compatible automatic updates |
| @v1.0.0     | Technically yes | Controlled releases          |
| @commit-sha | No              | Strict supply-chain security |

**Central workflow release lifecycle**

Major-version tags move to compatible releases. Breaking changes require a new major version.

---
