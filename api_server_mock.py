"""
한국 주식 데이터 API 서버 - Mock 버전
실제와 유사한 샘플 데이터 제공
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# 주요 종목 리스트
STOCK_LIST = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "서린바이오": "038070.KQ",
    "LG화학": "051910.KS",
    "현대차": "005380.KS",
    "셀트리온": "068270.KS"
}

# 종목별 기준 가격
BASE_PRICES = {
    "005930.KS": 70000,  # 삼성전자
    "000660.KS": 120000,  # SK하이닉스
    "035420.KS": 200000,  # 네이버
    "035720.KS": 50000,   # 카카오
    "038070.KQ": 8000,    # 서린바이오
    "051910.KS": 400000,  # LG화학
    "005380.KS": 180000,  # 현대차
    "068270.KS": 180000   # 셀트리온
}

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "한국 주식 데이터 API (Mock)",
        "note": "실제와 유사한 샘플 데이터를 제공합니다"
    })

@app.route('/api/search', methods=['GET'])
def search_stock():
    """종목명으로 종목코드 검색"""
    try:
        stock_name = request.args.get('name', '').strip()
        
        if not stock_name:
            return jsonify({
                "success": False,
                "message": "종목명을 입력해주세요"
            }), 400
        
        # 하드코딩된 리스트에서 검색
        if stock_name in STOCK_LIST:
            code = STOCK_LIST[stock_name]
            return jsonify({
                "success": True,
                "code": code,
                "name": stock_name,
                "market": "KS" if ".KS" in code else "KQ"
            })
        
        # 부분 일치 검색
        for name, code in STOCK_LIST.items():
            if stock_name in name or name in stock_name:
                return jsonify({
                    "success": True,
                    "code": code,
                    "name": name,
                    "market": "KS" if ".KS" in code else "KQ"
                })
        
        return jsonify({
            "success": False,
            "message": f"'{stock_name}' 종목을 찾을 수 없습니다. 지원 종목: 삼성전자, 카카오, 서린바이오 등"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }), 500

@app.route('/api/stock', methods=['GET'])
def get_stock_data():
    """주가 데이터 조회 (샘플 데이터)"""
    try:
        stock_code = request.args.get('code', '').strip()
        days = int(request.args.get('days', 750))
        
        if not stock_code:
            return jsonify({
                "success": False,
                "message": "종목코드를 입력해주세요"
            }), 400
        
        # 기준 가격 가져오기
        base_price = BASE_PRICES.get(stock_code, 50000)
        
        # 샘플 데이터 생성
        data = generate_realistic_data(base_price, days)
        
        return jsonify({
            "success": True,
            "code": stock_code,
            "count": len(data),
            "data": data,
            "note": "실제와 유사한 샘플 데이터입니다"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }), 500

def generate_realistic_data(base_price, days):
    """실제와 유사한 주가 데이터 생성"""
    data = []
    current_price = base_price
    
    today = datetime.now()
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y.%m.%d')
        
        # 최저점 시뮬레이션 (약 500일 전)
        if 450 <= i <= 550:
            current_price = current_price * 0.998  # 점진적 하락
        
        # 상승 추세 시뮬레이션 (300일 전부터)
        elif i <= 300:
            current_price = current_price * 1.001  # 점진적 상승
        
        # 일반 변동
        else:
            change_percent = random.uniform(-0.03, 0.03)
            current_price = current_price * (1 + change_percent)
        
        # 가격 범위 제한
        current_price = max(base_price * 0.3, min(base_price * 2.0, current_price))
        
        # OHLC 생성
        open_price = current_price * random.uniform(0.97, 1.03)
        close_price = current_price * random.uniform(0.97, 1.03)
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.05)
        low_price = min(open_price, close_price) * random.uniform(0.95, 1.0)
        
        # 거래량 (대량 거래 시뮬레이션 - 최근 60일 내 일부)
        volume = random.randint(500000, 2000000)
        
        # 미남 종목 조건 만족시키기
        if i <= 60 and random.random() > 0.85:  # 15% 확률로 대량 거래
            volume = random.randint(3500000, 6000000)  # 300만 이상
            close_price = open_price * 1.03  # 양봉
        
        data.append({
            "date": date_str,
            "open": round(open_price),
            "high": round(high_price),
            "low": round(low_price),
            "close": round(close_price),
            "volume": volume
        })
    
    # 최신순으로 (현재가 첫 번째)
    data.reverse()
    
    return data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
