# -*- coding: utf-8 -*-
"""
naming_rules.py
1PACK / 2PACK 이름 생성 규칙 적용 모듈

입력: OCR 결과 문자열 리스트
출력: 파일명 구성 요소 (ID, LOT, TAG)
"""

import re

# -------------------------------------------------------------
# 1) 기본 패턴 정의
# -------------------------------------------------------------
PATTERN_FULL = re.compile(r"[A-Z]{3}-\d{4}-\d{4}")      # LOT  (예: NSH-2511-1077)
PATTERN_TAG  = re.compile(r"[A-Z]{3}-\d{4}-\d{5}")      # TAG  (예: NSH-2511-10762)
PATTERN_ID   = re.compile(r"\d{4}")                    # ID   (예: 2511)


# -------------------------------------------------------------
# 2) 텍스트에서 ID / LOT / TAG 추출
# -------------------------------------------------------------
def extract_id_lot_tag(text: str):
    """
    OCR 텍스트에서 ID, LOT, TAG 를 추출.
    규칙:
        LOT  = 영문3 + 번호4 + 번호4
        TAG  = 영문3 + 번호4 + 번호5
        ID   = LOT 또는 TAG 중간의 4자리 숫자
    """
    if not text:
        return "", "", ""

    t = text.upper()

    tag = None
    lot = None
    id_val = None

    # TAG 먼저 찾기
    m_tag = PATTERN_TAG.search(t)
    if m_tag:
        tag = m_tag.group(0)
        id_val = tag.split("-")[1]

    # LOT 찾기
    m_lot = PATTERN_FULL.search(t)
    if m_lot:
        lot = m_lot.group(0)
        if id_val is None:
            id_val = lot.split("-")[1]

    return id_val or "", lot or "", tag or ""


# -------------------------------------------------------------
# 3) 1PACK 이름 생성 규칙
# -------------------------------------------------------------
def generate_names_1pack(ocr_texts):
    """
    입력 ocr_texts = [txt1, txt2]

    출력:
        name1: "SN. ID-LOT (TAG)"
        name2: "SN. ID-LOT (TAG)-1"
    """
    txt1 = ocr_texts[0] if len(ocr_texts) > 0 else ""
    id_val, lot, tag = extract_id_lot_tag(txt1)

    # 파일명 형식 (SN 은 main.py 에서 붙임)
    base = f"{id_val}-{lot} ({tag})"

    name1 = base + ".jpg"
    name2 = base + "-1.jpg"

    return name1, name2, id_val, lot, tag


# -------------------------------------------------------------
# 4) 2PACK 이름 생성 규칙
# -------------------------------------------------------------
def generate_names_2pack(ocr_texts):
    """
    입력 ocr_texts = [txt1, txt2, txt3]

    규칙:
        txt1 = Pack1
        txt2 = Pack2
        txt3 = Stack(두 개 올린 사진)

    출력:
        name1: SN. ID-LOT (TAG1)
        name2: SN. ID-LOT (TAG2)
        name3: SN. ID-LOT (TAG1, TAG2)
    """

    txt1 = ocr_texts[0] if len(ocr_texts) > 0 else ""
    txt2 = ocr_texts[1] if len(ocr_texts) > 1 else ""

    # 팩1
    id1, lot1, tag1 = extract_id_lot_tag(txt1)
    # 팩2
    id2, lot2, tag2 = extract_id_lot_tag(txt2)

    # ID, LOT 은 두 팩이 동일해야 한다는 전제
    id_val = id1 or id2
    lot_val = lot1 or lot2

    name1 = f"{id_val}-{lot_val} ({tag1}).jpg"
    name2 = f"{id_val}-{lot_val} ({tag2}).jpg"
    name3 = f"{id_val}-{lot_val} ({tag1}, {tag2}).jpg"

    return name1, name2, name3, id_val, lot_val, tag1, tag2
