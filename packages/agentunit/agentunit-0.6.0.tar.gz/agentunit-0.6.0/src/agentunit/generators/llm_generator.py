"""LLM-powered dataset generators using Llama and OpenAI models."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..datasets.base import DatasetCase, DatasetSource

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from huggingface_hub import InferenceClient
    HAS_HF_HUB = True
except ImportError:
    HAS_HF_HUB = False


@dataclass
class GeneratorConfig:
    """Configuration for dataset generation."""
    
    num_cases: int = 10
    temperature: float = 0.8
    max_tokens: int = 2048
    diversity_penalty: float = 0.5
    include_edge_cases: bool = True
    edge_case_ratio: float = 0.3


class LlamaDatasetGenerator:
    """Generate synthetic datasets using Llama models via HuggingFace Inference API."""
    
    def __init__(
        self, 
        model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct",
        api_token: Optional[str] = None,
        config: Optional[GeneratorConfig] = None
    ):
        """Initialize Llama dataset generator.
        
        Args:
            model: Llama model name on HuggingFace
            api_token: HuggingFace API token
            config: Generation configuration
        """
        if not HAS_HF_HUB:
            raise ImportError(
                "huggingface_hub required for LlamaDatasetGenerator. "
                "Install with: pip install huggingface_hub"
            )
        
        self.model = model
        self.client = InferenceClient(token=api_token)
        self.config = config or GeneratorConfig()
    
    def _create_generation_prompt(self, domain: str, task_description: str) -> str:
        """Create a prompt for synthetic dataset generation."""
        return f"""You are an expert test case generator for AI agent evaluation.

Domain: {domain}
Task: {task_description}

Generate {self.config.num_cases} diverse test cases for evaluating an AI agent on this task.
Each test case should include:
1. A unique query/question
2. Expected output or behavior
3. Difficulty level (easy/medium/hard)
4. Any relevant metadata

Format your response as a JSON array of test cases:
[
  {{
    "id": "case_1",
    "query": "...",
    "expected_output": "...",
    "difficulty": "easy|medium|hard",
    "metadata": {{}}
  }},
  ...
]

Make sure to include:
- {int(self.config.num_cases * (1 - self.config.edge_case_ratio))} typical cases
- {int(self.config.num_cases * self.config.edge_case_ratio)} edge cases (boundary conditions, ambiguous inputs, adversarial examples)

Ensure diversity in query formulation and complexity."""
    
    async def generate(
        self, 
        domain: str, 
        task_description: str,
        constraints: Optional[List[str]] = None
    ) -> DatasetSource:
        """Generate synthetic dataset.
        
        Args:
            domain: Domain of the task (e.g., "customer service", "code review")
            task_description: Detailed description of what the agent should do
            constraints: Optional list of constraints or requirements
        
        Returns:
            DatasetSource with generated cases
        """
        prompt = self._create_generation_prompt(domain, task_description)
        
        if constraints:
            prompt += f"\n\nAdditional constraints:\n" + "\n".join(f"- {c}" for c in constraints)
        
        # Generate with Llama
        response = await asyncio.to_thread(
            self.client.text_generation,
            prompt=prompt,
            model=self.model,
            max_new_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            return_full_text=False
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            cases_data = json.loads(response_text)
            
            cases = []
            for case_data in cases_data:
                case = DatasetCase(
                    id=case_data.get("id", f"generated_{len(cases)}"),
                    query=case_data["query"],
                    expected_output=case_data.get("expected_output"),
                    metadata={
                        "difficulty": case_data.get("difficulty", "medium"),
                        "generated": True,
                        "domain": domain,
                        **case_data.get("metadata", {})
                    }
                )
                cases.append(case)
            
            return DatasetSource.from_list(
                cases, 
                name=f"llama_generated_{domain.replace(' ', '_')}"
            )
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse generated dataset: {e}\nResponse: {response}")
    
    def generate_sync(
        self, 
        domain: str, 
        task_description: str,
        constraints: Optional[List[str]] = None
    ) -> DatasetSource:
        """Synchronous version of generate."""
        return asyncio.run(self.generate(domain, task_description, constraints))


class OpenAIDatasetGenerator:
    """Generate synthetic datasets using OpenAI models (GPT-4, etc.)."""
    
    def __init__(
        self, 
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        config: Optional[GeneratorConfig] = None
    ):
        """Initialize OpenAI dataset generator.
        
        Args:
            model: OpenAI model name
            api_key: OpenAI API key
            config: Generation configuration
        """
        if not HAS_OPENAI:
            raise ImportError(
                "openai required for OpenAIDatasetGenerator. "
                "Install with: pip install openai"
            )
        
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.config = config or GeneratorConfig()
    
    def _create_generation_prompt(self, domain: str, task_description: str) -> str:
        """Create a prompt for synthetic dataset generation."""
        return f"""You are an expert test case generator for AI agent evaluation.

