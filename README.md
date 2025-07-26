# APS 생산계획 시스템

## 개요
판매계획(수요)과 자원(인원·장비)·제약조건을 입력하면 자동으로 최적화된 생산계획을 생성하고, 시각적으로 검토·수정할 수 있는 데스크톱 애플리케이션입니다.

## 주요 기능
- 📊 **월별 판매계획을 일별 생산계획으로 자동 변환**
- 🏭 **제품/공정/장비/작업자 마스터 데이터 관리**
- ⚙️ **제약조건 기반 자동 스케줄링**
- 🎯 **드래그&드롭 기반 일정 수정**
- 💾 **CSV/Excel/XML 형식으로 결과 내보내기**

## 시스템 요구사항
- Python 3.8 이상
- Windows 10/11 (Linux, macOS 지원 예정)
- 최소 4GB RAM
- 1920x1080 이상 해상도 권장

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/aps-system.git
cd aps-system
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행 방법

### Windows
```bash
run.bat
```

### 직접 실행
```bash
python main.py
```

## 사용 방법

### 1. 마스터 데이터 설정
- 프로그램 실행 후 '마스터 설정' 탭에서 제품, 공정, 장비, 작업자 정보 입력
- 또는 `data/masters/` 폴더의 JSON 파일 직접 편집

### 2. 판매계획 업로드
- '파일 > 판매계획 열기' 메뉴 선택
- Excel 파일 형식: 제품명, 1월~12월 필수 컬럼

### 3. 스케줄 생성
- 툴바의 '⚙️ 스케줄 생성' 버튼 클릭
- 자동으로 최적화된 생산계획 생성

### 4. 결과 편집 및 내보내기
- '스케줄 편집' 탭에서 드래그&드롭으로 일정 수정
- '💾 결과 내보내기' 버튼으로 CSV/Excel/XML 저장

## 프로젝트 구조
```
NEW_APS/
├── main.py                 # 진입점
├── requirements.txt        # 의존성
├── run.bat                # 실행 스크립트
├── README.md              # 이 파일
├── config/
│   └── settings.json      # 애플리케이션 설정
├── data/
│   ├── masters/           # 마스터 데이터 (JSON)
│   └── plans/             # 계획 파일들
├── app/
│   ├── models/            # 데이터 모델
│   │   ├── master_data.py # 마스터 데이터 관리
│   │   └── production_plan.py # 생산계획 모델
│   ├── views/             # UI 컴포넌트
│   │   └── main_window.py # 메인 윈도우
│   ├── controllers/       # 비즈니스 로직
│   ├── core/              
│   │   └── scheduler.py   # 스케줄링 엔진
│   ├── utils/             
│   │   └── file_handler.py # 파일 입출력
│   └── resources/         
│       └── styles/        # UI 스타일
└── tests/                 # 테스트 코드
```

## 개발 로드맵

### 현재 구현됨 (MVP)
- ✅ 프로젝트 구조 설정
- ✅ 마스터 데이터 모델
- ✅ 스케줄링 엔진 (기본)
- ✅ 파일 입출력
- ✅ 메인 UI 프레임워크

### 진행 중
- 🔄 드래그&드롭 그리드 뷰
- 🔄 마스터 데이터 CRUD UI
- 🔄  실시간 제약조건 검증

### 계획됨
- 📋 세척 블록 상세 로직
- 📋 장비 가동중지 기간 관리
- 📋 대시보드 및 차트
- 📋 PDF 리포트 생성
- 📋 최적화 알고리즘 고도화

## 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 문의
- 이슈 트래커: [GitHub Issues](https://github.com/your-repo/aps-system/issues)
- 이메일: aps-team@example.com