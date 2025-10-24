"""
Copyright 2021 Adobe
All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it.
"""

from buildrunner.config.models_step import StepPypiPush
from buildrunner.errors import (
    BuildRunnerConfigurationError,
)
from buildrunner.steprunner.tasks import BuildStepRunnerTask


class PypiPushBuildStepRunnerTask(BuildStepRunnerTask):
    """
    Class used to push the resulting python packages to the given repository.
    """

    def __init__(self, step_runner, step: StepPypiPush):
        super().__init__(step_runner, step)

        if not self.step_runner.build_runner.push:
            # Was not invoked with ``--push`` so just skip this.  This avoids twine
            # complaining when the push repository is not configured and the user
            # is not even interested in pushing.
            return

        self._repository = step.repository
        self._username = step.username
        self._password = step.password
        self._skip_existing = step.skip_existing

        if self._repository not in self.step_runner.build_runner.pypi_packages:
            # Importing here avoids twine dependency when it is unnecessary
            import twine.settings  # pylint: disable=import-outside-toplevel
            import twine.exceptions  # pylint: disable=import-outside-toplevel

            try:
                if self._username is not None and self._password is not None:
                    upload_settings = twine.settings.Settings(
                        repository_url=self._repository,
                        username=self._username,
                        password=self._password,
                        disable_progress_bar=True,
                        skip_existing=self._skip_existing,
                    )
                else:
                    upload_settings = twine.settings.Settings(
                        repository_name=self._repository,
                        disable_progress_bar=True,
                        skip_existing=self._skip_existing,
                    )
            except twine.exceptions.InvalidConfiguration as twe:
                raise BuildRunnerConfigurationError(
                    f'Pypi is unable to find an entry for "{self._repository}" in your .pypirc.\n'
                ) from twe

            self.step_runner.build_runner.pypi_packages[self._repository] = {
                "upload_settings": upload_settings,
                "packages": [],
            }

    def run(self, context):
        if not self.step_runner.build_runner.push:
            self.step_runner.log.write('Push not requested with "--push": skipping\n')
            return

        self.step_runner.log.write(
            f'Preparing resulting packages for push to "{self._repository}".\n'
        )

        # get python-sdist packages for this step only
        for _artifact, _attributes in self.step_runner.build_runner.artifacts.items():
            if (
                _artifact.startswith(self.step_runner.name + "/")
                and _attributes
                and "type" in _attributes
                and _attributes["type"] in ("python-wheel", "python-sdist")
            ):
                self.step_runner.build_runner.pypi_packages[self._repository][
                    "packages"
                ].append(
                    f"{self.step_runner.build_runner.build_results_dir}/{_artifact}"
                )


# Local Variables:
# fill-column: 100
# End:
