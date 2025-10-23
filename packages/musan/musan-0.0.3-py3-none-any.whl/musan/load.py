# Copyright [2024] [Nikita Karpov]

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import torch
from huggingface_hub import hf_hub_download

from .model import SpectrogramTransformer, SmallSpectrogramTransformer


OUTPUT_DIMS = 2

device = "cuda" if torch.cuda.is_available() else "cpu"

def load_pretraned_hs_model():
    # Model loading.
    model_hs = SpectrogramTransformer(OUTPUT_DIMS, dropout=0., device=device).to(device)

    model_path = hf_hub_download(
        repo_id="nikarpoff/music-sentiment-analysis-happy-sad-13M",
        filename="msa_hs_13M.pth"
    )

    model_hs.load_state_dict(
        torch.load(
            model_path,
            map_location=device,
            weights_only=True
        )
    )

    return model_hs
    

def load_pretraned_re_model():
    # Model loading.
    model_re = SmallSpectrogramTransformer(OUTPUT_DIMS, dropout=0., device=device).to(device)

    model_path = hf_hub_download(
        repo_id="nikarpoff/music-sentiment-analysis-relaxing-energetic-8M",
        filename="msa_re_8M.pth"
    )
    
    model_re.load_state_dict(
        torch.load(
            model_path,
            map_location=device,
            weights_only=True
        )
    )

    return model_re

def load_pretraned_models():
    return load_pretraned_hs_model(), load_pretraned_re_model()
