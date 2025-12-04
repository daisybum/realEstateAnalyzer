# Real Estate Analysis Pipeline

이 프로젝트는 **Qwen3-VL** 멀티모달 모델을 활용하여 부동산 임장 보고서를 분석하는 파이프라인입니다. 텍스트, 이미지, PDF, PPTX 등 다양한 형태의 자료를 통합하여 분석하고, 투자 인사이트를 도출합니다.

## 📂 1. 다중 파일 처리 방식 (Multi-modal Data Processing)

이 파이프라인의 핵심은 **`DataLoader`** 클래스를 통해 이종(Heterogeneous) 데이터들을 하나의 '보고서(Report)' 단위로 묶어서 처리하는 것입니다.

### 데이터 구조 (Directory Structure)
분석기는 `data_dir` 내의 **폴더명**을 `report_id`로 인식합니다. 각 폴더 안에는 해당 보고서와 관련된 모든 파일이 위치해야 합니다.

```
data_dir/
├── 3635564/              # Report ID
│   ├── 3635564.txt       # [필수] 보고서 텍스트 본문
│   ├── image_1.png       # [선택] 임장 사진, 차트, 지도 등
│   ├── image_2.png
│   ├── report.pdf        # [선택] PDF 원본 (DataLoader가 경로 로드)
│   └── presentation.pptx # [선택] 발표 자료 (DataLoader가 경로 로드)
└── 3635565/
    ├── ...
```

### 처리 로직 (Processing Logic)
1.  **Aggregation (`data_loader.py`)**:
    *   `DataLoader.load_report(report_id)`가 호출되면 해당 폴더를 스캔합니다.
    *   `.txt` 파일은 읽어서 문자열로 변환합니다.
    *   `.png` 파일들은 알파벳 순으로 정렬하여 리스트로 저장합니다.
    *   `.pdf`, `.pptx` 파일이 존재하면 해당 경로를 저장합니다.
    *   이 모든 데이터는 하나의 Dictionary (`data`)로 묶여서 리턴됩니다.

2.  **Analysis (`main_analysis.py`)**:
    *   `main()` 함수는 `DataLoader`가 리턴한 `data` 딕셔너리를 받습니다.
    *   `data['text']`와 `data['images']`를 `QwenAnalyzer`에 전달하여 멀티모달 분석을 수행합니다.
    *   (확장 가능성) 현재는 텍스트와 이미지를 주로 분석하지만, `data['pdf']`나 `data['pptx']` 경로가 확보되어 있으므로 향후 파서(Parser)를 추가하여 내용을 추출하고 분석에 포함시킬 수 있는 구조입니다.

---

## 🏗️ 2. 코드 구조 (Code Structure)

코드는 모듈화되어 있으며, 각 파일은 명확한 역할을 가집니다.

### `main_analysis.py` (Entry Point)
*   **역할**: 전체 분석 파이프라인을 조율(Orchestration)합니다.
*   **주요 흐름**:
    1.  설정 로드 (`config.yaml`)
    2.  데이터 로드 (`DataLoader`)
    3.  단계별 분석 수행 (Fact Extraction -> Visual Verification -> Sentiment -> Insight)
    4.  결과 저장 (JSON)

### `data_loader.py` (Data Layer)
*   **역할**: 파일 시스템과 상호작용하여 Raw 데이터를 로드합니다.
*   **특징**:
    *   폴더 기반의 데이터 구조를 파싱합니다.
    *   이미지 파일의 순서를 보장하여 로드합니다.
    *   다양한 파일 포맷(TXT, PNG, PDF, PPTX)을 하나의 객체로 추상화합니다.

### `config.yaml` (Configuration)
*   **역할**: 시스템 설정과 프롬프트를 관리합니다.
*   **내용**:
    *   `system`: 데이터 경로, 모델 이름, API URL 등 환경 설정.
    *   `prompts`: 각 분석 단계(Fact, Verification, Sentiment, Insight)에 사용되는 LLM 프롬프트 템플릿. 코드를 수정하지 않고 프롬프트만 튜닝할 수 있도록 분리되어 있습니다.

### `prompt_manager.py`
*   **역할**: `config.yaml`에 정의된 프롬프트를 로드하고 제공하는 헬퍼 클래스입니다.

### `qwen_analyzer.py`
*   **역할**: vLLM API 서버와 통신하여 Qwen 모델에 추론을 요청합니다.
*   **기능**: 텍스트와 이미지를 포함한 멀티모달 요청을 구성하고 응답을 받아옵니다.

---

## 🚀 사용 방법 (Usage)

### 기본 실행
`config.yaml`에 설정된 기본 경로와 모델을 사용하여 분석을 수행합니다.
```bash
python analysis/main_analysis.py
```

### 옵션 지정
특정 보고서만 분석하거나 설정을 오버라이드할 수 있습니다.
```bash
# 특정 리포트 ID만 분석
python analysis/main_analysis.py --report_id 3635564

# 데이터 경로 변경
python analysis/main_analysis.py --data_dir /path/to/custom/data

# 사용할 모델 변경
python analysis/main_analysis.py --model Qwen/Qwen2.5-VL-72B-Instruct-AWQ
```
