"""Note processor agent for classifying and summarizing notes."""

import json
import torch
from typing import Any, Dict, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from .base_agent import BaseAgent


class NoteProcessorAgent(BaseAgent):
    """Agent for processing, classifying, and summarizing notes using a local LLM."""

    def __init__(
        self,
        model_id: str = "microsoft/Phi-3.5-mini-instruct",
        quantize: bool = True,
        device: str = "cuda",
    ):
        """
        Initialize the note processor agent with a language model.

        Args:
            model_id: The Hugging Face model ID to use
            quantize: Whether to use 4-bit quantization
            device: Device to load the model on ('cuda' or 'cpu')
        """
        super().__init__(name="NoteProcessor")
        self.model_id = model_id
        self.quantize = quantize
        self.device = device
        self.device_map = device
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.is_loaded = False

        # System prompt for note classification and summarization
        self.system_prompt = """
You are a helpful assistant that classifies notes into categories in a neat book keeping style and summarizes the content in individual notes.

You are tasked with the following:

1. Classify the notes into the following categories (might not have content for all categories):
- Computer Science; can include subcategories like AI, ML, Data Science or even applied areas like Biology, drug discovery since I work in the biotechnology industry as a software engineer.
- Investments; this can include notes related to stock market, personal finance, investment strategies, or any financial insights.
- Daily Journal; this will include personal reflections, thoughts, and experiences that are not directly related to work or specific study topics. It can cover a wide range of subjects, including emotions, relationships, hobbies, and general life events.
- Health and Fitness; this category will encompass notes related to physical and mental well-being, including exercise routines, dietary habits, mindfulness practices, and any insights or observations related to maintaining a healthy lifestyle.

2. Summarize this note in 2-3 sentences, highlighting the key points and insights.
3. Provide 3-5 relevant tags for each note, which could be used for organizing and searching the notes later.

You MUST generate the output as a JSON object with the following format:
{
   "Computer Science": {
      "Summary": "Your summary here",
      "Tags": ["tag1", "tag2", "tag3"]
   },
   "Daily Journal": {
      "Summary": "Your summary here",
      "Tags": ["tag1", "tag2", "tag3"]
   },
   "Health and Fitness": {
      "Summary": "Your summary here",
      "Tags": ["tag1", "tag2", "tag3"]
   },
   "Investments": {
      "Summary": "Your summary here",
      "Tags": ["tag1", "tag2", "tag3"]
   }
}

Notes from different categories can be present in the same note, so make sure to classify and summarize each relevant category separately. 
Only include categories that have content in the note. Return ONLY valid JSON, no additional text. 
"""

    def _extract_json_object(self, text: str) -> str:
        """
        Extract the first complete JSON object from model output.

        Handles common LLM artifacts like markdown code fences or extra text
        before/after the JSON object.
        """
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        start = cleaned.find("{")
        if start == -1:
            raise json.JSONDecodeError("No JSON object found in response", cleaned, 0)

        depth = 0
        in_string = False
        escape = False

        for idx in range(start, len(cleaned)):
            char = cleaned[idx]

            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return cleaned[start : idx + 1]

        raise json.JSONDecodeError("Incomplete JSON object in response", cleaned, start)

    def load_model(self) -> None:
        """Load the language model and tokenizer."""
        print(f"Loading model {self.model_id}...")
        if torch.cuda.is_available():
            print(f"CUDA is available. GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        else:
            print("CUDA is not available. Using CPU (this may be slow)")

        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

        # Configure quantization if requested
        config = None
        if self.quantize and torch.cuda.is_available():
            config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            quantization_config=config,
            device_map=self.device_map,
            trust_remote_code=False,
        )

        self.is_loaded = True
        print("Model loaded successfully!")

    def process(self, note_content: str) -> Dict[str, Any]:
        """
        Process a note by classifying and summarizing it.

        Args:
            note_content: The content of the note to process

        Returns:
            Dictionary containing the classification and summary results
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Add user message to history
        self.add_human_message(note_content)

        # Prepare the prompt
        messages = [{"role": "user", "content": self.system_prompt + "\n\nNote:\n" + note_content}]

        # Apply chat template and generate response
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=1024)

        # Decode the response
        generated_tokens = outputs[0][inputs.input_ids.shape[1] :]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        # Parse JSON response
        try:
            json_payload = self._extract_json_object(response)
            result = json.loads(json_payload)
            ai_message = f"Successfully classified and summarized note into {len(result)} categories"
            self.add_ai_message(ai_message)
            return {
                "status": "success",
                "classification": result,
                "note_content": note_content,
            }
        except json.JSONDecodeError as e:
            self.add_ai_message(f"Error parsing classification: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to parse LLM response: {str(e)}",
                "raw_response": response,
            }

    def process_batch(self, notes: list) -> Dict[str, Any]:
        """
        Process multiple notes in batch.

        Args:
            notes: List of note contents to process

        Returns:
            Dictionary containing results for all notes
        """
        results = []
        for i, note in enumerate(notes):
            print(f"Processing note {i + 1}/{len(notes)}...")
            result = self.process(note)
            results.append(result)

        return {
            "status": "success",
            "processed_notes": len(notes),
            "results": results,
        }
