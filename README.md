 # Diary Sentiment Analysis Agent 프로젝트 안내

##  프로젝트 개요
- **기능:** 사용자가 일기를 입력하면, Anthropic Claude API(LLM 프롬프트 기반)로 감정 점수(0~1), 감정 분류(긍정/부정/중립), 감정 메시지를 반환합니다.
- **특징:**
  - Claude 3 Haiku 모델 활용
  - 프롬프트 엔지니어링 기반 감정 분석
  - 결과를 웹 UI에서 실시간 확인

##  실행 방법

### 1. 필수 패키지 설치
```powershell
pip install fastapi uvicorn anthropic
```

### 2. API 키 환경변수 등록
- `.env` 파일 또는 PowerShell 환경변수로 등록
- 예시 (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-...여기에_본인_키..."
```

### 3. 서버 실행
```powershell
python api_server.py
```

### 4. 웹 UI 접속
- 브라우저에서 [http://localhost:8000/](http://localhost:8000/) 접속
- 일기를 입력하고 "분석하기" 클릭 → 감정 점수, 분류, 메시지 확인

## 주요 파일 설명
- `api_server.py` : FastAPI 기반 웹 API 및 정적 파일 제공
- `diary_sentiment_agent.py` : Claude API 프롬프트 기반 감정 분석 에이전트
- `static/index.html` : 웹 프론트엔드(UI)
- `.env` : (선택) API 키 환경변수 파일

##  에이전트(Agent)
- 이 프로젝트의 에이전트는 다음과 같은 파이프라인을 가집니다:
  1. **입력 수집:** 사용자가 일기를 입력하면,
  2. **프롬프트 생성:** 입력을 바탕으로 LLM(Claude)에 최적화된 프롬프트를 자동 생성하고,
  3. **LLM 호출:** 프롬프트를 LLM에 전달해 감정 분석 결과를 받아오며,
  4. **결과 해석 및 응답:** LLM의 응답을 파싱·해석해 점수/분류/메시지로 가공하여 반환합니다.

## 감정 관리 플랫폼
목적은 단순 감정 분석을 넘어, **공감과 연결, 감정 추적 및 피드백, 개인화, 자기 주도적 관리, 실질적 행동 제안, 위기 대응** 등 정서적 지원의 모든 요소를 통합적으로 제공하는 "감정 관리 플랫폼"을 만드는 것입니다.

## 프롬프트어링 기반 해결
- LLM 프롬프트를 통해 아래와 같은 고도화된 기능을 1차적으로 제공합니다:
  - **공감 메시지**: 사용자의 감정과 상황에 맞는 시적이고 따뜻한 공감/응원/위로
    - 예: "오늘은 마음에 햇살이 머문 하루였어요.", "구름이 낀 하루지만, 내일은 분명 맑아질 거예요."
  - **감정 추적 및 피드백**: 장기 이력 기반 감정 변화 분석 및 피드백
  - **개인화**: 감정 패턴, 최근 기록, 사용자의 목표/상황을 반영한 맞춤 메시지
  - **자기 주도적 관리**: 사용자가 직접 목표/관리법을 입력하면, 그에 맞는 코칭/동기부여 제공
  - **실질적 행동 제안**: 감정 상태별로 실천 가능한 구체적 행동(예: 산책, 대화, 명상 등) 제안
  - **위기 대응**: 부정적 감정 급증, 위험 신호 감지 시 즉각적 경고 및 도움말 제공

- **감정 상태 표현(시적/일상적, 긍정/중립/부정 단어 미사용)**:
  - **햇살 가득한 하루** (밝음, 기분 좋은 날)
  - **잔잔한 하루** (평온, 생각이 많은 날)
  - **구름 낀 하루** (지침, 위로가 필요한 날)

- **프롬프트 예시(긍정/중립/부정 단어 미사용)**:
  > "아래는 사용자의 최근 감정 이력과 오늘의 일기입니다.\n---\n[감정 이력: 날짜, 점수, 감정 상태(햇살/잔잔함/구름 등), 메시지 ...]\n오늘의 일기: ...\n---\n1. 오늘의 하루를 시적/일상적 표현으로 한 문장으로 요약\n2. 최근 감정 변화에 대한 따뜻한 피드백\n3. 맞춤 공감 메시지(친구처럼)\n4. 실천 가능한 작은 행동 제안(일상 속에서 실천할 수 있는 것)\n5. 위로와 희망을 담은 한마디\n를 JSON으로 만들어줘. 단, 긍정/중립/부정 같은 단어는 사용하지 말고, 어떤 하루였는지 자연스럽게 표현해줘."

- **LLM 응답 포맷 예시(긍정/중립/부정 단어 미사용)**:
```json
{
  "today_state": "구름이 머문 하루",
  "today_message": "오늘은 마음이 조금 무거웠지만, 그런 날도 소중해요.",
  "trend_feedback": "최근 감정이 잔잔하게 이어지고 있어요.",
  "empathy_message": "힘들 땐 잠시 멈춰 쉬어가도 괜찮아요. 당신의 하루를 응원합니다.",
  "action_suggestion": "따뜻한 차 한 잔과 함께 오늘을 정리해보세요.",
  "hope_message": "구름 뒤엔 언제나 햇살이 기다리고 있어요."
}
```

## 감정 분석 상세 설명

### 감정 점수 산정 방식
- 점수 범위: 0.0 ~ 1.0
- 점수 의미:
  - 0.0 ~ 0.3: 구름이 머문 하루 (위로가 필요한 상태)
  - 0.3 ~ 0.7: 잔잔한 하루 (평온한 상태)
  - 0.7 ~ 1.0: 햇살 가득한 하루 (밝은 상태)

### 프롬프트 구성 요소 설명
1. **감정 이력 데이터**
   - 최근 7일간의 감정 기록 제공
   - 날짜, 점수, 감정 상태, 메시지를 포함
   - 패턴 분석을 위한 기초 데이터로 활용

2. **오늘의 일기**
   - 사용자가 입력한 일기 전문
   - 텍스트 길이 제한 없음
   - 한글/영어 모두 지원

3. **응답 요소별 가이드라인**
   - today_state: 하루를 대표하는 한 문장 (예: "봄비가 내리는 하루")
   - today_message: 감정 상태에 대한 공감 메시지
   - trend_feedback: 최근 감정 흐름 분석
   - empathy_message: 상황별 맞춤 응원/위로
   - action_suggestion: 구체적인 행동 제안
   - hope_message: 긍정적 마무리 메시지

### 사용 예시
1. **일기 입력**
```
오늘은 프로젝트 마감이 있어서 바빴어. 
힘들었지만 무사히 끝내서 다행이야.
동료들과 저녁도 먹고 왔고.
피곤하지만 왠지 뿌듯해.
```

2. **LLM 응답 예시**
```json
{
  "today_state": "저녁 노을이 물드는 하루",
  "today_message": "바쁜 하루 끝에 맛본 달콤한 성취감이 느껴져요.",
  "trend_feedback": "최근 업무로 인한 피로가 쌓여있었는데, 오늘은 작은 승리를 맛보셨네요.",
  "empathy_message": "노력한 만큼 좋은 결과가 있어 다행이에요. 수고 많으셨어요!",
  "action_suggestion": "따뜻한 샤워로 하루의 피로를 씻어내는 건 어떨까요?",
  "hope_message": "오늘의 성취감을 내일의 에너지로 삼아보세요."
}
```

### 특별 케이스 처리
1. **위기 감지**
   - 자해/위험 관련 키워드 발견 시
   - 연속 3일 이상 낮은 감정 점수
   - 급격한 감정 하락
   → 긴급 대응 메시지 및 전문가 상담 안내 포함

2. **장기 패턴 분석**
   - 주간/월간 감정 변화 그래프
   - 요일별/상황별 패턴 분석
   - 개인화된 관리 제안

