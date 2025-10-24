# Copyright (c) 2025 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file is based on https://github.com/Kwai-Keye/Keye/blob/main/keye-vl-8b-preview/modeling_keye.py
# Original header:
# Copyright 2025 The Keye Team and The HuggingFace Inc. team. All rights reserved.
#
# This code is based on EleutherAI's GPT-NeoX library and the GPT-NeoX
# and OPT implementations in this library. It has been modified from its
# original forms to accommodate minor architectural differences compared
# to GPT-NeoX and OPT used by the Meta AI team that trained the model.
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

from contextvars import ContextVar
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

import numpy as np
import paddle
import paddle.nn as nn

from ....common.vlm.generation import GenerationMixin
from ....common.vlm.transformers.model_outputs import (
    CausalLMOutputWithCrossAttentions,
    ModelOutput,
)
from ._config import PaddleOCRVLConfig
from ._ernie import Ernie4_5Model, Ernie4_5PretrainedModel
from ._projector import Projector
from ._siglip import SiglipVisionModel


@dataclass
class PaddleOCRVLCausalLMOutputWithPast(ModelOutput):
    loss: Optional[paddle.Tensor] = None
    logits: paddle.Tensor = None
    past_key_values: Optional[List[paddle.Tensor]] = None
    hidden_states: Optional[Tuple[paddle.Tensor]] = None
    attentions: Optional[Tuple[paddle.Tensor]] = None
    rope_deltas: Optional[paddle.Tensor] = None


