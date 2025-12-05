"""
Qwen VL Analyzer

vLLM 서버 기반 Qwen Vision-Language 모델 분석기
"""
import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class QwenAnalyzer:
    """vLLM 기반 Qwen VL 분석기
    
    OpenAI 호환 API를 사용하여 멀티모달 분석 수행
    
    Example:
        >>> analyzer = QwenAnalyzer(model_name="Qwen/Qwen3-VL-30B-A3B-Instruct")
        >>> result = analyzer.analyze(text, images, prompt)
    """
    
    DEFAULT_MODEL = "Qwen/Qwen3-VL-30B-A3B-Instruct"
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_TOKENS = 4096
    MAX_IMAGES = 10  # 토큰 오버플로우 방지 (32768 토큰 제한)
    
    def __init__(self, 
                 api_key: str = "EMPTY", 
                 base_url: str = "http://localhost:8000/v1",
                 model_name: Optional[str] = None,
                 temperature: float = DEFAULT_TEMPERATURE,
                 max_tokens: int = DEFAULT_MAX_TOKENS,
                 max_images: int = MAX_IMAGES):
        """
        Args:
            api_key: vLLM 서버 API 키 (기본: EMPTY)
            base_url: vLLM 서버 URL
            model_name: 모델명 (None이면 환경변수 또는 기본값 사용)
            temperature: 생성 온도 (낮을수록 결정적)
            max_tokens: 최대 출력 토큰
            max_images: 최대 이미지 개수 (토큰 제한 방지)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name or self._get_model_name()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_images = max_images
        
        logger.info(f"Initialized QwenAnalyzer with model: {self.model_name}")
    
    def _get_model_name(self) -> str:
        """환경변수 또는 기본값에서 모델명 가져오기"""
        import os
        return os.environ.get("MODEL_NAME", self.DEFAULT_MODEL)
    
    def analyze(self, 
                text: str, 
                images: List[str], 
                prompt_template: ChatPromptTemplate, 
                **kwargs) -> str:
        """멀티모달 분석 수행
        
        Args:
            text: 보고서 텍스트
            images: 이미지 경로 리스트
            prompt_template: LangChain ChatPromptTemplate
            **kwargs: 프롬프트 템플릿 변수들
            
        Returns:
            분석 결과 문자열
        """
        messages = self._build_messages(text, images, prompt_template, **kwargs)
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return f"Error during analysis: {e}"
    
    def _build_messages(self,
                        text: str,
                        images: List[str],
                        prompt_template: ChatPromptTemplate,
                        **kwargs) -> List[Dict[str, Any]]:
        """OpenAI 호환 메시지 구성"""
        # LangChain 템플릿 포맷팅
        formatted = prompt_template.format_messages(report_text=text, **kwargs)
        
        system_content = formatted[0].content
        user_content_text = formatted[1].content if len(formatted) > 1 else ""
        
        # 메시지 구성
        messages = [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": self._build_user_content(user_content_text, images),
            },
        ]
        
        return messages
    
    def _build_user_content(self, 
                            text: str, 
                            images: List[str]) -> List[Dict[str, Any]]:
        """사용자 메시지 콘텐츠 구성 (텍스트 + 이미지)"""
        content = [{"type": "text", "text": text}]
        
        # 이미지 개수 제한 (토큰 오버플로우 방지)
        if len(images) > self.max_images:
            logger.warning(
                f"Truncating images: {len(images)} -> {self.max_images} "
                f"(max_images limit)"
            )
            images = images[:self.max_images]
        
        for img_path in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"file://{img_path}"}
            })
        
        return content


if __name__ == "__main__":
    # 테스트
    analyzer = QwenAnalyzer()
    print(f"Initialized analyzer for model: {analyzer.model_name}")
