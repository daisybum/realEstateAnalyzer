"""
Real Estate Analysis Pipeline

부동산 임장 보고서 분석 파이프라인 메인 진입점
Ontology-based Knowledge Graph 구축을 위한 정보 추출
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from data_loader import DataLoader, ReportData
from prompt_manager import PromptManager
from qwen_analyzer import QwenAnalyzer
from config_loader import get_config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_langsmith():
    """LangSmith 트레이싱 초기화 (SecretsManager 사용)"""
    from secrets_manager import get_langsmith_config
    
    config = get_langsmith_config()
    
    if config["enabled"]:
        os.environ["LANGSMITH_TRACING"] = "true" if config["tracing"] else "false"
        os.environ["LANGSMITH_PROJECT"] = config["project"]
        os.environ["LANGSMITH_API_KEY"] = config["api_key"]
        os.environ["LANGSMITH_ENDPOINT"] = config["endpoint"]
        
        logger.info(f"LangSmith tracing enabled for project: {config['project']}")
        return True
    else:
        logger.info("LangSmith disabled (no API key found)")
        return False


class AnalysisPipeline:
    """부동산 분석 파이프라인
    
    단계:
    1. Fact Extraction - 팩트 추출
    2. Visual Verification - 시각적 검증
    3. Sentiment Analysis - 감성 분석
    4. Insight Generation - 인사이트 생성
    """
    
    def __init__(self, 
                 analyzer: QwenAnalyzer, 
                 prompt_manager: PromptManager,
                 output_dir: Path):
        self.analyzer = analyzer
        self.pm = prompt_manager
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def process(self, data: ReportData) -> Optional[dict]:
        """단일 보고서 분석
        
        Args:
            data: ReportData 객체
            
        Returns:
            분석 결과 딕셔너리 또는 None (실패 시)
        """
        if data.is_empty:
            logger.warning(f"Skipping empty report {data.id}")
            return None
        
        logger.info(f"Processing report {data.id}...")
        
        try:
            # 1. 팩트 추출
            facts_json = self._extract_facts(data)
            
            # 2. 시각적 검증
            verification = self._verify_visuals(data)
            
            # 3. 감성 분석
            sentiment = self._analyze_sentiment(data)
            
            # 4. 인사이트 생성
            region_name = self._extract_region_name(facts_json)
            insight = self._generate_insight(
                region_name, facts_json, verification, sentiment
            )
            
            # 결과 저장
            result = {
                "report_id": data.id,
                "facts": facts_json,
                "verification": verification,
                "sentiment": sentiment,
                "insight": insight,
            }
            
            self._save_result(data.id, result)
            return result
            
        except Exception as e:
            logger.error(f"Failed to process report {data.id}: {e}")
            return None
    
    def _extract_facts(self, data: ReportData) -> str:
        """팩트 추출"""
        logger.info("  - Extracting facts...")
        prompt = self.pm.get_fact_extraction_prompt()
        return self.analyzer.analyze(data.text, data.images, prompt)
    
    def _verify_visuals(self, data: ReportData) -> str:
        """시각적 검증"""
        logger.info("  - Verifying visuals...")
        prompt = self.pm.get_visual_verification_prompt()
        return self.analyzer.analyze(data.text, data.images, prompt)
    
    def _analyze_sentiment(self, data: ReportData) -> str:
        """감성 분석"""
        logger.info("  - Analyzing sentiment...")
        prompt = self.pm.get_sentiment_analysis_prompt()
        return self.analyzer.analyze(data.text, [], prompt)
    
    def _generate_insight(self, 
                          region_name: str, 
                          facts: str, 
                          verification: str, 
                          sentiment: str) -> str:
        """인사이트 생성"""
        logger.info("  - Generating insights...")
        prompt = self.pm.get_insight_generation_prompt()
        return self.analyzer.analyze(
            "", [], prompt,
            region_name=region_name,
            fact_data=facts,
            verification_result=verification,
            risk_analysis=sentiment,
        )
    
    def _extract_region_name(self, facts_json: str) -> str:
        """팩트 JSON에서 지역명 추출"""
        try:
            clean = facts_json.replace("```json", "").replace("```", "").strip()
            facts_dict = json.loads(clean)
            return facts_dict.get("region_name", 
                                  facts_dict.get("complex_name", "Unknown Region"))
        except (json.JSONDecodeError, KeyError):
            return "Unknown Region"
    
    def _save_result(self, report_id: str, result: dict) -> None:
        """결과 저장"""
        output_file = self.output_dir / f"{report_id}_analysis.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"  - Saved analysis to {output_file}")


def parse_args() -> argparse.Namespace:
    """커맨드라인 인자 파싱"""
    config = get_config()
    system = config.system
    
    parser = argparse.ArgumentParser(
        description="Real Estate Analysis Pipeline with Qwen3-VL"
    )
    parser.add_argument("--data_dir", type=str, default=system.data_dir)
    parser.add_argument("--output_dir", type=str, default=system.output_dir)
    parser.add_argument("--report_id", type=str, help="특정 보고서 ID만 분석")
    parser.add_argument("--api_url", type=str, default=system.api_url)
    parser.add_argument("--model", type=str, default=system.model_name)
    parser.add_argument("--api_key", type=str, default=system.api_key)
    parser.add_argument("--max_samples", type=int, default=system.max_samples)
    
    return parser.parse_args()


def main():
    """메인 진입점"""
    args = parse_args()
    
    # LangSmith 트레이싱 초기화
    setup_langsmith()
    
    # 컴포넌트 초기화
    loader = DataLoader(args.data_dir)
    prompt_manager = PromptManager()
    analyzer = QwenAnalyzer(
        api_key=args.api_key,
        base_url=args.api_url,
        model_name=args.model,
    )
    
    pipeline = AnalysisPipeline(
        analyzer=analyzer,
        prompt_manager=prompt_manager,
        output_dir=Path(args.output_dir),
    )
    
    # 보고서 목록 결정
    if args.report_id:
        report_ids = [args.report_id]
    else:
        report_ids = loader.get_report_ids()
    
    logger.info(f"Found {len(report_ids)} reports to process")
    logger.info(f"Using model: {analyzer.model_name}")
    
    # 분석 실행
    success_count = 0
    for rid in tqdm(report_ids[:args.max_samples], desc="Processing"):
        try:
            data = loader.load_report(rid)
            result = pipeline.process(data)
            if result:
                success_count += 1
        except FileNotFoundError as e:
            logger.error(f"Report not found: {e}")
    
    logger.info(f"Completed: {success_count}/{len(report_ids)} reports processed")


if __name__ == "__main__":
    main()
