# Lab: Github Actions CI

## v1 Basic Workflow

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
