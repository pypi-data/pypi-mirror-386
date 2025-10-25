import re
import json
from typing import Optional, Union

from multi_swe_bench.harness.image import Config, File, Image
from multi_swe_bench.harness.instance import Instance, TestResult
from multi_swe_bench.harness.pull_request import PullRequest


class ImageDefault(Image):
    def __init__(self, pr: PullRequest, config: Config):
        self._pr = pr
        self._config = config

    @property
    def pr(self) -> PullRequest:
        return self._pr

    @property
    def config(self) -> Config:
        return self._config

    def dependency(self) -> str:
        return "python:3.9-slim"

    def image_prefix(self) -> str:
        return "envagent"

    def image_tag(self) -> str:
        return f"pr-{self.pr.number}"

    def workdir(self) -> str:
        return f"pr-{self.pr.number}"

    def files(self) -> list[File]:
        repo_name = self.pr.repo
        return [
            File(
                ".",
                "fix.patch",
                f"{self.pr.fix_patch}",
            ),
            File(
                ".",
                "test.patch",
                f"{self.pr.test_patch}",
            ),
            File(
                ".",
                "prepare.sh",
                """ls
###ACTION_DELIMITER###
go version
###ACTION_DELIMITER###
apt-get update && apt-get install -y golang-go
###ACTION_DELIMITER###
go version
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
apt-get update && apt-get install -y yq
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
apt-get remove -y yq && wget https://github.com/mikefarah/yq/releases/download/v4.35.1/yq_linux_amd64 -O /usr/bin/yq && chmod +x /usr/bin/yq
###ACTION_DELIMITER###
apt-get update && apt-get install -y wget
###ACTION_DELIMITER###
wget https://github.com/mikefarah/yq/releases/download/v4.35.1/yq_linux_amd64 -O /usr/bin/yq && chmod +x /usr/bin/yq
###ACTION_DELIMITER###
yq --version
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
GOBIN=$(pwd)/bin go install sigs.k8s.io/kustomize/kustomize/v3@v3.8.7
###ACTION_DELIMITER###
wget https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv3.8.7/kustomize_v3.8.7_linux_amd64.tar.gz -O - | tar xz -C ./bin
###ACTION_DELIMITER###
./bin/kustomize version
###ACTION_DELIMITER###
make test
###ACTION_DELIMITER###
export PATH=$(pwd)/bin:$PATH && make test
###ACTION_DELIMITER###
GOBIN=$(pwd)/bin go install sigs.k8s.io/controller-runtime/tools/setup-envtest@v0.11.0
###ACTION_DELIMITER###
apt-get remove -y golang-go && wget https://go.dev/dl/go1.24.0.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.24.0.linux-amd64.tar.gz && export PATH=$PATH:/usr/local/go/bin && go version
###ACTION_DELIMITER###
GOBIN=$(pwd)/bin go install sigs.k8s.io/controller-runtime/tools/setup-envtest@latest
###ACTION_DELIMITER###
./bin/setup-envtest version
###ACTION_DELIMITER###
export PATH=$(pwd)/bin:$PATH && make test
###ACTION_DELIMITER###
echo 'make test' > test_commands.sh
###ACTION_DELIMITER###
echo 'go test -v ./pkg/... ./cmd/...' > test_commands.sh
###ACTION_DELIMITER###
echo 'KUBEBUILDER_ASSETS="$(./bin/setup-envtest use 1.24 -p path)" go test -v ./pkg/... ./cmd/... -coverprofile coverage.out -coverpkg ./pkg/... ./cmd...' > test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
KUBEBUILDER_ASSETS="$(./bin/setup-envtest use 1.24 -p path)" go test -v ./pkg/... ./cmd/... -coverprofile coverage.out -coverpkg ./pkg/... ./cmd...

""".replace("[[REPO_NAME]]", repo_name),
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
KUBEBUILDER_ASSETS="$(./bin/setup-envtest use 1.24 -p path)" go test -v ./pkg/... ./cmd/... -coverprofile coverage.out -coverpkg ./pkg/... ./cmd...

""".replace("[[REPO_NAME]]", repo_name),
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
KUBEBUILDER_ASSETS="$(./bin/setup-envtest use 1.24 -p path)" go test -v ./pkg/... ./cmd/... -coverprofile coverage.out -coverpkg ./pkg/... ./cmd...

""".replace("[[REPO_NAME]]", repo_name),
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace [base image] with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.9-slim

## Set noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install basic requirements
# For example: RUN apt-get update && apt-get install -y git
# For example: RUN yum install -y git
# For example: RUN apk add --no-cache git
RUN apt-get update && apt-get install -y git

# Ensure bash is available
RUN if [ ! -f /bin/bash ]; then         if command -v apk >/dev/null 2>&1; then             apk add --no-cache bash;         elif command -v apt-get >/dev/null 2>&1; then             apt-get update && apt-get install -y bash;         elif command -v yum >/dev/null 2>&1; then             yum install -y bash;         else             exit 1;         fi     fi

WORKDIR /home/
COPY fix.patch /home/
COPY test.patch /home/
RUN git clone https://github.com/kserve/kserve.git /home/kserve

WORKDIR /home/kserve
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("kserve", "kserve_2848_to_2508")
class KSERVE_2848_TO_2508(Instance):
    def __init__(self, pr: PullRequest, config: Config, *args, **kwargs):
        super().__init__()
        self._pr = pr
        self._config = config

    @property
    def pr(self) -> PullRequest:
        return self._pr

    def dependency(self) -> Optional[Image]:
        return ImageDefault(self.pr, self._config)

    def run(self, run_cmd: str = "") -> str:
        if run_cmd:
            return run_cmd

        return "bash /home/run.sh"

    def test_patch_run(self, test_patch_run_cmd: str = "") -> str:
        if test_patch_run_cmd:
            return test_patch_run_cmd

        return "bash /home/test-run.sh"

    def fix_patch_run(self, fix_patch_run_cmd: str = "") -> str:
        if fix_patch_run_cmd:
            return fix_patch_run_cmd

        return "bash /home/fix-run.sh"

    def parse_log(self, log: str) -> TestResult:
        # Parse the log content and extract test execution results.
        passed_tests: set[str] = set()  # Tests that passed successfully
        failed_tests: set[str] = set()  # Tests that failed
        skipped_tests: set[str] = set()  # Tests that were skipped
        import re

        # Extract test statuses using regex
        passed_tests.update(re.findall(r"--- PASS: (\S+)", log))
        failed_tests.update(re.findall(r"--- FAIL: (\S+)", log))
        skipped_tests.update(re.findall(r"--- SKIP: (\S+)", log))
        parsed_results = {
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
        }

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
