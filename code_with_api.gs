/**
 * 미남 종목 분석 프로그램 - 실제 데이터 버전
 * - Python API 서버로 실제 한국 주식 데이터 수집
 * - 코스피/코스닥 전체 종목 지원
 */

// ⚙️ API 서버 URL (배포 후 업데이트 필요)
var API_BASE_URL = "https://korea-stock-api1.onrender.com";

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('미남 종목 분석기')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * 종목 분석 메인 함수
 */
function analyzeStock(stockName) {
  Logger.log("입력 종목명: " + stockName);
  
  try {
    // 1. 종목 코드 검색
    var searchResult = searchStockCode(stockName);
    
    if (!searchResult.success) {
      return {
        success: false,
        message: searchResult.message
      };
    }
    
    var stockCode = searchResult.code;
    Logger.log("찾은 코드: " + stockCode);
    
    // 2. 주가 데이터 수집 (750일)
    var stockDataResult = fetchStockData(stockCode, 750);
    
    if (!stockDataResult.success) {
      return {
        success: false,
        message: stockDataResult.message
      };
    }
    
    var stockData = stockDataResult.data;
    Logger.log("데이터 개수: " + stockData.length);
    
    if (stockData.length < 100) {
      return {
        success: false,
        message: "데이터가 부족합니다. (수집: " + stockData.length + "개)"
      };
    }
    
    // 3. 미남 종목 분석
    var analysis = checkMinamStock(stockData);
    
    return {
      success: true,
      stockName: searchResult.name,
      stockCode: stockCode,
      isMinam: analysis.isMinam,
      details: analysis
    };
    
  } catch (error) {
    Logger.log('분석 오류: ' + error.toString());
    return {
      success: false,
      message: '분석 중 오류가 발생했습니다: ' + error.toString()
    };
  }
}

/**
 * 종목 코드 검색 (API 호출)
 */
function searchStockCode(stockName) {
  try {
    var url = API_BASE_URL + '/api/search?name=' + encodeURIComponent(stockName);
    Logger.log("검색 URL: " + url);
    
    var response = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      headers: {
        'Accept': 'application/json'
      }
    });
    
    var result = JSON.parse(response.getContentText());
    Logger.log("검색 결과: " + JSON.stringify(result));
    
    return result;
    
  } catch (error) {
    Logger.log("검색 오류: " + error);
    return {
      success: false,
      message: "종목 검색 중 오류가 발생했습니다: " + error.toString()
    };
  }
}

/**
 * 주가 데이터 수집 (API 호출)
 */
function fetchStockData(stockCode, days) {
  try {
    var url = API_BASE_URL + '/api/stock?code=' + stockCode + '&days=' + days;
    Logger.log("데이터 조회 URL: " + url);
    
    var response = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      headers: {
        'Accept': 'application/json'
      }
    });
    
    var result = JSON.parse(response.getContentText());
    Logger.log("데이터 조회 결과: " + (result.success ? result.count + "개" : "실패"));
    
    return result;
    
  } catch (error) {
    Logger.log("데이터 조회 오류: " + error);
    return {
      success: false,
      message: "데이터 조회 중 오류가 발생했습니다: " + error.toString()
    };
  }
}

/**
 * 테스트 함수
 */
function test() {
  var result = analyzeStock("삼성전자");
  Logger.log(JSON.stringify(result, null, 2));
}

/**
 * 미남 종목 분석
 */
