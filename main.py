# -*- coding: utf-8 -*-
"""
main.py – GY LOT/TON Batch Automation (최종 안정화 버전)
[S1/S2] 독립 폴더 구조 및 자동 처리 플래그 적용
"""
import sys 
import os
from pathlib import Path

# ⭐⭐⭐ [최종 수정] 시스템 경로에 현재 폴더를 강제 추가 (ImportError 최종 방어) ⭐⭐⭐
# 모든 임포트보다 먼저 현재 경로를 sys.path의 최우선 순위(0)에 추가하여 모듈 로드를 보장합니다.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐


import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import threading
from typing import Dict, Any, List

# -----------------------------------------------
# 1. 모듈 임포트 (이 시점에서 S1 모듈 로드가 안정화되어야 합니다.)
# -----------------------------------------------
# S2 모듈
from ocr_local import ocr_extract_from_image 
from naming_rules import extract_id_lot_tag
from excel_builder import create_excel_template
from image_grouping import group_images 
from user_popup import ask_container_name
from utils import safe_mkdir, log_print, open_file_or_dir_cross_platform 

from config import get_config, save_config 

# S1 모듈 (try/except로 로드 시도)
try:
    from modules.processing_core import process_step1 
    from modules.report import generate_pdf
    _S1_MODULE_AVAILABLE = True
except ImportError:
    _S1_MODULE_AVAILABLE = False
    log_print("modules.processing_core / report를 찾을 수 없습니다. S1 기능 비활성화.", "WARN")

# -----------------------------------------------
# 2. 전역 설정 로드
# -----------------------------------------------
try:
    CONFIG = get_config()
    OCR_MIN_SCORE = CONFIG.get("OCR_MIN_SCORE", 0.30)
except Exception as e:
    CONFIG = {}
    OCR_MIN_SCORE = 0.30
    log_print(f"config.py 로드 실패: {e}. 기본값 사용.", "ERROR")


class BatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = CONFIG 
        self.title("GY Batch Automation – OCR + Rename System (최종)")
        self.geometry("750x450") 
        self.configure(bg='#F0F0F0')
        
        self.s1_lookup_data: Dict[int, Dict[str, Any]] = {} 

        self._init_vars()
        self._build_ui()
        self._load_s1_data() 
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _init_vars(self):
        """설정 파일에서 변수 초기화 및 S1/S2 독립 경로 변수 추가"""
        self.pack_mode = tk.StringVar(value=self.settings.get("PACK_MODE", "1PACK"))
        
        # S1/S2 독립 폴더 변수
        self.s1_source_var = tk.StringVar(value=self.settings.get("LAST_S1_FOLDER", ""))
        self.s2_source_var = tk.StringVar(value=self.settings.get("LAST_S2_FOLDER", ""))
        self.image_root_var = tk.StringVar(value=self.settings.get("LAST_IMAGE_ROOT", "")) 
        
        self.s1_excel_var = tk.StringVar(value=self.settings.get("LAST_S1_EXCEL_FILE", "")) 
        self.progress_val = tk.IntVar(value=0)

    def _save_settings_from_vars(self):
        """현재 변수 값을 설정 파일에 저장"""
        self.settings.update({
            "PACK_MODE": self.pack_mode.get(),
            "LAST_S1_FOLDER": self.s1_source_var.get(),
            "LAST_S2_FOLDER": self.s2_source_var.get(),
            "LAST_IMAGE_ROOT": self.image_root_var.get(),
            "LAST_S1_EXCEL_FILE": self.s1_excel_var.get(),
        })
        try:
            save_config(self.settings)
        except Exception as e:
            log_print(f"설정 저장 중 오류 발생: {e}", "ERROR")

    def _select_dir(self, var, title):
        """폴더 선택 헬퍼 함수"""
        folder = filedialog.askdirectory(title=title)
        if folder:
            var.set(folder)
            self._save_settings_from_vars()
            
    def _select_file(self, var, title):
        """파일 선택 헬퍼 함수"""
        path = filedialog.askopenfilename(title=title, filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")])
        if path:
            var.set(path)
            self._save_settings_from_vars()
            self._load_s1_data() 
            
    def _open_dir_safely(self, path_str: str):
        """ utils.py의 OS 호환 함수를 사용하여 파일/폴더 열기"""
        if not path_str:
            messagebox.showwarning("열기 오류", "경로가 비어 있습니다.")
            return

        if not Path(path_str).exists():
            messagebox.showwarning("열기 오류", f"경로가 존재하지 않습니다:\n{path_str}")
            return
            
        success = open_file_or_dir_cross_platform(path_str)
        if not success:
             messagebox.showerror("열기 오류", "파일/폴더 열기 실패. 콘솔 로그를 확인하세요.")

    def _load_s1_data(self):
        """S1 엑셀 파일에서 데이터를 읽어와 멤버 변수에 저장 (S2 백업용)"""
        self.s1_lookup_data = {} 
        s1_excel_path = self.s1_excel_var.get()

        if s1_excel_path and Path(s1_excel_path).exists():
            try:
                # Lot1, Tag1, Tag2가 대문자로 들어오도록 dtype을 str로 지정
                df_s1 = pd.read_excel(s1_excel_path, dtype={"순번": int, "ID1": str, "Lot1": str, "Tag1": str, "Tag2": str})
                
                if "순번" in df_s1.columns:
                    for index, row in df_s1.iterrows():
                        try:
                            sn = int(row["순번"])
                            self.s1_lookup_data[sn] = {
                                "ID1": str(row.get("ID1", "")).strip(),
                                "Lot1": str(row.get("Lot1", "")).strip(),
                                "Tag1": str(row.get("Tag1", "")).strip(),
                                "Tag2": str(row.get("Tag2", "")).strip(), 
                            }
                        except ValueError:
                            continue
                    log_print(f"S1 백업 데이터 {len(self.s1_lookup_data)}개 로드 완료.", "LOG")
                else:
                    log_print("S1 엑셀에 '순번' 컬럼이 없어 백업 기능 비활성화.", "WARN")
            except Exception as e:
                log_print(f"S1 엑셀 로드 오류. 백업 기능 비활성화: {e}", "ERROR")

    def _path_row(self, parent, row, label_text, var, browse_cmd, open_cmd):
        """경로 선택 UI를 위한 헬퍼 함수"""
        frm = ttk.Frame(parent)
        frm.grid(row=row, column=0, sticky='w', pady=2, columnspan=4)
        frm.grid_columnconfigure(1, weight=1)
        
        tk.Label(frm, text=label_text, width=15, anchor='w').pack(side='left', padx=(0,6))
        tk.Entry(frm, textvariable=var, width=60, font=("맑은 고딕", 10), justify='left').pack(side='left', fill='x', expand=True, padx=(0,6))
        ttk.Button(frm, text="선택", width=8, command=browse_cmd).pack(side='left', padx=(0,6))
        ttk.Button(frm, text="열기", width=8, command=open_cmd).pack(side='left', padx=(0,0))


    def _build_ui(self):
        main_frm = ttk.Frame(self, padding=12)
        main_frm.pack(fill="both", expand=True)
        
        tab_frm = tk.Frame(main_frm, padx=10, pady=10); tab_frm.pack(fill="both", expand=True)

        # 1. 공통 설정 영역
        tk.Label(tab_frm, text="📦 작업 공통 설정", font=("맑은 고딕", 12, "bold")).pack(anchor="w", pady=(0, 5))
        frm_common = ttk.Frame(tab_frm, padding=5, relief="groove")
        frm_common.pack(fill="x", pady=(0, 15))
        
        # PACK 모드 선택
        tk.Label(frm_common, text="PACK 모드:", width=10).pack(side="left", padx=(0, 10))
        tk.Radiobutton(frm_common, text="1 Pack (2샷)", variable=self.pack_mode, value="1PACK", command=self._save_settings_from_vars).pack(side="left") 
        tk.Radiobutton(frm_common, text="2 Pack (3샷)", variable=self.pack_mode, value="2PACK", command=self._save_settings_from_vars).pack(side="left", padx=10)
        
        # ------------------------------------------------------------------
        # 2. 이미지 폴더 선택 (S1/S2 독립 선택)
        # ------------------------------------------------------------------
        tk.Label(tab_frm, text="📁 이미지 폴더 지정", font=("맑은 고딕", 12, "bold")).pack(anchor="w", pady=(10, 5))
        frm_folders = ttk.Frame(tab_frm, padding=5, relief="groove")
        frm_folders.pack(fill="x", pady=(0, 15))
        
        # 컨테이너 루트 폴더 (S1/S2 폴더의 상위)
        self._path_row(frm_folders, 0, "컨테이너 루트:", self.image_root_var,
                       lambda: self._select_dir(self.image_root_var, "컨테이너 루트 폴더 선택"),
                       lambda: self._open_dir_safely(self.image_root_var.get()))

        # S1 작업 사진 폴더
        self._path_row(frm_folders, 1, "작업 사진 폴더:", self.s1_source_var,
                       lambda: self._select_dir(self.s1_source_var, "작업 사진 폴더 선택"),
                       lambda: self._open_dir_safely(self.s1_source_var.get()))
                       
        # S2 내품 사진 폴더
        self._path_row(frm_folders, 2, "내품 사진 폴더:", self.s2_source_var,
                       lambda: self._select_dir(self.s2_source_var, "내품 사진 폴더 선택"),
                       lambda: self._open_dir_safely(self.s2_source_var.get()))
        
        # ------------------------------------------------------------------
        # 3. S1/S2 실행 영역
        # ------------------------------------------------------------------
        tk.Label(tab_frm, text="▶ 작업 실행", font=("맑은 고딕", 12, "bold")).pack(anchor="w", pady=(10, 5))
        frm_exec = ttk.Frame(tab_frm, padding=5, relief="groove")
        frm_exec.pack(fill="x", pady=(0, 10))

        # S1 엑셀 파일 선택
        frm_s1_excel = ttk.Frame(frm_exec)
        frm_s1_excel.pack(fill="x")
        tk.Label(frm_s1_excel, text="작업 사진 엑셀:", width=15).pack(side="left", padx=(0, 5))
        tk.Entry(frm_s1_excel, textvariable=self.s1_excel_var, width=50).pack(side="left", fill="x", expand=True)
        tk.Button(frm_s1_excel, text="찾기", command=lambda: self._select_file(self.s1_excel_var, "작업 사진 엑셀")).pack(side="left", padx=5)
        tk.Button(frm_s1_excel, text="열기", command=lambda: self._open_dir_safely(self.s1_excel_var.get())).pack(side="left", padx=5)


        frm_buttons = ttk.Frame(frm_exec)
        frm_buttons.pack(fill="x", pady=(10, 5))
        
        # S1 실행 버튼
        self.s1_button = tk.Button(frm_buttons, 
                  text="[1단계] 작업 사진 리네임 시작",
                  font=("맑은 고딕", 12, "bold"),
                  command=self.run_s1_batch,
                  bg="#FFD700")
        self.s1_button.pack(side="left", fill="x", expand=True, padx=5)
        
        if not _S1_MODULE_AVAILABLE:
             self.s1_button.config(state=tk.DISABLED, text="[1단계] 모듈 로드 실패 (S2 기능만 사용 가능)")
             
        # S2 실행 버튼
        tk.Button(frm_buttons, text="[2단계] 내품 OCR 실행",
                  font=("맑은 고딕", 12, "bold"),
                  command=self.run_s2_batch,
                  bg="#1E90FF", fg="white").pack(side="left", fill="x", expand=True, padx=5)

        # 4. 상태 및 종료
        self.progress_bar = ttk.Progressbar(tab_frm, length=400, variable=self.progress_val, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(10, 5))
        
        tk.Button(main_frm, text="프로그램 종료", command=self.on_closing, width=15, bg="#FFCCCC").pack(side=tk.RIGHT, pady=(10, 0))


    # ----------------------------------------------------
    # S1 (작업 사진) 처리 로직
    # ----------------------------------------------------
    def run_s1_batch(self):
        s1_excel_path = Path(self.s1_excel_var.get())
        
        # S1/S2 독립 폴더 사용
        container_root = Path(self.image_root_var.get())
        s1_source_path = Path(self.s1_source_var.get())

        if not _S1_MODULE_AVAILABLE:
            messagebox.showerror("오류", "작업 사진 처리 모듈이 로드되지 않았습니다."); return
        if not s1_excel_path.exists():
            messagebox.showerror("입력 오류", "작업 사진 엑셀 파일을 선택하세요!"); return
        if not s1_source_path.exists():
            messagebox.showerror("입력 오류", "작업 사진 폴더를 선택하세요!"); return
        if not container_root.exists():
             messagebox.showerror("경로 오류", f"컨테이너 루트 폴더를 선택하세요."); return

        messagebox.showinfo("S1 작업 시작", "작업 사진 리네임 작업을 시작합니다.\n작업이 완료될 때까지 잠시 기다려주세요.")
        
        threading.Thread(
            target=self._worker_s1, 
            args=(container_root, s1_source_path, s1_excel_path), 
            daemon=True
        ).start()

    def _worker_s1(self, root_folder: Path, s1_source_path: Path, s1_excel_path: Path):
        self.progress_val.set(0)
        try:
            self.progress_val.set(10); self.update_idletasks() 
            
            s1_ok, s1_fail = process_step1(
                root_folder,       
                s1_source_path,    
                s1_excel_path,     
                clean=True
            )
            
            self.progress_val.set(80); self.update_idletasks()
            
            container_name = root_folder.name
            generate_pdf(str(root_folder), s1_ok, 0) 
            
            self.progress_val.set(100)
            
            self.after(0, lambda: messagebox.showinfo(
                "S1 작업 완료", 
                f"작업 사진 처리 완료!\n\n컨테이너: {container_name}\n성공: {s1_ok}개, 실패: {s1_fail}개"
            ))
            
        except Exception as e:
            log_print(f"S1 작업 중 오류 발생: {e}", "ERROR")
            self.after(0, lambda: messagebox.showerror(
                "S1 작업 오류", 
                f"S1 작업 중 오류 발생:\n{e}"
            ))
        finally:
            self.after(0, lambda: self.progress_val.set(0)) 


    # ----------------------------------------------------
    # S2 (내품 사진) 처리 로직
    # ----------------------------------------------------
    def run_s2_batch(self):
        # S2 독립 폴더 사용
        s2_image_folder = Path(self.s2_source_var.get())
        if not s2_image_folder.exists():
            messagebox.showerror("오류", "내품 사진 폴더를 선택하세요.")
            return

        self._worker_s2(s2_image_folder)

    def _worker_s2(self, folder: Path):
        """S2 작업 함수 (동기 실행)"""
        
        s1_lookup_data = self.s1_lookup_data 

        # 1. 이미지 묶음 만들기 (자연 정렬 적용)
        pack_mode = self.pack_mode.get()
        groups = group_images(folder, pack_mode)

        if len(groups) == 0:
            return

        # 2. 컨테이너 번호 입력 및 엑셀 틀 생성
        container_name = ask_container_name(self)
        if not container_name:
            return

        excel_path = folder / f"{container_name}_OCR_Result_S2.xlsx"
        df = create_excel_template(len(groups), container_name) 

        # 3. OCR 수행 + 자동 처리 + 백업 로직
        try:
            for idx, image_set in enumerate(groups, start=1):
                sn = idx
                
                final_ocr_texts: List[str] = []
                scores: List[float] = [] 
                
                # A. OCR 추출 및 자동 처리 (수동 팝업 제거)
                for img in image_set:
                    txt, score = ocr_extract_from_image(img) 
                    final_txt = txt 
                    final_ocr_texts.append(final_txt)
                    if score > 0.0:
                        scores.append(score)

                # B. 추출 및 백업 로직
                txt1 = final_ocr_texts[0]
                id_val, lot, tag1 = extract_id_lot_tag(txt1)
                
                tag2 = ""
                if pack_mode == "2PACK" and len(final_ocr_texts) > 1:
                    txt2 = final_ocr_texts[1]
                    _, _, tag2_ocr = extract_id_lot_tag(txt2)
                    tag2 = tag2_ocr 

                s1_data = s1_lookup_data.get(sn, {})
                inspection_flag = "" 
                
                current_avg_score = sum(scores) / len(scores) if scores else 0.0
                needs_inspection = False
                
                # 1. 자동 검수 필요 조건 확인
                if current_avg_score < OCR_MIN_SCORE:
                    needs_inspection = True
                
                if not lot or not tag1:
                    needs_inspection = True

                # 2. 백업 적용 
                if (not lot or not tag1) and s1_data:
                    log_print(f"[SN {sn}] 추출 값 누락으로 S1 백업 시도.", "WARN")

                    id_val = id_val or s1_data.get("ID1", "")
                    lot = lot or s1_data.get("Lot1", "")
                    tag1 = tag1 or s1_data.get("Tag1", "")
                    
                    if pack_mode == "2PACK":
                         tag2 = tag2 or s1_data.get("Tag2", "")
                         
                    log_print(f"[SN {sn}] S1 백업 값 적용 완료.", "LOG")
                
                # 3. 필드 누락 최종 점검 및 안전 값 설정
                if not lot:
                    log_print(f"[SN {sn}] 최종 Lot1 추출 실패. 'NO_LOT'으로 처리.", "ERROR")
                    lot = "NO_LOT"
                    needs_inspection = True
                if not tag1:
                    log_print(f"[SN {sn}] 최종 Tag1 추출 실패. 'NO_TAG'으로 처리.", "ERROR")
                    tag1 = "NO_TAG"
                    needs_inspection = True
                    
                if needs_inspection:
                    inspection_flag = "확인 요함"

                # ------------------------------------------------
                # 엑셀 기록 및 안전한 리네임
                # ------------------------------------------------

                if pack_mode == "1PACK":
                    df.loc[sn - 1, ["ID1", "Lot1", "Tag1", "검수 필요"]] = [id_val, lot, tag1, inspection_flag]
                else:
                    df.loc[sn - 1, ["ID1", "Lot1", "Tag1", "Tag2", "검수 필요"]] = [
                        id_val, lot, tag1, tag2, inspection_flag
                    ]

                # 이미지는 SN 기반으로 rename
                self._rename_images(image_set, sn, folder, pack_mode, df, sn - 1)

            df.to_excel(excel_path, index=False) 
            messagebox.showinfo("S2 작업 완료", f"OCR 자동 처리 완료!\n엑셀의 '검수 필요' 컬럼을 확인하세요.\n엑셀 저장됨:\n{excel_path}")
            
        except Exception as e:
            log_print(f"S2 작업 중 치명적인 오류 발생: {e}", "ERROR")
            messagebox.showerror("S2 작업 오류", f"S2 작업 중 오류 발생:\n{e}")
            
            
    def _rename_images(self, img_paths, sn, folder, pack_mode, df, row_idx):
        """
        SN 번호 기반 rename 기능 (충돌 방지 로직 포함)
        """
        id_val = df.loc[row_idx, "ID1"]
        lot = df.loc[row_idx, "Lot1"]
        tag1 = df.loc[row_idx, "Tag1"]
        tag2 = df.loc[row_idx, "Tag2"] if pack_mode == "2PACK" else None

        sn_prefix = f"{sn}. {id_val}-{lot}"

        if pack_mode == "1PACK":
            new_names = [
                f"{sn_prefix} ({tag1}){Path(img_paths[0]).suffix}",
                f"{sn_prefix} ({tag1})-1{Path(img_paths[1]).suffix}"
            ]
        else:
            new_names = [
                f"{sn_prefix} ({tag1}){Path(img_paths[0]).suffix}",
                f"{sn_prefix} ({tag2}){Path(img_paths[1]).suffix}",
                f"{sn_prefix} ({tag1}, {tag2}){Path(img_paths[2]).suffix}",
            ]

        for old, new in zip(img_paths, new_names):
            new_path = folder / new
            try:
                # 리네임 충돌 방지: 대상 파일이 존재하면 삭제 후 덮어쓰기
                if new_path.exists():
                    os.remove(new_path)
                
                os.rename(old, new_path)
            except Exception as e:
                 log_print(f"파일 리네임 실패 (충돌/경로 오류): {old} -> {new_path}: {e}", "ERROR")


    def on_closing(self):
        self._save_settings_from_vars()
        self.destroy()

if __name__ == "__main__":
    app = BatchApp()
    app.mainloop()