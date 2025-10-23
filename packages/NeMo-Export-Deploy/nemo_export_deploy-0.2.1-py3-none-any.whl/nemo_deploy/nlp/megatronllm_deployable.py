# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.distributed
from jinja2 import Template
from megatron.core.inference.common_inference_params import CommonInferenceParams
from megatron.core.inference.inference_request import InferenceRequest

from nemo_deploy import ITritonDeployable
from nemo_deploy.nlp.inference.inference_base import create_mcore_engine
from nemo_deploy.utils import (
    NEMO2,
    broadcast_list,
    cast_output,
    nemo_checkpoint_version,
    str_ndarray2list,
)
from nemo_export_deploy_common.import_utils import MISSING_TRITON_MSG, UnavailableError, null_decorator

try:
    from pytriton.decorators import batch, first_value
    from pytriton.model_config import Tensor

    HAVE_TRITON = True
except (ImportError, ModuleNotFoundError):
    from unittest.mock import MagicMock

    HAVE_TRITON = False
    batch = MagicMock()
    first_value = MagicMock()
    Tensor = MagicMock()

    batch = null_decorator
    first_value = null_decorator

LOGGER = logging.getLogger("NeMo")


class MegatronLLMDeploy:
    """A factory class for creating deployable instances of Megatron LLM models.

    This class provides a method to get the appropriate deployable instance
    based on the version of the NeMo checkpoint model used.
    """

    @staticmethod
    def get_deployable(
        nemo_checkpoint_filepath: str,
        num_devices: int = None,
        num_nodes: int = None,
        tensor_model_parallel_size: int = 1,
        pipeline_model_parallel_size: int = 1,
        expert_model_parallel_size: int = 1,
        context_parallel_size: int = 1,
        max_batch_size: int = 32,
        random_seed: Optional[int] = None,
        enable_flash_decode: bool = False,
        enable_cuda_graphs: bool = False,
        legacy_ckpt: bool = False,
    ):
        """Returns the appropriate deployable instance for the given NeMo checkpoint.

        Args:
            nemo_checkpoint_filepath (str): Path to the .nemo checkpoint file.
            num_devices (int): Number of devices to use for deployment.
            num_nodes (int): Number of nodes to use for deployment.
            tensor_model_parallel_size (int): Size of the tensor model parallelism.
            pipeline_model_parallel_size (int): Size of the pipeline model parallelism.
            context_parallel_size (int): Size of the context parallelism.
            enable_flash_decode (bool): Whether to enable flash decode for inference.
            enable_cuda_graphs (bool): Whether to enable CUDA graphs for inference.
            legacy_ckpt (bool): Whether to use legacy checkpoint format. Defaults to False.

        Returns:
            ITritonDeployable: An instance of a deployable class compatible with Triton inference server.
        """
        if nemo_checkpoint_version(nemo_checkpoint_filepath) == NEMO2:
            return MegatronLLMDeployableNemo2(
                num_devices=num_devices,
                num_nodes=num_nodes,
                nemo_checkpoint_filepath=nemo_checkpoint_filepath,
                tensor_model_parallel_size=tensor_model_parallel_size,
                pipeline_model_parallel_size=pipeline_model_parallel_size,
                context_parallel_size=context_parallel_size,
                expert_model_parallel_size=expert_model_parallel_size,
                max_batch_size=max_batch_size,
                random_seed=random_seed,
                enable_flash_decode=enable_flash_decode,
                enable_cuda_graphs=enable_cuda_graphs,
                legacy_ckpt=legacy_ckpt,
            )
        else:
            raise Exception("Only NeMo 2.0 checkpoint is supported.")


def dict_to_str(messages):
    """Serializes dict to str."""
    return json.dumps(messages)


