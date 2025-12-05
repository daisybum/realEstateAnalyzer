import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate

class QwenAnalyzer:
    def __init__(self, 
                 api_key: str = "EMPTY", 
                 base_url: str = "http://localhost:8000/v1",
                 model_name: Optional[str] = None):
        """
        Initialize the QwenAnalyzer with OpenAI-compatible vLLM client.
        
        Args:
            api_key: API key for vLLM server
            base_url: vLLM server URL
            model_name: Model name (if None, loads from config)
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        # 모델명: 파라미터 > 환경변수 > 기본값
        if model_name:
            self.model_name = model_name
        else:
            self.model_name = os.environ.get(
                "MODEL_NAME", 
                "Qwen/Qwen3-VL-30B-A3B-Instruct"
            ) 

    def analyze(self, text: str, images: List[str], prompt_template: ChatPromptTemplate, **kwargs) -> str:
        """
        Perform analysis using the Qwen model.
        
        Args:
            text: The text content of the report.
            images: List of image paths.
            prompt_template: LangChain ChatPromptTemplate to use.
            **kwargs: Additional arguments for the prompt template (e.g., complex_name).
            
        Returns:
            The analysis result as a string.
        """
        # Format the prompt using LangChain
        # We need to handle the image part separately because LangChain's standard formatting 
        # might not directly map to OpenAI's multi-modal format for local images easily without some work.
        # So we'll extract the text prompt from LangChain and construct the OpenAI message manually.
        
        # 1. Format the text part of the prompt
        formatted_messages = prompt_template.format_messages(report_text=text, **kwargs)
        system_content = formatted_messages[0].content
        user_content_text = formatted_messages[1].content

        # 2. Construct OpenAI messages
        messages = [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content_text},
                ],
            },
        ]

        # 3. Add images to the user message
        # vLLM supports passing local file paths directly if configured, 
        # or we can pass base64. For simplicity and performance with vLLM, 
        # we'll try passing file URIs if the server supports it (which Qwen3-VL vLLM usually does).
        # If not, we might need to convert to base64. 
        # For this implementation, we'll use the file URI format: "file:///path/to/image.png"
        
        for img_path in images:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"file://{img_path}"
                }
            })

        # 4. Call the API
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1, # Low temperature for factual extraction
                max_tokens=4096,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error during analysis: {e}"

if __name__ == "__main__":
    # Test the analyzer (requires running vLLM server)
    analyzer = QwenAnalyzer()
    print(f"Initialized analyzer for model: {analyzer.model_name}")
