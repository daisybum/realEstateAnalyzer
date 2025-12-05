import os
import json
import argparse
import yaml
from pathlib import Path
from tqdm import tqdm
from data_loader import DataLoader
from prompt_manager import PromptManager
from qwen_analyzer import QwenAnalyzer

def load_config(config_path: str = "analysis/config.yaml") -> dict:
    path = Path(config_path)
    if not path.exists():
        # Fallback to relative path
        path = Path(__file__).parent / "config.yaml"
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    # Load config first
    try:
        config = load_config()
        system_config = config.get('system', {})
    except Exception as e:
        print(f"Warning: Could not load config.yaml: {e}")
        system_config = {}

    parser = argparse.ArgumentParser(description="Real Estate Analysis Pipeline with Qwen3-VL")
    # Use config values as defaults
    parser.add_argument("--data_dir", type=str, default=system_config.get("data_dir", "~/Projects/realEstateCrawler/output/"), help="Path to data directory")
    parser.add_argument("--output_dir", type=str, default=system_config.get("output_dir", "analysis_results"), help="Directory to save results")
    parser.add_argument("--report_id", type=str, help="Specific report ID to analyze (optional)")
    parser.add_argument("--api_url", type=str, default=system_config.get("api_url", "http://localhost:8000/v1"), help="vLLM API URL")
    parser.add_argument("--model", type=str, default=system_config.get("model_name", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), help="Model name")
    parser.add_argument("--api_key", type=str, default=system_config.get("api_key", "EMPTY"), help="API Key")
    parser.add_argument("--max_samples", type=int, default=system_config.get("max_samples", 100000), help="Maximum number of samples to process")
    args = parser.parse_args()

    # Initialize components
    loader = DataLoader(args.data_dir)
    pm = PromptManager() # It loads config internally too, or we could pass the config object if we refactored it further.
    analyzer = QwenAnalyzer(api_key=args.api_key, base_url=args.api_url)
    analyzer.model_name = args.model

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    # Get reports to process
    if args.report_id:
        report_ids = [args.report_id]
    else:
        report_ids = loader.get_report_ids()

    print(f"Found {len(report_ids)} reports to process.")

    for rid in tqdm(report_ids[:args.max_samples]):
        try:
            print(f"Processing report {rid}...")
            data = loader.load_report(rid)
            
            if not data['text'] and not data['images']:
                print(f"Skipping empty report {rid}")
                continue

            # 1. Fact Extraction
            print("  - Extracting facts...")
            fact_prompt = pm.get_fact_extraction_prompt()
            facts_json = analyzer.analyze(data['text'], data['images'], fact_prompt)
            
            # 2. Visual Verification
            print("  - Verifying visuals...")
            verify_prompt = pm.get_visual_verification_prompt()
            verification_result = analyzer.analyze(data['text'], data['images'], verify_prompt)

            # 3. Sentiment Analysis
            print("  - Analyzing sentiment...")
            sentiment_prompt = pm.get_sentiment_analysis_prompt()
            sentiment_result = analyzer.analyze(data['text'], [], sentiment_prompt)

            # 4. Insight Generation
            print("  - Generating insights...")
            # Parse facts to pass to insight prompt
            try:
                # Try to clean json if it has markdown code blocks
                clean_facts = facts_json.replace("```json", "").replace("```", "").strip()
                facts_dict = json.loads(clean_facts)
                # Extract region_name (regional analysis) or complex_name (fallback)
                region_name = facts_dict.get("region_name", facts_dict.get("complex_name", "Unknown Region"))
            except:
                region_name = "Unknown Region"
                
            insight_prompt = pm.get_insight_generation_prompt()
            insight_result = analyzer.analyze(
                "", [], 
                insight_prompt,
                region_name=region_name,
                fact_data=facts_json,
                verification_result=verification_result,
                risk_analysis=sentiment_result
            )

            # Save results
            result_data = {
                "report_id": rid,
                "facts": facts_json,
                "verification": verification_result,
                "sentiment": sentiment_result,
                "insight": insight_result
            }
            
            with open(output_path / f"{rid}_analysis.json", "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
                
            print(f"  - Saved analysis for {rid}")

        except Exception as e:
            print(f"Failed to process report {rid}: {e}")

if __name__ == "__main__":
    main()
