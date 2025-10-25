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
        return "python:3.8-bullseye"

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
pip install -r requirements.txt
###ACTION_DELIMITER###
pip install -r requirements_dev.txt
###ACTION_DELIMITER###
coverage run -m unittest discover -v
###ACTION_DELIMITER###
apt-get update && apt-get install -y postgresql
###ACTION_DELIMITER###
apt-get install -y libspatialite-dev
###ACTION_DELIMITER###
coverage run -m unittest discover -v
###ACTION_DELIMITER###
pg_ctlcluster 13 main start
###ACTION_DELIMITER###
sudo -u postgres createuser --superuser-V
###ACTION_DELIMITER###
createuser --superuser postgres
###ACTION_DELIMITER###
find / -name mod_spatialite.so
###ACTION_DELIMITER###
find / -name mod_spatialite.so 2>/dev/null
###ACTION_DELIMITER###
dpkg -L libspatialite-dev
###ACTION_DELIMITER###
apt-get install -y libsqlite3-mod-spatialite
###ACTION_DELIMITER###

###ACTION_DELIMITER###
coverage run -m unittest discover -v
###ACTION_DELIMITER###
python setup.py test
###ACTION_DELIMITER###
ls -F
###ACTION_DELIMITER###
ls /usr/lib/x86_64-linux-gnu/mod_spatialite.so
###ACTION_DELIMITER###
ls tests/
###ACTION_DELIMITER###
echo "python setup.py test" > /home/pepys-import/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
python setup.py test

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
python setup.py test

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
python setup.py test

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
FROM python:3.8-bullseye

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
RUN git clone https://github.com/debrief/pepys-import.git /home/pepys-import

WORKDIR /home/pepys-import
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("debrief", "pepys-import_v0_0_2")
class PEPYS_IMPORT_V0_0_2(Instance):
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
        # TODO: Implement the parse_log function
        test_pattern = re.compile(
            r"^(\w+\s\(.*\)|test_\w+)\s\.\.\.\s(ok|FAIL|ERROR|skipped.*|expected failure)"
        )
        for line in log.splitlines():
            match = test_pattern.match(line)
            if match:
                test_name = match.group(1).strip()
                status = match.group(2).strip()
                if status == "ok":
                    passed_tests.add(test_name)
                elif status == "FAIL" or status == "ERROR":
                    failed_tests.add(test_name)
                elif status.startswith("skipped"):
                    skipped_tests.add(test_name)

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
