# vLLM on Blackwell GPU (GB10/B200) - Docker Setup

## 개요

이 디렉토리는 NVIDIA Blackwell 아키텍처(GB10, B200)에서 vLLM을 실행하기 위한 Docker 환경을 제공합니다. `sm_121a` 타겟 미지원 오류를 해결하고 최적의 성능을 보장합니다.

## 주요 기능

- **Blackwell GPU 전용 최적화**: sm_121a 아키텍처 완전 지원
- **CUDA 13.0 기반**: 최신 GPU 기능 활용
- **소스 빌드**: 하드웨어에 최적화된 네이티브 컴파일
- **Docker Compose**: 간편한 배포 및 관리
- **환경 변수 자동화**: Triton 컴파일러 경로 자동 설정

## 필수 요구사항

### 하드웨어
- NVIDIA GB10/B200 GPU (Blackwell 아키텍처)
- 128GB+ GPU 메모리 권장 (30B 모델 기준)
- aarch64 CPU (Grace CPU) 권장

### 소프트웨어
- Ubuntu 22.04+ 
- Docker 24.0+
- Docker Compose v2.0+
- NVIDIA Container Toolkit
- CUDA 13.0 Toolkit (호스트 시스템)
- NVIDIA Driver 550+

## 디렉토리 구조

```
docker/vllm-blackwell/
├── Dockerfile                # vLLM 이미지 빌드 정의
├── docker-compose.yml        # 서비스 구성
├── .env.example              # 환경 변수 템플릿
├── update_cuda_env.sh        # CUDA 환경 설정 스크립트
└── README.md                 # 이 문서
```

## 빠른 시작

### 1. 환경 변수 설정

```bash
cd docker/vllm-blackwell
cp .env.example .env
# 필요시 .env 파일 수정
```

### 2. Docker 이미지 빌드

```bash
# 기본 빌드
docker-compose build

# 빌드 로그 확인 (문제 발생 시)
docker-compose build --progress=plain --no-cache
```

**예상 빌드 시간**: 20-30분 (네트워크 속도 및 CPU 성능에 따라 다름)

### 3. 서비스 시작

```bash
# 백그라운드에서 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 초기화 완료 대기 (5-10분 소요 가능)
# 다음 메시지가 표시되면 준비 완료:
# "Uvicorn running on http://0.0.0.0:8000"
```

### 4. API 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 모델 정보
curl http://localhost:8000/v1/models

# 추론 테스트
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-VL-30B-A3B-Instruct",
    "prompt": "Explain quantum computing in simple terms.",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## 고급 구성

### 다른 모델 사용

`docker-compose.yml`에서 `MODEL_NAME` 환경 변수 수정:

```yaml
environment:
  - MODEL_NAME=meta-llama/Llama-3-70b-chat-hf
```

또는 `.env` 파일에서:

```bash
MODEL_NAME=mistralai/Mixtral-8x7B-Instruct-v0.1
```

### GPU 메모리 조정

```yaml
environment:
  - GPU_MEMORY_UTILIZATION=0.85  # 기본값 0.90
```

### Tensor Parallel 활성화 (다중 GPU)

```yaml
environment:
  - TENSOR_PARALLEL_SIZE=2  # GPU 개수
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 2  # GPU 개수와 일치
```

### 호스트 네트워킹 사용

고성능이 필요한 경우:

```yaml
network_mode: host
```

**주의**: 이 경우 `ports` 매핑은 무시됩니다.

## 문제 해결

### sm_121a 오류가 여전히 발생하는 경우

1. **호스트 CUDA 버전 확인**:
   ```bash
   nvcc --version
   # CUDA 12.8+ 필요
   ```

2. **Docker 컨테이너 내부에서 확인**:
   ```bash
   docker-compose exec vllm-qwen3-vl-30b bash
   echo $TRITON_PTXAS_PATH
   $TRITON_PTXAS_PATH --version
   ```

3. **호스트 CUDA 마운트 확인**:
   ```bash
   docker-compose exec vllm-qwen3-vl-30b ls -la /usr/local/cuda-13.0/bin/ptxas
   ```

### 메모리 부족 오류

```yaml
environment:
  - GPU_MEMORY_UTILIZATION=0.80  # 낮춤
  - MAX_MODEL_LEN=16384           # 컨텍스트 길이 감소
```

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs --tail=100

# 상세 로그
docker-compose up --no-start
docker-compose start
docker-compose logs -f
```

### "Sink Setting Not Supported" 오류

```yaml
environment:
  - VLLM_USE_V1=0                    # V1 엔진 비활성화
  - VLLM_ATTENTION_BACKEND=FLASH_ATTN
```

## 성능 최적화

### 1. 컴파일 캐시 활성화

Dockerfile에 추가:

```dockerfile
ENV TRITON_CACHE_DIR=/workspace/.triton_cache
RUN mkdir -p /workspace/.triton_cache
```

볼륨 마운트:

```yaml
volumes:
  - triton-cache:/workspace/.triton_cache
```

### 2. 모델 사전 다운로드

별도로 모델을 다운로드한 후 마운트:

```bash
# 호스트에서 모델 다운로드
mkdir -p ./models
huggingface-cli download Qwen/Qwen3-VL-30B-A3B-Instruct --local-dir ./models/qwen3-vl-30b
```

```yaml
volumes:
  - ./models:/workspace/models:ro

environment:
  - MODEL_NAME=/workspace/models/qwen3-vl-30b
```

### 3. 컴파일 스레드 증가

```yaml
environment:
  - NVCC_THREADS=16  # CPU 코어 수에 따라 조정
```

## 프로덕션 배포 권장사항

1. **리소스 제한 설정**:
   ```yaml
   mem_limit: 256g
   cpus: 32
   ```

2. **재시작 정책 조정**:
   ```yaml
   restart: on-failure:3
   ```

3. **로그 로테이션**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "100m"
       max-file: "5"
   ```

4. **모니터링 통합**:
   - Prometheus metrics: http://localhost:8000/metrics
   - NVIDIA DCGM for GPU monitoring

## 정리

```bash
# 서비스 중지 및 제거
docker-compose down

# 볼륨도 함께 제거
docker-compose down -v

# 이미지 제거
docker rmi vllm-blackwell:cuda13.0-v0.12.0
```

## 참고 자료

- [vLLM 공식 문서](https://docs.vllm.ai/)
- [NVIDIA Blackwell 아키텍처](https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/)
- [Triton 컴파일러 문서](https://triton-lang.org/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

## 라이선스

이 구성은 vLLM의 Apache 2.0 라이선스를 따릅니다.

## 지원

문제가 발생하면 다음을 제공하여 이슈를 보고해주세요:
- `docker-compose logs` 전체 출력
- `nvidia-smi` 출력
- `nvcc --version` 출력
