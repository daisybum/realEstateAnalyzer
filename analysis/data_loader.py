import os
from typing import List, Dict, Optional, Union
from pathlib import Path

class DataLoader:
    def __init__(self, base_path: str):
        """
        Initialize the DataLoader.
        
        Args:
            base_path: The base directory containing report folders (e.g., ~/realEstateCrawler/output/)
        """
        self.base_path = Path(base_path).expanduser()

    def get_report_ids(self) -> List[str]:
        """
        Get a list of all report IDs (folder names) in the base path.
        """
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path {self.base_path} does not exist.")
        
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]

    def load_report(self, report_id: str) -> Dict[str, Union[str, List[str]]]:
        """
        Load text and image paths for a specific report ID.
        
        Args:
            report_id: The ID of the report to load.
            
        Returns:
            A dictionary containing:
            - 'id': report_id
            - 'text': content of the .txt file
            - 'images': list of absolute paths to image files
            - 'pdf': path to pdf file (if exists)
            - 'pptx': path to pptx file (if exists)
        """
        report_dir = self.base_path / report_id
        if not report_dir.exists():
            raise FileNotFoundError(f"Report directory {report_dir} does not exist.")

        result = {
            'id': report_id,
            'text': "",
            'images': [],
            'pdf': None,
            'pptx': None
        }

        # Load text content
        txt_file = report_dir / f"{report_id}.txt"
        if txt_file.exists():
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    result['text'] = f.read()
            except Exception as e:
                print(f"Error reading text file {txt_file}: {e}")

        # Load images
        # Sorting images to maintain order (image_1.png, image_2.png, etc.)
        images = sorted(list(report_dir.glob("*.png")))
        result['images'] = [str(img.absolute()) for img in images]

        # Check for PDF and PPTX
        pdfs = list(report_dir.glob("*.pdf"))
        if pdfs:
            result['pdf'] = str(pdfs[0].absolute())
            
        pptxs = list(report_dir.glob("*.pptx"))
        if pptxs:
            result['pptx'] = str(pptxs[0].absolute())

        return result

if __name__ == "__main__":
    # Simple test
    loader = DataLoader("~/Projects/realEstateCrawler/output/")
    report_ids = loader.get_report_ids()
    print(f"Found {len(report_ids)} reports.")
    
    if report_ids:
        sample_id = "3635564" # Using the known sample
        if sample_id in report_ids:
            data = loader.load_report(sample_id)
            print(f"Loaded report {sample_id}:")
            print(f"Text length: {len(data['text'])}")
            print(f"Image count: {len(data['images'])}")
            print(f"Images: {data['images']}")
        else:
            print(f"Sample {sample_id} not found, loading first available: {report_ids[0]}")
            data = loader.load_report(report_ids[0])
            print(data)