Domain: {domain}
Task: {task_description}

Generate {self.config.num_cases} diverse test cases for evaluating an AI agent on this task.
Each test case should include:
1. A unique query/question
2. Expected output or behavior
3. Difficulty level (easy/medium/hard)
4. Any relevant metadata

Format your response as a JSON array only, with no additional text:
[
  {{
    "id": "case_1",
    "query": "...",
    "expected_output": "...",
    "difficulty": "easy|medium|hard",
    "metadata": {{}}
  }}
]

Distribution:
- {int(self.config.num_cases * (1 - self.config.edge_case_ratio))} typical cases
- {int(self.config.num_cases * self.config.edge_case_ratio)} edge cases (boundary conditions, ambiguous inputs, adversarial examples)

Ensure diversity in query formulation and complexity."""
    
    async def generate(
        self, 
        domain: str, 
        task_description: str,
        constraints: Optional[List[str]] = None,
        seed_examples: Optional[List[Dict[str, Any]]] = None
    ) -> DatasetSource:
        """Generate synthetic dataset.
        
        Args:
            domain: Domain of the task
            task_description: Detailed description of what the agent should do
            constraints: Optional list of constraints
            seed_examples: Optional seed examples to guide generation
        
        Returns:
            DatasetSource with generated cases
        """
        messages = [
            {"role": "system", "content": "You are an expert test case generator."},
            {"role": "user", "content": self._create_generation_prompt(domain, task_description)}
        ]
        
        if constraints:
            messages[1]["content"] += f"\n\nAdditional constraints:\n" + "\n".join(f"- {c}" for c in constraints)
        
        if seed_examples:
            messages[1]["content"] += f"\n\nSeed examples:\n{json.dumps(seed_examples, indent=2)}"
        
        # Generate with GPT
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"} if "gpt-4" in self.model else None
        )
        
        response_text = response.choices[0].message.content
        
        # Parse JSON response
        try:
            # Handle potential wrapping
            if not response_text.strip().startswith("["):
                # Try to extract JSON array
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            cases_data = json.loads(response_text)
            
            cases = []
            for case_data in cases_data:
                case = DatasetCase(
                    id=case_data.get("id", f"generated_{len(cases)}"),
                    query=case_data["query"],
                    expected_output=case_data.get("expected_output"),
                    metadata={
                        "difficulty": case_data.get("difficulty", "medium"),
                        "generated": True,
                        "domain": domain,
                        **case_data.get("metadata", {})
                    }
                )
                cases.append(case)
            
            return DatasetSource.from_list(
                cases, 
                name=f"openai_generated_{domain.replace(' ', '_')}"
            )
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse generated dataset: {e}\nResponse: {response_text}")
    
    def generate_sync(
        self, 
        domain: str, 
        task_description: str,
        constraints: Optional[List[str]] = None,
        seed_examples: Optional[List[Dict[str, Any]]] = None
    ) -> DatasetSource:
        """Synchronous version of generate."""
        return asyncio.run(self.generate(domain, task_description, constraints, seed_examples))


__all__ = [
    "GeneratorConfig",
    "LlamaDatasetGenerator",
    "OpenAIDatasetGenerator",
]
