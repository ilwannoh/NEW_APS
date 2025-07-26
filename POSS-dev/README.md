# 📊 생산계획 검증 플랫폼 "POSS"

## 📂 프로젝트 소개
본 프로젝트는 SSAFY 12기, 삼성전자(생산기술연구소) 기업 연계 프로젝트 입니다 <br><br>
기존에 수작업으로 이루어지는 생산 계획 설계 작업을 자동화 하여, <br>
생산 계획을 수립할 때의 많은 제약 사항과 지표들을 검증하고 <br>
해외 공장 등 인터넷 환경이 없는 곳에서도 사용할 수 있는 웹 어플리케이션입니다 <br>

## 📅 프로젝트 수행 기간
- 2025-04-21 ~ 2025-05-22

## 🧑‍🚀 팀원 소개

|                             김고은                             |                              박수미                           |                             박주찬                              |                             이국건                            |                            최은진                               |                            최유정                            
| :-------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------: |
| <img src="./readmeImg/5fe639ef6c64fd6607b11bc7e90c5be6.jpg" width="100" height="100"> | <img src="https://secure.gravatar.com/avatar/5fe0b115865ecc60ccb67be965001aec9dad030047b6c637f56192d63d8c097a?s=1600&d=identicon" width="100" height="100"> | <img src="https://secure.gravatar.com/avatar/06f3973709d03d11b1afc119be856d713bde049f846aca023f157502fd6b884e?s=1600&d=identicon" width="100" height="100"> | <img src="https://secure.gravatar.com/avatar/73cfd003a12ce57f0c5274da1cf012317658e750575c33ff6e3cf48f43a4f2cf?s=1600&d=identicon" width="100" height="100"> | <img src="https://github.com/user-attachments/assets/a6c14a53-26ec-4980-a81c-6b89c439e1bb" width="100" height="100"> | <img src="https://secure.gravatar.com/avatar/6f3940d0790743c62c0641050bfa950f04d527e31f47adafac747a5b614440f4?s=1600&d=identicon" width="100" height="100"> |

<br><br>
## 🔧 사용 스택
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/PyQt-3776AB?style=for-the-badge&logoColor=white">
<img src="https://img.shields.io/badge/PyInstaller-3776AB?style=for-the-badge&logoColor=white">
<img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white">
<img src="https://img.shields.io/badge/numpy-013243?style=for-the-badge&logo=numpy&logoColor=white">
<img src="https://img.shields.io/badge/matplotlib-013243?style=for-the-badge&logoColor=white">
<img src="https://img.shields.io/badge/scipy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white">
<img src="https://img.shields.io/badge/pulp-FFAE1A?style=for-the-badge&logoColor=white">

<br><br>
## 📢 기능 요약

1. 생산 계획 분석
    - 실제 수요를 바탕으로 생산 계획 구성
    - SOP 기준으로 사전에 생산 계획 점검 및 분석
    - 생산 불가능한 모델 사전 탐지
2. 생산 계획 사용자 커스텀
    - Drag & Drop을 기반으로 단순 조회뿐만 아니라 생산 계획을 사용자가 수정하며 확인할 수 있는 실시간 반영 지표 제공
    - 수정하는 동시에 바로 분석되는 데이터와 지표로 쉬운 결과 조정 
3. 사전할당 알고리즘
    - 생산 계획을 도출하기 전, 미리 사전에 생산 물량을 할당하는 알고리즘으로 생산 계획 수립의 시간 효율성 향상
4. LP/MIP 기능
    - 엑셀로 저장해 공유 및 리포팅 최적화
    - 단순한 최적화 모델이 아닌, 실제 공장에서의 상황을 고려한 현실적 판단 도출
5. UI/UX 관련
    - 인터넷 환경이 없거나 느린 환경에서도 실행 가능하게 하기 위해서 사양이 낮은 PyQt 사용
    - FHD와 QHD 비율로 계산을 해서 화면에 따라 같은 화면으로 도출될 수 있게 구현

<br><br>
## 🎁 프로젝트 구성

### 1. 시스템 흐름도
<img src="./readmeImg/아키텍처.png">

### 2. 기능 명세서
[여기](https://steady-elf-917.notion.site/1e310b2e3d6b8180b073efc8b2976081?pvs=4)에서 확인

### 3. 프로젝트 목업
[피그마](https://www.figma.com/design/Yry2l3ZdsffmFtATkF6GNF/S107-%EC%99%80%EC%9D%B4%EC%96%B4%ED%94%84%EB%A0%88%EC%9E%84?node-id=0-1&t=2p2h4bctCItjWjV9-1)에서 확인

<br><br>
## 🌈 주요 기능

### 1. 첨부한 파일로 계획 검증
<img src="./readmeImg/1.png"/>

- .xlsx와 .csv 파일을 직접 첨부해 로컬에서 실행 가능하도록 구현
- 현장 공장에서의 다양한 제약 사항을 반영해 지표로 제공하며 생산 계획 수립 전 검증
- 전처리를 거친 데이터로, 선형 계획법(scipy, perp) 등을 활용해 로직 설계
- pyqt의 Thread를 이용해 progress bar를 구현하고 알고리즘을 기다리는 시간을 시각화 

### 2. 사전할당 알고리즘
<img src="./readmeImg/2.png"/>

- 계획을 검증하기 전, 생산 계획을 짜는 시간을 단축하기 위해 미리 특정 생산을 효율적으로 특정 라인에 분배하는 사전할당 알고리즘 구현

### 3. 생산 계획 검증
<img src="./readmeImg/3.png"/>

- 생산 계획 결과가 도출되면, 도출된 결과로 생산 계획 재검증
- 실제 SOP와 Capacity로 실제 공장에서 사용할 수 있도록 함
- Export로 결과를 언제든지 파일로 저장할 수 있음

### 4. 생산 계획 커스텀
<img src="./readmeImg/last.png"/>

- 드래그 앤 드랍으로 사용자가 계획 커스텀을 할 수 있도록 구현
- 계획 커스텀을 하면 실시간으로 지표에 반영 되어 빠른 결과 조회
- 복사, 붙여넣기, 삭제 등 사용자 친화적인 키보드 커맨드 제공
- 에러별, 라인별 필터링과 검색 기능 등 사용자 편의 기능 제공