class PaddleOCRVLForConditionalGeneration(Ernie4_5PretrainedModel, GenerationMixin):
    _tied_weights_keys = ["lm_head.weight"]
    config_class = PaddleOCRVLConfig
    _no_split_modules = ["Ernie4_5DecoderLayer", "SiglipEncoderLayer"]

    base_model_prefix = ""

    def __init__(self, config):
        super().__init__(config)

        self.mlp_AR = Projector(config, config.vision_config)
        self.visual = SiglipVisionModel(config.vision_config)
        self.model = Ernie4_5Model(config)
        self.vocab_size = config.vocab_size
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias_attr=False)
        self.rope_deltas_var = ContextVar("rope_deltas", default=None)

    def get_input_embeddings(self):
        return self.model.embed_tokens

    def set_input_embeddings(self, value):
        self.model.embed_tokens = value

    def get_output_embeddings(self):
        return self.lm_head

    def set_output_embeddings(self, new_embeddings):
        self.lm_head = new_embeddings

    def set_decoder(self, decoder):
        self.model = decoder

    def get_decoder(self):
        return self.model

    def get_rope_index(
        self,
        input_ids: Optional[paddle.Tensor] = None,
        image_grid_thw: Optional[paddle.Tensor] = None,
        video_grid_thw: Optional[paddle.Tensor] = None,
        second_per_grid_ts: Optional[paddle.Tensor] = None,
        attention_mask: Optional[paddle.Tensor] = None,
    ) -> Tuple[paddle.Tensor, paddle.Tensor]:
        """
        Calculate the 3D rope index based on image and video's temporal, height and width in LLM.

        Explanation:
            Each embedding sequence contains vision embedding and text embedding or just contains text embedding.

            For pure text embedding sequence, the rotary position embedding has no difference with modern LLMs.
            Examples:
                input_ids: [T T T T T], here T is for text.
                temporal position_ids: [0, 1, 2, 3, 4]
                height position_ids: [0, 1, 2, 3, 4]
                width position_ids: [0, 1, 2, 3, 4]

            For vision and text embedding sequence, we calculate 3D rotary position embedding for vision part
            and 1D rotary position embedding for text part.
            Examples:
                Temporal (Time): 3 patches, representing different segments of the video in time.
                Height: 2 patches, dividing each frame vertically.
                Width: 2 patches, dividing each frame horizontally.
                We also have some important parameters:
                fps (Frames Per Second): The video's frame rate, set to 1. This means one frame is processed each second.
                tokens_per_second: This is a crucial parameter. It dictates how many "time-steps" or "temporal tokens" are conceptually packed into a one-second interval of the video. In this case, we have 25 tokens per second. So each second of the video will be represented with 25 separate time points. It essentially defines the temporal granularity.
                temporal_patch_size: The number of frames that compose one temporal patch. Here, it's 2 frames.
                interval: The step size for the temporal position IDs, calculated as tokens_per_second * temporal_patch_size / fps. In this case, 25 * 2 / 1 = 50. This means that each temporal patch will be have a difference of 50 in the temporal position IDs.
                input_ids: [V V V V V V V V V V V V T T T T T], here V is for vision.
                vision temporal position_ids: [0, 0, 0, 0, 50, 50, 50, 50, 100, 100, 100, 100]
                vision height position_ids: [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
                vision width position_ids: [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
                text temporal position_ids: [101, 102, 103, 104, 105]
                text height position_ids: [101, 102, 103, 104, 105]
                text width position_ids: [101, 102, 103, 104, 105]
                Here we calculate the text start position_ids as the max vision position_ids plus 1.

        Args:
            input_ids (`paddle.Tensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary. Padding will be ignored by default should you provide
                it.
            image_grid_thw (`paddle.Tensor` of shape `(num_images, 3)`, *optional*):
                The temporal, height and width of feature shape of each image in LLM.
            video_grid_thw (`paddle.Tensor` of shape `(num_videos, 3)`, *optional*):
                The temporal, height and width of feature shape of each video in LLM.
            second_per_grid_ts (`paddle.Tensor` of shape `(num_videos)`, *optional*):
                The time interval (in seconds) for each grid along the temporal dimension in the 3D position IDs.
            attention_mask (`paddle.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

                - 1 for tokens that are **not masked**,
                - 0 for tokens that are **masked**.

        Returns:
            position_ids (`paddle.Tensor` of shape `(3, batch_size, sequence_length)`)
            mrope_position_deltas (`paddle.Tensor` of shape `(batch_size)`)
        """
        spatial_merge_size = self.config.vision_config.spatial_merge_size
        image_token_id = self.config.image_token_id
        video_token_id = self.config.video_token_id
        vision_start_token_id = self.config.vision_start_token_id
        mrope_position_deltas = []
        if input_ids is not None and (
            image_grid_thw is not None or video_grid_thw is not None
        ):
            total_input_ids = input_ids
            if attention_mask is None:
                attention_mask = paddle.ones_like(total_input_ids)
            position_ids = paddle.ones(
                [3, input_ids.shape[0], input_ids.shape[1]],
                dtype=input_ids.dtype,
            )
            image_index, video_index = 0, 0
            for i, input_ids in enumerate(total_input_ids):
                input_ids = input_ids[attention_mask[i] == 1]
                image_nums, video_nums = 0, 0
                vision_start_indices = paddle.nonzero(
                    input_ids == vision_start_token_id
                ).squeeze(1)
                vision_tokens = input_ids[vision_start_indices + 1]
                image_nums = (vision_tokens == image_token_id).sum()
                video_nums = (vision_tokens == video_token_id).sum()
                input_tokens = input_ids.tolist()
                llm_pos_ids_list: list = []
                st = 0
                remain_images, remain_videos = image_nums, video_nums
                for _ in range(image_nums + video_nums):
                    if image_token_id in input_tokens and remain_images > 0:
                        ed_image = input_tokens.index(image_token_id, st)
                    else:
                        ed_image = len(input_tokens) + 1
                    if video_token_id in input_tokens and remain_videos > 0:
                        ed_video = input_tokens.index(video_token_id, st)
                    else:
                        ed_video = len(input_tokens) + 1
                    if ed_image < ed_video:
                        t, h, w = (
                            image_grid_thw[image_index][0],
                            image_grid_thw[image_index][1],
                            image_grid_thw[image_index][2],
                        )
                        second_per_grid_t = 0
                        image_index += 1
                        remain_images -= 1
                        ed = ed_image

                    else:
                        t, h, w = (
                            video_grid_thw[video_index][0],
                            video_grid_thw[video_index][1],
                            video_grid_thw[video_index][2],
                        )
                        if second_per_grid_ts is not None:
                            second_per_grid_t = second_per_grid_ts[video_index]
                        else:
                            second_per_grid_t = 1.0
                        video_index += 1
                        remain_videos -= 1
                        ed = ed_video
                    llm_grid_t, llm_grid_h, llm_grid_w = (
                        t.item(),
                        h.item() // spatial_merge_size,
                        w.item() // spatial_merge_size,
                    )
                    text_len = ed - st

                    st_idx = (
                        llm_pos_ids_list[-1].max() + 1
                        if len(llm_pos_ids_list) > 0
                        else 0
                    )
                    llm_pos_ids_list.append(
                        paddle.arange(text_len).reshape((1, -1)).expand((3, -1))
                        + st_idx
                    )

                    if paddle.is_tensor(second_per_grid_t):
                        second_per_grid_t = second_per_grid_t.detach().item()
                    range_tensor = paddle.arange(llm_grid_t).reshape((-1, 1))
                    expanded_range = range_tensor.expand((-1, llm_grid_h * llm_grid_w))

                    time_tensor = (
                        expanded_range
                        * second_per_grid_t
                        * self.config.vision_config.tokens_per_second
                    )

                    time_tensor_long = time_tensor.astype("int64")
                    t_index = time_tensor_long.flatten()

                    h_index = (
                        paddle.arange(llm_grid_h)
                        .reshape((1, -1, 1))
                        .expand((llm_grid_t, -1, llm_grid_w))
                        .flatten()
                    )
                    w_index = (
                        paddle.arange(llm_grid_w)
                        .reshape((1, 1, -1))
                        .expand((llm_grid_t, llm_grid_h, -1))
                        .flatten()
                    )
                    llm_pos_ids_list.append(
                        paddle.stack([t_index, h_index, w_index]) + text_len + st_idx
                    )
                    st = ed + llm_grid_t * llm_grid_h * llm_grid_w

                if st < len(input_tokens):
                    st_idx = (
                        llm_pos_ids_list[-1].max() + 1
                        if len(llm_pos_ids_list) > 0
                        else 0
                    )
                    text_len = len(input_tokens) - st
                    llm_pos_ids_list.append(
                        paddle.arange(text_len).reshape((1, -1)).expand((3, -1))
                        + st_idx
                    )

                llm_positions = paddle.concat(llm_pos_ids_list, axis=1).reshape((3, -1))
                position_ids[..., i, attention_mask[i] == 1] = llm_positions
                mrope_position_deltas.append(
                    llm_positions.max() + 1 - len(total_input_ids[i])
                )
            mrope_position_deltas = paddle.to_tensor(mrope_position_deltas).unsqueeze(1)
            return position_ids, mrope_position_deltas
        else:
            if attention_mask is not None:
                position_ids = attention_mask.long().cumsum(-1) - 1
                position_ids.masked_fill_(attention_mask == 0, 1)
                position_ids = position_ids.unsqueeze(0).expand((3, -1, -1))
                max_position_ids = position_ids.max(0, keepdim=False)[0].max(
                    -1, keepdim=True
                )[0]
                mrope_position_deltas = max_position_ids + 1 - attention_mask.shape[-1]
            else:
                position_ids = (
                    paddle.arange(input_ids.shape[1])
                    .reshape((1, 1, -1))
                    .expand((3, input_ids.shape[0], -1))
                )
                mrope_position_deltas = paddle.zeros(
                    [input_ids.shape[0], 1],
                    dtype=input_ids.dtype,
                )

            return position_ids, mrope_position_deltas

    def prepare_attention_mask_for_generation(
        self, input_ids, pad_token_id, eos_token_id
    ):
        """Avoid using attention_mask with flash_attn on generation."""
        if self.config.use_flash_attention:
            return None
        return super().prepare_attention_mask_for_generation(
            input_ids, pad_token_id, eos_token_id
        )

    def prepare_inputs_for_generation(
        self,
        input_ids,
        use_cache=False,
        past_key_values=None,
        inputs_embeds=None,
        pixel_values=None,
        pixel_values_videos=None,
        position_ids=None,
        **kwargs,
    ):
        if past_key_values:
            input_ids = input_ids[:, -1:]
            pixel_values = None
            pixel_values_videos = None

        # if `inputs_embeds` are passed, we only want to use them in the 1st generation step
        if inputs_embeds is not None and past_key_values is None:
            model_inputs = {"inputs_embeds": inputs_embeds}
        else:
            model_inputs = {"input_ids": input_ids}

        model_inputs.update(
            {
                "past_key_values": past_key_values,
                "use_cache": use_cache,
                "pixel_values": pixel_values,
                "pixel_values_videos": pixel_values_videos,
                "position_ids": None,
                **kwargs,
            }
        )

        return model_inputs

    def update_model_kwargs_for_generation(
        self, outputs, model_kwargs, is_encoder_decoder=False
    ):
        """
        Updates model kwargs for generation.

        Args:
            outputs (Any): Model outputs.
            model_kwargs (dict): Current model kwargs.
            is_encoder_decoder (bool): Whether using encoder-decoder architecture.

        Returns:
            dict: Updated model kwargs.
        """
        # update cache
        if (
            isinstance(outputs, tuple)
            and len(outputs) > 1
            and not isinstance(outputs[1], paddle.Tensor)
        ):
            model_kwargs["past_key_values"] = outputs[1]

        if (
            isinstance(outputs, CausalLMOutputWithCrossAttentions)
            and "past_key_values" in outputs
        ):
            model_kwargs["past_key_values"] = outputs.past_key_values

        if (
            not is_encoder_decoder
            and model_kwargs.get("attention_mask", None) is not None
        ):
            # update attention mask
            attention_mask = model_kwargs["attention_mask"]
            model_kwargs["attention_mask"] = paddle.concat(
                [
                    attention_mask,
                    paddle.ones(
                        [attention_mask.shape[0], 1], dtype=attention_mask.dtype
                    ),
                ],
                axis=-1,
            )

        return model_kwargs

    def get_transpose_weight_keys(self):
        t_layers = [
            "out_proj",
            "q_proj",
            "k_proj",
            "v_proj",
            "lm_head",
            "gate_proj",
            "up_proj",
            "down_proj",
            "o_proj",
            "lm_head",
            "linear_1",
            "linear_2",
            "fc",
            "in_proj",
        ]
        keys = []
        for key, _ in self.get_hf_state_dict().items():
            for t_layer in t_layers:
                if t_layer in key and key.endswith("weight"):
                    keys.append(key)
        return keys

    def get_hf_state_dict(self, *args, **kwargs):
        def _merge_attention_weights(
            q_weight=None,
            k_weight=None,
            v_weight=None,
            q_bias=None,
            k_bias=None,
            v_bias=None,
        ):
            if q_weight is not None and k_weight is not None and v_weight is not None:
                return paddle.concat([q_weight, k_weight, v_weight], axis=1)
            elif q_bias is not None and k_bias is not None and v_bias is not None:
                return paddle.concat([q_bias, k_bias, v_bias], axis=0)
            else:
                raise ValueError

        def _convert_to_hf_state_dict(current_state_dict):
            hf_state_dict = {}

            for key in list(current_state_dict.keys()):
                if "up_gate_proj" in key:
                    combined_weights = current_state_dict[key]
                    split_size = combined_weights.shape[-1] // 2
                    gate_proj = combined_weights[..., :split_size]
                    up_proj = combined_weights[..., split_size:]

                    hf_state_dict[key.replace("up_gate_proj", "gate_proj")] = gate_proj
                    hf_state_dict[key.replace("up_gate_proj", "up_proj")] = up_proj
                    continue

                if "qkv_proj" in key and ("weight" in key or "bias" in key):
                    combined_weights = current_state_dict[key]
                    if getattr(self.config, "head_dim", None) is None:
                        head_dim = self.hidden_size // self.num_heads
                    else:
                        head_dim = self.config.head_dim
                    num_heads = self.config.num_attention_heads
                    num_kv_heads = self.config.num_key_value_heads
                    q_proj, k_proj, v_proj = paddle.split(
                        combined_weights,
                        [
                            num_heads * head_dim,
                            num_kv_heads * head_dim,
                            num_kv_heads * head_dim,
                        ],
                        axis=-1,
                    )

                    if "weight" in key:
                        hf_state_dict[
                            key.replace("qkv_proj.weight", "q_proj.weight")
                        ] = q_proj
                        hf_state_dict[
                            key.replace("qkv_proj.weight", "k_proj.weight")
                        ] = k_proj
                        hf_state_dict[
                            key.replace("qkv_proj.weight", "v_proj.weight")
                        ] = v_proj
                    else:  # bias
                        hf_state_dict[key.replace("qkv_proj.bias", "q_proj.bias")] = (
                            q_proj
                        )
                        hf_state_dict[key.replace("qkv_proj.bias", "k_proj.bias")] = (
                            k_proj
                        )
                        hf_state_dict[key.replace("qkv_proj.bias", "v_proj.bias")] = (
                            v_proj
                        )
                    continue

                if "up_gate_proj" not in key and "qkv_proj" not in key:
                    hf_state_dict[key] = current_state_dict[key]

            new_hf_state_dict = {}
            keys_to_remove = set()

            for key, value in hf_state_dict.items():
                if "head.attention" in key and "out_proj" not in key:
                    if "weight" in key:
                        q_key = key
                        k_key = key.replace("q_proj", "k_proj")
                        v_key = key.replace("q_proj", "v_proj")

                        if (
                            q_key in hf_state_dict
                            and k_key in hf_state_dict
                            and v_key in hf_state_dict
                        ):
                            merged_weights = _merge_attention_weights(
                                q_weight=hf_state_dict[q_key],
                                k_weight=hf_state_dict[k_key],
                                v_weight=hf_state_dict[v_key],
                            )
                            new_key = key.replace("q_proj.weight", "in_proj_weight")
                            new_hf_state_dict[new_key] = merged_weights
                            keys_to_remove.update([q_key, k_key, v_key])

                    elif "bias" in key:
                        q_key = key
                        k_key = key.replace("q_proj", "k_proj")
                        v_key = key.replace("q_proj", "v_proj")

                        if (
                            q_key in hf_state_dict
                            and k_key in hf_state_dict
                            and v_key in hf_state_dict
                        ):
                            merged_bias = _merge_attention_weights(
                                q_bias=hf_state_dict[q_key],
                                k_bias=hf_state_dict[k_key],
                                v_bias=hf_state_dict[v_key],
                            )
                            new_key = key.replace("q_proj.bias", "in_proj_bias")
                            new_hf_state_dict[new_key] = merged_bias
                            keys_to_remove.update([q_key, k_key, v_key])
                else:
                    new_hf_state_dict[key] = value

            for key in keys_to_remove:
                if key in new_hf_state_dict:
                    del new_hf_state_dict[key]

            return new_hf_state_dict

        current_state_dict = self.state_dict(*args, **kwargs)

        hf_state_dict = _convert_to_hf_state_dict(current_state_dict)

        return hf_state_dict

    def set_hf_state_dict(self, state_dict, *args, **kwargs):
        def _split_attention_weights(weight=None, bias=None):
            if weight is not None:
                split_size = weight.shape[1] // 3
                q_weight = weight[:, :split_size]
                k_weight = weight[:, split_size : 2 * split_size]
                v_weight = weight[:, 2 * split_size :]
                return q_weight, k_weight, v_weight
            elif bias is not None:
                split_size = bias.shape[0] // 3
                q_bias = bias[:split_size]
                k_bias = bias[split_size : 2 * split_size]
                v_bias = bias[2 * split_size :]
                return q_bias, k_bias, v_bias

        def _convert_state_dict(old_state_dict):
            new_state_dict = {}
            for key, value in old_state_dict.items():
                if "head.attention.in_proj" in key:
                    if key.endswith("weight"):
                        q_w, k_w, v_w = _split_attention_weights(weight=value)
                        new_state_dict[
                            key.replace("in_proj_weight", "q_proj.weight")
                        ] = q_w
                        new_state_dict[
                            key.replace("in_proj_weight", "k_proj.weight")
                        ] = k_w
                        new_state_dict[
                            key.replace("in_proj_weight", "v_proj.weight")
                        ] = v_w
                    elif key.endswith("bias"):
                        q_b, k_b, v_b = _split_attention_weights(bias=value)
                        new_state_dict[key.replace("in_proj_bias", "q_proj.bias")] = q_b
                        new_state_dict[key.replace("in_proj_bias", "k_proj.bias")] = k_b
                        new_state_dict[key.replace("in_proj_bias", "v_proj.bias")] = v_b
                    else:
                        raise ValueError(f"Unexpected key: {key}")
                else:
                    new_state_dict[key] = value

            for key in list(new_state_dict.keys()):
                if key.startswith("model."):
                    if "mlp.gate_proj." in key:
                        gate_proj = new_state_dict.pop(key)
                        up_proj = new_state_dict.pop(
                            key.replace("gate_proj", "up_proj")
                        )
                        new_state_dict[key.replace("gate_proj", "up_gate_proj")] = (
                            paddle.concat([gate_proj, up_proj], axis=-1)
                        )

                    if "self_attn.q_proj" in key:
                        q_proj = new_state_dict.pop(key)
                        k_proj = new_state_dict.pop(key.replace("q_proj", "k_proj"))
                        v_proj = new_state_dict.pop(key.replace("q_proj", "v_proj"))
                        new_state_dict[key.replace("q_proj", "qkv_proj")] = (
                            paddle.concat([q_proj, k_proj, v_proj], axis=-1)
                        )

            return new_state_dict

        state_dict = _convert_state_dict(state_dict)

        std_state_dict = self.state_dict()
        assert std_state_dict.keys() == state_dict.keys()
        for key in std_state_dict:
            v1 = std_state_dict[key]
            state_dict[key] = state_dict[key].to(v1.place)

        return self.set_state_dict(state_dict, *args, **kwargs)

    def forward(
        self,
        input_ids: paddle.Tensor = None,
        attention_mask: Optional[paddle.Tensor] = None,
        position_ids: Optional[paddle.Tensor] = None,
        past_key_values: Optional[List[paddle.Tensor]] = None,
        inputs_embeds: Optional[paddle.Tensor] = None,
        labels: Optional[paddle.Tensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        pixel_values: Optional[paddle.Tensor] = None,
        pixel_values_videos: Optional[paddle.Tensor] = None,
        image_grid_thw: Optional[paddle.Tensor] = None,
        video_grid_thw: Optional[paddle.Tensor] = None,
        rope_deltas: Optional[paddle.Tensor] = None,
        second_per_grid_ts: Optional[paddle.Tensor] = None,
        **kwargs,
    ) -> Union[Tuple, PaddleOCRVLCausalLMOutputWithPast]:
        output_attentions = (
            output_attentions
            if output_attentions is not None
            else self.config.output_attentions
        )
        output_hidden_states = (
            output_hidden_states
            if output_hidden_states is not None
            else self.config.output_hidden_states
        )
        return_dict = (
            return_dict if return_dict is not None else self.config.use_return_dict
        )

        curr_rope_deltas = self.rope_deltas_var.get()

        if inputs_embeds is None:
            if input_ids.shape[0] != 1:
                raise NotImplementedError
            inputs_embeds = self.model.embed_tokens(input_ids)
            if pixel_values is not None:
                pixel_values = pixel_values.astype(inputs_embeds.dtype)
                pixel_values = pixel_values.unsqueeze(0)
                siglip_position_ids = list()
                image_grid_hws = list()
                sample_indices = list()
                cu_seqlens = [0]

                pro = 0
                for idx, thw in enumerate(image_grid_thw):
                    thw_tuple = tuple(thw.detach().cpu().numpy().tolist())
                    numel = np.prod(thw_tuple)
                    image_grid_hws.append(thw_tuple)
                    image_position_ids = paddle.arange(numel) % np.prod(thw_tuple[1:])
                    siglip_position_ids.append(image_position_ids)
                    sample_indices.append(
                        paddle.full((numel,), idx, dtype=paddle.int64)
                    )
                    cu_seqlens.append(cu_seqlens[-1] + numel)

                siglip_position_ids = paddle.concat(siglip_position_ids, axis=0)
                cu_seqlens = paddle.to_tensor(cu_seqlens, dtype=paddle.int32)
                sample_indices = paddle.concat(sample_indices, axis=0)

                vision_outputs = self.visual(
                    pixel_values=pixel_values,
                    image_grid_thw=image_grid_hws,
                    position_ids=siglip_position_ids,
                    vision_return_embed_list=True,
                    interpolate_pos_encoding=True,
                    sample_indices=sample_indices,
                    cu_seqlens=cu_seqlens,
                    return_pooler_output=False,
                    use_rope=True,
                    window_size=-1,
                )
                image_embeds = vision_outputs.last_hidden_state

                image_embeds = self.mlp_AR(image_embeds, image_grid_thw)

                n_image_tokens = (input_ids == self.config.image_token_id).sum().item()
                image_embeds = paddle.concat(image_embeds, axis=0)
                n_image_features = image_embeds.shape[0]
                if n_image_tokens != n_image_features:
                    raise ValueError(
                        f"Image features and image tokens do not match: tokens: {n_image_tokens}, features {n_image_features}"
                    )

                mask = input_ids == self.config.image_token_id
                mask_unsqueezed = mask.unsqueeze(-1)
                mask_expanded = mask_unsqueezed.expand_as(inputs_embeds)
                image_mask = mask_expanded

                image_embeds = image_embeds.astype(inputs_embeds.dtype)

                inputs_embeds = inputs_embeds.masked_scatter(image_mask, image_embeds)
        else:
            if inputs_embeds.shape[0] != 1:
                raise NotImplementedError

        if attention_mask is not None and attention_mask.dtype != paddle.bool:
            attention_mask = paddle.cast(attention_mask, paddle.bool)

        # position_ids = None
        # if we get 4D attention mask we cannot calculate rope deltas anymore. TODO @raushan fixme
        if position_ids is None and (
            attention_mask is None or attention_mask.ndim == 2
        ):
            # calculate RoPE index once per generation in the pre-fill stage only
            if curr_rope_deltas is None or (
                past_key_values is None or past_key_values[0] is None
            ):
                position_ids, rope_deltas = self.get_rope_index(
                    input_ids,
                    image_grid_thw,
                    video_grid_thw,
                    second_per_grid_ts,
                    attention_mask,
                )
                self.rope_deltas_var.set(rope_deltas)
            # then use the prev pre-calculated rope-deltas to get the correct position ids
            else:
                batch_size, seq_length, _ = inputs_embeds.shape
                delta = (
                    (past_key_values[0][0].shape[1] + curr_rope_deltas)
                    if past_key_values is not None and past_key_values[0] is not None
                    else 0
                )
                position_ids = paddle.arange(seq_length)
                position_ids = position_ids.reshape((1, -1)).expand((batch_size, -1))
                if (
                    past_key_values is not None and past_key_values[0] is not None
                ):  # otherwise `deltas` is an int `0`
                    delta = delta.repeat_interleave(
                        batch_size // delta.shape[0], axis=0
                    )
                position_ids = position_ids.add(delta)
                position_ids = position_ids.unsqueeze(0).expand((3, -1, -1))

        outputs = self.model(
            input_ids=None,
            position_ids=position_ids,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            **kwargs,
        )

        hidden_states = outputs[0]
        logits = self.lm_head(hidden_states)

        loss = None
        if labels is not None:
            # Upcast to float if we need to compute the loss to avoid potential precision issues
            logits = logits.astype("float32")
            # Shift so that tokens < n predict n
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            # Flatten the tokens
            loss_fct = paddle.nn.CrossEntropyLoss()
            shift_logits = shift_logits.reshape((-1, self.config.vocab_size))
            shift_labels = shift_labels.reshape((-1,))
            loss = loss_fct(shift_logits, shift_labels)

        if not return_dict:
            output = (logits,) + outputs[1:]
            return (loss,) + output if loss is not None else output

        return PaddleOCRVLCausalLMOutputWithPast(
            loss=loss,
            logits=logits,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            rope_deltas=curr_rope_deltas,
        )

    def generate(self, inputs, **kwargs):
        gen_kwargs = {
            "max_new_tokens": kwargs.get("max_new_tokens", 8192),
            "use_cache": kwargs.get("use_cache", True),
        }
        gen_kwargs = {**inputs, **gen_kwargs}
        with paddle.no_grad():
            generated_ids = super().generate(**gen_kwargs)
        return generated_ids

    def _get_image_nums_and_video_nums(
        self,
        input_ids: Optional[paddle.Tensor],
    ) -> Tuple[paddle.Tensor, paddle.Tensor]:
        """
        Get the number of images and videos for each sample to calculate the separation length of the sample tensor.
        These parameters are not passed through the processor to avoid unpredictable impacts from interface modifications.

        Args:
            input_ids (`paddle.Tensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary.

        Returns:
            image_nums (`paddle.Tensor` of shape `(batch_size, num_images_sample)`)
            video_nums (`paddle.Tensor` of shape `(batch_size, num_videos_sample)`)
        """
        image_token_id = self.config.image_token_id
        video_token_id = self.config.video_token_id
        vision_start_token_id = self.config.vision_start_token_id

        vision_start_mask = input_ids == vision_start_token_id
        vision_first_mask = paddle.roll(vision_start_mask, shifts=1, axis=1)
        image_mask = input_ids == image_token_id
        video_mask = input_ids == video_token_id
        image_nums = paddle.sum(vision_first_mask & image_mask, axis=1)
        video_nums = paddle.sum(vision_first_mask & video_mask, axis=1)

        return image_nums, video_nums
