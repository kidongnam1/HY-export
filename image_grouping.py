# -*- coding: utf-8 -*-
"""
image_grouping.py

1Pack / 2Pack 모드에 따라 이미지 파일을
SN(세트) 단위로 묶어주는 모듈. (수정됨: 자연 정렬 적용)
"""

import os
from pathlib import Path
from tkinter import messagebox
import re # 정규 표현식 모듈 추가


IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")


def _natural_sort_key(s):
    """
    파일명에서 숫자와 문자열을 분리하여 자연 정렬을 위한 키를 생성한다.
    예: ["IMG_10.jpg"] < ["IMG_100.jpg"]
    """
    # 숫자(d+)와 나머지 문자열을 기준으로 분리
    return [
        int(s) if s.isdigit() else s.lower() 
        for s in re.split(r'(\d+)', s)
    ]


def list_images(folder: Path):
    """
    폴더 내의 이미지 파일을 확장자 기준으로 정렬하여 리스트로 반환.
    (자연 정렬 적용)
    """
    if isinstance(folder, str):
        folder = Path(folder)

    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    ]
    
    # ⭐ 파일 경로 대신 파일 이름에 자연 정렬 키 적용 ⭐
    files.sort(key=lambda p: _natural_sort_key(p.name))
    
    return files


def _check_count_and_confirm(total: int, pack_mode: str) -> bool:
    # ... (기존 로직 유지) ...
    if pack_mode == "1PACK":
        # 2의 배수 여부 검사 (필수 조건)
        if total % 2 != 0:
            messagebox.showerror(
                "심각 오류",
                f"1Pack 모드에서는 이미지 개수가 반드시 2의 배수여야 합니다.\n"
                f"현재 개수: {total}장\n"
                f"사진 누락/중복 여부를 확인해주세요."
            )
            return False

        # 40장이 아닐 때 경고 (선택 조건)
        if total != 40:
            ans = messagebox.askyesno(
                "경고",
                f"1Pack 모드 기준 권장 사진 수는 40장입니다.\n"
                f"현재 개수: {total}장\n\n"
                f"그래도 계속 진행하시겠습니까?"
            )
            if not ans:
                return False

    elif pack_mode == "2PACK":
        # 3의 배수 여부 검사 (필수 조건)
        if total % 3 != 0:
            messagebox.showerror(
                "심각 오류",
                f"2Pack 모드에서는 이미지 개수가 반드시 3의 배수여야 합니다.\n"
                f"현재 개수: {total}장\n"
                f"사진 누락/중복 여부를 확인해주세요."
            )
            return False

        # 60장이 아닐 때 경고 (선택 조건)
        if total != 60:
            ans = messagebox.askyesno(
                "경고",
                f"2Pack 모드 기준 권장 사진 수는 60장입니다.\n"
                f"현재 개수: {total}장\n\n"
                f"그래도 계속 진행하시겠습니까?"
            )
            if not ans:
                return False

    else:
        messagebox.showerror("오류", f"알 수 없는 PACK 모드: {pack_mode}")
        return False

    return True


def group_images(folder: Path, pack_mode: str):
    # ... (기존 로직 유지) ...
    files = list_images(folder) # 정렬된 리스트 사용
    total = len(files)

    if total == 0:
        messagebox.showwarning("경고", "선택한 폴더에 이미지 파일이 없습니다.")
        return []

    # 개수 검사 및 사용자 확인
    if not _check_count_and_confirm(total, pack_mode):
        return []

    groups = []
    if pack_mode == "1PACK":
        step = 2
    else:
        step = 3

    for i in range(0, total, step):
        group = files[i:i + step]
        # 혹시라도 마지막 그룹이 step보다 작으면 버림 (안정성)
        if len(group) == step:
            groups.append(group)

    return groups