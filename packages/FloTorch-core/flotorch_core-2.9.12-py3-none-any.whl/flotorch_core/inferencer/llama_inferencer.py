from typing import List, Dict, Tuple, Any
import logging
import time
import random
from .sagemaker_inferencer import SageMakerInferencer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LlamaInferencer(SageMakerInferencer):
    def __init__(self, model_id: str, region: str, role_arn: str, n_shot_prompts: int = 0, temperature: float = 0.7, n_shot_prompt_guide_obj: Dict[str, List[Dict[str, str]]] = None, max_tokens: int = 512, topP: int = 0.9):
        super().__init__(model_id, region, role_arn, n_shot_prompts, temperature, n_shot_prompt_guide_obj, max_tokens, topP)
        
    def _prepare_conversation(self, message: str, role: str):
        # Format message and role into a conversation
        if not message or not role:
            logger.error(f"Error in parsing message or role")
        conversation = {
                "role": role, 
                "content": message
            }
        return conversation
    
    def generate_prompt(self, user_query: str, context: List[Dict], use_system: bool) -> Tuple[str, List[Dict[str, Any]]]:
        # Input validation
        if self.n_shot_prompts < 0:
            raise ValueError("n_shot_prompt must be non-negative")
        
        # Get system prompt
        system_prompt = None
        if use_system:
            system_prompt = self.n_shot_prompt_guide_obj.get("system_prompt", "") if self.n_shot_prompt_guide_obj and self.n_shot_prompt_guide_obj.get("system_prompt") else DEFAULT_SYSTEM_PROMPT
            
        context_text = ""
        if context:
            context_text = self.format_context(user_query, context)
        
        base_prompt = self.n_shot_prompt_guide_obj.get("user_prompt", "") if self.n_shot_prompt_guide_obj else ""
        
        if self.n_shot_prompts == 0:
            logger.info("into zero shot prompt")
    
            messages = []
            messages.append(self._prepare_conversation(role="user", message=base_prompt))
            if context_text:
                messages.append(self._prepare_conversation(role="user", message=context_text))
            messages.append(self._prepare_conversation(role="user", message=user_query))

            return system_prompt, messages

        # Get examples if nshot is not zero
        examples = self.n_shot_prompt_guide_obj['examples']
        
        # Format examples
        selected_examples = (random.sample(examples, n_shot_prompt) 
                        if len(examples) > n_shot_prompt 
                        else examples)
        
        logger.info(f"into {n_shot_prompt} shot prompt  with examples {len(selected_examples)}")
        
        messages = []
        messages.append(self._prepare_conversation(role="user", message=base_prompt))
        for example in selected_examples:
            if 'example' in example:
                messages.append(self._prepare_conversation(role="user", message=example['example']))
            elif 'question' in example and 'answer' in example:
                messages.append(self._prepare_conversation(role="user", message=example['question']))
                messages.append(self._prepare_conversation(role="assistant", message=example['answer']))
        
        if context_text:
            messages.append(self._prepare_conversation(role="user", message=context_text))
            
        messages.append(self._prepare_conversation(role="user", message=user_query))

        return system_prompt, messages
        
    def construct_payload(self, system_prompt: str, prompt: str) -> dict:
        """
        Constructs llama 4 payload dictionary for model inference with the given prompts and default parameters.
        
        Args:
            system_prompt (str): The system-level prompt that guides the model's behavior
            prompt (str): The actual prompt/query to be sent to the model

        """
        # Define default parameters for the model's generation
        default_params = {
            "temperature": self.temperature,
            "do_sample": True
            }
        for param, value in [
            ("max_new_tokens", self.max_tokens),
            ("top_p", self.topP)
        ]:
            if value is not None:
                default_params[param] = value    
        
        # Prepare payload for model inference
        payload = {
            "system": system_prompt,
            "messages": prompt,
            "parameters": default_params
            }
        
        return payload
    
    def _extract_response(self, response: dict) -> str:
        """
        Parses the response from the model and extracts the generated text.

        Args:
            response (dict): The raw response from the model
        """
        if "choices" in response and isinstance(response["choices"], list):
            return response["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"Unexpected Llama-4 response format: {response}")
        