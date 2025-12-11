# -*- coding: utf-8 -*-
"""
user_popup.py

Tkinter 팝업 유틸 모듈

1) 컨테이너 이름 입력
2) OCR 결과 텍스트를 사용자가 직접 수정할 수 있는 팝업
"""

import tkinter as tk
from tkinter import simpledialog, messagebox


def ask_container_name(parent: tk.Tk) -> str:
    """
    한 컨테이너 작업이 끝난 후,
    사용자에게 컨테이너 번호(이름)를 입력받는 팝업.

    Parameters
    ----------
    parent : tk.Tk or tk.Toplevel
        메인 윈도우 핸들

    Returns
    -------
    str
        사용자가 입력한 컨테이너 이름 (취소 시 빈 문자열)
    """
    while True:
        ctn = simpledialog.askstring(
            "컨테이너 번호 입력",
            "이 컨테이너의 번호(이름)를 입력하세요.\n\n예) MSCU1234567, C101 등",
            parent=parent,
        )

        if ctn is None:
            # 사용자가 취소를 누른 경우
            ans = messagebox.askyesno(
                "확인",
                "컨테이너 번호 입력을 취소하시겠습니까?\n"
                "취소하면 이 컨테이너 작업도 중단됩니다.",
                parent=parent,
            )
            if ans:
                return ""
            else:
                # 다시 입력 루프로
                continue

        ctn = ctn.strip()
        if not ctn:
            messagebox.showwarning(
                "입력 필요",
                "컨테이너 번호가 비어 있습니다.\n다시 입력해주세요.",
                parent=parent,
            )
            continue

        # 마지막 확인
        ok = messagebox.askyesno(
            "컨테이너 번호 확인",
            f"컨테이너 번호를 '{ctn}'(으)로 설정할까요?",
            parent=parent,
        )
        if ok:
            return ctn
        # 아니오를 누르면 다시 입력 루프


def popup_edit_ocr(parent: tk.Tk, ocr_text: str, image_path) -> str:
    """
    OCR 로 읽어온 원본 텍스트를 사용자에게 보여주고,
    직접 수정할 수 있게 하는 팝업.

    Parameters
    ----------
    parent : tk.Tk or tk.Toplevel
        메인 윈도우 핸들
    ocr_text : str
        OCR 엔진(Paddle 등)에서 읽은 원본 텍스트
    image_path : str or Path
        어느 이미지에서 읽은 텍스트인지(파일명 표시용)

    Returns
    -------
    str
        사용자가 최종 확정한 텍스트
        (그냥 확인만 누르면 원래 텍스트 그대로 반환)
    """
    img_name = str(image_path)
    title = "OCR 결과 확인 / 수정"

    # 메시지 박스로 한 번 안내
    msg = (
        f"다음 이미지에서 읽은 OCR 결과입니다.\n"
        f"파일: {img_name}\n\n"
        f"내용을 확인하고, 필요하면 수정해주세요."
    )

    messagebox.showinfo(title, msg, parent=parent)

    # 실제 편집 팝업 (멀티라인이 아니어도 괜찮다면 askstring 사용)
    new_text = simpledialog.askstring(
        title,
        "OCR 텍스트 (수정 가능):",
        initialvalue=ocr_text,
        parent=parent,
    )

    # 사용자가 취소를 눌렀을 경우 -> 원본 텍스트 유지
    if new_text is None:
        return ocr_text

    return new_text.strip()
