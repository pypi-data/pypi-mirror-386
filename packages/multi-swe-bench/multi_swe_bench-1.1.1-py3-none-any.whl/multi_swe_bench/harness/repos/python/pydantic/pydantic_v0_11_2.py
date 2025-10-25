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
        return "python:3.7-slim"

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
make install
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make install
###ACTION_DELIMITER###
pip install -U attrs==18.1.0 coverage==4.5.1 flake8==3.5.0 isort==4.3.4 mypy==0.610 pycodestyle==2.3.1 pytest==3.6.2 pytest-cov==2.5.1 pytest-isort==0.2.0 pytest-mock==1.10.0 pytest-sugar==0.9.1
###ACTION_DELIMITER###
pip install -U -r requirements.txt
###ACTION_DELIMITER###
pip install -U devtools python-dateutil trafaret django djangorestframework toastedmarshmallow docutils==0.14 Pygments==2.2.0 Sphinx==1.7.5 sphinxcontrib-websupport==1.1.0 ujson==1.35 email-validator==1.0.3
###ACTION_DELIMITER###
apt-get install -y gcc
###ACTION_DELIMITER###
pip install -U ujson==1.35
###ACTION_DELIMITER###
pip install -U devtools python-dateutil trafaret django djangorestframework toastedmarshmallow docutils==0.14 Pygments==2.2.0 Sphinx==1.7.5 sphinxcontrib-websupport==1.1.0 email-validator==1.0.3
###ACTION_DELIMITER###
pip install -U .
###ACTION_DELIMITER###
echo 'pytest --cov=pydantic' > /home/pydantic/test_commands.sh
###ACTION_DELIMITER###
bash /home/pydantic/test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y devtools
###ACTION_DELIMITER###
bash /home/pydantic/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest --cov=pydantic

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
pytest --cov=pydantic

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
pytest --cov=pydantic

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
FROM python:3.7-slim

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
RUN git clone https://github.com/pydantic/pydantic.git /home/pydantic

WORKDIR /home/pydantic
RUN git reset --hard
RUN git checkout c31b8d671955384b31253ab2bf4d857a80ee0da0

RUN git checkout {pr.base.sha}"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pydantic", "pydantic_v0_11_2")
class PYDANTIC_V0_11_2(Instance):
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
        # Extract failed test names from the FAILURES section
        failure_pattern = re.compile(r"^_{5,}\s+([\w\d_]+)\s+_{5,}", re.MULTILINE)
        for match in failure_pattern.finditer(log):
            failed_tests.add(match.group(1))
        # Extract summary lines for file-level results
        summary_pattern = re.compile(r"^(tests/[^\s]+)\s+([.sF]+)", re.MULTILINE)
        for match in summary_pattern.finditer(log):
            filename = match.group(1)
            results = match.group(2)
            for idx, ch in enumerate(results):
                test_id = f"{filename}::{idx + 1}"
                if ch == ".":
                    passed_tests.add(test_id)
                elif ch == "s":
                    skipped_tests.add(test_id)
                elif ch == "F":
                    # Only add to failed_tests if not already in failed_tests (by function name)
                    # This is just for completeness; function names are preferred
                    pass
        # Note: Only function names for failed tests, file::index for passed/skipped

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
