# -*- coding: utf-8 -*-
"""
utils.py

GY OCR + Rename 시스템용 공통 유틸 모듈 (수정됨: 로그 레벨, OS 호환 열기)
"""

import re
import os
import subprocess
from pathlib import Path


def safe_mkdir(path) -> Path:
    # ... (기존 로직 유지) ...
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def normalize_code(text: str) -> str:
    # ... (기존 로직 유지) ...
    if not text:
        return ""

    t = str(text).upper()
    t = t.replace(" ", "")
    t = t.replace("_", "-")
    # 허용 문자(A~Z, 0~9, '-')만 남기기
    t = re.sub(r"[^A-Z0-9\-]", "", t)
    return t


def log_print(msg: str, level="LOG"):
    """
    로그 출력용 함수. 레벨(LOG/WARN/ERROR)을 구분하여 출력한다.
    """
    level = level.upper()
    
    # ANSI Color Code 사용 (Windows 환경에서는 Tkinter/메시지 박스 사용이 일반적이나, 콘솔 로깅 개선)
    if level == "ERROR":
        color_code = "\033[91m" # Red
    elif level == "WARN":
        color_code = "\033[93m" # Yellow
    else:
        color_code = "\033[0m"  # Default
        
    print(f"{color_code}[{level}] {msg}\033[0m")


def open_file_or_dir_cross_platform(path_str: str):
    """
    OS 환경에 따라 파일(엑셀) 또는 폴더를 여는 함수.
    os.startfile 대신 subprocess를 사용하여 크로스-플랫폼 호환성을 높인다.
    """
    if not path_str:
        return False
        
    path = Path(path_str)
    if not path.exists():
        log_print(f"경로가 존재하지 않습니다: {path_str}", "WARN")
        return False
        
    try:
        if os.name == 'nt':  # Windows
            os.startfile(path_str)
        elif os.uname().sysname == 'Darwin':  # macOS
            subprocess.call(('open', path_str))
        else:  # Linux 및 기타 POSIX 환경
            subprocess.call(('xdg-open', path_str))
        return True
    except Exception as e:
        log_print(f"파일/폴더 열기 실패 ({path_str}): {e}", "ERROR")
        return False