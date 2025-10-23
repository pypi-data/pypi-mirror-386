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

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from datetime import datetime
import torch
import numpy as np

from .model import *
from .utils import SpectrogramProcessor, inference

TIMESTAMP_FORMAT = "%d.%m.%Y %H:%M:%S"

classes_hs = ["happy", "sad"]
classes_re = ["energetic", "relaxing"]

device = "cuda" if torch.cuda.is_available() else "cpu"

specs_processor = SpectrogramProcessor(device=device)

def predict(audio_bytes, model_hs=None, model_re=None, verbose=True):
    if not model_hs and not model_re:
        print("You must provide at least one model to use predict.")
        return None

    # Form mel-spectrogram
    try:
        spec = specs_processor.pipeline(audio_bytes)
    except ValueError as e:
        print(f"{datetime.now().strftime(TIMESTAMP_FORMAT)}: Error processing audio: {e}")
        return None

    if verbose:
        # Log current time.
        start_time = datetime.now()
        print(f"{start_time.strftime(TIMESTAMP_FORMAT)}: spec shape: {spec.shape}")

    classes = []
    probabilities = []

    # Make prediction.
    if model_hs:
        hs_probs = inference(model_hs, spec.to(model_hs.device, non_blocking=True))
        classes.extend(classes_hs)
        probabilities.extend(hs_probs.tolist())

    if model_re:
        re_probs = inference(model_re, spec.to(model_re.device, non_blocking=True))
        classes.extend(classes_re)
        probabilities.extend(re_probs.tolist())

    if verbose:
        # Log prediction time.
        end_time = datetime.now()
        print(f"{end_time.strftime(TIMESTAMP_FORMAT)}: prediction time: {end_time - start_time}; running on {device}")

    # Form result.
    prediction = classes[np.argmax(probabilities)]
    
    result = {
        "predict": prediction
    }

    for i, mood_class in enumerate(classes):
        result[mood_class] = probabilities[i]

    return result
