#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel and Text File Processor for Vietnamese TTS
Xử lý file Excel và Text cho TTS tiếng Việt
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional


class ExcelProcessor:
    """
    Process Excel and text files for TTS conversion
    Xử lý file Excel và text để chuyển đổi TTS
    """
    
    # Required Excel columns / Các cột bắt buộc trong Excel
    REQUIRED_COLUMNS = {
        'ID': 'ID',
        'Title': 'Title',
        'Part': 'Part',
        'Source Text (Chinese)': 'Source Text (Chinese)',
        'QuickTrans (Draft)': 'QuickTrans (Draft)',
        'AI Result (Vietnamese)': 'AI Result (Vietnamese)'
    }
    
    def __init__(self):
        """Initialize the processor"""
        self.data = None
        self.file_path = None
    
    def load_excel(self, file_path: str) -> bool:
        """
        Load and validate Excel or CSV file
        Tải và kiểm tra file Excel hoặc CSV
        
        Args:
            file_path: Path to Excel (.xlsx) or CSV (.csv) file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.file_path = Path(file_path)
            file_ext = self.file_path.suffix.lower()
            
            # Read file based on extension / Đọc file dựa trên đuôi file
            if file_ext == '.csv':
                # Read CSV file / Đọc file CSV
                self.data = pd.read_csv(file_path, encoding='utf-8')
                print(f"[OK] Da tai file CSV: {self.file_path.name}")
            elif file_ext in ['.xlsx', '.xls']:
                # Read Excel file / Đọc file Excel
                self.data = pd.read_excel(file_path, engine='openpyxl')
                print(f"[OK] Da tai file Excel: {self.file_path.name}")
            else:
                print(f"[ERROR] Dinh dang file khong ho tro: {file_ext}")
                print(f"        Chi ho tro: .xlsx, .xls, .csv")
                return False
            
            # Validate columns / Kiểm tra các cột
            if not self._validate_columns():
                return False
            
            # Remove empty rows / Xóa các dòng trống
            self.data = self.data.dropna(subset=['AI Result (Vietnamese)'])
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Loi khi doc file: {e}")
            return False
    
    def load_text_file(self, file_path: str) -> bool:
        """
        Load text file as simple input
        Tải file text đơn giản
        
        Args:
            file_path: Path to text file
            
        Returns:
            True if successful
        """
        try:
            self.file_path = Path(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create simple DataFrame / Tạo DataFrame đơn giản
            self.data = pd.DataFrame({
                'ID': [1],
                'Title': [self.file_path.stem],
                'Part': [1],
                'Source Text (Chinese)': [''],
                'QuickTrans (Draft)': [''],
                'AI Result (Vietnamese)': [content]
            })
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Loi khi doc file text: {e}")
            return False
    
    def _validate_columns(self) -> bool:
        """
        Validate required columns exist
        Kiểm tra các cột bắt buộc
        
        Returns:
            True if all required columns exist
        """
        missing_cols = []
        for col in self.REQUIRED_COLUMNS.values():
            if col not in self.data.columns:
                missing_cols.append(col)
        
        if missing_cols:
            print(f"[ERROR] Thieu cac cot: {', '.join(missing_cols)}")
            return False
        
        return True
    
    def get_rows_for_processing(self) -> List[Dict]:
        """
        Get all rows ready for TTS processing
        Lấy tất cả các dòng để xử lý TTS
        
        Returns:
            List of dictionaries containing row data
        """
        if self.data is None:
            return []
        
        rows = []
        for idx, row in self.data.iterrows():
            rows.append({
                'id': str(row['ID']).strip(),
                'title': str(row['Title']).strip(),
                'part': str(row['Part']).strip(),
                'text': str(row['AI Result (Vietnamese)']).strip(),
                'row_index': idx
            })
        
        return rows
    
    def get_preview_data(self, max_rows: int = 10) -> pd.DataFrame:
        """
        Get preview of data for display
        Lấy dữ liệu xem trước để hiển thị
        
        Args:
            max_rows: Maximum number of rows to return
            
        Returns:
            DataFrame with preview data
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Select key columns / Chọn các cột chính
        preview_cols = ['ID', 'Title', 'Part', 'AI Result (Vietnamese)']
        available_cols = [col for col in preview_cols if col in self.data.columns]
        
        preview_df = self.data[available_cols].head(max_rows).copy()
        
        # Truncate long text for preview / Cắt ngắn text để xem trước
        if 'AI Result (Vietnamese)' in preview_df.columns:
            preview_df['AI Result (Vietnamese)'] = preview_df['AI Result (Vietnamese)'].apply(
                lambda x: str(x)[:100] + '...' if len(str(x)) > 100 else str(x)
            )
        
        return preview_df
    
    def get_row_count(self) -> int:
        """
        Get total number of rows
        Lấy tổng số dòng
        
        Returns:
            Number of rows
        """
        return len(self.data) if self.data is not None else 0


# Test the module / Kiểm tra module
if __name__ == "__main__":
    processor = ExcelProcessor()
    
    # Test with sample data
    sample_data = pd.DataFrame({
        'ID': [1, 2, 3],
        'Title': ['Chương 1', 'Chương 2', 'Chương 3'],
        'Part': [1, 2, 3],
        'Source Text (Chinese)': ['测试', '测试', '测试'],
        'QuickTrans (Draft)': ['test', 'test', 'test'],
        'AI Result (Vietnamese)': [
            'Xin chào, đây là chương một.',
            'Đây là chương hai với nội dung dài hơn.',
            'Chương ba kết thúc câu chuyện.'
        ]
    })
    
    # Save sample Excel / Lưu Excel mẫu
    sample_file = 'test_sample.xlsx'
    sample_data.to_excel(sample_file, index=False, engine='openpyxl')
    
    # Test loading / Kiểm tra tải file
    if processor.load_excel(sample_file):
        print("[OK] Tai file Excel thanh cong!")
        print(f"[INFO] So dong: {processor.get_row_count()}")
        print("\n[INFO] Preview:")
        print(processor.get_preview_data())
        print("\n[INFO] Du lieu xu ly:")
        for row in processor.get_rows_for_processing():
            print(f"  - {row['id']}: {row['title']} (Part {row['part']})")
