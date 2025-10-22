# Copyright 2024 The AI Edge Torch Authors.
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
# ==============================================================================

"""Example of building a SmolLM model."""

from typing import Callable, Dict
import ai_edge_torch.generative.layers.model_config as cfg
from ai_edge_torch.generative.utilities import model_builder
import torch
from torch import nn

TENSOR_NAMES = model_builder.TENSOR_NAMES


class SmolLM(model_builder.DecoderOnlyModel):
  """A SmolLM model built from the Edge Generative API layers."""
  pass


def get_model_config() -> cfg.ModelConfig:
  """Returns the model config for a SmolLM 135M model."""
  attn_config = cfg.AttentionConfig(
      num_heads=9,
      head_dim=64,
      num_query_groups=3,
      rotary_base=10000,
      rotary_percentage=1.0,
  )
  ff_config = cfg.FeedForwardConfig(
      type=cfg.FeedForwardType.GATED,
      activation=cfg.ActivationConfig(cfg.ActivationType.SILU),
      intermediate_size=1536,
  )
  norm_config = cfg.NormalizationConfig(type=cfg.NormalizationType.RMS_NORM)
  block_config = cfg.TransformerBlockConfig(
      attn_config=attn_config,
      ff_config=ff_config,
      pre_attention_norm_config=norm_config,
      post_attention_norm_config=norm_config,
  )
  config = cfg.ModelConfig(
      vocab_size=49152,
      num_layers=30,
      max_seq_len=2048,
      embedding_dim=576,
      block_configs=block_config,
      final_norm_config=norm_config,
  )
  return config


def get_fake_model_config() -> cfg.ModelConfig:
  config = get_model_config()
  config.vocab_size = 128
  config.num_layers = 2
  # SmolLM has only one block config.
  config.block_config(0).ff_config.intermediate_size = 64
  return config


def build_model(
    checkpoint_path: str,
    custom_loader: Callable[[str], Dict[str, torch.Tensor]] = None,
    mask_cache_size: int = 0,
) -> nn.Module:
  return model_builder.build_decoder_only_model(
      checkpoint_path=checkpoint_path,
      config=get_model_config(),
      tensor_names=TENSOR_NAMES,
      model_class=SmolLM,
      custom_loader=custom_loader,
      mask_cache_size=mask_cache_size,
  )


class SmolLM2(model_builder.DecoderOnlyModel):
  """A SmolLM2 model built from the Edge Generative API layers."""
  pass


def get_model_config_v2() -> cfg.ModelConfig:
  """Returns the model config for a SmolLM2 135M model."""
  config = get_model_config()
  config.block_config(0).attn_config.rotary_base = 100000
  return config


def get_fake_model_config_v2() -> cfg.ModelConfig:
  config = get_model_config_v2()
  config.vocab_size = 128
  config.num_layers = 2
  # SmolLM2 has only one block config.
  config.block_config(0).ff_config.intermediate_size = 64
  return config


def build_model_v2(
    checkpoint_path: str,
    custom_loader: Callable[[str], Dict[str, torch.Tensor]] = None,
    mask_cache_size: int = 0,
) -> nn.Module:
  return model_builder.build_decoder_only_model(
      checkpoint_path=checkpoint_path,
      config=get_model_config_v2(),
      tensor_names=TENSOR_NAMES,
      model_class=SmolLM2,
      custom_loader=custom_loader,
      mask_cache_size=mask_cache_size,
  )
