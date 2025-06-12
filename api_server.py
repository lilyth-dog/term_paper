from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from diary_sentiment_agent import DiarySentimentAgent
import uvicorn
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime, timedelta

app = FastAPI()

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = DiarySentimentAgent()

# ThreadPoolExecutor 초기화 - 최대 작업자 수 지정
executor = ThreadPoolExecutor(max_workers=3)

# 정적 파일 제공을 위한 디렉토리 구조 확인
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# 정적 파일 디렉토리 구조 확인 및 생성
for dir_path in [
    os.path.join(STATIC_DIR, "css"),
    os.path.join(STATIC_DIR, "js"),
]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

HISTORY_FILE = "sentiment_history.json"

def save_history(entry):
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = []
    # 같은 날짜의 기존 entry가 있으면 덮어쓰기 (수정)
    history = [h for h in history if h["date"] != entry["date"]]
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def convert_state_to_score(state: str) -> float:
    """
    감정 상태 텍스트를 기반으로 점수를 계산합니다.
    
    Args:
        state (str): 감정 상태 텍스트
    
    Returns:
        float: 0-100 사이의 감정 점수
    """
    state = state.strip()
    # 긍정 패턴
    if any(x in state for x in ["햇살", "맑음", "따스", "밝은", "봄", "행복", "기쁨", "설렘", "감사", "완벽", "환한", "미소", "따뜻", "희망", "평화로운", "의욕", "자신감"]):
        return 85.0
    # 중립/잔잔 패턴
    elif any(x in state for x in ["잔잔", "평온", "고요", "평화", "무던", "평범", "조용", "무미건조", "그저 그런", "무난", "안정", "차분", "담담", "일상", "평이한", "보통"]):
        return 60.0
    # 부정/구름/힘듦 패턴
    elif any(x in state for x in ["구름", "흐림", "비", "바람", "안개", "힘들", "지친", "폭풍", "어두운", "우울", "불안", "슬픔", "지루", "무거운", "불편", "불쾌", "불행", "상실", "외로움", "고통", "좌절", "눈물", "버거운", "불안정"]):
        return 25.0
    # 복합/모호/기타: 긍정+부정 혼합, 또는 미확정
    elif any(x in state for x in ["구름과 햇살", "잔잔하지만 어딘가 흐린", "밝지만 어딘가 무거운", "평온하지만 불안한", "힘들었지만 견디는"]):
        return 45.0
    else:
        # 기본 점수로 중립값 반환
        return 50.0