function checkMinamStock(data) {
  var result = {
    isMinam: false,
    condition1_lowest: false,
    condition2_uptrend: false,
    condition3_volume: false,
    lowestPoint: null,
    volumeSignal: null,
    reason: []
  };
  
  Logger.log("분석 시작 - 데이터 개수: " + data.length);
  
  var sortedData = data.slice().reverse();
  
  // 1. 최저점 확인
  var lowestPrice = Math.min.apply(null, sortedData.map(function(d) { return d.low; }));
  var lowestIndex = -1;
  
  for (var i = 0; i < sortedData.length; i++) {
    if (sortedData[i].low === lowestPrice) {
      lowestIndex = i;
      result.lowestPoint = {
        date: sortedData[i].date,
        price: lowestPrice
      };
      break;
    }
  }
  
  if (lowestIndex !== -1) {
    result.condition1_lowest = true;
    result.reason.push('✓ 최저점 확인: ' + result.lowestPoint.date + ' (' + Math.round(lowestPrice).toLocaleString() + '원)');
  } else {
    result.reason.push('✗ 최저점을 찾을 수 없습니다');
    return result;
  }
  
  // 2. 상승 추세 확인
  var swingLows = findSwingPoints(sortedData, 'low');
  var swingHighs = findSwingPoints(sortedData, 'high');
  
  var afterLowest = sortedData.slice(lowestIndex);
  var recentLows = swingLows.filter(function(s) { 
    return afterLowest.some(function(d) { return d.date === s.date; }); 
  });
  var recentHighs = swingHighs.filter(function(s) { 
    return afterLowest.some(function(d) { return d.date === s.date; }); 
  });
  
  var hasHigherLow = false;
  var hasHigherHigh = false;
  
  if (recentLows.length >= 2) {
    var lastLow = recentLows[recentLows.length - 1].price;
    var prevLow = recentLows[recentLows.length - 2].price;
    hasHigherLow = lastLow > prevLow;
  }
  
  if (recentHighs.length >= 2) {
    var lastHigh = recentHighs[recentHighs.length - 1].price;
    var prevHigh = recentHighs[recentHighs.length - 2].price;
    hasHigherHigh = lastHigh > prevHigh;
  }
  
  if (hasHigherLow && hasHigherHigh) {
    result.condition2_uptrend = true;
    result.reason.push('✓ 상승 추세 확인: 저점 상승 + 고점 상승');
  } else {
    var msg = '✗ 상승 추세 미확인:';
    if (!hasHigherLow) msg += ' 저점 미상승';
    if (!hasHigherHigh) msg += ' 고점 미상승';
    result.reason.push(msg);
  }
  
  // 3. 세력 개입 신호
  var recent60Days = sortedData.slice(-60);
  var volumeSignals = [];
  
  for (var i = 0; i < recent60Days.length; i++) {
    var d = recent60Days[i];
    if (d.close > d.open && d.volume >= 3000000) {
      volumeSignals.push({
        date: d.date,
        volume: d.volume,
        closePrice: d.close
      });
    }
  }
  
  if (volumeSignals.length > 0) {
    result.condition3_volume = true;
    var maxVolumeSignal = volumeSignals.reduce(function(max, sig) {
      return sig.volume > max.volume ? sig : max;
    });
    result.volumeSignal = maxVolumeSignal;
    result.reason.push('✓ 세력 개입 신호: ' + maxVolumeSignal.date + ' (거래량 ' + 
                       (maxVolumeSignal.volume / 10000).toFixed(0) + '만주)');
  } else {
    result.reason.push('✗ 최근 60일 내 대량 거래 없음 (거래량 300만주 이상 양봉)');
  }
  
  result.isMinam = result.condition1_lowest && 
                   result.condition2_uptrend && 
                   result.condition3_volume;
  
  Logger.log("최종 판정: " + result.isMinam);
  
  return result;
}

/**
 * 스윙 포인트 찾기
 */
function findSwingPoints(data, type) {
  var swings = [];
  var windowSize = 5;
  
  for (var i = windowSize; i < data.length - windowSize; i++) {
    var currentPrice = data[i][type];
    var isSwing = true;
    
    for (var j = i - windowSize; j <= i + windowSize; j++) {
      if (j === i) continue;
      
      if (type === 'low') {
        if (data[j][type] <= currentPrice) {
          isSwing = false;
          break;
        }
      } else {
        if (data[j][type] >= currentPrice) {
          isSwing = false;
          break;
        }
      }
    }
    
    if (isSwing) {
      swings.push({
        date: data[i].date,
        price: currentPrice
      });
    }
  }
  
  return swings;
}
