"""
Prompt Manager - 호환성 래퍼

기존 인터페이스를 유지하면서 새로운 엔터프라이즈급 프롬프트 관리 시스템으로 위임
"""
import yaml
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Optional

# 새로운 프롬프트 관리 시스템
from prompts.manager import PromptManager as CorePromptManager
from prompts.loaders import PromptLoader


class PromptManager:
    """호환성 래퍼 - 기존 인터페이스 유지
    
    기존 main_analysis.py와의 호환성을 위해 동일한 메서드 시그니처 제공
    """
    
    def __init__(self, config_path: str = "analysis/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 새로운 코어 매니저 초기화
        templates_dir = self._get_templates_dir()
        self._core = CorePromptManager(
            templates_dir=templates_dir,
            environment="prod",
        )
        
        # 시스템 프롬프트 로드 (폴백용)
        self._system_prompt = self._load_system_prompt()
    
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
    
    def _get_templates_dir(self) -> Path:
        """템플릿 디렉토리 경로 결정"""
        # config.yaml에서 설정된 경로 사용
        prompts_config = self.config.get('prompts', {})
        templates_dir = prompts_config.get('templates_dir', 'analysis/prompts/templates')
        
        path = Path(templates_dir)
        if not path.is_absolute():
            # 상대 경로인 경우 config 파일 기준으로 해석
            path = self.config_path.parent / "prompts" / "templates"
        
        return path
    
    def _load_system_prompt(self) -> str:
        """시스템 프롬프트 로드"""
        # 새로운 시스템에서 로드 시도
        system_prompt_path = self._get_templates_dir() / "base_system.yaml"
        if system_prompt_path.exists():
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('content', '')
        
        # 폴백: 기존 config.yaml에서 로드
        return self.config.get('prompts', {}).get('system_prompt', '')

    def get_fact_extraction_prompt(self) -> ChatPromptTemplate:
        """Returns a prompt for extracting factual data from the report."""
        try:
            return self._core.get_prompt("fact_extraction")
        except FileNotFoundError:
            # 폴백: 기존 config.yaml에서 로드
            template = self.config['prompts']['fact_extraction']
            return ChatPromptTemplate.from_messages([
                ("system", self._system_prompt),
                ("user", template)
            ])

    def get_visual_verification_prompt(self) -> ChatPromptTemplate:
        """Returns a prompt for verifying text claims against visual data."""
        try:
            return self._core.get_prompt("visual_verification")
        except FileNotFoundError:
            template = self.config['prompts']['visual_verification']
            return ChatPromptTemplate.from_messages([
                ("system", self._system_prompt),
                ("user", template)
            ])

    def get_sentiment_analysis_prompt(self) -> ChatPromptTemplate:
        """Returns a prompt for analyzing sentiment and hidden risks."""
        try:
            return self._core.get_prompt("sentiment_analysis")
        except FileNotFoundError:
            template = self.config['prompts']['sentiment_analysis']
            return ChatPromptTemplate.from_messages([
                ("system", self._system_prompt),
                ("user", template)
            ])

    def get_insight_generation_prompt(self) -> ChatPromptTemplate:
        """Returns a prompt for generating final investment insights."""
        try:
            return self._core.get_prompt("insight_generation")
        except FileNotFoundError:
            template = self.config['prompts']['insight_generation']
            return ChatPromptTemplate.from_messages([
                ("system", self._system_prompt),
                ("user", template)
            ])

    # ==================== 새로운 엔터프라이즈 기능 노출 ====================
    
    @property
    def core(self) -> CorePromptManager:
        """새로운 코어 프롬프트 매니저 접근"""
        return self._core
    
    def get_prompt(self, name: str, version: str = "latest") -> ChatPromptTemplate:
        """새로운 방식으로 프롬프트 로드"""
        return self._core.get_prompt(name, version)
    
    def list_prompts(self) -> List[str]:
        """등록된 모든 프롬프트 목록"""
        return self._core.list_prompts()
    
    def with_few_shot(self, name: str, examples: List[Dict[str, str]]) -> ChatPromptTemplate:
        """Few-shot 예시가 적용된 프롬프트"""
        return self._core.with_few_shot(name, examples)
    
    def with_history(self, name: str, history_variable: str = "chat_history") -> ChatPromptTemplate:
        """대화 기록 슬롯이 추가된 프롬프트"""
        return self._core.with_history(name, history_variable)


if __name__ == "__main__":
    # Test the prompt manager
    try:
        pm = PromptManager()
        
        print("=== 호환성 테스트 ===")
        print("Fact Extraction Prompt:")
        prompt = pm.get_fact_extraction_prompt()
        result = prompt.format(report_text="샘플 텍스트")
        print(f"  - Format 성공: {len(result)} chars")
        
        print("\n=== 새로운 기능 테스트 ===")
        print("등록된 프롬프트:", pm.list_prompts())
        
        print("\n새 방식 로드:")
        prompt2 = pm.get_prompt("fact_extraction")
        print(f"  - 로드 성공: {type(prompt2).__name__}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
