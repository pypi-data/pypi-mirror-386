import os
from typing import Any, Generic, TypeVar

import picsellia
from picsellia import ModelVersion

from picsellia_cv_engine.core.contexts import PicselliaContext
from picsellia_cv_engine.core.parameters import Parameters

TParameters = TypeVar("TParameters", bound=Parameters)


class PicselliaModelProcessingContext(PicselliaContext, Generic[TParameters]):
    """
    Context for model version processing jobs in Picsellia, including export logic.
    """

    def __init__(
        self,
        processing_parameters_cls: type[TParameters],
        api_token: str | None = None,
        host: str | None = None,
        organization_id: str | None = None,
        organization_name: str | None = None,
        job_id: str | None = None,
        use_id: bool | None = True,
        working_dir: str | None = None,
    ):
        """
        Initialize the model processing context.

        Raises:
            ValueError: If job ID is missing or model version ID is not found.
        """
        super().__init__(
            api_token=api_token,
            host=host,
            organization_id=organization_id,
            organization_name=organization_name,
            working_dir=working_dir,
        )

        self.job_id = job_id or os.environ.get("job_id")
        if not self.job_id:
            raise ValueError(
                "Job ID not provided. Please provide it as an argument or set the 'job_id' environment variable."
            )

        self.job = self._initialize_job()
        self.job_type = self.job.sync()["type"]
        self.job_context = self._initialize_job_context()

        self._model_version_id = self.job_context.get("input_model_version_id")
        if self._model_version_id:
            self.model_version = self.get_model_version()

        self.use_id = use_id

        self.processing_parameters = processing_parameters_cls(
            log_data=self.job_context["parameters"]
        )

    @property
    def working_dir(self) -> str:
        """Return the working directory path for the job."""
        if self._working_dir_override:
            return self._working_dir_override
        return os.path.join(os.getcwd(), f"job_{self.job_id}")

    @property
    def model_version_id(self) -> str | None:
        """Return the model version ID, or raise if missing."""
        if not self._model_version_id:
            raise ValueError(
                "Model version ID not found. Please ensure the job is correctly configured."
            )
        return self._model_version_id

    def to_dict(self) -> dict[str, Any]:
        """Convert context to a dictionary representation."""
        return {
            "context_parameters": {
                "host": self.host,
                "organization_id": self.organization_id,
                "job_id": self.job_id,
            },
            "model_version_id": self.model_version_id,
            "processing_parameters": self._process_parameters(
                parameters_dict=self.processing_parameters.to_dict(),
                defaulted_keys=self.processing_parameters.defaulted_keys,
            ),
        }

    def _initialize_job_context(self) -> dict[str, Any]:
        """Fetch job context from Picsellia."""
        return self.job.sync()["model_version_processing_job"]

    def _initialize_job(self) -> picsellia.Job:
        """Retrieve the Picsellia job by ID."""
        return self.client.get_job_by_id(self.job_id)

    def get_model_version(self) -> ModelVersion:
        """Fetch a model version by ID."""
        return self.client.get_model_version_by_id(self.model_version_id)
