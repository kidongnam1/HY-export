# -*- coding: utf-8 -*-
"""
report.py

GY OCR + Rename 시스템용 검수/요약 리포트 모듈

기능 요약
---------
1) 한 컨테이너에 대해 생성된 S2 DataFrame(df)을 기준으로
   - 세트(SN) 개수
   - Pack 모드별 기대 사진 수
   - 실제 사진 수
   - 필수 필드(ID, LOT, TAG) 누락 여부
   를 점검한다.

2) 점검 결과를 사람이 읽기 쉬운 텍스트로 정리하여
   컨테이너 폴더에 'ocr_summary_report.txt' 파일로 저장한다.

사용 예
-------
    from report import generate_report

    report_text, report_path = generate_report(
        df=df,
        folder=folder_path,
        pack_mode="1PACK",
        image_count=len(images),
        excel_path=excel_path,
    )

"""

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


def _safe_path(folder) -> Path:
    """
    folder 인자를 pathlib.Path 로 안전하게 변환.
    """
    if isinstance(folder, Path):
        return folder
    return Path(folder)


def _count_missing_fields(df: pd.DataFrame, pack_mode: str):
    """
    필수 필드 누락 개수를 계산한다.

    1Pack:
        - ID1, Lot1, Tag1
    2Pack:
        - ID1, Lot1, Tag1, Tag2

    Returns
    -------
    dict
        {
            "ID1": 누락 개수,
            "Lot1": 누락 개수,
            "Tag1": 누락 개수,
            "Tag2": 누락 개수 (2Pack일 때만 의미 있음)
        }
    """
    missing = {"ID1": 0, "Lot1": 0, "Tag1": 0, "Tag2": 0}

    if "ID1" in df.columns:
        missing["ID1"] = int(df["ID1"].isna() | (df["ID1"] == "")).sum()

    if "Lot1" in df.columns:
        missing["Lot1"] = int(df["Lot1"].isna() | (df["Lot1"] == "")).sum()

    if "Tag1" in df.columns:
        missing["Tag1"] = int(df["Tag1"].isna() | (df["Tag1"] == "")).sum()

    if pack_mode == "2PACK" and "Tag2" in df.columns:
        missing["Tag2"] = int(df["Tag2"].isna() | (df["Tag2"] == "")).sum()

    return missing


def _collect_sn_with_missing(df: pd.DataFrame, pack_mode: str):
    """
    필수 필드가 누락된 SN 번호 목록을 수집한다.
    """
    required_cols = ["ID1", "Lot1", "Tag1"]
    if pack_mode == "2PACK":
        required_cols.append("Tag2")

    sn_list = []
    for idx, row in df.iterrows():
        # 순번 컬럼이 없으면 인덱스를 SN으로 사용
        sn = row["순번"] if "순번" in df.columns else (idx + 1)

        # 한 행이라도 필수 필드 중 비어 있으면 수집
        missing_flag = False
        for col in required_cols:
            if col not in df.columns:
                continue
            val = row[col]
            if pd.isna(val) or str(val).strip() == "":
                missing_flag = True
                break

        if missing_flag:
            sn_list.append(sn)

    return sn_list


def generate_report(
    df: pd.DataFrame,
    folder,
    pack_mode: str,
    image_count: int,
    excel_path: Optional[Path] = None,
) -> Tuple[str, Path]:
    """
    한 컨테이너에 대한 OCR/이름생성 결과를 검수하여
    요약 텍스트 리포트를 생성하고 파일로 저장한다.

    Parameters
    ----------
    df : pd.DataFrame
        S2 표준 스키마(13컬럼)를 가진 DataFrame
    folder : str or Path
        컨테이너 관련 파일들이 있는 폴더
    pack_mode : str
        "1PACK" 또는 "2PACK"
    image_count : int
        실제 이미지 파일 개수
    excel_path : Path, optional
        방금 저장한 엑셀 파일 경로 (없어도 됨)

    Returns
    -------
    (report_text, report_path) : (str, Path)
        report_text : 생성된 리포트 전체 텍스트
        report_path : 저장된 리포트 파일 경로
    """
    folder_path = _safe_path(folder)

    # 세트(SN) 개수
    num_sets = len(df)

    # Pack 모드별 기대 사진 수
    if pack_mode == "1PACK":
        expected_images = num_sets * 2
        pack_desc = "1PACK (2샷/세트)"
    else:
        expected_images = num_sets * 3
        pack_desc = "2PACK (3샷/세트)"

    # 필수 필드 누락 개수
    missing = _count_missing_fields(df, pack_mode)
    sn_with_missing = _collect_sn_with_missing(df, pack_mode)

    # 컨테이너 이름(가능하면) 추출
    container_name = ""
    if "컨테이너 No" in df.columns:
        # 여러 값이 섞여 있을 수도 있으나, 보통은 동일 값이라고 가정
        unique_ctn = df["컨테이너 No"].dropna().unique()
        if len(unique_ctn) == 1:
            container_name = str(unique_ctn[0])
        elif len(unique_ctn) > 1:
            container_name = f"{unique_ctn[0]} 외 {len(unique_ctn) - 1}개"
        else:
            container_name = ""

    # 엑셀 파일 이름 문자열
    excel_info = str(excel_path) if excel_path is not None else "(미저장 또는 경로 미지정)"

    # 리포트 텍스트 구성
    lines = []
    lines.append("========================================")
    lines.append(" GY OCR / Rename 검수 리포트")
    lines.append("========================================")
    lines.append("")
    lines.append(f"- 컨테이너 폴더 : {folder_path}")
    lines.append(f"- 컨테이너 No   : {container_name if container_name else '(미입력)'}")
    lines.append(f"- PACK 모드     : {pack_desc}")
    lines.append(f"- 세트(SN) 개수 : {num_sets}")
    lines.append("")
    lines.append("▶ 사진 개수 점검")
    lines.append(f"  · 기대 사진 수 : {expected_images}장")
    lines.append(f"  · 실제 사진 수 : {image_count}장")
    diff = image_count - expected_images
    if diff == 0:
        lines.append("  · 결과         : OK (기대 사진 수와 일치)")
    else:
        lines.append("  · 결과         : ⚠ 불일치")
        lines.append(f"    - 차이       : {diff}장 (실제 - 기대)")
    lines.append("")
    lines.append("▶ 필수 필드 누락 개수")
    lines.append(f"  · ID1  누락 : {missing['ID1']}개")
    lines.append(f"  · Lot1 누락 : {missing['Lot1']}개")
    lines.append(f"  · Tag1 누락 : {missing['Tag1']}개")
    if pack_mode == "2PACK":
        lines.append(f"  · Tag2 누락 : {missing['Tag2']}개")
    lines.append("")
    lines.append("▶ 필수 값 누락된 SN 목록")
    if sn_with_missing:
        sn_str = ", ".join(str(x) for x in sn_with_missing)
        lines.append(f"  · SN : {sn_str}")
    else:
        lines.append("  · 없음 (모든 행에서 필수 필드가 채워져 있음)")
    lines.append("")
    lines.append("▶ 엑셀 파일")
    lines.append(f"  · 저장 경로 : {excel_info}")
    lines.append("")
    lines.append("※ 이 리포트는 1컨테이너 기준 자동 생성된 요약이며,")
    lines.append("   실제 선적서류 및 사진과 교차 검증하는 것을 권장합니다.")
    lines.append("========================================")
    lines.append("")

    report_text = "\n".join(lines)

    # 리포트 파일 저장
    report_path = folder_path / "ocr_summary_report.txt"
    report_path.write_text(report_text, encoding="utf-8")

    return report_text, report_path
