import torch

from .engine import EngineArgs
from .model import InitArgs, InternalModelConfig, PeftArgs, TrainerArgs
from .torchtune import TorchtuneArgs


def get_model_config(
    base_model: str,
    output_dir: str,
    config: "InternalModelConfig | None",
) -> "InternalModelConfig":
    from ..local.checkpoints import get_last_checkpoint_dir

    if config is None:
        config = InternalModelConfig()
    enable_sleep_mode = config.get("engine_args", {}).get("enable_sleep_mode", True)
    init_args = InitArgs(
        disable_log_stats=False,
        enable_prefix_caching=True,
        fast_inference=True,
        gpu_memory_utilization=(0.79 if enable_sleep_mode else 0.55),
        load_in_4bit=True,
        max_lora_rank=8,
        max_seq_length=32768,
        model_name=base_model,
        use_async=True,
    )
    if config.get("_decouple_vllm_and_unsloth", False):
        init_args["fast_inference"] = False
        init_args.pop("disable_log_stats")
        init_args.pop("enable_prefix_caching")
        init_args.pop("gpu_memory_utilization")
        init_args.pop("max_lora_rank")
        init_args.pop("use_async")
    engine_args = EngineArgs(
        allowed_local_media_path="/tmp",
        disable_log_requests=True,
        enable_sleep_mode=enable_sleep_mode,
        generation_config="vllm",
    )
    engine_args.update(config.get("engine_args", {}))
    init_args.update(config.get("init_args", {}))
    if last_checkpoint_dir := get_last_checkpoint_dir(output_dir):
        init_args["model_name"] = last_checkpoint_dir
        if config.get("torchtune_args") is not None:
            engine_args["model"] = last_checkpoint_dir
    elif config.get("torchtune_args") is not None:
        engine_args["model"] = base_model
    if config.get("_decouple_vllm_and_unsloth", False):
        engine_args["model"] = base_model
    peft_args = PeftArgs(
        lora_alpha=16,
        r=8,
        random_state=3407,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        use_gradient_checkpointing="unsloth",
    )
    peft_args.update(config.get("peft_args", {}))
    trainer_args = TrainerArgs(
        adam_beta1=0.9,
        adam_beta2=0.99,
        disable_tqdm=True,
        gradient_accumulation_steps=1,
        learning_rate=5e-6,
        logging_steps=1,
        lr_scheduler_type="constant",
        max_grad_norm=0.1,
        num_generations=2,
        optim="paged_adamw_8bit",
        output_dir=output_dir,
        per_device_train_batch_size=2,
        report_to="none",
        save_strategy="no",
        weight_decay=0.1,
    )
    trainer_args.update(config.get("trainer_args", {}))
    if config.get("torchtune_args") is not None:
        torchtune_args = TorchtuneArgs(model="qwen3_32b", model_type="QWEN3")
        torchtune_args.update(config.get("torchtune_args", {}) or {})
    else:
        torchtune_args = None
    return InternalModelConfig(
        init_args=init_args,
        engine_args=engine_args,
        peft_args=peft_args,
        trainer_args=trainer_args,
        torchtune_args=torchtune_args,
        _decouple_vllm_and_unsloth=config.get("_decouple_vllm_and_unsloth", False),
    )
