import os
import anthropic
import re
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DiarySentimentAgent:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        print(f"[DEBUG] Loaded API Key: {self.api_key}")  # Debug statement
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def analyze(self, diary_text, history=None):
        """일기 텍스트를 분석하여 감정 상태와 피드백을 생성합니다."""
        # 기본 응답 템플릿
        default_response = {
            "today_state": "분석 실패",
            "today_message": "감정 분석에 실패했습니다.",
            "pattern_feedback": "-",
            "empathy_message": "-",
            "action_suggestion": "-",
            "hope_message": "-",
            "score": 50.0
        }
        
        try:
            # 일기 본문이 800자 이상이면 앞부분만 사용
            diary_short = diary_text[:800] if len(diary_text) > 800 else diary_text
            
            # 프롬프트 구성
            prompt = """다음 일기를 분석하고 정확히 아래 JSON 형식으로만 응답해주세요.

일기 내용:
{diary_text}

규칙:
1. 아래 JSON 형식만 사용하세요
2. 다른 설명이나 텍스트는 절대 포함하지 마세요
3. 모든 필드는 한글로 작성하세요
4. score는 반드시 0과 100 사이의 숫자여야 합니다

응답 형식:
{{
    "today_state": "감정 상태를 한 문장으로",
    "today_message": "일기 내용에 대한 구체적 설명",
    "pattern_feedback": "감정 패턴에 대한 피드백",
    "action_suggestion": "실천 가능한 제안",
    "hope_message": "희망적 메시지",
    "empathy_message": "공감 메시지",
    "score": 50.0
}}""".format(diary_text=diary_short)

            # Claude 호출
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text if hasattr(response, 'content') else response.completion
            
            # 디버깅을 위해 원본 응답 저장
            print("[Claude 응답]", content)
            with open("claude_response_debug.txt", "w", encoding="utf-8") as f:
                f.write(content)
            
            try:
                # JSON 추출
                json_match = re.search(r'\{[\s\S]*\}', content)
                if not json_match:
                    raise ValueError("JSON not found in response")
                
                json_str = json_match.group()
                print("\n=== 추출된 JSON ===")
                print(json_str)
                
                # JSON 파싱
                result = json.loads(json_str)
                
                # 필수 필드 및 타입 검증
                required_fields = {
                    "today_state": (str, "감정 분석 실패"),
                    "today_message": (str, "감정 분석에 실패했습니다."),
                    "pattern_feedback": (str, "-"),
                    "action_suggestion": (str, "-"),
                    "hope_message": (str, "-"),
                    "empathy_message": (str, "-"),
                    "score": (float, 50.0)
                }
                
                # 각 필드 검증 및 변환
                for field, (field_type, default_value) in required_fields.items():
                    try:
                        if field not in result or result[field] is None:
                            result[field] = default_value
                            continue
                            
                        if field == "score":
                            # score 특별 처리
                            score = result[field]
                            if isinstance(score, str):
                                score_match = re.search(r'(-?\d+\.?\d*)', str(score))
                                score = float(score_match.group(1)) if score_match else default_value
                            else:
                                score = float(score)
                            
                            # 범위 검증
                            if not (0 <= score <= 100):
                                score = default_value
                            result[field] = score
                        else:
                            # 문자열 필드는 str로 변환
                            result[field] = str(result[field]).strip() if result[field] else default_value
                    except Exception as e:
                        print(f"[WARNING] {field} 필드 처리 중 오류: {e}")
                        result[field] = default_value
                
                print("\n=== 최종 결과 ===")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return result
                
            except Exception as e:
                print(f"[ERROR] JSON 파싱 실패: {str(e)}\n원본: {content}")
                print(traceback.format_exc())
                return default_response
                
        except Exception as e:
            print(f"[ERROR] Claude API 호출 실패: {e}")
            print(traceback.format_exc())
            return default_response

if __name__ == "__main__":
    agent = DiarySentimentAgent()
    diary = input("오늘의 일기를 입력하세요: ")
    result = agent.analyze(diary)
    print(json.dumps(result, ensure_ascii=False, indent=2))