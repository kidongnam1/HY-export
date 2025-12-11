# -*- coding: utf-8 -*-
"""
config.py

전체 시스템의 공통 설정을 관리하는 모듈.

기능 요약
---------
1) DEFAULT_CONFIG (기본 설정) 제공
2) user_settings.json 파일을 자동 생성/갱신
3) get_config() → 합쳐진 설정 반환
4) save_config() → 사용자 변경 사항 저장

⭐ 수정 사항 (Ruby 디버깅):
- OUTPUT_POLICY 키 추가 (processing_core.py에서 사용)

리오(GY LOGIS) OCR/리네임 시스템 용 구조
"""

import json
from pathlib import Path
from typing import Dict, Any

# ---------------------------
# 1. 기본 설정 정의
# ---------------------------

DEFAULT_CONFIG = {
    # 운영 여부
    "DARK_MODE": False,

    # 기본 Pack 모드: 1PACK or 2PACK
    "PACK_MODE": "1PACK",

    # OCR 동작 모드: "LOCAL" 또는 "CLOUD" (기본은 LOCAL)
    "OCR_MODE": "LOCAL",

    # PaddleOCR 설정
    "OCR_MIN_SCORE": 0.30, # S2 OCR 백업 로직의 임계값으로 사용됨

    # 파일 경로들
    "LAST_OPEN_FOLDER": "",
    "LAST_SAVE_FOLDER": "",
    
    # S1 엑셀 파일 경로
    "LAST_S1_EXCEL_FILE": "",

    # S1/S2 독립 폴더 키
    "LAST_S1_FOLDER": "",
    "LAST_S2_FOLDER": "",
    "LAST_IMAGE_ROOT": "",

    # ⭐ 출력 정책 추가 (processing_core.py에서 사용) ⭐
    # "same_as_input": 원본 폴더에 결과 저장
    # "new_folder": 새 폴더 생성하여 저장 (기본값)
    "OUTPUT_POLICY": "new_folder",

    # 결과 파일 이름 규칙
    "RESULT_EXCEL_NAME": "S2_내품사진_자동생성.xlsx",
    "REPORT_FILE_NAME": "ocr_summary_report.txt",

    # Google Cloud Vision API JSON 경로 (선택)
    "GOOGLE_CLOUD_JSON": "",

    # 이미지 최대 가로길이(px)
    "MAX_IMAGE_WIDTH": 1600,

    # 파일명 생성 시 최대 글자수
    "MAX_FILENAME_LENGTH": 180,
}

# 사용자 설정 파일 위치
CONFIG_PATH = Path("user_settings.json")


# ---------------------------
# 2. 설정 파일 읽기
# ---------------------------

def _load_user_config() -> Dict[str, Any]:
    """
    user_settings.json 파일을 읽어 dict로 반환한다.
    파일이 없거나 파싱 실패하면 빈 dict 반환.
    """
    if not CONFIG_PATH.exists():
        return {}

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 파일이 깨졌거나 JSON 파싱 오류
        return {}


# ---------------------------
# 3. 설정 파일 저장
# ---------------------------

def save_config(cfg: Dict[str, Any]):
    """
    전달받은 설정 dict를 user_settings.json 파일에 저장.
    """
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] 설정 저장 실패: {e}")


# ---------------------------
# 4. 현재 설정 읽기
# ---------------------------

def get_config() -> Dict[str, Any]:
    """
    DEFAULT_CONFIG + user_settings.json 조합한 최종 설정 dict 반환.
    잘못된 키는 자동으로 복구.
    """
    user_cfg = _load_user_config()
    merged = {}

    # 기본 설정부터 채우고
    for key, value in DEFAULT_CONFIG.items():
        merged[key] = value

    # 사용자 설정으로 덮어쓰기
    for key, value in user_cfg.items():
        if key in DEFAULT_CONFIG:
            merged[key] = value
        else:
            print(f"[WARN] 알 수 없는 설정 키 무시됨: {key}")

    return merged


# ---------------------------
# 5. 설정 업데이트 함수
# ---------------------------

def update_config(updates: Dict[str, Any]):
    """
    특정 설정 값만 부분적으로 수정하고 저장.
    예: update_config({"PACK_MODE": "2PACK"})
    """
    cfg = get_config()
    for key, value in updates.items():
        if key in DEFAULT_CONFIG:
            cfg[key] = value
        else:
            print(f"[WARN] 존재하지 않는 설정키({key}) → 무시됨")
    save_config(cfg)
