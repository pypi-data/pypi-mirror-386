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
        return "python:3.8-slim"

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
ls -la requirements
###ACTION_DELIMITER###
python --version
###ACTION_DELIMITER###
nox --version
###ACTION_DELIMITER###
pip install -r requirements/dev.txt
###ACTION_DELIMITER###
nox -s omegaconf
###ACTION_DELIMITER###
sed -i 's/PyYAML>=5.1.*/PyYAML>=5.1/' requirements/base.txt
###ACTION_DELIMITER###
nox -s omegaconf
###ACTION_DELIMITER###
apt-get update && apt-get install -y default-jre
###ACTION_DELIMITER###
nox -s omegaconf
###ACTION_DELIMITER###
cat .nox/omegaconf-3-8/log.txt | grep -i error || true
###ACTION_DELIMITER###
pytest --no-header -rA --tb=no -p no:cacheprovider
###ACTION_DELIMITER###
python setup.py antlr
###ACTION_DELIMITER###
pytest --no-header -rA --tb=no -p no:cacheprovider
###ACTION_DELIMITER###
pytest --no-header -rA -p no:cacheprovider
###ACTION_DELIMITER###
sed -i 's/^pytest$/pytest<8.0.0/' requirements/dev.txt
###ACTION_DELIMITER###
pip install -r requirements/dev.txt
###ACTION_DELIMITER###
pytest --no-header -rA --tb=short -p no:cacheprovider
###ACTION_DELIMITER###
echo 'pytest --no-header -rA --tb=short -p no:cacheprovider' > /home/omegaconf/test_commands.sh
###ACTION_DELIMITER###
cat /home/omegaconf/test_commands.sh
###ACTION_DELIMITER###
chmod +x /home/omegaconf/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest --no-header -rA --tb=short -p no:cacheprovider

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
pytest --no-header -rA --tb=short -p no:cacheprovider

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
pytest --no-header -rA --tb=short -p no:cacheprovider

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
FROM python:3.8-slim

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
RUN git clone https://github.com/omry/omegaconf.git /home/omegaconf

WORKDIR /home/omegaconf
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("omry", "omegaconf_v2_1_0")
class OMEGACONF_V2_1_0(Instance):
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
        # Implement the log parsing logic here
        # Patterns for test results
        patterns = {
            "passed_tests": re.compile(r"^PASSED (.+)$", re.MULTILINE),
            "failed_tests": re.compile(r"^FAILED (.+)$", re.MULTILINE),
            "skipped_tests": re.compile(r"^SKIPPED (.+)$", re.MULTILINE),
        }
        for status, pattern in patterns.items():
            for match in pattern.findall(log):
                # Only extract the test name (remove extra info if present)
                test_name = match.strip()
                if status == "passed_tests":
                    passed_tests.add(test_name)
                elif status == "failed_tests":
                    failed_tests.add(test_name)
                elif status == "skipped_tests":
                    skipped_tests.add(test_name)
        # Optionally handle XFAIL/XPASS as failed/skipped if needed
        # xfail_pattern = re.compile(r'^XFAIL (.+)$', re.MULTILINE)
        # xpass_pattern = re.compile(r'^XPASS (.+)$', re.MULTILINE)
        # for match in xfail_pattern.findall(log):
        #     failed_tests.add(match.strip())
        # for match in xpass_pattern.findall(log):
        #     passed_tests.add(match.strip())

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
