# -*- coding: utf-8 -*-
"""
excel_builder.py

한 컨테이너 기준 S2 표준 엑셀 형식(단일 시트)을 생성하는 모듈.
(최종 수정: '검수 필요' 컬럼 추가 및 타입 강제)
"""

import pandas as pd


S2_COLUMNS = [
    "순번",          # 1
    "컨테이너 No",   # 2
    "품명",          # 3
    "Ton Bag No1",   # 4
    "Lot No1",       # 5
    "Ton Bag No2",   # 6
    "Lot No2",       # 7
    "ID1",           # 8
    "Lot1",          # 9
    "Tag1",          # 10
    "ID2",           # 11
    "Lot2",          # 12
    "Tag2",          # 13
    "검수 필요"      # 14. 신규 추가 컬럼 (확인 요함 플래그)
]

# 데이터 관련 컬럼을 문자열 타입으로 명시적으로 정의
STRING_COLUMNS = [
    "컨테이너 No", "품명", "Ton Bag No1", "Lot No1", 
    "Ton Bag No2", "Lot No2", "ID1", "Lot1", 
    "Tag1", "ID2", "Lot2", "Tag2", "검수 필요"
]


def create_excel_template(num_sets: int, container_name: str = "") -> pd.DataFrame:
    """
    S2 표준 스키마(14컬럼)를 갖는 DataFrame을 생성하고, 
    핵심 데이터 컬럼의 타입을 'object' (문자열)로 강제한다.
    """
    if num_sets <= 0:
        num_sets = 1

    # 1단계: 기본 데이터 틀 생성 (모든 값은 우선 빈 문자열)
    data = {col: [""] * num_sets for col in S2_COLUMNS}

    # 2단계: 순번 및 컨테이너 No 채우기
    data["순번"] = list(range(1, num_sets + 1))

    if container_name is None:
        container_name = ""
    data["컨테이너 No"] = [container_name] * num_sets

    df = pd.DataFrame(data, columns=S2_COLUMNS)
    
    # 3단계: 핵심 컬럼 타입을 문자열(object)로 강제 변환
    for col in STRING_COLUMNS:
        if col in df.columns:
            # fillna("")를 통해 NaN 값이 object 타입으로 들어가는 것을 방지
            df[col] = df[col].astype(str).fillna("")

    return df