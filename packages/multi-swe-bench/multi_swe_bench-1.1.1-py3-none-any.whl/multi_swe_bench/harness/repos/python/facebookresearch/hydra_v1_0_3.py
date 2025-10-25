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
        return "python:3.10-slim"

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
                """ls -al
###ACTION_DELIMITER###
ls -al requirements/
###ACTION_DELIMITER###
pip install -r requirements/dev.txt
###ACTION_DELIMITER###
echo 'pytest --no-header -rA --tb=no -p no:cacheprovider build_helpers tests' > /home/hydra/test_commands.sh
###ACTION_DELIMITER###
bash /home/hydra/test_commands.sh
###ACTION_DELIMITER###
echo 'pytest --no-header -rA --tb=no build_helpers tests' > /home/hydra/test_commands.sh
###ACTION_DELIMITER###
bash /home/hydra/test_commands.sh
###ACTION_DELIMITER###
python setup.py antlr
###ACTION_DELIMITER###
apt-get update && apt-get install -y default-jdk
###ACTION_DELIMITER###
python setup.py antlr
###ACTION_DELIMITER###
bash /home/hydra/test_commands.sh
###ACTION_DELIMITER###
pytest -v tests/test_config_repository.py
###ACTION_DELIMITER###
pip install importlib_resources
###ACTION_DELIMITER###
bash /home/hydra/test_commands.sh
###ACTION_DELIMITER###
pytest -v tests/test_examples/test_tutorials_basic.py
###ACTION_DELIMITER###
pip install 'pytest==7.4.4'
###ACTION_DELIMITER###
bash /home/hydra/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest --no-header -rA --tb=no build_helpers tests

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
pytest --no-header -rA --tb=no build_helpers tests

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
pytest --no-header -rA --tb=no build_helpers tests

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
FROM python:3.10-slim

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
RUN git clone https://github.com/facebookresearch/hydra.git /home/hydra

WORKDIR /home/hydra
RUN git reset --hard
RUN git checkout f386932ab13831467011eca3825f8c3578f5acdb

RUN git checkout {pr.base.sha}"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("facebookresearch", "hydra_v1_0_3")
class HYDRA_V1_0_3(Instance):
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
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        # Match lines like: PASSED tests/test_file.py::test_name
        passed_pattern = re.compile(r"^PASSED (.+)", re.MULTILINE)
        failed_pattern = re.compile(r"^FAILED (.+)", re.MULTILINE)
        # Match lines like: SKIPPED [N] tests/test_file.py:LINE: reason
        skipped_pattern = re.compile(r"^SKIPPED \[\d+\] ([^:]+):\d+", re.MULTILINE)
        # Match lines like: ERROR tests/test_file.py
        error_pattern = re.compile(r"^ERROR (.+)", re.MULTILINE)
        passed_tests.update(passed_pattern.findall(log))
        failed_tests.update(failed_pattern.findall(log))
        # For skipped, we only get file:line, not test name
        for match in skipped_pattern.findall(log):
            skipped_tests.add(match)
        # For errors, treat the file as a failed test (if not already in failed)
        for match in error_pattern.findall(log):
            failed_tests.add(match)

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
