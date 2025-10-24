# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Lora params for bert_base_uncased"""

from .lora_base import BaseLora, LoraBlockConstants
from typing import Dict, Any


class LoraMbart(BaseLora):
    """Class for defining Lora Params for bert_base_uncased"""

    # TODO Warp the lora_r, alpha and dropout into a dataclass
    def __init__(self, lora_r, lora_alpha, lora_dropout, merge_weights):
        """initializing lora params"""
        super().__init__(lora_r, lora_alpha, lora_dropout, merge_weights)

    def get_lora_blocks_meta_data(self) -> Dict[str, Any]:
        """lora block meta data"""
        return {
            "self_attn": {
                LoraBlockConstants.LayersToModify: ["q_proj", "v_proj"],
                LoraBlockConstants.LoraLayer: "Linear"
            },
            "encoder_attn": {
                LoraBlockConstants.LayersToModify: ["q_proj", "v_proj"],
                LoraBlockConstants.LoraLayer: "Linear"
            }
        }
