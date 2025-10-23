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

"""Verifies the reauthored decoder of PaliGemma2 3B model."""

import logging

from absl import app
from absl import flags
from ai_edge_torch.generative.examples.paligemma import decoder2
from ai_edge_torch.generative.utilities import transformers_verifier
from ai_edge_torch.generative.utilities import verifier
import kagglehub
import transformers

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
  checkpoint = kagglehub.model_download(
      "google/paligemma-2/transformers/paligemma2-3b-pt-224"
  )
  logging.info("Loading the original model from: %s", checkpoint)
  original_full_model = (
      transformers.PaliGemmaForConditionalGeneration.from_pretrained(checkpoint)
  )
  original_language_model = original_full_model.eval().language_model

  logging.info("Building the reauthored model from: %s", checkpoint)
  reauthored_model = decoder2.build_decoder2(
      checkpoint, mask_cache_size=verifier.DEFAULT_KV_CACHE_MAX_LEN
  )

  logging.info("Loading the tokenizer from: %s", checkpoint)
  # It works only when GemmaTokenizerFast is available. In some environments,
  # use_fast=False doeesn't work either if the tokenizer cannot load the
  # sentencepiece model file properly.
  processor = transformers.AutoProcessor.from_pretrained(checkpoint)

  verifier.verify_reauthored_model(
      original_model=transformers_verifier.TransformersModelWrapper(
          original_language_model
      ),
      reauthored_model=verifier.ReauthoredModelWrapper(reauthored_model),
      tokenizer=verifier.TokenizerWrapper(processor.tokenizer),
      generate_prompts=_PROMPTS.value,
      max_new_tokens=_MAX_NEW_TOKENS.value,
      atol=1e-04,
  )


if __name__ == "__main__":
  app.run(main)
