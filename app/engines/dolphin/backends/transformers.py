import asyncio
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

from app.engines.dolphin.backends.base import DolphinBackend
from app.engines.dolphin.utils import resize_image


class TransformersBackend(DolphinBackend):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = None

    async def initialize(self) -> None:
        print(f"[TransformersBackend] Loading model {self.model_name}...")

        def load_model():
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(self.model_name)
            self.model.eval()

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)

            if self.device == "cuda":
                self.model = self.model.bfloat16()
            else:
                self.model = self.model.float()

            self.processor.tokenizer.padding_side = "left"

        await asyncio.to_thread(load_model)
        print(f"[TransformersBackend] Model loaded on {self.device}")

    async def health_check(self) -> bool:
        return self.model is not None

    async def cleanup(self) -> None:
        if self.model:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    async def chat(self, prompt: str, image: Image.Image) -> str:
        return await asyncio.to_thread(self._inference, prompt, image)

    def _inference(self, prompt: str, image: Image.Image) -> str:
        resized = resize_image(image)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": resized},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, _ = process_vision_info(messages)

        inputs = self.processor(text=[text], images=image_inputs, padding=True, return_tensors="pt")
        inputs = inputs.to(self.model.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=4096, do_sample=False)
        generated_ids_trimmed = generated_ids[0][len(inputs.input_ids[0]):]

        return self.processor.decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
