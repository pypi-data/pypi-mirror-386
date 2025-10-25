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
                """ls -la
###ACTION_DELIMITER###
cat setup.cfg
###ACTION_DELIMITER###
cat tox.ini
###ACTION_DELIMITER###
ls -la test/unit
###ACTION_DELIMITER###
echo -e '#!/bin/bash
cd test/unit
pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
python -m pip install --upgrade pip && pip install -r .virtualenv.dev-requirements.txt
###ACTION_DELIMITER###
poetry install --all-extras
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
cd test/unit
PYTHONPATH=../.. pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
cd test/unit
 export PYTHONPATH=../../test
 export PYTHONUNBUFFERED=yes
 export WITH_COVERAGE=yes
 pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
cd test/unit
 export PYTHONPATH=../..
 export PYTHONUNBUFFERED=yes
 export WITH_COVERAGE=yes
 pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
cd test/unit
 export PYTHONPATH=../..
 export PYTHONUNBUFFERED=yes
 export WITH_COVERAGE=yes
 poetry run pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y xz-utils
###ACTION_DELIMITER###
pip install toml
###ACTION_DELIMITER###
poetry add toml
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
cd test/unit
 export PYTHONPATH=../..
 export PYTHONUNBUFFERED=yes
 export WITH_COVERAGE=yes
 poetry run pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc

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
cd test/unit
 export PYTHONPATH=../..
 export PYTHONUNBUFFERED=yes
 export WITH_COVERAGE=yes
 poetry run pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc

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
cd test/unit
 export PYTHONPATH=../..
 export PYTHONUNBUFFERED=yes
 export WITH_COVERAGE=yes
 poetry run pytest --verbose --doctest-modules --no-cov-on-fail --cov=kiwi --cov-report=term-missing --cov-fail-under=100 --cov-config .coveragerc

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
RUN git clone https://github.com/OSInside/kiwi.git /home/kiwi

WORKDIR /home/kiwi
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("OSInside", "kiwi_2637_to_2595")
class KIWI_2637_TO_2595(Instance):
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

        # Extract test cases using regex patterns
        # Pattern for PASSED tests: [line_num] test_name PASSED [percentage]
        passed_pattern = re.compile(r"\]\s+(.+?)\s+PASSED\s+\[")
        passed_tests = set(passed_pattern.findall(log))
        # Patterns for FAILED tests: individual lines and summary
        failed_pattern = re.compile(r"FAILED\s+([\w/]+\.py::[\w:]+)")
        failed_tests = set(failed_pattern.findall(log))
        # Pattern for SKIPPED tests: [line_num] test_name SKIPPED [percentage]
        skipped_pattern = re.compile(r"\[\s*\d+\]\s+(.+?)\s+SKIPPED\s+\[\s*\d+%\]")
        skipped_tests = set(skipped_pattern.findall(log))
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