@app.post("/analyze")
async def analyze_diary(request: Request):
    try:
        data = await request.json()
        diary = data.get("diary", "")
        diary_date = data.get("date")
        
        print(f"\n=== 새로운 분석 요청 ===")
        print(f"날짜: {diary_date}")
        print(f"일기 길이: {len(diary)}자")
        print(f"일기 내용: {diary[:100]}...")  # 처음 100자만 로깅
        if diary_date:
            try:
                # YYYY-MM-DD 형식 검증 및 변환
                datetime.strptime(diary_date, "%Y-%m-%d")
            except Exception:
                diary_date = datetime.now().strftime("%Y-%m-%d")
        else:
            diary_date = datetime.now().strftime("%Y-%m-%d")
        loop = asyncio.get_event_loop()
        history = load_history()
        
        # 입력 데이터 검증
        if not diary:
            return JSONResponse({"error": "diary 필드는 비어 있을 수 없습니다."}, status_code=400)

        try:
            print("\n=== agent.analyze 호출 시작 ===")
            # diary_sentiment_agent.py의 analyze에 history 전달
            result = await loop.run_in_executor(executor, agent.analyze, diary, history)
            print(f"[DEBUG] agent.analyze 결과: {result}")
            
            # 기본 응답 템플릿
            default_response = {
                "today_state": "분석 실패",
                "today_message": "감정 분석 중 오류가 발생했습니다.",
                "pattern_feedback": "-",
                "empathy_message": "-",
                "action_suggestion": "-",
                "hope_message": "-",
                "score": 50.0
            }
            
            # result가 None인 경우
            if result is None:
                print("[ERROR] agent.analyze 결과가 None입니다")
                result = default_response
            # result가 문자열인 경우 JSON 파싱 시도
            elif isinstance(result, str):
                try:
                    print(f"[DEBUG] 문자열을 JSON으로 파싱 시도: {result}")
                    result = json.loads(result)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON 파싱 실패: {e}\n원본 문자열: {result}")
                    result = default_response
            # result가 dict가 아닌 경우
            elif not isinstance(result, dict):
                print(f"[ERROR] 예상치 못한 결과 타입: {type(result)}")
                result = default_response
            
            # 필수 필드 검증
            for field in ["today_state", "today_message", "pattern_feedback", 
                         "empathy_message", "action_suggestion", "hope_message"]:
                if field not in result or not result[field]:
                    print(f"[WARNING] {field} 필드가 없거나 비어있어 기본값으로 대체합니다")
                    result[field] = default_response[field]
                    
        except Exception as e:
            print(f"[ERROR] agent.analyze 처리 중 예외 발생: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JSONResponse({"error": "감정 분석 중 오류가 발생했습니다."}, status_code=500)

        # today_state가 없거나 None/빈문자열이면 기본값
        state = result.get("today_state") or "-"

        # LLM이 반환한 score가 있으면 우선 사용, 없거나 잘못된 경우만 fallback
        score = result.get("score")
        score_valid = False
        try:
            score = float(score)
            if 0 <= score <= 100:
                score_valid = True
        except Exception:
            pass

        if not score_valid:
            # LLM의 score가 유효하지 않은 경우, 감정 상태에서 추론
            score = convert_state_to_score(state)

        # 새 entry 생성
        entry = {
            "date": diary_date,
            "score": score,
            "today_state": result.get("today_state", "-"),
            "today_message": result.get("today_message", "-"),
            "pattern_feedback": result.get("pattern_feedback", "-"),
            "empathy_message": result.get("empathy_message", "-"),
            "action_suggestion": result.get("action_suggestion", "-"),
            "hope_message": result.get("hope_message", "-"),
            "diary": diary
        }
        save_history(entry)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"today_state": "-", "today_message": f"감정 분석 실패: {e}"}, status_code=500)

@app.get("/history")
async def get_history(period: str = "all"):
    print("[DEBUG] /history endpoint called")
    try:
        history = load_history()
        print("[DEBUG] Loaded history:", history)
        history.sort(key=lambda h: h.get("date", ""))
        if period != "all":
            try:
                days = int(period)
                cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                history = [h for h in history if h["date"] >= cutoff]
            except Exception as e:
                print("[ERROR] Invalid period parameter:", e)
        if not history:
            print("[DEBUG] No history data available")
            return {"history": [], "avg_score": None, "count": 0, "sentiment_ratio": {"긍정": 0, "중립": 0, "부정": 0}}

        valid_scores = [h["score"] if h["score"] is not None else 50.0 for h in history]
        avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None
        pos = sum(1 for s in valid_scores if s > 70)
        neu = sum(1 for s in valid_scores if 40 <= s <= 70)
        neg = sum(1 for s in valid_scores if s < 40)
        total = len(valid_scores) or 1
        sentiment_ratio = {
            "긍정": round(pos / total * 100),
            "중립": round(neu / total * 100),
            "부정": round(neg / total * 100)
        }
        print("[DEBUG] Sentiment ratio:", sentiment_ratio)
        return {
            "history": history,
            "avg_score": avg_score,
            "count": len(history),
            "sentiment_ratio": sentiment_ratio
        }
    except Exception as e:
        print("[ERROR] Exception in /history endpoint:", e)
        return {"error": "Failed to fetch history data"}

