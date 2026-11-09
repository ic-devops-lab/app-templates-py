# Some techniques to reduce vulnerabilities of the base image.

## Comparing base image versions and choosing a safer one

Example:
```bash
docker pull python:3.13-slim-bookworm
docker pull python:3.13-slim-trixie

echo -e "====   python:3.13-slim-bookworm scan results   ===\n" > tmp/base_image_compare.txt
trivy image --scanners vuln \
  --severity HIGH,CRITICAL \
  python:3.13-slim-bookworm \
  >> tmp/base_image_compare.txt

echo -e "\n\n\n====   python:3.13-slim-trixie scan results   ===\n" >> tmp/base_image_compare.txt
trivy image --scanners vuln \
  --severity HIGH,CRITICAL \
  python:3.13-slim-trixie \
  >> tmp/base_image_compare.txt
```

Analyzing results you can find that:
- Trixie eliminates both CRITICAL findings, although it actually has more HIGH findings than Bookworm (for the moment I've ran those scans)
- the five Python findings are present in both unmodified base images. They aren't introduced by our application
- Trixie also reports two zlib1g findings with available fixes, while many of the other HIGH findings have no fixed version listed

So we could proceed with Trixie as our runtime base, but not consider the security issue resolved yet. Removing two CRITICAL findings is meaningful, even though the total finding count increases.

---

## Rebuild using fresh base images

```bash
docker compose build --pull --no-cache app
docker compose run --rm app
make docker-scan
```

---

## Apply known fixed versions

For example, our Trixie report identifies:
- Installed: 1:1.3.dfsg+really1.3.1-1+b1
- Fixed: 1:1.3.dfsg+really1.3.1-1+deb13u1

We can try adding a targeted security upgrade to the runtime stage, before switching to the non-root user:
```Dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade zlib1g \
    && rm -rf /var/lib/apt/lists/*
```

If the fixed package is available in the configured repositories, this should address those findings.

---

## What about the remaining HIGH findings?

Before starting to suppress them individually there are two separate questions:
    1. Can we fix them? Many currently have no patched version available.
    2. Are they exploitable in our application? For example, vulnerabilities in privileged mount utilities may have limited relevance to a non-root Python application container, depending on how it is deployed.
For the next iteration, we may keep Trivy's full reporting but introduce a more practical CI policy based on fix availability and documented risk acceptance.

---

## Choosing Alpine base image and tuning our Dockerfile

Alpine Python image is a good candidate for us as it has just 5 high vulnerabilities, all related to Python.

There's an important clue: Trivy reports the five vulnerabilities under the generic Python target, while every application dependency under `/app/.venv` is clean.

| Package | Installed | Fixed version |
| --- | --- | --- |
| msgpack | 1.1.2 | 1.2.3 |
| setuptools | 70.3.0 | 78.1.1 |
| urllib3 | 2.7.0 | 2.8.0 |

These packages were also reported in the original Alpine base image, so they are not introduced by our application.

```bash
# Locate the packages
docker run --rm --entrypoint sh py-app-tmpl:dev -c '
find / -type d \( \
  -name "msgpack-*.dist-info" -o \
  -name "setuptools-*.dist-info" -o \
  -name "urllib3-*.dist-info" \
\) 2>/dev/null
'

# If no directories are found, the next step is to inspect Trivy's JSON report and determine exactly what evidence it used to identify these packages.
trivy image \
  --scanners vuln \
  --severity HIGH,CRITICAL \
  --format json \
  --output tmp/trivy-report.json \
  py-app-tmpl:dev

jq '.Results[] |
  select(.Vulnerabilities != null) |
  {
    Target,
    Type,
    Packages: [
      .Vulnerabilities[] |
      {PkgName, InstalledVersion, PkgPath, VulnerabilityID}
    ]
  }' tmp/trivy-report.json
# output looks like this
{
  "Target": "Python",
  "Type": "python-pkg",
  "Packages": [
    {
      "PkgName": "msgpack",
      "InstalledVersion": "1.1.2",
      "PkgPath": null,
      "VulnerabilityID": "CVE-2026-114613"
    },
    {
      "PkgName": "msgpack",
      "InstalledVersion": "1.1.2",
      "PkgPath": null,
      "VulnerabilityID": "GHSA-6v7p-g79w-8964"
    },
    {
      "PkgName": "setuptools",
      "InstalledVersion": "70.3.0",
      "PkgPath": null,
      "VulnerabilityID": "CVE-2025-47273"
    },
    {
      "PkgName": "urllib3",
      "InstalledVersion": "2.7.0",
      "PkgPath": null,
      "VulnerabilityID": "CVE-2026-97687"
    },
    {
      "PkgName": "urllib3",
      "InstalledVersion": "2.7.0",
      "PkgPath": null,
      "VulnerabilityID": "CVE-2026-97689"
    }
  ]
}
```

Verify the runtime packages
```bash
docker run --rm --entrypoint sh py-app-tmpl:dev -c '
find / -type d \( \
  -name "msgpack*" -o \
  -name "setuptools*" -o \
  -name "urllib3*" \
\) 2>/dev/null
'
/usr/local/lib/python3.13/site-packages/pip/_vendor/urllib3
/usr/local/lib/python3.13/site-packages/pip/_vendor/msgpack
/usr/local/lib/python3.13/site-packages/pip-26.2.2.dist-info/licenses/src/pip/_vendor/urllib3
/usr/local/lib/python3.13/site-packages/pip-26.2.2.dist-info/licenses/src/pip/_vendor/msgpack
```

We can narrow this down without modifying the Dockerfile by:
- Removing pip from the runtime image

---

## Final solution

We selected Python 3.13 on Alpine for both build and runtime stages.

Trivy initially reported five HIGH findings originating from
pip's vendored Python dependencies.

Removing pip from the runtime image eliminated these findings.

The resulting image:
- Builds successfully
- Runs the application as a non-root user
- Contains no uv or pip installation in the final filesystem
- Passes Trivy scanning for HIGH and CRITICAL vulnerabilities

This result applies to the image and vulnerability database
versions used during validation. Future rebuilds must be rescanned.

---
