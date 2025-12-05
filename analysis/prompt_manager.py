"""
Prompt Manager - 호환성 래퍼

기존 인터페이스를 유지하면서 새로운 엔터프라이즈급 프롬프트 관리 시스템으로 위임
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional

import yaml
from langchain_core.prompts import ChatPromptTemplate

from prompts.manager import PromptManager as CorePromptManager

logger = logging.getLogger(__name__)


class PromptManager:
    """호환성 래퍼 - 기존 인터페이스 유지
    
    기존 main_analysis.py와의 호환성을 위해 동일한 메서드 시그니처 제공.
    내부적으로 새로운 CorePromptManager에 위임.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 설정 파일 경로 (None이면 자동 탐색)
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config = None  # Lazy loading
        
        # 새로운 코어 매니저 초기화
        templates_dir = self._get_templates_dir()
        self._core = CorePromptManager(
            templates_dir=templates_dir,
            environment="prod",
        )
        
        logger.debug(f"Initialized PromptManager with templates: {templates_dir}")
    
    @property
    def config(self) -> Dict:
        """설정 지연 로딩"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """설정 파일 경로 결정"""
        candidates = [
            Path(config_path) if config_path else None,
            Path("analysis/config.yaml"),
            Path(__file__).parent / "config.yaml",
        ]
        
        for path in candidates:
            if path and path.exists():
                return path
        
        raise FileNotFoundError("Config file not found")
    
    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_templates_dir(self) -> Path:
        """템플릿 디렉토리 경로 결정"""
        return self.config_path.parent / "prompts" / "templates"
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 로드 (폴백용)"""
        # 레거시 config에서 로드
        legacy = self.config.get('legacy_prompts', {})
        return legacy.get('system_prompt', '')
    
    # ==================== 기존 인터페이스 ====================
    
    def get_fact_extraction_prompt(self) -> ChatPromptTemplate:
        """팩트 추출 프롬프트"""
        return self._get_prompt_with_fallback("fact_extraction")
    
    def get_visual_verification_prompt(self) -> ChatPromptTemplate:
        """시각적 검증 프롬프트"""
        return self._get_prompt_with_fallback("visual_verification")
    
    def get_sentiment_analysis_prompt(self) -> ChatPromptTemplate:
        """감성 분석 프롬프트"""
        return self._get_prompt_with_fallback("sentiment_analysis")
    
    def get_insight_generation_prompt(self) -> ChatPromptTemplate:
        """인사이트 생성 프롬프트"""
        return self._get_prompt_with_fallback("insight_generation")
    
    def _get_prompt_with_fallback(self, name: str) -> ChatPromptTemplate:
        """새 시스템에서 로드 시도, 실패 시 레거시 폴백"""
        try:
            return self._core.get_prompt(name)
        except FileNotFoundError:
            logger.warning(f"Prompt '{name}' not found, using legacy fallback")
            return self._build_legacy_prompt(name)
    
    def _build_legacy_prompt(self, name: str) -> ChatPromptTemplate:
        """레거시 설정에서 프롬프트 빌드"""
        legacy = self.config.get('legacy_prompts', {})
        template = legacy.get(name, "")
        system_prompt = self._get_system_prompt()
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", template),
        ])
    
    # ==================== 새로운 인터페이스 노출 ====================
    
    @property
    def core(self) -> CorePromptManager:
        """코어 프롬프트 매니저 접근"""
        return self._core
    
    def get_prompt(self, name: str, version: str = "latest") -> ChatPromptTemplate:
        """새로운 방식으로 프롬프트 로드"""
        return self._core.get_prompt(name, version)
    
    def list_prompts(self) -> List[str]:
        """등록된 모든 프롬프트 목록"""
        return self._core.list_prompts()
    
    def with_few_shot(self, name: str, examples: List[Dict[str, str]]) -> ChatPromptTemplate:
        """Few-shot 예시 적용"""
        return self._core.with_few_shot(name, examples)
    
    def with_history(self, name: str, history_variable: str = "chat_history") -> ChatPromptTemplate:
        """대화 기록 슬롯 추가"""
        return self._core.with_history(name, history_variable)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        pm = PromptManager()
        
        print("=== 호환성 테스트 ===")
        prompt = pm.get_fact_extraction_prompt()
        result = prompt.format(report_text="샘플 텍스트")
        print(f"Format 성공: {len(result)} chars")
        
        print("\n=== 등록된 프롬프트 ===")
        print(pm.list_prompts())
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
