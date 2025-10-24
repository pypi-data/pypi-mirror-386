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

"""Verifies the reauthored Gemma1 model."""

import logging
from absl import app
from absl import flags
from ai_edge_torch.generative.examples.gemma import gemma1
from ai_edge_torch.generative.examples.gemma import verify_util
from ai_edge_torch.generative.utilities import verifier
import kagglehub


_PROMPTS = flags.DEFINE_multi_string(
    "prompts",
    "What is the meaning of life?",
    "The input prompts to generate answers.",
)
_MAX_NEW_TOKENS = flags.DEFINE_integer(
    "max_new_tokens",
    30,
    "The maximum size of the generated tokens.",
)


def main(_):
  checkpoint = kagglehub.model_download("google/gemma/pyTorch/2b-it")

  logging.info("Building the reauthored model from: %s", checkpoint)
  reauthored_model = gemma1.build_2b_model(
      checkpoint, mask_cache_size=verifier.DEFAULT_KV_CACHE_MAX_LEN
  )

  verify_util.verify_reauthored_gemma_model(
      checkpoint=checkpoint,
      variant="2b",
      reauthored_model=reauthored_model,
      weight_filename="gemma-2b-it.ckpt",
      generate_prompts=_PROMPTS.value,
      forward_input_ids=[[1, 2, 3, 4]],
      max_new_tokens=_MAX_NEW_TOKENS.value,
  )


if __name__ == "__main__":
  app.run(main)
