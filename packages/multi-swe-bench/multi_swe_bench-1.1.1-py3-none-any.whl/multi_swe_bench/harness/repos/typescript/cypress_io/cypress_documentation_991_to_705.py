import re

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
        return "node:20-bookworm"

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
                """npm install
###ACTION_DELIMITER###
apt-get update && apt-get install -y python3 make g++ python-is-python3
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2.7
###ACTION_DELIMITER###
bash -c 'echo "deb http://deb.debian.org/debian buster main" >> /etc/apt/sources.list && apt-get update && apt-get install -y python2.7 && sed -i "$ d" /etc/apt/sources.list && apt-get update'
###ACTION_DELIMITER###
bash -c 'apt-get install -y debian-archive-keyring && echo "deb http://deb.debian.org/debian oldstable main" >> /etc/apt/sources.list && apt-get update && apt-get install -y python2.7 && sed -i "$ d" /etc/apt/sources.list && apt-get update'
###ACTION_DELIMITER###
bash -c 'sed -i "/buster/d" /etc/apt/sources.list && echo "deb http://deb.debian.org/debian oldstable main" >> /etc/apt/sources.list && apt-get update && apt-get install -y python2.7 && sed -i "$ d" /etc/apt/sources.list && apt-get update && export PYTHON=/usr/bin/python2.7 && npm install'
###ACTION_DELIMITER###
bash -c 'sed -i "/oldstable/d; /buster/d" /etc/apt/sources.list && echo "deb http://deb.debian.org/debian oldstable main" >> /etc/apt/sources.list && apt-get update && apt-get install -y python2 && sed -i "$ d" /etc/apt/sources.list && apt-get update && export PYTHON=/usr/bin/python2 && npm install'
###ACTION_DELIMITER###
bash -c 'echo "deb http://archive.debian.org/debian buster main" >> /etc/apt/sources.list && apt-get update -o Acquire::Check-Valid-Until=false && apt-get install -y python2.7 && sed -i "$ d" /etc/apt/sources.list && apt-get update && export PYTHON=/usr/bin/python2.7 && npm install'
###ACTION_DELIMITER###
bash -c 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && source ~/.nvm/nvm.sh && nvm install 8.17.0 && nvm use 8.17.0 && npm install'
###ACTION_DELIMITER###
echo -e '#!/bin/bash
npm test -- --verbose
npx start-server-and-test start http://localhost:2222 "cypress run --verbose"' > /home/cypress-documentation/test_commands.sh
###ACTION_DELIMITER###
chmod +x /home/cypress-documentation/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
npm test -- --verbose
npx start-server-and-test start http://localhost:2222 "cypress run --verbose"

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
npm test -- --verbose
npx start-server-and-test start http://localhost:2222 "cypress run --verbose"

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
npm test -- --verbose
npx start-server-and-test start http://localhost:2222 "cypress run --verbose"

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
FROM node:20-bookworm

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
RUN git clone https://github.com/cypress-io/cypress-documentation.git /home/cypress-documentation

WORKDIR /home/cypress-documentation
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("cypress-io", "cypress_documentation_991_to_705")
class CYPRESS_DOCUMENTATION_991_TO_705(Instance):
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
        passed_tests: set[str] = set()
        failed_tests: set[str] = set()
        skipped_tests: set[str] = set()
        # Regex patterns for test statuses (adjust based on log patterns)
        # Passed tests: matches '✓ test_name (time)'
        passed_pattern = re.compile(
            r"✓\s+(.+?)\s+\(\d+ms\)",
        )
        # Failed tests: assume '✕' marker (adjust if logs use different symbols)
        failed_pattern = re.compile(
            r"✕\s+(.+?)\s+\(\d+ms\)",
        )
        # Skipped tests: assume 'SKIPPED' prefix (adjust based on logs)
        skipped_pattern = re.compile(
            r"SKIPPED\s+(.+)",
        )
        # Extract test names
        passed_tests.update(passed_pattern.findall(log))
        failed_tests.update(failed_pattern.findall(log))
        skipped_tests.update(skipped_pattern.findall(log))
        # Handle summary lines if individual tests aren't captured (fallback)
        # If no failed tests found, use summary count (placeholder logic)
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
