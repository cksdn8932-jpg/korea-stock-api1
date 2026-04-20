"""
한국 주식 데이터 API 서버
FinanceDataReader 사용 (계좌 불필요)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
def get_fdr():
    import FinanceDataReader as fdr
    return fdr
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
CORS(app)  # CORS 허용

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
    try:
        fdr = get_fdr()

        stock_name = request.args.get('name', '').strip()

        if not stock_name:
            return jsonify({
                "success": False,
                "message": "종목명을 입력해주세요"
            }), 400

        df_krx = fdr.StockListing('KRX')

        result = df_krx[df_krx['Name'].str.contains(stock_name, na=False)]

        if len(result) == 0:
            return jsonify({
                "success": False,
                "message": f"'{stock_name}' 종목을 찾을 수 없습니다"
            }), 404

        stock = result.iloc[0]

        return jsonify({
            "success": True,
            "code": stock['Code'],
            "name": stock['Name'],
            "market": stock['Market']
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "message": str(e),
            "trace": traceback.format_exc()   # 🔥 핵심 (디버깅용)
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
        
        # ✅ 여기 위치 중요
        fdr = get_fdr()
        
        # 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 100)
        
        # 주가 데이터 가져오기
        df = fdr.DataReader(
            stock_code,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
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
            "message": f"오류 발생: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
