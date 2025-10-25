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
                """apt-get update && apt-get install -y make build-essential
###ACTION_DELIMITER###
make dev-install
###ACTION_DELIMITER###
pip install -r dev_requirements.txt
###ACTION_DELIMITER###
echo 'pytest -v -rA --cov' > /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
cat /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
pip show jsonschema
###ACTION_DELIMITER###
pip install jsonschema==4.17.3
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
pip show qutip
###ACTION_DELIMITER###
pip install qutip==4.7.0
###ACTION_DELIMITER###
pip install qutip==4.7.1
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.23.5
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
pip install qutip==4.7.3
###ACTION_DELIMITER###
pip install scipy==1.7.3
###ACTION_DELIMITER###
pip install scipy==1.8.0 numpy==1.23.5
###ACTION_DELIMITER###
pip install qutip==4.7.4
###ACTION_DELIMITER###
pip install scipy==1.7.3
###ACTION_DELIMITER###
pip install numpy==1.23.5 scipy==1.8.0 qutip==4.7.4
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
pip install --upgrade pasqal-sdk
###ACTION_DELIMITER###
pip install pasqal-sdk==0.1.16
###ACTION_DELIMITER###
pip install pasqal-sdk==0.1.12
###ACTION_DELIMITER###
pip install pasqal-sdk==0.1.15
###ACTION_DELIMITER###
pip install pasqal-sdk==0.1.10
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
echo 'export PASQAL_CLIENT_ID=dummy
pytest -v -rA --cov' > /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
echo 'export PASQAL_CLIENT_ID=dummy
export PASQAL_CLIENT_SECRET=dummy
pytest -v -rA --cov' > /home/Pulser/test_commands.sh
###ACTION_DELIMITER###
bash /home/Pulser/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
export PASQAL_CLIENT_ID=dummy
export PASQAL_CLIENT_SECRET=dummy
pytest -v -rA --cov

""".format(pr=self.pr),
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
if ! git -C /home/{pr.repo} apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
export PASQAL_CLIENT_ID=dummy
export PASQAL_CLIENT_SECRET=dummy
pytest -v -rA --cov

""".format(pr=self.pr),
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
if ! git -C /home/{pr.repo} apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
export PASQAL_CLIENT_ID=dummy
export PASQAL_CLIENT_SECRET=dummy
pytest -v -rA --cov

""".format(pr=self.pr),
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace python:3.9-slim with actual base image
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
RUN git clone https://github.com/pasqal-io/Pulser.git /home/Pulser

WORKDIR /home/Pulser
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pasqal-io", "Pulser_491_to_475")
class PULSER_491_TO_475(Instance):
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
        passed_tests = set[str]()  # Tests that passed successfully
        failed_tests = set[str]()  # Tests that failed
        skipped_tests = set[str]()  # Tests that were skipped
        import re

        # Regex pattern to match test lines with status
        pattern = re.compile(
            r"^(?:\[\s*\d+\s*\]\s*)?"  # Optional line number
            r"(?:(\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)|(PASSED|FAILED|ERROR|SKIPPED)\s+(\S+))"  # Test + status or status + test
            r"(?:\s+\[.+\]|\s*-.*)?$"  # Optional [percentage] or error message
        )
        for line in log.split("\n"):
            line = line.strip()
            match = pattern.match(line)
            if match:
                # Extract test name and status
                if match.group(1) and match.group(2):
                    test_name = match.group(1)
                    status = match.group(2)
                elif match.group(3) and match.group(4):
                    test_name = match.group(4)
                    status = match.group(3)
                else:
                    continue  # No valid groups
                # Categorize the test based on status
                if status == "PASSED":
                    passed_tests.add(test_name)
                elif status in ("FAILED", "ERROR"):
                    failed_tests.add(test_name)
                elif status == "SKIPPED":
                    skipped_tests.add(test_name)
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
