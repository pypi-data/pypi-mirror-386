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
        return "node:18"

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
npm install
###ACTION_DELIMITER###
npm install --legacy-peer-deps
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
rimraf lib esm
###ACTION_DELIMITER###
npm run clean
###ACTION_DELIMITER###
npm test
###ACTION_DELIMITER###
echo 'npm test -- --verbose --runInBand' > test_commands.sh
###ACTION_DELIMITER###
sed -i 's/"compilerOptions": {/"compilerOptions": {\n    "skipLibCheck": true,/' tsconfig.json
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
sed -i '/"runner": "jest-electron\/runner",/d' package.json && sed -i '/"testEnvironment": "jest-electron\/environment",/d' package.json
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl
###ACTION_DELIMITER###
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
###ACTION_DELIMITER###
source $HOME/.nvm/nvm.sh
###ACTION_DELIMITER###
nvm install 20 && nvm use 20
###ACTION_DELIMITER###
npm install --legacy-peer-deps
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
sed -i 's/"compilerOptions": {/"compilerOptions": {\n    "skipLibCheck": true,\n    "suppressImplicitAnyIndexErrors": true,\n    "strictNullChecks": false,/' tsconfig.json
###ACTION_DELIMITER###
sed -i '/"compilerOptions": {/a\    "baseUrl": ".",\n    "paths": {\n      "@antv/g-base": ["node_modules/@antv/g-base"]\n    },' tsconfig.json
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
sed -i '9s/export { default as Component } from './component';/export { Component } from './component';/' src/core.ts
###ACTION_DELIMITER###
sed -i '9s|export { default as Component } from './component';|export { Component } from './component';|' src/core.ts
###ACTION_DELIMITER###
sed -i 's/default as Component/Component/' src/core.ts
###ACTION_DELIMITER###
sed -i '9s|{ default as Component }|{ Component }|' src/core.ts
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
sed -i '9s|export { Component } from './component';|export { default as Component } from './component';|' src/core.ts
###ACTION_DELIMITER###
sed -i '8i// @ts-ignore' src/core.ts
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
sed -i '9i// @ts-ignore' src/core.ts
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
cat src/component/index.ts
###ACTION_DELIMITER###
sed -i 's/export { Component } from './component';/export { Text as Component } from './component';/' src/core.ts
###ACTION_DELIMITER###
sed -i 's|export { Component } from './component';|export { Text as Component } from './component';|' src/core.ts
###ACTION_DELIMITER###
sed -i 's|export { Component } from './component';|export { Text as Component } from './component';|' src/core.ts
###ACTION_DELIMITER###
sed -i "s|export { Component } from './component';|export { Text as Component } from './component';|" src/core.ts
###ACTION_DELIMITER###
npm run build
###ACTION_DELIMITER###
echo 'npm test -- --verbose --json' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
npm install @antv/color-util --legacy-peer-deps
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
sed -i '/"jest": {/a\    "testEnvironment": "jsdom",' package.json
###ACTION_DELIMITER###

###ACTION_DELIMITER###
npm install --save-dev jsdom --legacy-peer-deps
###ACTION_DELIMITER###
sed -i '/"jest": {/a\    "testEnvironment": "jsdom",\n    "testEnvironmentOptions": {\n      "customExportConditions": ["node", "default"]\n    },' package.json
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###

###ACTION_DELIMITER###
""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
npm test -- --verbose --json

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
npm test -- --verbose --json

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
npm test -- --verbose --json

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
FROM node:18

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
RUN git clone https://github.com/antvis/G2.git /home/G2

WORKDIR /home/G2
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("antvis", "G2_1768_to_1643")
class G2_1768_TO_1643(Instance):
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
        passed_tests: set[str] = set()  # Tests that passed successfully
        failed_tests: set[str] = set()  # Tests that failed
        skipped_tests: set[str] = set()  # Tests that were skipped
        import re
        import json

        # Extract JSON from log content
        # Capture JSON starting with test results (more specific pattern)
        json_match = re.search(r'\{"numFailedTestSuites":.*\}', log, re.DOTALL)
        if json_match:
            try:
                test_results = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                test_results = None
        else:
            test_results = None
        if test_results:
            for test_suite in test_results.get("testResults", []):
                for assertion in test_suite.get("assertionResults", []):
                    status = assertion.get("status")
                    test_name = assertion.get("fullName")
                    if not test_name:
                        continue
                    if status == "passed":
                        passed_tests.add(test_name)
                    elif status == "failed":
                        failed_tests.add(test_name)
                    elif status == "skipped":
                        skipped_tests.add(test_name)
                    # Add handling for other statuses if needed
        else:
            # Fallback: parse text-based log (if JSON is not available)
            # Check for individual test results and test suites
            # Parse passed tests
            passed_matches = re.findall(r"^\s+✓\s+(.*)$", log, re.MULTILINE)
            for test in passed_matches:
                passed_tests.add(test.strip())
            # Parse failed tests
            failed_matches = re.findall(r"^\s+✗\s+(.*)$", log, re.MULTILINE)
            for test in failed_matches:
                failed_tests.add(test.strip())
            # Parse failed test suites
            suite_failed_matches = re.findall(r"FAIL (.*)$", log, re.MULTILINE)
            for suite in suite_failed_matches:
                failed_tests.add(suite.strip())
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
