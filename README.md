# 🌦️ Streamlit_map_weather

## 📌 프로젝트 소개

**Streamlit, Python, Folium, MongoDB**를 활용한 **날씨 데이터 시각화 및 지도 표시 프로젝트**입니다.  
기상청 API에서 수집한 과거 날씨 데이터를 지도와 차트로 시각화합니다.

---

## ⚙️ 사용 기술

- **프론트엔드 (대시보드)**: Streamlit
- **데이터 처리 및 시각화**: Python, Folium
- **데이터베이스**: MongoDB
- **외부 API**: 기상청 과거 날씨 API

---

## ✨ 주요 기능

- ✅ 과거 날씨 데이터 지도 시각화 (강수량, 온도, 습도 등)
- ✅ 강수량 데이터 전처리 및 가공 (예: "강수없음", "1mm 미만" → 0)
- ✅ MongoDB에 데이터 저장 및 불러오기
- ✅ Streamlit 웹 대시보드로 사용자 인터페이스 제공

---

## 예시

![지도 예시](images/weather_map.png)

## 🚀 설치 및 실행 방법

```bash
# 1. 저장소 클론
git clone https://github.com/ysyoung1205/Streamlit_map_weather.git
cd Streamlit_map_weather

# 2. 가상환경 설정 (선택)
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# 3. 패키지 설치
pip install -r requirements.txt

# 4. Streamlit 앱 실행
streamlit run folium_weather.py

```
