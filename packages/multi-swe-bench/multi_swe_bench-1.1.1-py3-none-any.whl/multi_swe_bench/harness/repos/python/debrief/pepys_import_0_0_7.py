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
                """ls -F
###ACTION_DELIMITER###
sudo apt-get update && sudo apt-get install -y spatialite-bin libsqlite3-mod-spatialite
###ACTION_DELIMITER###
apt-get update && apt-get install -y spatialite-bin libsqlite3-mod-spatialite
###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
apt-get install -y libpq-dev python3-dev
###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
apt-get install -y gcc
###ACTION_DELIMITER###
pip install -r requirements.txt
###ACTION_DELIMITER###
apt-get install -y git
###ACTION_DELIMITER###
pip install -r requirements_dev.txt
###ACTION_DELIMITER###
python setup.py test
###ACTION_DELIMITER###
apt-get install -y postgis
###ACTION_DELIMITER###
python setup.py test
###ACTION_DELIMITER###
service postgresql start
###ACTION_DELIMITER###
su - postgres -c "createuser pepys_admin"
###ACTION_DELIMITER###
su - postgres -c "createdb pepys"
###ACTION_DELIMITER###
cp default_config.ini my_config.ini
###ACTION_DELIMITER###
sed -i 's/db_type = sqlite/db_type = postgresql/' my_config.ini
###ACTION_DELIMITER###
sed -i 's/db_name = :memory:/db_name = pepys/' my_config.ini
###ACTION_DELIMITER###

###ACTION_DELIMITER###
sed -i 's/db_username =/db_username = pepys_admin/' my_config.ini
###ACTION_DELIMITER###
export PEPYS_CONFIG_FILE=my_config.ini && python setup.py test
###ACTION_DELIMITER###

###ACTION_DELIMITER###
ls -F tests/
###ACTION_DELIMITER###
echo "pytest --no-header -rA --tb=no -p no:cacheprovider" > /home/pepys-import/test_commands.sh
###ACTION_DELIMITER###
""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest --no-header -rA --tb=no -p no:cacheprovider

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
pytest --no-header -rA --tb=no -p no:cacheprovider

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
pytest --no-header -rA --tb=no -p no:cacheprovider

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
RUN git clone https://github.com/debrief/pepys-import.git /home/pepys-import

WORKDIR /home/pepys-import
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("debrief", "pepys-import_0_0_7")
class PEPYS_IMPORT_0_0_7(Instance):
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
        # TODO: Implement the parse_log function
        passed_regex = re.compile(r"^PASSED\s+(.*)$")
        failed_regex = re.compile(r"^FAILED\s+(.*)$")
        skipped_regex = re.compile(r"^SKIPPED.* (.*):.*$")
        xfailed_regex = re.compile(r"^XFAIL\s+(.*) - reason:.*$")
        error_regex = re.compile(r"^ERROR\s+(.*)$")
        for line in log.splitlines():
            passed_match = passed_regex.match(line)
            if passed_match:
                passed_tests.add(passed_match.group(1).strip())
                continue
            failed_match = failed_regex.match(line)
            if failed_match:
                failed_tests.add(failed_match.group(1).strip())
                continue
            skipped_match = skipped_regex.match(line)
            if skipped_match:
                skipped_tests.add(skipped_match.group(1).strip())
                continue
            xfailed_match = xfailed_regex.match(line)
            if xfailed_match:
                # Treat xfailed tests as passed, as they are expected to fail
                passed_tests.add(xfailed_match.group(1).strip())
                continue
            error_match = error_regex.match(line)
            if error_match:
                failed_tests.add(error_match.group(1).strip())

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
