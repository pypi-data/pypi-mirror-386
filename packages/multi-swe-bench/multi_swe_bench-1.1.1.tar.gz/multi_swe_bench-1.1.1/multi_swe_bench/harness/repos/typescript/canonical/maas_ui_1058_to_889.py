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
        return "ubuntu:latest"

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
                """ls -la
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y nodejs npm
###ACTION_DELIMITER###
npm install -g yarn
###ACTION_DELIMITER###
yarn install
###ACTION_DELIMITER###
apt-get install -y python3 && ln -s /usr/bin/python3 /usr/bin/python
###ACTION_DELIMITER###
ln -sf /usr/bin/python3 /usr/bin/python
###ACTION_DELIMITER###
yarn install
###ACTION_DELIMITER###
apt-get install -y python2 && export PYTHON=python2
###ACTION_DELIMITER###
echo -e '#!/bin/bash
if [[ "$1" == "-c" ]]; then
    shift
    cmd="$1"
    modified_cmd=$(echo "$cmd" | sed "s/print \(.*\)/print(\1)/g")
    exec python3 -c "$modified_cmd"
else
    exec python3 "$@"
fi' > /usr/local/bin/python_wrapper && chmod +x /usr/local/bin/python_wrapper && export PYTHON=/usr/local/bin/python_wrapper
###ACTION_DELIMITER###
PYTHON=/usr/local/bin/python_wrapper yarn install
###ACTION_DELIMITER###
echo -e '#!/bin/bash
if [[ "$1" == "-c" ]]; then
    shift
    cmd="$1"
    modified_cmd=$(echo "$cmd" | sed "s/print \(.*\);/print(\1);/g")
    exec python3 -c "$modified_cmd"
else
    exec python3 "$@"
fi' > /usr/local/bin/python_wrapper && chmod +x /usr/local/bin/python_wrapper
###ACTION_DELIMITER###
PYTHON=/usr/local/bin/python_wrapper yarn install
###ACTION_DELIMITER###
apt-get install -y build-essential
###ACTION_DELIMITER###
apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y python2.7 && ln -sf /usr/bin/python2.7 /usr/bin/python
###ACTION_DELIMITER###
apt-get install -y python2.7 && ln -sf /usr/bin/python2.7 /usr/bin/python
###ACTION_DELIMITER###
sed -i '/"private": true/a \  "resolutions": { "node-sass": "sass" },' package.json
###ACTION_DELIMITER###
yarn install
###ACTION_DELIMITER###
sed -i 's/"node-sass": "sass"/"node-sass": "npm:sass@^1.60.0"/' package.json
###ACTION_DELIMITER###
yarn install
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e

yarn test --verbose
 yarn test-cypress --verbose' > test_commands.sh && chmod +x test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
set -e

yarn test --verbose
 yarn test-cypress --verbose

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
#!/bin/bash
set -e

yarn test --verbose
 yarn test-cypress --verbose

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
#!/bin/bash
set -e

yarn test --verbose
 yarn test-cypress --verbose

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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:latest with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:latest

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
RUN git clone https://github.com/canonical/maas-ui.git /home/maas-ui

WORKDIR /home/maas-ui
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("canonical", "maas_ui_1058_to_889")
class MAAS_UI_1058_TO_889(Instance):
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
        passed_tests = set()  # Tests that passed successfully
        failed_tests = set()  # Tests that failed
        skipped_tests = set()  # Tests that were skipped
        import re

        # Extract test names using regex patterns
        passed_tests = set(re.findall(r"PASS\s+([^\s(]+)", log, re.MULTILINE))
        failed_tests = set(re.findall(r"\((src/[^:]+test\.js)", log, re.MULTILINE))
        skipped_tests = set(
            re.findall(
                r"(?:SKIP|SKIPPED)\s*[:-]?\s*([^\s(]+)",
                log,
                re.IGNORECASE | re.MULTILINE,
            )
        )
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
