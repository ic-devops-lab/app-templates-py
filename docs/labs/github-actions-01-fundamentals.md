# Lab: Github Actions CI: 01 Fundamentals

## Self-hosted runners and runner groups

For this lab will need
- 2 organization runners
- a runner group

Create a Runner Group:
- Github Organization → Settings → Actions → Runner groups → New runner group

Check [this runbook](https://github.com/ic-devops-lab/devops-labs/blob/main/GitHubSelfHostedRunners/runbook.md) to create a runner and run it as a service.

Use this command to register a runner at Organization Scope with created group:
```bash
export RUNNER_GROUP=my-runner-group
sudo -u "$RUNNER_USER" -H bash -lc "cd '$ORG_RUNNER_DIR' && ./config.sh --url $ORG_URL --token '$ORG_RUNNER_TOKEN' --name '$ORG_RUNNER_NAME --runnergroup $RUNNER_GROUP' --labels '$ORG_LABELS' --unattended"
```
Otherwise you need to move a new runner from a default group to the one you've just created.

Use [Runners Smoke Test](../../.github/workflows/runners-smoke-test.yaml) to verify runners.

---

## Basic Workflow

[workflow file](../../.github/workflows/gha-lab-ci-v1.yml)

Contains deliberately introduced dublications which will be eliminated later using reusable workflows and composite actions.

```yaml
on:	# Workflow triggers
  workflow_dispatch:	# Manual execution with parameters
    inputs:	# Runtime configuration
permissions: # Explicit token privileges
concurrency:	# Cancellation of superseded runs
env:	# Workflow-level environment variables
jobs:
  job:
    runs-on: # Runner selection
    needs: # Job dependencies
    steps:
      uses:	# Existing action invocation
        upload-artifact	# Persistence of build results
      run:	# Shell command execution
```

---

## Explore contexts and expressions

[workflow file](../../.github/workflows/gha-lab-demo-v1.yml)

GitHub Actions contexts are particularly important because they are used extensively in reusable workflows.

Let's add a diagnostic job to the workflow:
```yaml
  metadata:
    name: Workflow metadata
    runs-on: ubuntu-latest

    steps:
      - name: Show execution context
        env:
          REPOSITORY: ${{ github.repository }}
          REF: ${{ github.ref }}
          SHA: ${{ github.sha }}
          EVENT: ${{ github.event_name }}
          ACTOR: ${{ github.actor }}
          RUN_ID: ${{ github.run_id }}
          RUN_ATTEMPT: ${{ github.run_attempt }}
          RUNNER_OS: ${{ runner.os }}
          RUNNER_NAME: ${{ runner.name }}
        run: |
          echo "Repository: $REPOSITORY"
          echo "Ref: $REF"
          echo "Commit: $SHA"
          echo "Event: $EVENT"
          echo "Actor: $ACTOR"
          echo "Run ID: $RUN_ID"
          echo "Attempt: $RUN_ATTEMPT"
          echo "Runner OS: $RUNNER_OS"
          echo "Runner: $RUNNER_NAME"
```

The main contexts worth remembering:

| Context  | Contains |
| -------- | -------- |
| github   | Repository, event and workflow metadata |
| env      | Defined environment variables |
| vars     | Repository, organization and environment configuration variables |
| secrets  | Accessible secrets |
| inputs   | Workflow or action inputs, depending on context |
| runner   | Runner properties |
| job      | Current job information |
| steps    | Step outcomes and outputs |
| needs    | Dependency job results and outputs |
| matrix   | Current matrix configuration |
| strategy | Matrix execution metadata |

---

### Expression evaluation vs shell execution

This distinction is important for both troubleshooting and security.

```yaml
if: ${{ github.event_name == 'pull_request' }}
```
The expression is evaluated by GitHub Actions.

```yaml
run: echo "$GITHUB_SHA"
```
The variable is expanded by the shell on the runner.

Avoid directly interpolating untrusted event data into shell scripts.

For example, this is potentially vulnerable to script injection:
```yaml
run: echo "${{ github.event.pull_request.title }}"
```

Prefer passing the value through an environment variable:
```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: echo "$PR_TITLE"
```

---

## Step and job outputs

[workflow file](../../.github/workflows/gha-lab-demo-v2.yml)

This is something we'll need when implementing reusable workflows.

Add another experimental job:
```yaml
  prepare:
    name: Prepare build metadata
    runs-on: ubuntu-latest

    outputs:
      version: ${{ steps.version.outputs.value }}

    steps:
      - name: Generate version
        id: version
        run: |
          VERSION="0.1.0-${GITHUB_SHA::7}"
          echo "value=$VERSION" >> "$GITHUB_OUTPUT"
```

Then add a consumer job:
```yaml
  display-version:
    runs-on: ubuntu-latest
    needs: prepare

    steps:
      - name: Display version
        env:
          VERSION: ${{ needs.prepare.outputs.version }}
        run: echo "Build version is $VERSION"
```

```text
Job: prepare
  Step: version
    → Writes value to $GITHUB_OUTPUT
            ↓
    Step output: steps.version.outputs.value
            ↓
  Job output: outputs.version
            ↓
Dependent job: needs.prepare.uotputs.version
```
This mechanism becomes especially useful when a centralized build workflow needs to return an image tag, image digest, package version or release identifier to its caller.

---

## Matrix strategy

[workflow file](../../.github/workflows/gha-lab-ci-v2.yml)

The tests job has been modified to execute against two Python versions.

```yaml
tests:
  name: Tests (Python ${{ matrix.python-version }})
  ...
  strategy:
    fail-fast: false
    max-parallel: 2

    matrix:
      python-version:
        - "3.13"
        - "3.14"

  steps:
    ...
    - uses: astral-sh/setup-uv@v6
      with:
        python-version: ${{ matrix.python-version }}
    ...
```

---

## Test concurrency

We already defined:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Make two consecutive pushes while the first workflow is still running.

Observe whether the previous execution is cancelled.

- Cancel obsolete executions on feature branch CI or pull request validation.
- Usually avoid cancelling an active deployment on production deployment.
- Serialize competing deployments for shared deployment environment.

For release pipelines concurrency is not necessarily a strict FIFO deployment queue.

---
