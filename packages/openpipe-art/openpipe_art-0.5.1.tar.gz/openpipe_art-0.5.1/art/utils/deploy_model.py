import asyncio
import json
import os
import time
from enum import Enum
from typing import TYPE_CHECKING, Any

import aiohttp
from pydantic import BaseModel

from art.errors import (
    LoRADeploymentTimedOutError,
    UnsupportedBaseModelDeploymentError,
    UnsupportedLoRADeploymentProviderError,
)
from art.utils.get_model_step import get_model_step
from art.utils.output_dirs import get_default_art_path
from art.utils.s3 import archive_and_presign_step_url, pull_model_from_s3

if TYPE_CHECKING:
    from art.model import TrainableModel


class LoRADeploymentProvider(str, Enum):
    TOGETHER = "together"


class LoRADeploymentJobStatus(str, Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETE = "Complete"
    FAILED = "Failed"


class LoRADeploymentJob(BaseModel):
    status: LoRADeploymentJobStatus
    job_id: str
    model_name: str
    failure_reason: str | None


def init_together_session() -> aiohttp.ClientSession:
    """
    Initializes a session for interacting with Together.
    """
    if "TOGETHER_API_KEY" not in os.environ:
        raise ValueError("TOGETHER_API_KEY is not set, cannot deploy LoRA to Together")
    session = aiohttp.ClientSession()
    session.headers.update(
        {
            "Authorization": f"Bearer {os.environ['TOGETHER_API_KEY']}",
            "Content-Type": "application/json",
        }
    )
    return session


def model_checkpoint_id(model: "TrainableModel", step: int) -> str:
    """
    Generates a unique ID for a model checkpoint.
    """
    return f"{model.project}-{model.name}-{step}"


TOGETHER_SUPPORTED_BASE_MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
]


