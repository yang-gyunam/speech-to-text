# 빌드 지침서

## PyInstaller + Tauri 통합 빌드 시스템

이 프로젝트는 PyInstaller로 독립 실행 파일을 생성하고 Tauri 앱에 번들하는 구조를 사용합니다.

**성공적으로 구현 완료**: 파이썬 런타임 의존성 문제가 해결되어, 사용자가 파이썬이나 가상환경 없이도 앱을 사용할 수 있습니다.

### 빌드 단계

#### 1단계: PyInstaller로 독립 실행 파일 생성

```bash
# 프로젝트 루트 디렉토리에서 실행
python3 build_standalone.py
```

이 명령은:
- 가상환경 생성 (`venv_build/`)
- 의존성 설치 (Whisper, PyTorch 등)
- PyInstaller로 독립 실행 파일 빌드
- Tauri 디렉토리에 실행 파일 복사

#### 2단계: Tauri 앱 빌드

```bash
cd tauri-svelte5-app
npm run tauri:build
```

이 명령은:
- 프론트엔드 빌드
- Rust 백엔드 빌드
- 독립 실행 파일을 사이드카로 번들
- macOS 앱 패키지 생성
- DMG 설치 파일 생성

### 결과물

빌드 완료 후 다음 파일들이 생성됩니다:

1. **독립 실행 파일**: `dist/speech-to-text`
2. **앱 번들**: `tauri-svelte5-app/src-tauri/target/release/bundle/macos/SpeechToText.app`
3. **DMG 설치 파일**: `tauri-svelte5-app/src-tauri/target/release/bundle/dmg/SpeechToText_1.0.0_aarch64.dmg`

### 아키텍처 개선점

#### 문제 해결
- 파이썬 런타임 의존성 제거 (PyInstaller 사용)
- 가상환경 경로 문제 해결
- 플랫폼별 독립 실행 파일 생성
- Tauri 사이드카 통합

#### 기술적 구현
1. **PyInstaller**: 모든 의존성을 포함하는 독립 실행 파일 생성 (143MB)
2. **CLI 래퍼**: 임포트 문제 해결을 위한 래퍼 스크립트 (`cli_wrapper.py`)
3. **Tauri 사이드카**: 번들된 실행 파일을 앱과 함께 배포 (`externalBin`)
4. **자동 경로 탐지**: 번들된 실행 파일을 자동으로 찾아 사용
5. **Whisper 에셋 번들링**: Whisper 모델 에셋 파일들이 PyInstaller에 포함됨

### 자동화된 빌드 스크립트

전체 빌드 과정을 자동화하려면:

```bash
# 전체 빌드 스크립트 생성
cat > build_all.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting full build process..."

# Step 1: Build standalone executable
echo "Building PyInstaller executable..."
python3 build_standalone.py

# Step 2: Build Tauri app
echo "Building Tauri application..."
cd tauri-svelte5-app
npm run tauri:build
cd ..

echo "Build completed successfully!"
echo "Results:"
echo "   - App: tauri-svelte5-app/src-tauri/target/release/bundle/macos/SpeechToText.app"
echo "   - DMG: tauri-svelte5-app/src-tauri/target/release/bundle/dmg/SpeechToText_1.0.0_aarch64.dmg"
EOF

chmod +x build_all.sh
```

### 배포

생성된 DMG 파일을 사용자에게 배포하면:
- 파이썬 설치 불필요
- 가상환경 설정 불필요
- 의존성 설치 불필요
- 즉시 실행 가능

모든 의존성이 앱 번들에 포함되어 있어서 깔끔한 설치와 실행이 가능합니다.

### 구현 완료 내역

#### 해결된 문제들
- **CLI execution failed with exit code: Some(1)** 오류 해결
- 파이썬 런타임 의존성 문제 완전 제거
- 가상환경 경로 문제 해결
- Whisper 에셋 파일 번들링 (`mel_filters.npz` 오류 해결)
- Tauri sidecar 통합 성공

#### 핵심 파일들
- `build_standalone.py`: PyInstaller 빌드 자동화 스크립트
- `cli_wrapper.py`: 임포트 문제 해결용 래퍼
- `tauri.conf.json`: `externalBin` 설정으로 사이드카 통합
- `src-tauri/src/cli.rs`: 번들된 실행 파일 자동 탐지

#### 테스트 결과
개발 환경에서 정상 동작 확인:
- PyInstaller 실행 파일 자동 탐지 성공
- Whisper 모델 로딩 정상
- 오디오 파일 처리 진행 확인