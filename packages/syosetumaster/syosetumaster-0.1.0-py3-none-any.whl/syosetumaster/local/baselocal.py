

import os
import json
from pathlib import Path


class BaseLocal():
    def read_txt(
        file_path: str,
    ) -> str | None:
        """ read txt file from file_path.
        """
                
        try:
            with open(file_path, 'r', encoding='UTF8') as f:
                lines = f.readlines()
            text = ""
            for line in lines:
                text += line
        except FileNotFoundError:
            print(f"No such file directory: {file_path}")
        return text
    
    
    def write_txt(
        file_path: str,
        text: str
    ) -> None:
        """ write txt file to file_path
        """
        
        file_dir = Path(file_path).parent
        os.makedirs(file_dir, exist_ok=True)
        with open(file_path, 'w', encoding = 'UTF8') as f:
            f.write(text)
        return None
    
    
    def read_json(
        file_path: str
    ) -> dict:
        """ read json file from file_path.
        """
        
        try:
            with open(file_path, encoding= 'UTF-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"No such file directory: {file_path}")
        return data
    
    
    def write_json(
        file_path: str,
        data: str
    ) -> None:
        """ write json file to file_path
        """
        
        file_dir = Path(file_path).parent
        os.makedirs(file_dir, exist_ok=True)
        with open(file_path, 'w', encoding= 'UTF-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return None
    
    
    def read_jsonl(
        file_path: str
    ) -> list[dict] | None:
        """ read jsonl file to file_path.
        """
        
        data = []
        try:
            with open(file_path, 'r', encoding= 'UTF-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data.append(json.loads(line))
        except FileNotFoundError:
            print(f"No such file directory: {file_path}")
        return data
    
    
    def write_jsonl(
        file_path: str,
        data: list[str]
    ) -> None:
        """ write jsonl file to file_path.
        """
        
        file_dir = Path(file_path).parent
        os.makedirs(file_dir, exist_ok=True)
        with open(file_path, 'w', encoding= 'UTF-8') as f:
            for entry in data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return None