async def deploy_together(
    model: "TrainableModel",
    presigned_url: str,
    step: int,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Deploys a model to Together. Supported base models:

    * meta-llama/Meta-Llama-3.1-8B-Instruct
    * meta-llama/Meta-Llama-3.1-70B-Instruct
    * Qwen/Qwen2.5-14B-Instruct
    * Qwen/Qwen2.5-72B-Instruct
    """
    # check if base model is supported for serverless LoRA deployment by Together
    if model.base_model not in TOGETHER_SUPPORTED_BASE_MODELS:
        raise UnsupportedBaseModelDeploymentError(
            message=f"Base model {model.base_model} is not supported for serverless LoRA deployment by Together. Supported models: {TOGETHER_SUPPORTED_BASE_MODELS}"
        )

    async with init_together_session() as session:
        session.headers.update(
            {
                "Authorization": f"Bearer {os.environ['TOGETHER_API_KEY']}",
                "Content-Type": "application/json",
            }
        )

        async with session.post(
            url="https://api.together.xyz/v1/models",
            json={
                "model_name": model_checkpoint_id(model=model, step=step),
                "model_source": presigned_url,
                "model_type": "adapter",
                "base_model": model.base_model,
                "description": f"Deployed from ART. Project: {model.project}. Model: {model.name}. Step: {step}",
            },
        ) as response:
            if response.status != 200:
                print("Error uploading to Together:", await response.text())
            response.raise_for_status()
            result = await response.json()
            if verbose:
                print(f"Successfully uploaded to Together: {result}")
            return result


def convert_together_job_status(
    status: str, message: str | None = None
) -> LoRADeploymentJobStatus:
    MODEL_ALREADY_EXISTS_ERROR_MESSAGE = "409 Client Error: Conflict for url: https://api.together.ai/api/admin/entity/Model"
    if (
        status == "Error"
        and message is not None
        and MODEL_ALREADY_EXISTS_ERROR_MESSAGE in message
    ):
        return LoRADeploymentJobStatus.COMPLETE
    if status == "Bad" or status == "Error":
        return LoRADeploymentJobStatus.FAILED
    if status == "Retry Queued":
        return LoRADeploymentJobStatus.QUEUED
    return LoRADeploymentJobStatus(status)


async def find_existing_together_job_id(
    model: "TrainableModel",
    step: int,
) -> str | None:
    """
    Finds an existing model deployment job in Together.
    """
    checkpoint_id = model_checkpoint_id(model, step)
    async with init_together_session() as session:
        async with session.get(url="https://api.together.xyz/v1/jobs") as response:
            response.raise_for_status()
            result = await response.json()
            jobs = result["data"]
            # ensure we get the most recent job
            jobs.sort(key=lambda x: x["updated_at"], reverse=True)
            for job in jobs:
                if checkpoint_id in job["args"]["modelName"]:
                    return job["job_id"]
            return None


async def check_together_job_status(
    job_id: str, verbose: bool = False
) -> LoRADeploymentJob:
    """
    Checks the status of a model deployment job in Together.
    """
    async with init_together_session() as session:
        async with session.get(
            url=f"https://api.together.xyz/v1/jobs/{job_id}"
        ) as response:
            response.raise_for_status()
            result = await response.json()
            if verbose:
                print(f"Job status: {json.dumps(result, indent=4)}")

            last_update = result["status_updates"][-1]
            status_body = LoRADeploymentJob(
                status=convert_together_job_status(
                    result["status"], last_update.get("message")
                ),
                job_id=job_id,
                model_name=result["args"]["modelName"],
                failure_reason=result.get("failure_reason"),
            )

            if status_body.status == LoRADeploymentJobStatus.FAILED:
                status_body.failure_reason = last_update.get("message")
            return status_body


async def wait_for_together_job(
    job_id: str, verbose: bool = False
) -> LoRADeploymentJob:
    """
    Waits for a model deployment job to complete in Together.

    Checks the status every 15 seconds for 5 minutes.
    """
    print(f"checking status of job {job_id} every 15 seconds for 5 minutes")
    start_time = time.time()
    max_time = start_time + 300
    while time.time() < max_time:
        job_status = await check_together_job_status(job_id, verbose)
        if job_status.status == "Complete" or job_status.status == "Failed":
            return job_status
        await asyncio.sleep(15)

    raise LoRADeploymentTimedOutError(
        message=f"LoRA deployment timed out after 5 minutes. Job ID: {job_id}"
    )


async def deploy_model(
    deploy_to: LoRADeploymentProvider,
    model: "TrainableModel",
    step: int | None = None,
    s3_bucket: str | None = None,
    prefix: str | None = None,
    verbose: bool = False,
    pull_s3: bool = True,
    wait_for_completion: bool = True,
    art_path: str | None = get_default_art_path(),
) -> LoRADeploymentJob:
    """
    Deploy the model's latest checkpoint to a hosted inference endpoint.

    Together is currently the only supported provider. See link for supported base models:
    https://docs.together.ai/docs/lora-inference#supported-base-models
    """

    art_path = art_path or get_default_art_path()
    os.makedirs(art_path, exist_ok=True)
    if pull_s3:
        # pull the latest step from S3
        await pull_model_from_s3(
            model_name=model.name,
            project=model.project,
            step=step,
            s3_bucket=s3_bucket,
            prefix=prefix,
            verbose=verbose,
            art_path=art_path,
        )

    if step is None:
        step = get_model_step(model, art_path)

    presigned_url = await archive_and_presign_step_url(
        model_name=model.name,
        project=model.project,
        step=step,
        s3_bucket=s3_bucket,
        prefix=prefix,
        verbose=verbose,
        art_path=art_path,
    )

    if deploy_to == LoRADeploymentProvider.TOGETHER:
        existing_job_id = await find_existing_together_job_id(model, step)
        existing_job = None
        if existing_job_id is not None:
            existing_job = await check_together_job_status(
                existing_job_id, verbose=verbose
            )

        if not existing_job or existing_job.status == "Failed":
            deployment_result = await deploy_together(
                model=model,
                presigned_url=presigned_url,
                step=step,
                verbose=verbose,
            )
            job_id = deployment_result["data"]["job_id"]
        else:
            job_id = existing_job_id
            assert job_id is not None
            print(
                f"Previous deployment for {model.name} at step {step} has status '{existing_job.status}', skipping redployment"
            )

        if wait_for_completion:
            return await wait_for_together_job(job_id, verbose=verbose)
        else:
            return await check_together_job_status(job_id, verbose=verbose)

    raise UnsupportedLoRADeploymentProviderError(
        f"Unsupported deployment option: {deploy_to}"
    )
