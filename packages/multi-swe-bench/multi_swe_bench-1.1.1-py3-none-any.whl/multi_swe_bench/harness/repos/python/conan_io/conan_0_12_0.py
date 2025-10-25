import re
from typing import Optional

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

    def dependency(self) -> Image | None:
        return "python:3.5-buster"

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
                """ls -la
###ACTION_DELIMITER###
ls -la conans
###ACTION_DELIMITER###
pip install -r conans/requirements_dev.txt
###ACTION_DELIMITER###
echo 'PYTHONPATH=$PYTHONPATH:$(pwd) nosetests --verbose' > test_commands.sh
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh
###ACTION_DELIMITER###
pip install pyyaml
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh
###ACTION_DELIMITER###
pip install patch
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh
###ACTION_DELIMITER###
pip install requests
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh
###ACTION_DELIMITER###
pip install colorama
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh
###ACTION_DELIMITER###

###ACTION_DELIMITER###
pip install pyjwt
###ACTION_DELIMITER###
pip install fasteners
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh
###ACTION_DELIMITER###
pip install bottle
###ACTION_DELIMITER###
bash /home/conan/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
PYTHONPATH=$PYTHONPATH:$(pwd) nosetests --verbose

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
PYTHONPATH=$PYTHONPATH:$(pwd) nosetests --verbose

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
PYTHONPATH=$PYTHONPATH:$(pwd) nosetests --verbose

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

# Choose an appropriate base image based on the project's requirements - replace [base image] with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.5-buster

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
RUN git clone https://github.com/conan-io/conan.git /home/conan

WORKDIR /home/conan
RUN git reset --hard
RUN git checkout 3eaafa1a2532f022d9ad2c6168222491349862d1

RUN git checkout {pr.base.sha}"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("conan-io", "conan_0_12_0")
class CONAN_0_12_0(Instance):
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
        # Track the most severe status for each test.
        # Severity order: fail/error > skipped > ok
        status_priority = {"fail": 3, "error": 3, "skipped": 2, "ok": 1}
        test_status = {}
        pattern = re.compile(
            r"^(.*?)(?:\s*\([^)]*\))?\s*\.\.\.\s*(ok|FAIL|ERROR|skipped)$",
            re.IGNORECASE,
        )
        for line in log.splitlines():
            match = pattern.match(line.strip())
            if match:
                test_name = match.group(1).strip()
                status = match.group(2).lower()
                prev_status = test_status.get(test_name)
                # Only update if this status is more severe
                if (
                    prev_status is None
                    or status_priority[status] > status_priority[prev_status]
                ):
                    test_status[test_name] = status
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        for test_name, status in test_status.items():
            if status == "ok":
                passed_tests.add(test_name)
            elif status in ("fail", "error"):
                failed_tests.add(test_name)
            elif status == "skipped":
                skipped_tests.add(test_name)

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