class MegatronLLMDeployableNemo2(ITritonDeployable):
    """Triton inference server compatible deploy class for a .nemo model file.

    Args:
        nemo_checkpoint_filepath (str): path for the nemo checkpoint.
        num_devices (int): number of GPUs.
        num_nodes (int): number of nodes.
        tensor_model_parallel_size (int): tensor parallelism.
        pipeline_parallelism_size (int): pipeline parallelism.
        context_parallel_size (int): context parallelism.
        expert_model_parallel_size (int): expert parallelism.
        params_dtype (torch.dtype): max input length.
        inference_batch_times_seqlen_threshold (int): squence threshold.
        inference_max_seq_length (int): max_seq_length for inference. Required by MCoreEngine (>=0.12). Defaults to
        4096.
        max_batch_size (int): max batch size for inference. Defaults to 32.
        random_seed (Optional[int]): random seed for inference. Defaults to None.
        enable_flash_decode (bool): enable flash decode for inference. Defaults to False.
        enable_cuda_graphs (bool): enable CUDA graphs for inference. Defaults to False.`
        legacy_ckpt (bool): use legacy checkpoint format. Defaults to False.
        megatron_checkpoint_filepath (str): path for the megatron checkpoint.
        model_type (str): type of model to load. Defaults to "gpt".(Only for Megatron models)
        model_format (str): format of model to load. Defaults to "nemo".
        micro_batch_size (Optional[int]): micro batch size for model execution. Defaults to None.(Only for Megatron models)
    """

    def __init__(
        self,
        num_devices: int = None,
        num_nodes: int = None,
        nemo_checkpoint_filepath: str = None,
        tensor_model_parallel_size: int = 1,
        pipeline_model_parallel_size: int = 1,
        context_parallel_size: int = 1,
        expert_model_parallel_size: int = 1,
        params_dtype: torch.dtype = torch.bfloat16,
        inference_batch_times_seqlen_threshold: int = 32768,
        inference_max_seq_length: int = 4096,
        enable_flash_decode: bool = False,
        enable_cuda_graphs: bool = False,
        max_batch_size: int = 8,
        random_seed: Optional[int] = None,
        legacy_ckpt: bool = False,
        megatron_checkpoint_filepath: str = None,
        model_type: str = "gpt",
        model_format: str = "nemo",
        micro_batch_size: Optional[int] = None,
        **model_config_kwargs,
    ):
        if not HAVE_TRITON:
            raise UnavailableError(MISSING_TRITON_MSG)

        if model_format == "nemo":
            checkpoint_filepath = nemo_checkpoint_filepath
        elif model_format == "megatron":
            if model_type not in ["gpt", "mamba"]:
                raise ValueError(f"Model type {model_type} not supported for Megatron models.")
            checkpoint_filepath = megatron_checkpoint_filepath
        else:
            raise ValueError(f"Model format {model_format} not supported.")

        self.mcore_engine, self.inference_wrapped_model, self.mcore_tokenizer = create_mcore_engine(
            num_devices=num_devices,
            num_nodes=num_nodes,
            path=Path(checkpoint_filepath),
            params_dtype=params_dtype,
            inference_batch_times_seqlen_threshold=inference_batch_times_seqlen_threshold,
            inference_max_seq_length=inference_max_seq_length,
            max_batch_size=max_batch_size,
            random_seed=random_seed,
            tensor_model_parallel_size=tensor_model_parallel_size,
            expert_model_parallel_size=expert_model_parallel_size,
            pipeline_model_parallel_size=pipeline_model_parallel_size,
            context_parallel_size=context_parallel_size,
            enable_flash_decode=enable_flash_decode,
            enable_cuda_graphs=enable_cuda_graphs,
            legacy_ckpt=legacy_ckpt,
            model_type=model_type,
            model_format=model_format,
            micro_batch_size=micro_batch_size,
            **model_config_kwargs,
        )
        self.enable_cuda_graphs = enable_cuda_graphs
        self.max_batch_size = max_batch_size

    def generate(
        self,
        prompts: List[str],
        inference_params: Optional[CommonInferenceParams] = None,
    ) -> List[InferenceRequest]:
        """Generates text based on the provided input prompts.

        Args:
            prompts (List[str]): A list of input strings.
            inference_params (Optional[CommonInferenceParams]): Parameters for controlling the inference process.

        Returns:
            List[InferenceRequest]: A list containing the generated results.
        """
        inference_params = inference_params or CommonInferenceParams()

        # Store the original number of prompts
        orig_num_prompts = len(prompts)

        # If CUDA graphs are enabled and we have fewer prompts than max_batch_size,
        # pad the prompts array to reach max_batch_size
        if self.enable_cuda_graphs and orig_num_prompts < self.max_batch_size:
            # Create a copy of the prompts to avoid modifying the original list
            padded_prompts = prompts.copy()

            # Add sample prompts to reach max_batch_size
            # We'll duplicate the first prompt for simplicity
            sample_prompt = prompts[0] if prompts else ""
            padded_prompts.extend([sample_prompt] * (self.max_batch_size - orig_num_prompts))

            results = self.mcore_engine.generate(
                prompts=padded_prompts,
                add_BOS=False,
                common_inference_params=inference_params,
            )

            # Only return results for the original prompts
            return list(results)[:orig_num_prompts]
        else:
            results = self.mcore_engine.generate(
                prompts=prompts,
                add_BOS=False,
                common_inference_params=inference_params,
            )
            return list(results)

    def generate_other_ranks(self):
        """Generate function for ranks other than the rank 0."""
        while True:
            message = torch.empty(1, dtype=torch.long, device="cuda")
            torch.distributed.broadcast(message, src=0)
            if message == 0:
                prompts = broadcast_list(data=[None], src=0)
                temperature, top_k, top_p, num_tokens_to_generate, log_probs = broadcast_list(data=[None], src=0)

                inference_params = CommonInferenceParams(
                    temperature=temperature,
                    top_k=int(top_k),
                    top_p=float(top_p),
                    num_tokens_to_generate=num_tokens_to_generate,
                    return_log_probs=log_probs,
                )

                self.generate(prompts, inference_params)
            else:
                return

    def apply_chat_template(self, messages, add_generation_prompt=True):
        """Load the chat template.

        Works when model's tokenizer has chat template (typically chat models).
        """
        try:
            tokenizer_chat_template = self.mcore_tokenizer.tokenizer.tokenizer.chat_template

            # Try to get bos_token, handle different tokenizer types
            bos_token = None
            try:
                bos_token = self.mcore_tokenizer.tokenizer.tokenizer.bos_token
            except AttributeError:
                # Some tokenizers might not have bos_token, use empty string as fallback
                bos_token = ""

            # Check if chat_template is None or empty
            if tokenizer_chat_template is None:
                raise ValueError(
                    "The tokenizer does not have a chat template defined. "
                    "If you would like to evaluate a chat model, ensure your model's tokenizer has a chat template."
                )

            template = Template(tokenizer_chat_template)
        except AttributeError:
            # If the tokenizer does not have chat_template
            raise ValueError(
                "The tokenizer does not have chat template, if you would like to evaluate chat model \
                             ensure your model's tokenizer has a chat template"
            )
        # Render the template with the provided messages
        rendered_output = template.render(
            messages=messages,
            bos_token=bos_token,
            add_generation_prompt=add_generation_prompt,
        )

        return rendered_output

    def remove_eos_token(self, text):
        """Removes eos token if it exists in the output, otherwise does nothing."""
        # Handle different tokenizer types
        try:
            eos_token = self.mcore_tokenizer.tokenizer.tokenizer.eos_token
        except AttributeError:
            # Fallback for TiktokenTokenizer and similar tokenizers
            try:
                eos_id = self.mcore_tokenizer.tokenizer.tokenizer.eos_id
                eos_token = self.mcore_tokenizer.tokenizer.tokenizer.special_tokens[eos_id]
            except AttributeError:
                # If neither approach works, return text unchanged
                return text

        output = []
        for t in text:
            if eos_token in t:
                output.append(t.rsplit(eos_token, 1)[0])
            else:
                output.append(t)
        return output

    def str_to_dict(self, json_str):
        """Convert str to dict."""
        return json.loads(json_str)

    @property
    def get_triton_input(self):
        inputs = (
            Tensor(name="prompts", shape=(-1,), dtype=bytes),
            Tensor(name="max_length", shape=(-1,), dtype=np.int_, optional=True),
            Tensor(name="max_batch_size", shape=(-1,), dtype=np.int_, optional=True),
            Tensor(name="top_k", shape=(-1,), dtype=np.int_, optional=True),
            Tensor(name="top_p", shape=(-1,), dtype=np.single, optional=True),
            Tensor(name="temperature", shape=(-1,), dtype=np.single, optional=True),
            Tensor(name="random_seed", shape=(-1,), dtype=np.int_, optional=True),
            Tensor(name="compute_logprob", shape=(-1,), dtype=np.bool_, optional=True),
            Tensor(name="apply_chat_template", shape=(-1,), dtype=np.bool_, optional=True),
            Tensor(name="n_top_logprobs", shape=(-1,), dtype=np.int_, optional=True),
            Tensor(name="echo", shape=(-1,), dtype=np.bool_, optional=True),
        )
        return inputs

    @property
    def get_triton_output(self):
        return (
            Tensor(name="sentences", shape=(-1,), dtype=bytes),
            Tensor(name="log_probs", shape=(-1,), dtype=np.single),
            Tensor(name="top_logprobs", shape=(-1,), dtype=bytes),
        )

    @batch
    @first_value(
        "max_length",
        "max_batch_size",
        "top_k",
        "top_p",
        "temperature",
        "random_seed",
        "compute_logprob",
        "apply_chat_template",
        "n_top_logprobs",
        "echo",
    )
    def triton_infer_fn(self, **inputs: np.ndarray):
        prompts = str_ndarray2list(inputs.pop("prompts"))
        temperature = inputs.pop("temperature", 1.0)
        top_k = inputs.pop("top_k", 1)
        top_p = inputs.pop("top_p", 0.0)
        num_tokens_to_generate = inputs.pop("max_length", 256)
        log_probs = inputs.pop("compute_logprob", False)
        apply_chat_template = inputs.pop("apply_chat_template", False)
        top_logprobs = inputs.pop("n_top_logprobs", 0)
        echo = inputs.pop("echo", False)
        text_only = inputs.pop("text_only", True)

        if apply_chat_template:
            prompts = [self.str_to_dict(prompt) for prompt in prompts]

        # Use the shared inference function
        output_infer = self._infer_fn(
            prompts=prompts,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            num_tokens_to_generate=num_tokens_to_generate,
            log_probs=log_probs,
            apply_chat_template=apply_chat_template,
            text_only=text_only,
            top_logprobs=top_logprobs,
            echo=echo,
        )

        # Format output for triton
        output_infer["sentences"] = cast_output(output_infer["sentences"], np.bytes_)
        if "top_logprobs" in output_infer.keys():
            output_infer["top_logprobs"] = cast_output(output_infer["top_logprobs"], np.bytes_)
        return output_infer

    def _infer_fn(
        self,
        prompts,
        temperature=0.0,
        top_k=0.0,
        top_p=0.0,
        num_tokens_to_generate=256,
        log_probs=False,
        apply_chat_template=False,
        text_only=True,
        top_logprobs=0,
        echo=False,
    ):
        """Private helper function that handles the core inference logic shared between triton and ray inference.

        Args:
            prompts (List[str]): List of input prompts
            max_batch_size (int): Maximum batch size for inference
            random_seed (int): Random seed for reproducibility
            temperature (float): Sampling temperature
            top_k (int): Top-k sampling parameter
            top_p (float): Top-p sampling parameter
            num_tokens_to_generate (int): Maximum number of tokens to generate
            log_probs (bool): Whether to compute log probabilities
            apply_chat_template (bool): Whether to apply chat template
            text_only (bool): Whether to return only text or full results
            top_logprobs (int): Number of top logprobs to return
            echo (bool): If True, returns the prompt and generated text. If log_probs is True, returns the prompt and
            generated log_probs. If top_logprobs is > 0, returns the prompt and generated top_logprobs.

        Returns:
            dict: sentences and required log probs.
        """
        if apply_chat_template:
            prompts = [self.apply_chat_template(prompt) for prompt in prompts]

        if torch.distributed.is_initialized():
            if torch.distributed.get_world_size() > 1:
                torch.distributed.broadcast(torch.tensor([0], dtype=torch.long, device="cuda"), src=0)
                broadcast_list(prompts, src=0)
                broadcast_list(
                    data=[
                        temperature,
                        top_k,
                        top_p,
                        num_tokens_to_generate,
                        log_probs,
                    ],
                    src=0,
                )

        # cast top_k,top_p to native int, float since typecheck assert statements added in MCore0.13 error otherwise
        # return_prompt_top_n_logprobs returns top_logprobs for prompt tokens too when top_logprobs>0.
        inference_params = CommonInferenceParams(
            temperature=temperature,
            top_k=int(top_k),
            top_p=float(top_p),
            num_tokens_to_generate=num_tokens_to_generate,
            return_log_probs=log_probs,
            top_n_logprobs=top_logprobs,
            return_prompt_top_n_logprobs=bool(top_logprobs),
        )

        results = self.generate(prompts, inference_params)
        if echo:
            output_texts = [r.prompt + r.generated_text if text_only else r for r in results]
        else:
            output_texts = [r.generated_text if text_only else r for r in results]
        output_texts = self.remove_eos_token(output_texts)
        output_infer = {"sentences": output_texts}

        if log_probs:
            output_log_probs = []
            for r in results:
                # Convert to torch tensor and then move to cpu as generated_log_probs is a list and cant be moved
                # to cpu otherwise
                if echo:
                    lp = torch.tensor(r.prompt_log_probs + r.generated_log_probs).cpu().detach().numpy()
                else:
                    lp = torch.tensor(r.generated_log_probs).cpu().detach().numpy()

                if len(lp) == 0:
                    output_log_probs.append([0])
                else:
                    output_log_probs.append(lp)

            if echo:
                # if echo, arrays in output_log_probs can have diff len due to diff num of prompt tokens. Pad the
                # tokens in that case
                # Find the maximum length
                max_len = max(len(arr) for arr in output_log_probs)
                # Pad each array to the maximum length. Pads 0.
                padded = np.array([np.pad(arr, (0, max_len - len(arr)), constant_values=0) for arr in output_log_probs])
                output_infer["log_probs"] = padded
            else:
                output_infer["log_probs"] = np.array(output_log_probs)

        if top_logprobs:
            output_top_n_log_probs = []
            for r in results:
                # Convert to torch tensor and then move to cpu as generated_log_probs is a list and cant be moved
                # to cpu otherwise.
                # top_logprobs for input tokens is supported with MCore 0.13 and above.
                if echo:
                    top_n_lp = dict_to_str(r.prompt_top_n_logprobs + r.generated_top_n_logprobs)
                else:
                    top_n_lp = dict_to_str(r.generated_top_n_logprobs)
                output_top_n_log_probs.append(top_n_lp)
            output_infer["top_logprobs"] = output_top_n_log_probs

        return output_infer

    def ray_infer_fn(self, inputs: dict):
        """Ray-compatible inference function that takes a dictionary of inputs and returns a dictionary of outputs.

        Args:
            inputs (dict): Dictionary containing the following optional keys:
                - prompts (List[str]): List of input prompts
                - max_batch_size (int): Maximum batch size for inference (default: 32)
                - random_seed (int): Random seed for reproducibility (default: None)
                - temperature (float): Sampling temperature (default: 1.0)
                - top_k (int): Top-k sampling parameter (default: 1)
                - top_p (float): Top-p sampling parameter (default: 0.0)
                - max_length (int): Maximum number of tokens to generate (default: 256)
                - logprobs (int): Whether to compute log probabilities (default: 0)
                - apply_chat_template (bool): Whether to apply chat template (default: False)

        Returns:
            dict: Dictionary containing:
                - sentences (List[str]): List of generated texts
                - log_probs (List[float], optional): List of log probabilities if compute_logprob is True
        """
        prompts = inputs.get("prompts", [])
        temperature = inputs.get("temperature", 1.0)
        top_k = inputs.get("top_k", 0)
        top_p = inputs.get("top_p", 0.0)
        num_tokens_to_generate = inputs.get("max_length", 256)
        log_probs = inputs.get("compute_logprob", False)
        apply_chat_template = inputs.get("apply_chat_template", False)
        top_logprobs = inputs.pop("n_top_logprobs", 0)
        echo = inputs.pop("echo", False)
        text_only = inputs.pop("text_only", True)

        return self._infer_fn(
            prompts=prompts,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            num_tokens_to_generate=num_tokens_to_generate,
            log_probs=log_probs,
            apply_chat_template=apply_chat_template,
            text_only=text_only,
            top_logprobs=top_logprobs,
            echo=echo,
        )
