import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import requests
import datetime
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

def latlon_to_grid(lat, lon):
    """
    기상청(단기예보) 격자 변환 공식
    WGS84 위도(lat), 경도(lon) → 격자좌표 (nx, ny)
    """
    RE = 6371.00877
    GRID = 5.0
    SLAT1 = 30.0
    SLAT2 = 60.0
    OLON = 126.0
    OLAT = 38.0
    XO = 210 / GRID
    YO = 675 / GRID

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon  = OLON  * DEGRAD
    olat  = OLAT  * DEGRAD

    sn = math.tan(math.pi*0.25 + slat2*0.5) / math.tan(math.pi*0.25 + slat1*0.5)
    sn = math.log(math.cos(slat1)/math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi*0.25 + slat1*0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi*0.25 + olat*0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi*0.25 + (lat)*DEGRAD*0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon*DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0*math.pi
    if theta < -math.pi:
        theta += 2.0*math.pi
    theta *= sn

    x = (ra * math.sin(theta)) + XO + 0.5
    y = (ro - ra * math.cos(theta)) + YO + 0.5
    return int(x), int(y)



def get_ultra_srt_ncst(service_key, nx, ny):
    """
    기상청 초단기실황 (getUltraSrtNcst) 예시 호출
    - 일반적으로 base_date: YYYYMMDD, base_time: HHMM (매 정시+30분~안팎)
    """
    today = datetime.datetime.today().strftime("%Y%m%d")
    
    now = datetime.datetime.now()

    available_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
    
    # 현재 시간보다 가장 가까운 base_time 선택
    base_time = max([t for t in available_times if int(t[:2]) <= now.hour], default="2300")


    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?"
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": today,
        "base_time": base_time,
        "nx": nx,
        "ny": ny
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error(f"API 요청 실패 (HTTP {response.status_code})")
        return None

    try:
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # DataFrame 변환
        if items:
            df = pd.DataFrame(items)[["category", "fcstDate", "fcstTime", "fcstValue"]]
            # 날짜 + 시간 컬럼 추가
            df["datetime"] = df["fcstDate"] + " " + df["fcstTime"].str[:2] + ":00"
            # 피벗 테이블로 변환 (카테고리별 행, 날짜+시간별 열)
            df_pivot = df.pivot(index="category", columns="datetime", values="fcstValue")

            # 빈칸을 공백 문자열로 채우기
            df_pivot = df_pivot.fillna("")

            return df_pivot
        else:
            st.warning("API 응답 데이터가 없습니다.")
            return None
    except Exception as e:
        st.error(f"API 응답 처리 중 오류 발생: {e}")
        return None

def main():
    st.title("Folium 지도 - 기상청 API 연동")

    # (C-1) Folium 지도 생성
    m = folium.Map(location=[37.247331465665276, 127.05076500468245], zoom_start=14)  # 강남역 부근
    map_data = st_folium(m, width=700, height=500)
    
    # 지도에서 클릭된 좌표 가져오기
    last_clicked = map_data.get("last_clicked")

    # # (C-2) 지도에서 최근에 클릭된 좌표
    # last_clicked = map_data["last_clicked"]
    if last_clicked:
        lat = last_clicked["lat"]
        lon = last_clicked["lng"]

        st.write(f"**클릭한 좌표**: 위도={lat:.6f}, 경도={lon:.6f}")

        # (C-3) 버튼 클릭 시 -> 기상청 API 조회
        if st.button("이 위치 날씨 조회"):
            # (1) 위·경도 → 격자(nx, ny)
            nx, ny = latlon_to_grid(lat, lon)
            st.info(f"격자 좌표 (nx, ny) = ({nx}, {ny})")

            # (2) 기상청 초단기실황 API 호출
            service_key = "YhEcDR4HFCRAfQ+EnagWgpFx3CSj5hL8gRAQ8iqYBL1lELwtPB9n8i5FzymaZxo7bE7eQrlyApafUYmYDEOIvQ=="  # TODO: 본인 인증키
            df = get_ultra_srt_ncst(service_key, nx, ny)


            if df is not None:
                # DataFrame을 Streamlit과 ace_tools를 이용하여 표시
                with st.expander("📋 원본 데이터"):
                    st.dataframe(df)  # ✅ 사용자가 클릭하면 펼쳐지는 데이터프레임

                tab1, tab2, tab3, tab4 = st.tabs(["🌡 기온", "☔ 강수량", "💨 바람", "💧 습도"])
                data = np.random.randn(10, 1)
                
                # tab1.subheader("A tab with a chart")
                # 🔹 TMP(기온) 값 필터링
                if "TMP" in df.index:
                    tmp_data = df.loc["TMP"].astype(float)  # 숫자로 변환
                    tmp_data.index = pd.to_datetime(tmp_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환

                    # 📌 TMP 데이터를 Plotly에서 사용할 수 있도록 변환
                    df_tmp = pd.DataFrame({
                        "날짜시간": tmp_data.index,  # 날짜 + 시간 컬럼 사용
                        "기온(℃)": tmp_data.values
                    })

                    # 📌 Plotly 차트 생성 (줌 & 팬 가능)
                    fig = px.line(df_tmp, x="날짜시간", y="기온(℃)", markers=True)

                    fig.update_layout(
                        xaxis_title="날짜 및 시간",
                        yaxis_title="기온(℃)",
                        yaxis=dict(autorange=True),  # Y축 자동 조정
                        xaxis=dict(
                            # rangeslider=dict(visible=True),  # X축 줌 슬라이더 추가
                            range=[df_tmp["날짜시간"].iloc[0], df_tmp["날짜시간"].iloc[12]],  # 초기 13개 데이터만 보이게 설정
                            fixedrange=False,  # 줌 & 팬 가능
                            constrain='domain',  # ✅ 데이터가 없는 곳으로 이동 제한
                            rangebreaks=[  # 🔹 빈 곳(데이터 없는 곳)으로 이동 제한
                                dict(bounds=["min", df_tmp["날짜시간"].min()]),  # 최소 데이터 이전으로 이동 불가
                                dict(bounds=["max", df_tmp["날짜시간"].max()])  # 최대 데이터 이후로 이동 불가
                            ]
                        ),
                        width=900, height=400  # 차트 크기 조정
                    )

                    # 📌 탭 1에 차트 표시
                    tab1.subheader("🌡 시간별 기온 변화")
                    tab1.plotly_chart(fig, use_container_width=True)

                else:
                    tab1.warning("TMP(기온) 데이터가 없습니다.")
#----------------------------------------------------------------------------------------------ㅡㅡㅡㅡㅡㅡㅡㅡ
                if "POP" in df.index:
                    POP_data = df.loc["POP"].astype(float)  # 숫자로 변환
                    PCP_data = df.loc["PCP"].replace("강수없음", 0).astype(float)  # 숫자로 변환

                    POP_data.index = pd.to_datetime(POP_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환
                    PCP_data.index = pd.to_datetime(PCP_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환

                    # 📌 TMP 데이터를 Plotly에서 사용할 수 있도록 변환
                    df_POP = pd.DataFrame({
                        "날짜시간": POP_data.index,  # 날짜 + 시간 컬럼 사용
                        "강수확율(%)": POP_data.values,
                        "강수량(mm)": PCP_data.values
                    })

                    fig = go.Figure()

                    # ✅ 강수 확률 (POP) → 막대 그래프
                    fig.add_trace(go.Bar(
                        x=df_POP["날짜시간"],
                        y=df_POP["강수확율(%)"],
                        name="강수확률(%)",
                        marker_color="lightblue",
                        opacity=0.6
                    ))
                    
                    # ✅ 강수량 (PRE) → 선 그래프
                    fig.add_trace(go.Scatter(
                        x=df_POP["날짜시간"],
                        y=df_POP["강수량(mm)"],
                        name="강수량(mm)",
                        mode="lines+markers",
                        marker=dict(color="blue"),

                    ))
                    
                    
                    # ✅ 레이아웃 설정 (이중 Y축 추가)
                    fig.update_layout(
                        xaxis_title="날짜 및 시간",
                        yaxis=dict( range=[0, 100]),
                        xaxis=dict(
                            range=[df_POP["날짜시간"].iloc[0], df_POP["날짜시간"].iloc[12]],  # 초기 13개 데이터만 보이게 설정
                            fixedrange=False,  # 줌 & 팬 가능
                            rangebreaks=[  # 🔹 빈 곳(데이터 없는 곳)으로 이동 제한
                                dict(bounds=["min", df_POP["날짜시간"].min()]),  # 최소 데이터 이전으로 이동 불가
                                dict(bounds=["max", df_POP["날짜시간"].max()])  # 최대 데이터 이후로 이동 불가
                            ]
                        ),
                        width=900, height=400
                    )

                    # 📌 탭 2(강수)에서 그래프 표시
                    tab2.subheader("☔ 시간별 강수 확률 & 강수량")
                    tab2.plotly_chart(fig, use_container_width=True)

                else:
                    tab2.warning("TMP(기온) 데이터가 없습니다.")
                                    
#----------------------------------------------------------------------------------------------

                if "WSD" in df.index:
                    WSD_data = df.loc["WSD"].astype(float)  # 숫자로 변환
                    # PCP_data = df.loc["PCP"].replace("강수없음", 0).astype(float)  # 숫자로 변환

                    WSD_data.index = pd.to_datetime(WSD_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환
                    # PCP_data.index = pd.to_datetime(PCP_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환

                    # 📌 TMP 데이터를 Plotly에서 사용할 수 있도록 변환
                    df_WSD = pd.DataFrame({
                        "날짜시간": WSD_data.index,  # 날짜 + 시간 컬럼 사용
                        "풍속(m/s)": WSD_data.values
                    })

                    fig = go.Figure()

                    # ✅ 강수 확률 (POP) → 막대 그래프
                    fig.add_trace(go.Bar(
                        x=df_WSD["날짜시간"],
                        y=df_WSD["풍속(m/s)"],
                        name="풍속(m/s)",
                        marker_color="lightblue",
                        opacity=0.6
                    ))
                    
                    # # ✅ 강수량 (PRE) → 선 그래프
                    # fig.add_trace(go.Scatter(
                    #     x=df_WSD["날짜시간"],
                    #     y=df_WSD["강수량(mm)"],
                    #     name="강수량(mm)",
                    #     mode="lines+markers",
                    #     marker=dict(color="blue"),

                    # ))
                    
                    
                    # ✅ 레이아웃 설정 (이중 Y축 추가)
                    fig.update_layout(
                        xaxis_title="날짜 및 시간",
                        yaxis_title="풍속(m/s)",
                        yaxis=dict(autorange=True),  # Y축 자동 조정
                        xaxis=dict(
                            range=[df_WSD["날짜시간"].iloc[0], df_WSD["날짜시간"].iloc[12]],  # 초기 13개 데이터만 보이게 설정
                            fixedrange=False,  # 줌 & 팬 가능
                            rangebreaks=[  # 🔹 빈 곳(데이터 없는 곳)으로 이동 제한
                                dict(bounds=["min", df_WSD["날짜시간"].min()]),  # 최소 데이터 이전으로 이동 불가
                                dict(bounds=["max", df_WSD["날짜시간"].max()])  # 최대 데이터 이후로 이동 불가
                            ]
                        ),
                        width=900, height=400
                    )

                    tab3.subheader("🌬시간별 풍속")
                    tab3.plotly_chart(fig, use_container_width=True)
#----------------------------------------------------------------------------------------------
                if "REH" in df.index:
                    REH_data = df.loc["REH"].astype(float)  # 숫자로 변환
                    # PCP_data = df.loc["PCP"].replace("강수없음", 0).astype(float)  # 숫자로 변환

                    REH_data.index = pd.to_datetime(REH_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환
                    # PCP_data.index = pd.to_datetime(PCP_data.index, format="%Y%m%d %H:%M")  # 날짜+시간 변환

                    # 📌 TMP 데이터를 Plotly에서 사용할 수 있도록 변환
                    df_REH = pd.DataFrame({
                        "날짜시간": REH_data.index,  # 날짜 + 시간 컬럼 사용
                        "습도(%)": REH_data.values
                    })

                    fig = go.Figure()

                    # ✅ 강수 확률 (POP) → 막대 그래프
                    fig.add_trace(go.Bar(
                        x=df_REH["날짜시간"],
                        y=df_REH["습도(%)"],
                        name="습도(%)",
                        marker_color="lightblue",
                        opacity=0.6
                    ))
                    
                    # # ✅ 강수량 (PRE) → 선 그래프
                    # fig.add_trace(go.Scatter(
                    #     x=df_WSD["날짜시간"],
                    #     y=df_WSD["강수량(mm)"],
                    #     name="강수량(mm)",
                    #     mode="lines+markers",
                    #     marker=dict(color="blue"),

                    # ))
                    
                    
                    # ✅ 레이아웃 설정 (이중 Y축 추가)
                    fig.update_layout(
                        xaxis_title="날짜 및 시간",
                        yaxis_title="습도(%)",
                        yaxis=dict( range=[0, 100]),
                        xaxis=dict(
                            range=[df_REH["날짜시간"].iloc[0], df_REH["날짜시간"].iloc[12]],  # 초기 13개 데이터만 보이게 설정
                            fixedrange=False,  # 줌 & 팬 가능
                            rangebreaks=[  # 🔹 빈 곳(데이터 없는 곳)으로 이동 제한
                                dict(bounds=["min", df_REH["날짜시간"].min()]),  # 최소 데이터 이전으로 이동 불가
                                dict(bounds=["max", df_REH["날짜시간"].max()])  # 최대 데이터 이후로 이동 불가
                            ]
                        ),
                        width=900, height=400
                    )

                    tab4.subheader("시간별 습도")
                    tab4.plotly_chart(fig, use_container_width=True)
            else:
                st.error("🌧 날씨 데이터 조회 실패!")

            
    else:
        st.info("📍 지도를 클릭해서 위치를 선택하세요!")

if __name__ == "__main__":
    main()