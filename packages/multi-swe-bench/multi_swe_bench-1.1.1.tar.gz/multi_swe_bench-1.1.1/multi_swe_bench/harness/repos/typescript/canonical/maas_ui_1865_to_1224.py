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
        return "node:20"

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
                """yarn install
###ACTION_DELIMITER###
apt-get update && apt-get install -y python3 python-is-python3
###ACTION_DELIMITER###
yarn install
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2.7 && export PYTHON=python2.7
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential
###ACTION_DELIMITER###
npm config set python python3 && yarn install
###ACTION_DELIMITER###
export PYTHON=python3 && yarn install
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2
###ACTION_DELIMITER###

###ACTION_DELIMITER###

###ACTION_DELIMITER###
sed -i 's/print "%s.%s.%s" % sys.version_info\[:3\];/print("%s.%s.%s" % sys.version_info[:3]);/' /home/maas-ui/node_modules/node-gyp/lib/configure.js
###ACTION_DELIMITER###
export PYTHON=python3 && yarn install
###ACTION_DELIMITER###
sed -i '451s/print "%s.%s.%s" %/print("%s.%s.%s" %/' /home/maas-ui/node_modules/node-gyp/lib/configure.js
###ACTION_DELIMITER###
sed -i '451s/print "%s.%s.%s" % sys.version_info\[:3\];/print("%s.%s.%s" % sys.version_info[:3]);/' /home/maas-ui/node_modules/node-gyp/lib/configure.js
###ACTION_DELIMITER###
sed -i 's/print "%s.%s.%s" % sys.version_info\[:3\];/print("%s.%s.%s" % sys.version_info[:3]);/' /home/maas-ui/node_modules/node-gyp/lib/configure.js && export PYTHON=python3 && yarn install
###ACTION_DELIMITER###
sed -i '451s/print /print(/' /home/maas-ui/node_modules/node-gyp/lib/configure.js && sed -i '451s/;/);/' /home/maas-ui/node_modules/node-gyp/lib/configure.js && export PYTHON=python3 && yarn install
###ACTION_DELIMITER###
yarn remove node-sass && yarn add sass && yarn install
###ACTION_DELIMITER###
yarn remove node-sass -W && yarn add sass -W && yarn install
###ACTION_DELIMITER###
find . -name 'package.json' -exec grep -H 'node-sass' {} +
###ACTION_DELIMITER###
cd proxy && yarn remove node-sass && cd ..
###ACTION_DELIMITER###
cd ../root && yarn remove node-sass && yarn add sass && cd ..
###ACTION_DELIMITER###
cd ../ui && yarn remove node-sass && yarn add sass && sed -i 's/node-sass/sass/g' package.json && cd ..
###ACTION_DELIMITER###
cd ../legacy && yarn remove node-sass && yarn add sass && sed -i 's/node-sass/sass/g' package.json && cd ..
###ACTION_DELIMITER###
echo 'yarn test --verbose' > /home/maas-ui/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
yarn test --verbose

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
yarn test --verbose

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
yarn test --verbose

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

# Choose an appropriate base image based on the project's requirements - replace node:20 with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM node:20

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
RUN git clone https://github.com/canonical/maas-ui.git /home/maas-ui

WORKDIR /home/maas-ui
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("canonical", "maas_ui_1865_to_1224")
class MAAS_UI_1865_TO_1224(Instance):
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
        import json

        # Extract passed tests
        passed_matches = re.findall(r"PASS\s+([^\s]+)", log)
        passed_tests = set(passed_matches)
        # Extract failed tests
        failed_matches = re.findall(r"FAIL\s+([^\s]+)", log)
        failed_tests = set(failed_matches)
        # Extract skipped tests
        skipped_matches = re.findall(r"SKIPPED\s+([^\s]+)", log, re.IGNORECASE)
        skipped_tests = set(skipped_matches)
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
