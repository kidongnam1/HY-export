# -*- coding: utf-8 -*-
"""
ocr_local.py

로컬 OCR 전용 모듈. (수정됨: 신뢰도 점수 반환)
- 기본 엔진: PaddleOCR (영문/숫자 위주)
"""

import os
from pathlib import Path
from typing import Tuple, List

import cv2
import numpy as np

# PaddleOCR는 외부 패키지이므로, 설치 여부를 안전하게 체크
try:
    from paddleocr import PaddleOCR
    _PADDLE_AVAILABLE = True
except ImportError:
    _PADDLE_AVAILABLE = False
    PaddleOCR = None  # type: ignore


# 전역 OCR 엔진 (필요 시 한 번만 초기화)
_OCR_ENGINE = None


def _init_ocr_engine():
    """
    PaddleOCR 엔진을 지연 초기화(lazy init) 한다.
    설치가 안 되어 있으면 None 유지.
    """
    global _OCR_ENGINE

    if not _PADDLE_AVAILABLE:
        return None

    if _OCR_ENGINE is None:
        # 영문/숫자 위주이므로 lang="en"
        _OCR_ENGINE = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            show_log=False,
        )
    return _OCR_ENGINE


def _preprocess_image(image_path: Path) -> np.ndarray:
    """
    간단 전처리:
    - 이미지 로드
    - 너무 크면 리사이즈 (가로 기준 1600px)
    - 그레이스케일 변환
    - 약한 블러 + OTSU 이진화
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    h, w = img.shape[:2]
    max_width = 1600

    if w > max_width:
        scale = max_width / float(w)
        img = cv2.resize(
            img,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA,
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, bw = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return bw


def ocr_extract_from_image(image_path) -> Tuple[str, float]:
    """
    단일 이미지에서 텍스트를 추출하고 평균 신뢰도 점수를 반환한다.

    Returns
    -------
    Tuple[str, float]
        (인식된 전체 텍스트, 평균 신뢰도 점수)
        실패 시 ("", 0.0) 반환
    """
    if isinstance(image_path, str):
        image_path = Path(image_path)

    # PaddleOCR 사용 가능 여부 체크
    if not _PADDLE_AVAILABLE:
        print("[WARN] PaddleOCR가 설치되어 있지 않습니다.")
        return "", 0.0

    try:
        engine = _init_ocr_engine()
        if engine is None:
            print("[WARN] PaddleOCR 엔진 초기화 실패")
            return "", 0.0

        # 전처리
        bw = _preprocess_image(image_path)

        # OCR 수행
        result = engine.ocr(bw, cls=True)

        texts: List[str] = []
        scores: List[float] = []
        
        # result 구조: [ [ [ box, (text, score) ], ... ] ]
        for line in result:
            for box, (txt, score) in line:
                # 여기서 신뢰도 임계값(MIN_SCORE)을 적용할 수도 있지만,
                # 모든 결과를 반환하여 main.py에서 최종 결정하도록 합니다.
                texts.append(txt)
                scores.append(score)

        full_text = " ".join(texts).strip()
        
        # ⭐ 신뢰도 점수 계산 ⭐
        if not scores:
            avg_score = 0.0
        else:
            # 평균 점수 (0.0 ~ 1.0)
            avg_score = sum(scores) / len(scores)

        return full_text, avg_score

    except Exception as e:
        print(f"[ERROR] 로컬 OCR 처리 중 오류 발생: {e}")
        return "", 0.0