# 날짜별로 여러 개의 기록이 있을 수 있으니, 날짜+인덱스 쿼리 지원
@app.get("/diary_entry")
async def get_diary_entry(date: str = Query(...), idx: int = Query(0)):
    history = load_history()
    # 해당 날짜의 모든 기록 필터
    entries = [h for h in history if h["date"] == date]
    if not entries or idx >= len(entries):
        return {"error": "해당 날짜의 일기 기록이 없습니다."}
    return entries[idx]

@app.put("/diary_entry")
async def update_diary_entry(date: str = Body(...), diary: str = Body(...)):
    """
    날짜(date)와 새 일기(diary)를 받아 해당 날짜의 일기를 수정(LLM 재분석 후 덮어쓰기)
    """
    try:
        # 날짜 형식 검증
        datetime.strptime(date, "%Y-%m-%d")
        
        # 기존 기록 불러오기
        history = load_history()
        
        # 기존 entry 삭제
        history = [h for h in history if h["date"] != date]
        
        # LLM 재분석
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(executor, agent.analyze, diary, history)
            print(f"[DEBUG] 일기 수정 분석 결과: {result}")
            
            # 기본 응답 템플릿
            default_response = {
                "today_state": "분석 실패",
                "today_message": "감정 분석 중 오류가 발생했습니다.",
                "pattern_feedback": "-",
                "empathy_message": "-",
                "action_suggestion": "-",
                "hope_message": "-",
                "score": 50.0
            }
            
            # result가 None인 경우
            if result is None:
                print("[ERROR] agent.analyze 결과가 None입니다")
                result = default_response
            # result가 문자열인 경우 JSON 파싱 시도
            elif isinstance(result, str):
                try:
                    print(f"[DEBUG] 문자열을 JSON으로 파싱 시도: {result}")
                    result = json.loads(result)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON 파싱 실패: {e}\n원본 문자열: {result}")
                    result = default_response
            # result가 dict가 아닌 경우
            elif not isinstance(result, dict):
                print(f"[ERROR] 예상치 못한 결과 타입: {type(result)}")
                result = default_response
            
            # 점수 처리
            score = result.get("score")
            score_valid = False
            try:
                score = float(score)
                if 0 <= score <= 100:
                    score_valid = True
            except Exception:
                pass

            if not score_valid:
                # LLM의 score가 유효하지 않은 경우, 감정 상태 기반으로 추론
                state = result.get("today_state") or "-"
                score = convert_state_to_score(state)
        
        except Exception as e:
            print(f"[ERROR] agent.analyze 처리 중 예외 발생: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JSONResponse({"error": "감정 분석 중 오류가 발생했습니다."}, status_code=500)

        # 새 entry 생성
        entry = {
            "date": date,
            "score": score,
            "today_state": result.get("today_state", "-"),
            "today_message": result.get("today_message", "-"),
            "pattern_feedback": result.get("pattern_feedback", "-"),
            "empathy_message": result.get("empathy_message", "-"),
            "action_suggestion": result.get("action_suggestion", "-"),
            "hope_message": result.get("hope_message", "-"),
            "diary": diary
        }
        
        # 기록 저장
        save_history(entry)
        
        return JSONResponse({"success": True, "message": "일기가 성공적으로 수정되었습니다."})
        
    except ValueError as e:
        return JSONResponse(
            {"success": False, "error": f"날짜 형식이 올바르지 않습니다: {str(e)}"},
            status_code=400
        )
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": f"수정 중 오류가 발생했습니다: {str(e)}"},
            status_code=500
        )

@app.get("/")
async def read_root():
    """루트 경로 요청 시 기본 페이지로 리다이렉트"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return JSONResponse({"error": "index.html not found"}, status_code=404)
    return FileResponse(index_path)

@app.get("/diary")
async def get_diary():
    """일기 관련 기본 페이지로 리다이렉트"""
    diary_path = os.path.join(STATIC_DIR, "diary.html")
    if not os.path.exists(diary_path):
        return JSONResponse({"error": "diary.html not found"}, status_code=404)
    return FileResponse(diary_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
