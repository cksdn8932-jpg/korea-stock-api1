"""
한국 주식 데이터 API 서버
yfinance 사용 (계좌 불필요)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
CORS(app)  # CORS 허용

# 주요 종목 리스트 (코스피/코스닥)
STOCK_LIST = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "LG화학": "051910.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "POSCO홀딩스": "005490.KS",
    "삼성SDI": "006400.KS",
    "LG전자": "066570.KS",
    "현대모비스": "012330.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "삼성물산": "028260.KS",
    "LG생활건강": "051900.KS",
    "삼성전기": "009150.KS",
    "기업은행": "024110.KS",
    "하나금융지주": "086790.KS",
    "SK이노베이션": "096770.KS",
    "현대글로비스": "086280.KS",
    "삼성화재": "000810.KS",
    "LG": "003550.KS",
    "SK텔레콤": "017670.KS",
    "KT&G": "033780.KS",
    "포스코퓨처엠": "003670.KS",
    "HMM": "011200.KS",
    "SK": "034730.KS",
    "두산에너빌리티": "034020.KS",
    "한국전력": "015760.KS",
    "엔씨소프트": "036570.KS",
    "카카오뱅크": "323410.KS",
    "크래프톤": "259960.KS",
    "LG유플러스": "032640.KS",
    "삼성생명": "032830.KS",
    "고려아연": "010130.KS",
    "한화에어로스페이스": "012450.KS",
    "하이브": "352820.KS",
    "서린바이오": "038070.KQ",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "엘앤에프": "066970.KQ",
    "포스코DX": "022100.KS",
    "삼성에스디에스": "018260.KS",
    "두산": "000150.KS"
}

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "한국 주식 데이터 API",
        "endpoints": {
            "/api/search": "종목명 검색 (GET: ?name=삼성전자)",
            "/api/stock": "주가 데이터 (GET: ?code=005930&days=750)"
        }
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
    """주가 데이터 조회"""
    try:
        stock_code = request.args.get('code', '').strip()
        days = int(request.args.get('days', 750))
        
        if not stock_code:
            return jsonify({
                "success": False,
                "message": "종목코드를 입력해주세요"
            }), 400
        
        # yfinance로 데이터 가져오기
        ticker = yf.Ticker(stock_code)
        
        # 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 100)  # 여유있게
        
        # 데이터 다운로드
        df = ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if df is None or len(df) == 0:
            return jsonify({
                "success": False,
                "message": "데이터를 가져올 수 없습니다"
            }), 404
        
        # 데이터 변환
        data = []
        for index, row in df.iterrows():
            data.append({
                "date": index.strftime('%Y.%m.%d'),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        # 최신순으로 정렬
        data.reverse()
        
        # 요청한 일수만큼만 반환
        data = data[:days]
        
        return jsonify({
            "success": True,
            "code": stock_code,
            "count": len(data),
            "data": data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류 발생: {str(e)}",
            "trace": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
