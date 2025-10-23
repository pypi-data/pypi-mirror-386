import os

from pydantic import Field

import easymaker
from easymaker.api.request_body import PipelineRecurringRunCreateBody
from easymaker.common import exceptions, utils
from easymaker.common.base_model.easymaker_base_model import EasyMakerBaseModel
from easymaker.common.instance_type import InstanceType
from easymaker.common.parameter import Parameter
from easymaker.common.storage import Nas, Storage
from easymaker.experiment.experiment import Experiment
from easymaker.pipeline.pipeline import Pipeline


class PipelineRecurringRun(EasyMakerBaseModel):
    pipeline_recurring_run_id: str | None = None
    pipeline_recurring_run_name: str | None = None
    pipeline_recurring_run_status_code: str | None = None
    pipeline: Pipeline | None = None
    experiment: Experiment | None = None
    instance_type: InstanceType | None = Field(default=None, validation_alias="flavor")
    instance_count: int | None = None
    boot_storage: Storage | None = None
    nas_list: list[Nas] | None = None
    parameter_list: list[Parameter] | None = None
    schedule_periodic_minutes: int | None = None
    schedule_cron_expression: str | None = None
    max_concurrency_count: int | None = None
    schedule_start_datetime: str | None = None
    schedule_end_datetime: str | None = None
    use_catchup: bool | None = None

    def create(
        self,
        pipeline_recurring_run_name: str,
        pipeline_id: str,
        instance_type_name: str,
        boot_storage_size: int,
        instance_count: int = 1,
        max_concurrency_count: int = 1,
        description: str | None = None,
        experiment_id: str | None = None,
        experiment_name: str | None = None,
        experiment_description: str | None = None,
        parameter_list: list[Parameter] | None = None,
        nas_list: list[Nas] | None = None,
        schedule_periodic_minutes: int | None = None,
        schedule_cron_expression: str | None = None,
        schedule_start_datetime: str | None = None,
        schedule_end_datetime: str | None = None,
        use_catchup: bool | None = True,
        wait: bool | None = True,
    ):
        if not experiment_id:
            experiment_id = os.environ.get("EM_EXPERIMENT_ID")
        if not schedule_cron_expression and not schedule_periodic_minutes:
            raise exceptions.EasyMakerError("Either schedule_cron_expression or schedule_periodic_minutes must be provided.")

        instance_type_list = easymaker.easymaker_config.api_sender.get_instance_type_list()
        response = easymaker.easymaker_config.api_sender.create_pipeline_recurring_run(
            PipelineRecurringRunCreateBody(
                pipeline_run_or_recurring_run_name=pipeline_recurring_run_name,
                description=description,
                pipeline_id=pipeline_id,
                experiment_id=experiment_id,
                experiment_name=experiment_name,
                experiment_description=experiment_description,
                parameter_list=parameter_list,
                flavor_id=utils.from_name_to_id(instance_type_list, instance_type_name, InstanceType),
                instance_count=instance_count,
                boot_storage_size=boot_storage_size,
                nas_list=nas_list,
                schedule_periodic_minutes=schedule_periodic_minutes,
                schedule_cron_expression=schedule_cron_expression,
                max_concurrency_count=max_concurrency_count,
                schedule_start_datetime=schedule_start_datetime,
                schedule_end_datetime=schedule_end_datetime,
                use_catchup=use_catchup,
            )
        )
        super().__init__(**response)
        print(f"[AI EasyMaker] Pipeline recurring run create request complete. pipeline_recurring_run_id: {self.pipeline_recurring_run_id}")
        if wait:
            self.wait()

        return self

    def stop(self):
        if self.pipeline_recurring_run_id:
            easymaker.easymaker_config.api_sender.stop_pipeline_recurring_run_by_id(self.pipeline_recurring_run_id)
            print(f"[AI EasyMaker] Pipeline recurring run stop request complete. Pipeline recurring run ID : {self.pipeline_recurring_run_id}")
        else:
            print("[AI EasyMaker] Pipeline recurring run stop fail. pipeline_recurring_run_id is empty.")

    def start(self):
        if self.pipeline_recurring_run_id:
            easymaker.easymaker_config.api_sender.start_pipeline_recurring_run_by_id(self.pipeline_recurring_run_id)
            print(f"[AI EasyMaker] Pipeline recurring run start request complete. Pipeline recurring run ID : {self.pipeline_recurring_run_id}")
        else:
            print("[AI EasyMaker] Pipeline recurring run start fail. pipeline_recurring_run_id is empty.")
