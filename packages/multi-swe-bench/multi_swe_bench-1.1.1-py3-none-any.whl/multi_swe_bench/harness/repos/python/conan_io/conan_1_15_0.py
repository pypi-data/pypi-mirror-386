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

    def dependency(self) -> str:
        return "python:3.5-slim"

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
                """ls -F
###ACTION_DELIMITER###
pip install -r conans/requirements_dev.txt
###ACTION_DELIMITER###
nosetests -A "not slow and not svn"
###ACTION_DELIMITER###
pip install patch
###ACTION_DELIMITER###
nosetests -A "not slow and not svn"
###ACTION_DELIMITER###
pip install colorama
###ACTION_DELIMITER###
nosetests -A "not slow and not svn"
###ACTION_DELIMITER###
pip install fasteners
###ACTION_DELIMITER###
nosetests -A "not slow and not svn"
###ACTION_DELIMITER###
pip install deprecation
###ACTION_DELIMITER###
nosetests -A "not slow and not svn"
###ACTION_DELIMITER###
pip install pyyaml
###ACTION_DELIMITER###
pip install -r conans/requirements.txt
###ACTION_DELIMITER###
pip install -r conans/requirements_server.txt
###ACTION_DELIMITER###
nosetests
###ACTION_DELIMITER###
pip install .
###ACTION_DELIMITER###

###ACTION_DELIMITER###
nosetests
###ACTION_DELIMITER###
apt-get install -y gcc
###ACTION_DELIMITER###
apt-get install -y meson ninja-build pkg-config
###ACTION_DELIMITER###

###ACTION_DELIMITER###
nosetests
###ACTION_DELIMITER###
echo 'nosetests --verbose -A "not slow and not svn"' > /home/conan/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
nosetests --verbose -A "not slow and not svn"

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
nosetests --verbose -A "not slow and not svn"

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
nosetests --verbose -A "not slow and not svn"

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
FROM python:3.5-slim

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
RUN git checkout a21899a3cded38650cf5c83d3177d1cdd5665114

RUN git checkout {pr.base.sha}"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("conan-io", "conan_1_15_0")
class CONAN_1_15_0(Instance):
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
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        test_statuses = {}
        test_pattern = re.compile(r"^(.*?) \(.*?\) \.\.\. (.*)$")
        for line in log.splitlines():
            match = test_pattern.match(line)
            if match:
                test_name = match.group(1).strip()
                status = match.group(2).strip()
                if test_name not in test_statuses:
                    test_statuses[test_name] = []
                test_statuses[test_name].append(status)
        for test_name, statuses in test_statuses.items():
            if "FAIL" in statuses or "ERROR" in statuses:
                failed_tests.add(test_name)
            elif "ok" in statuses:
                passed_tests.add(test_name)
            else:
                skipped_tests.add(test_name)

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
