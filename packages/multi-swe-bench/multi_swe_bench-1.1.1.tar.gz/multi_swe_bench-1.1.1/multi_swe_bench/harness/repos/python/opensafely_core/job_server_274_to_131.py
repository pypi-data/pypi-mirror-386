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
        return "ubuntu:latest"

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
                """ls -l
###ACTION_DELIMITER###
ls tests
###ACTION_DELIMITER###
apt-get update && apt-get install -y python3.8 python3.8-venv python3.8-dev
###ACTION_DELIMITER###
apt-get install -y software-properties-common
###ACTION_DELIMITER###
add-apt-repository -y ppa:deadsnakes/ppa
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y python3.8 python3.8-dev python3.8-venv
###ACTION_DELIMITER###
python3.8 -m venv venv
###ACTION_DELIMITER###
venv/bin/pip install --requirement requirements.txt
###ACTION_DELIMITER###
echo -e '#!/bin/bash\nexport DEBUG=1\nexport OPENSAFELY_JOB_SERVER_SECRET_KEY=12345\nexport SOCIAL_AUTH_GITHUB_KEY=foo\nexport SOCIAL_AUTH_GITHUB_SECRET=bar\nexport OPENSAFELY_QUEUE_USER=test\nexport OPENSAFELY_QUEUE_PASS=test\nexport GITHUB_TOKEN=dummy\nvenv/bin/python manage.py test --verbosity 2' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash\nexport DEBUG=1\nexport OPENSAFELY_JOB_SERVER_SECRET_KEY=12345\nexport SOCIAL_AUTH_GITHUB_KEY=foo\nexport SOCIAL_AUTH_GITHUB_SECRET=bar\nexport OPENSAFELY_QUEUE_USER=test\nexport OPENSAFELY_QUEUE_PASS=test\nexport GITHUB_TOKEN=dummy\nvenv/bin/pytest -v' > test_commands.sh && chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
export DEBUG=1
export OPENSAFELY_JOB_SERVER_SECRET_KEY=12345
export SOCIAL_AUTH_GITHUB_KEY=foo
export SOCIAL_AUTH_GITHUB_SECRET=bar
export OPENSAFELY_QUEUE_USER=test
export OPENSAFELY_QUEUE_PASS=test
export GITHUB_TOKEN=dummy
venv/bin/pytest -v

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
export DEBUG=1
export OPENSAFELY_JOB_SERVER_SECRET_KEY=12345
export SOCIAL_AUTH_GITHUB_KEY=foo
export SOCIAL_AUTH_GITHUB_SECRET=bar
export OPENSAFELY_QUEUE_USER=test
export OPENSAFELY_QUEUE_PASS=test
export GITHUB_TOKEN=dummy
venv/bin/pytest -v

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
export DEBUG=1
export OPENSAFELY_JOB_SERVER_SECRET_KEY=12345
export SOCIAL_AUTH_GITHUB_KEY=foo
export SOCIAL_AUTH_GITHUB_SECRET=bar
export OPENSAFELY_QUEUE_USER=test
export OPENSAFELY_QUEUE_PASS=test
export GITHUB_TOKEN=dummy
venv/bin/pytest -v

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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:latest with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:latest

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
RUN git clone https://github.com/opensafely-core/job-server.git /home/job-server

WORKDIR /home/job-server
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("opensafely-core", "job_server_274_to_131")
class JOB_SERVER_274_TO_131(Instance):
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
        import re

        # Pattern to match test lines with status
        pattern = r"^.*?(tests/[^:]+::[^ ]+)\s+(PASSED|FAILED|SKIPPED)\s+\[\s*\d+%\]"
        matches = re.finditer(pattern, log, re.MULTILINE)
        for match in matches:
            test_name = match.group(1)
            status = match.group(2)
            if status == "PASSED":
                passed_tests.add(test_name)
            elif status == "FAILED":
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
