import yaml
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Optional

class PromptManager:
    def __init__(self, config_path: str = "analysis/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.system_prompt = self.config['prompts']['system_prompt']

    def _load_config(self) -> Dict:
        if not self.config_path.exists():
            # Fallback to looking relative to this file if run from elsewhere
            current_file_path = Path(__file__).parent
            potential_path = current_file_path / "config.yaml"
            if potential_path.exists():
                self.config_path = potential_path
            else:
                raise FileNotFoundError(f"Config file not found at {self.config_path} or {potential_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_fact_extraction_prompt(self) -> ChatPromptTemplate:
        """
        Returns a prompt for extracting factual data from the report.
        """
        template = self.config['prompts']['fact_extraction']
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", template)
        ])

    def get_visual_verification_prompt(self) -> ChatPromptTemplate:
        """
        Returns a prompt for verifying text claims against visual data.
        """
        template = self.config['prompts']['visual_verification']
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", template)
        ])

    def get_sentiment_analysis_prompt(self) -> ChatPromptTemplate:
        """
        Returns a prompt for analyzing sentiment and hidden risks.
        """
        template = self.config['prompts']['sentiment_analysis']
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", template)
        ])

    def get_insight_generation_prompt(self) -> ChatPromptTemplate:
        """
        Returns a prompt for generating final investment insights.
        """
        template = self.config['prompts']['insight_generation']
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", template)
        ])

if __name__ == "__main__":
    # Test the prompt manager
    try:
        pm = PromptManager()
        print("Fact Extraction Prompt:")
        print(pm.get_fact_extraction_prompt().format(report_text="샘플 텍스트"))
    except Exception as e:
        print(f"Error: {e}")
