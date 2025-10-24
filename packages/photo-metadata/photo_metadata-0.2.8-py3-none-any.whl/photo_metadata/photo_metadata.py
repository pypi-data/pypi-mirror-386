import datetime, subprocess,concurrent.futures, os, json, csv, glob, re, copy, collections, tempfile

from typing import Callable, Literal, Any
from tqdm import tqdm
from uuid import uuid4
import sys
from pathlib import Path
from charset_normalizer import from_bytes





_exiftool_path = Path(r"exiftool")
_jp_tags_json_path = Path(os.path.join(os.path.dirname(__file__), r"exiftool_japanese_tag.json"))

key_map: dict | None = None


def _detect_encoding(data: bytes) -> str:
    
    if not data:
        return None
    try:
        results = from_bytes(data)
        best = results.best()
        if best and best.encoding:
            return best.encoding
    except Exception:
        pass
    return None


def date_format(date_text: str, old_format: str, new_format: str) -> str:
    return datetime.datetime.strptime(date_text, old_format).strftime(new_format)



def set_exiftool_path(exiftool_path: str | Path) -> None:
    """
    Set exiftool path.

    exiftool_path defaults to "exiftool".

    Parameters
    ----------
    exiftool_path : str | Path
        Path to exiftool executable.


    """
    global _exiftool_path
    _exiftool_path = Path(exiftool_path)

    

def get_exiftool_path() -> Path:
    """
    Get exiftool path.

    Returns
    -------
    Path
        Path to exiftool executable.

    """
    global _exiftool_path
    return Path(_exiftool_path)


def set_jp_tags_json_path(jp_tags_json_path: str | Path) -> None:
    """
    Set Japanese tags JSON path.

    jp_tags_json_path defaults to os.path.join(os.path.dirname(__file__), "exiftool_Japanese_tag.json").

    Parameters
    ----------
    jp_tags_json_path : str | Path
        Path to Japanese tags JSON file.
    """
    global _jp_tags_json_path
    _jp_tags_json_path = Path(jp_tags_json_path)

    if not _jp_tags_json_path.is_file():
        raise FileNotFoundError(f"JP tags json file not found: {_jp_tags_json_path}")
    

def get_jp_tags_json_path() -> Path:
    """
    Get Japanese tags JSON path.

    Returns
    -------
    Path
        Path to Japanese tags JSON file.

    """
    global _jp_tags_json_path
    return Path(_jp_tags_json_path)

def read_jp_tags_json() -> None:
    global key_map
    if key_map is None:
        try:
            if not os.path.exists(_jp_tags_json_path):
                raise FileNotFoundError(f"{_jp_tags_json_path} が存在しません")
            with open(_jp_tags_json_path, "r", encoding="utf-8") as f:
                key_map = json.load(f)

                
        except Exception as e:
            print("タグマップ読み込みに失敗:", e)
            key_map = {}

    

def get_key_map() -> dict:
    global key_map
    read_jp_tags_json()
    return key_map
            


def key_en_to_ja(key_en: str) -> str:
    """
    Convert English key to Japanese key.

    Parameters
    ----------
    key_en : str
        English key.

    Returns
    -------
    str
        Japanese key.

    """
    read_jp_tags_json()

    if ":" not in key_en:
        return key_map.get(key_en, key_en)
    group, tag_name = key_en.split(':')
    if tag_name in key_map:
        return f"{group}:{key_map[tag_name]}"
    else:
        return key_en

    


def key_ja_to_en(key_ja: str) -> str:
    """
    Convert Japanese key to English key.

    Parameters
    ----------
    key_ja : str
        Japanese key.

    Returns
    -------
    str
        English key.

    """
    read_jp_tags_json()

    reversed_key_map = {v: k for k, v in key_map.items()}
    if ":" not in key_ja:
        return reversed_key_map.get(key_ja, key_ja)
    group, tag_name = key_ja.split(':')
    if tag_name in reversed_key_map:
        return f"{group}:{reversed_key_map[tag_name]}"
    else:
        return key_ja

    
    
    



class Metadata:
    """
    Metadata Class

    Attributes
    ----------
    metadata : dict
        Metadata dictionary.
    

    """

    error_string: str = "Error"

    
    def __init__(self, file_path: str | Path):

        
        
        
        if not _jp_tags_json_path.is_file():
            raise FileNotFoundError(f"JP tags json file not found: {_jp_tags_json_path}")
            
        

        if not isinstance(file_path, (str, Path)):
            raise TypeError("file_path must be str or Path.")
        
        self.file_path = Path(file_path)

        if not self.file_path.is_file():
            raise FileNotFoundError(f"file not found: {self.file_path}")
        

        
        command_exiftool_text = f'{str(_exiftool_path)} -G -json "{self.file_path}"'
        
        if sys.platform == "linux":
            result = subprocess.run(command_exiftool_text, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        else:
            result = subprocess.run(command_exiftool_text, stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        
        
        # stdout / stderr のどちらかからエンコーディングを推定
        encoding = (
            _detect_encoding(result.stdout)
            or _detect_encoding(result.stderr)
            or "utf-8"
        )

        # 推定したエンコーディングでデコード
        stdout_text = result.stdout.decode(encoding, errors="replace")
        stderr_text = result.stderr.decode(encoding, errors="replace")
        

        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get metadata error: {stdout_text}\n{stderr_text}")
        
        self.metadata: dict = json.loads(stdout_text)[0]
        self.metadata["SourceFile"] = str(file_path)


    def display_japanese(self, return_type: Literal["str", "print", "dict"] = "print") -> dict | str | None:
        """
        Display metadata in Japanese

        If you want to display in English, use 
        
        Parameters
        ----------
        return_type : str, dict, None

        

        """

        read_jp_tags_json()


        m = {}
        for key, value in self.metadata.items():
                if ":" not in key:
                    if key in key_map:
                        m[f"{key} ({key_map[key]})"] = value
                    else:
                        m[key] = value
                    continue
                group, tag_name = key.split(':')
                if tag_name in key_map:
                    
                    m[f"{key} ({key_map[tag_name]})"] = value
                    
                else:
                    m[key] = value

        if return_type == "str":
            return json.dumps(m, indent=4, ensure_ascii=False)
        elif return_type == "print":
            return print(json.dumps(m, indent=4, ensure_ascii=False))
            
        elif return_type == "dict":
            return copy.deepcopy(m)
        else:
            raise TypeError(f"invalid return_type: {return_type}")
    



    
    def __getitem__(self, key: str) -> Any:
        if key not in self.metadata:
            raise KeyError(f"not found: {key}")
        
        return self.metadata[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        if not isinstance(value, (str, int, float, bool)):
            raise TypeError(f"invalid type: {type(value)}")
        
        self.metadata[key] = value

    
    def __delitem__(self, key: str):
        if key not in self.metadata:
            raise KeyError(f"not found: {key}")
        
        del self.metadata[key]

    def __str__(self) -> str:
        return json.dumps(self.metadata, indent=4, ensure_ascii=False)
    
    def __repr__(self) -> str:
        
        return f"Metadata(file_path={self.file_path}, \nmetadata=\n{json.dumps(self.metadata, indent=4, ensure_ascii=False)})"
    
    def __eq__(self, other: "Metadata") -> bool:
        metadata_copy = self.metadata.copy()
        other_metadata_copy = other.metadata.copy()
        
        del metadata_copy["SourceFile"]
        del other_metadata_copy["SourceFile"]

        for key, value in metadata_copy.copy().items():

            if key.split(":")[0] == "File" or key.split(":")[0] == "ExifTool":
                del metadata_copy[key]
        
        for key, value in other_metadata_copy.copy().items():

            if key.split(":")[0] == "File" or key.split(":")[0] == "ExifTool":
                del other_metadata_copy[key]

        
        
        
        return metadata_copy == other_metadata_copy
    
    def __ne__(self, other: "Metadata") -> bool:
        metadata_copy = self.metadata.copy()
        other_metadata_copy = other.metadata.copy()
        
        del metadata_copy["SourceFile"]
        del other_metadata_copy["SourceFile"]

        for key, value in metadata_copy.copy().items():

            if key.split(":")[0] == "File" or key.split(":")[0] == "ExifTool":
                del metadata_copy[key]
        
        for key, value in other_metadata_copy.copy().items():

            if key.split(":")[0] == "File" or key.split(":")[0] == "ExifTool":
                del other_metadata_copy[key]
        
        return not metadata_copy == other_metadata_copy
    

    def write_metadata_to_file(self, file_path: str = None) -> None:
        """
        Write metadata to file.

        Parameters
        ----------
        file_path : str, optional
            File path, by default None

        Returns
        -------
        None

        """
        if file_path is None:
            file_path = self.file_path

        print(file_path)

        write_metadata = {}

        
        
        write_metadata["SourceFile"] = "*"
        

        

        # メタデータをJSONファイルに一時的に保存
        temp_json = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_json.close()
        print(temp_json.name)
        with open(temp_json.name, 'w', encoding='utf-8') as f:
            json.dump(write_metadata, f, ensure_ascii=False, indent=4)

        try:
            # exiftoolを使用してメタデータを書き込む
            command = f'{str(_exiftool_path)} -json="{temp_json.name}" -overwrite_original "{file_path}"'
            if sys.platform == "linux":
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)

            # stdout / stderr のどちらかからエンコーディングを推定
            encoding = (
                _detect_encoding(result.stdout)
                or _detect_encoding(result.stderr)
                or "utf-8"
            )

            # 推定したエンコーディングでデコード
            stdout_text = result.stdout.decode(encoding, errors="replace")
            stderr_text = result.stderr.decode(encoding, errors="replace")
            
            print(f"exiftool standard output: {stdout_text}")
            print(f"exiftool standard error: {stderr_text}")

            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to write metadata. Error: {stdout_text}\n{stderr_text}")

            
            

        finally:
            # 一時ファイルを削除
            os.unlink(temp_json.name)

        

    def get_metadata_dict(self) -> dict:
        """
        Get metadata dictionary.

        Returns
        -------
        dict
            Metadata dictionary.

        """
        return self.metadata.copy()


    def export_metadata(self, output_path: str = None, format: Literal["json", "csv"] = 'json', lang_ja_metadata: bool = False) -> None:
        """
        Export metadata to file.

        Parameters
        ----------
        output_path : str, optional
            Output path, by default None
        format : str, optional
            Output format, by default 'json'
        lang_ja_metadata : bool, optional
            Whether to use Japanese metadata, by default False

        Returns
        -------
        None

        """
        
        
        format = format.lower()
        # エクスポートするメタデータを選択
        metadata_to_export = self.display_japanese(return_type="dict") if lang_ja_metadata else self.metadata.copy()
        
        # output_pathが指定されていない場合、ファイルと同じフォルダに設定
        if output_path is None:
            output_path = os.path.join(os.getcwd(), f"{os.path.basename(self.file_path)}_metadata.{format}")

        # メタデータをエクスポート
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_to_export, f, ensure_ascii=False, indent=4)
        elif format == 'csv':
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for key, value in metadata_to_export.items():
                    writer.writerow([key, value])
        else:
            
            
            raise ValueError("argument format must be \"csv\" or \"json\"")
        
    def keys(self) -> list[str]:
        return copy.deepcopy(list(self.metadata.keys()))
        
    def values(self) -> list[Any]:
        return copy.deepcopy(list(self.metadata.values()))
    
    def items(self) -> list[tuple[str, Any]]:
        return copy.deepcopy(list(self.metadata.items()))
        
    def get_gps_coordinates(self) -> str:
        degree_symbol = u"\u00B0"
        if "Composite:GPSLatitude" in self.metadata and "Composite:GPSLongitude" in self.metadata:
            location = f'{self.metadata["Composite:GPSLatitude"].replace("deg", degree_symbol).replace(" ", "")} {self.metadata["Composite:GPSLongitude"].replace("deg", degree_symbol).replace(" ", "")}'
            return location
        else:
            return self.error_string

    def export_gps_to_google_maps(self) -> str:
        coordinates = self.get_gps_coordinates()
        if coordinates != self.error_string:
            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={coordinates}"
            return google_maps_url
        else:
            return coordinates


    def get_date(self, format: str = '%Y:%m:%d %H:%M:%S', default_time_zone: str = '+00:00') -> str:
        
        
        date_tags = [
            "EXIF:DateTimeOriginal", 
            "QuickTime:MediaCreateDate", 
            "QuickTime:CreationDate", 
            "XMP:DateCreated", 
            "RIFF:DateTimeOriginal"
        ]

        for tag in date_tags:
            if tag in self.metadata and self.metadata[tag] not in ("", "0000:00:00 00:00:00"):
                raw_date = self.metadata[tag]
                try:
                    # QuickTime
                    if tag.startswith("QuickTime:"):
                        tz_offset = self.metadata.get("QuickTime:TimeZone", default_time_zone)
                        
                        tz_offset = tz_offset.replace("Z", "+00:00").replace("+", "")
                        tz_dt = datetime.datetime.strptime(tz_offset, "%H:%M")
                        tz = datetime.timedelta(hours=int(tz_dt.strftime("%H")), minutes=int(tz_dt.strftime("%M")))

                        dt = datetime.datetime.strptime(raw_date, '%Y:%m:%d %H:%M:%S')
                        dt = dt + tz
                        return dt.strftime(format)

                    # EXIF/XMP/RIFF
                    dt = datetime.datetime.strptime(raw_date, '%Y:%m:%d %H:%M:%S')
                    return dt.strftime(format)

                except Exception:
                    continue

        # 撮影日時が見つからない場合
        return self.error_string
    
    def get_image_dimensions(self) -> str:

        if "Composite:ImageSize" in self.metadata:
            size = self.metadata["Composite:ImageSize"]
            return size
        else:
            return self.error_string
        
    
    def get_file_size(self) -> tuple[str, int]:

        if self.file_path is None:
            
            
            raise ValueError("file_path is None")

        if not os.path.exists(self.file_path):
            
            
            raise FileNotFoundError(f"file not found: {self.file_path}")
        # ファイルサイズをバイト単位で取得
        file_size_bytes = os.path.getsize(self.file_path)
        
        # 桁数に応じて適切な単位に変換
        if file_size_bytes < 1024:
            return f"{file_size_bytes} B", file_size_bytes
        elif file_size_bytes < 1024**2:
            file_size_kb = file_size_bytes / 1024
            return f"{file_size_kb:.3f} KB", file_size_bytes
        elif file_size_bytes < 1024**3:
            file_size_mb = file_size_bytes / (1024**2)
            return f"{file_size_mb:.3f} MB", file_size_bytes
        else:
            file_size_gb = file_size_bytes / (1024**3)
            return f"{file_size_gb:.3f} GB", file_size_bytes
    
    

    def get_model_name(self) -> str:
        if "EXIF:Model" in self.metadata:
            model_name = self.metadata["EXIF:Model"]
        elif "XML:DeviceModelName" in self.metadata:
            model_name = self.metadata["XML:DeviceModelName"]
        else:
            model_name = self.error_string
        return model_name
    
    def get_lens_name(self) -> str:
        if "EXIF:LensModel" in self.metadata:
            lens = self.metadata["EXIF:LensModel"]
        else:
            lens = self.error_string
        return lens

    def get_focal_length(self) -> dict:
        focal_length_dict = {}
        if "EXIF:FocalLength" in self.metadata:
            focal_length = self.metadata["EXIF:FocalLength"]
        else:
            focal_length = self.error_string
        
        
        
        
        focal_length_dict["Focal_Length"] = focal_length
        
        if "EXIF:FocalLengthIn35mmFormat" in self.metadata:
            focal_length35 = self.metadata["EXIF:FocalLengthIn35mmFormat"]
        else:
            focal_length35 = self.error_string
        
        
        
        focal_length_dict["Focal_Length_35mm"] = focal_length35
        
        return focal_length_dict
    

    def get_main_metadata(self, get_date_format: str = '%Y:%m:%d %H:%M:%S', get_date_default_time_zone: str = '+00:00') -> dict:
        """
        Get main metadata dictionary.

        Parameters
        ----------
        get_date_format : str
            Date format for self.get_date().

        get_date_default_time_zone : str
            Default time zone for self.get_date().

        Returns
        -------
        dict
            Main metadata dictionary.

        """

        
        
        md_dict = {}
        md_dict["File_Path"] = str(self.file_path)
        md_dict["File_Name"] = os.path.basename(str(self.file_path))
        md_dict["Date"] = self.get_date(format=get_date_format, default_time_zone=get_date_default_time_zone)
        md_dict["Model_Name"] = self.get_model_name()
        md_dict["Lens_Name"] = self.get_lens_name()
        for key in ["FNumber", "ExposureTime", "ISO"]:
            try:
                data = self.metadata[f"EXIF:{key}"]
            except KeyError:
                data = self.error_string
            md_dict[key] = data
        
        focal_length = self.get_focal_length()
        
           
        md_dict["Focal_Length"] = focal_length["Focal_Length"]
        md_dict["Focal_Length_35mm"] = focal_length["Focal_Length_35mm"]
            
        
        md_dict["Image_Size"] = self.get_image_dimensions()
        md_dict["File_Size"] = self.get_file_size()

        
        
        

        return md_dict
    

    def show(self) -> None:
        """
        Show file
        """
        
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"file not found: {self.file_path}")
        
        os.startfile(str(self.file_path))

    def copy(self) -> "Metadata":
        """
        Create a copy of the current Metadata instance.
        """
        return copy.deepcopy(self)
    
    def contains_key(self, key, exact_match: bool = True):
        """
        Check if a key exists in the metadata.

        """
        if exact_match:
            return key in self.metadata
        else:
            for k in self.metadata.keys():
                if isinstance(k, str) and isinstance(key, str):
                    if key.lower() in k.lower():
                        return True
                else:
                    k == key
            return False

    
    def contains_value(self, value, exact_match: bool = True):
        """
        Check if a value exists in the metadata.

        """""
        if exact_match:
            return value in self.metadata.values()
        else:
            for v in self.metadata.values():
                if isinstance(v, str) and isinstance(value, str):
                    if value.lower() in v.lower():
                        return True
                else:
                    v == value
            return False
    

    @classmethod
    def load_all_metadata(
        cls,
        file_path_list: list[str],
        progress_func: Callable[[int], None] | None = None,
        max_workers: int = 40
        
    ) -> dict[str, "Metadata"]:
        """
        Load metadata from multiple file paths in parallel.

        Args:
            file_path_list (list[str]): List of file paths to extract metadata from.
            progress_func (Callable[[int], None] | None): Optional function to receive progress updates (0–100).
            max_workers (int): Number of threads to use for parallel processing.

        Returns:
            dict[str, Metadata]: A dictionary mapping each file path to its corresponding Metadata object.

        Example:
            >>> file_list = ["image1.jpg", "image2.png"]
            >>> metadata_dict = Metadata.load_all_metadata(file_list)
            >>> metadata_dict["image1.jpg"]["DateTimeOriginal"]
            '2023:01:01 10:00:00'
        """

        def load_one(file_path: str):
            return file_path, cls(file_path)

        total = len(file_path_list)
        result_dict: dict[str, Metadata] = {}
        progress = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(load_one, path) for path in file_path_list]

            for future in tqdm(concurrent.futures.as_completed(futures), total=total, dynamic_ncols=True):
                file_path, metadata = future.result()
                result_dict[file_path] = metadata

                progress += 1
                if progress_func is not None:
                    progress_func((progress * 100) // total)

        if progress_func is not None:
            progress_func(100)

        return result_dict
    

class MetadataBatchProcess:
    """
    A class to manage and batch process metadata from multiple files.
    """

    DUP_SEQ_1_DIGIT = "重複連番1桁"
    DUP_SEQ_2_DIGIT = "重複連番2桁"
    DUP_SEQ_3_DIGIT = "重複連番3桁"
    DUP_SEQ_4_DIGIT = "重複連番4桁"
    NUMBER = "連番"

    dup_seq_list = [DUP_SEQ_1_DIGIT, DUP_SEQ_2_DIGIT, DUP_SEQ_3_DIGIT, DUP_SEQ_4_DIGIT]

    def __init__(self, file_list: list[str], 
                 progress_func: Callable[[int], None] | None = None, 
                 max_workers: int = 40):
        """
        Initialize the MetadataBatchProcess instance.

        Args:
            file_list (list[str]): List of file paths to process.
            progress_func (Callable[[int], None], optional): Progress callback (0–100).
            max_workers (int): Number of threads to use.
        """
        self.file_list = list(map(os.path.normpath, file_list))
        
        self.progress_func = progress_func

        self.metadata_objects: dict[str, Metadata] = Metadata.load_all_metadata(
            self.file_list, 
            progress_func=self.progress_func,
            max_workers=max_workers
        )

    def filter_by_custom_condition(self, condition_func: Callable[[Metadata], bool]) -> None:
        """
        Filter files using a custom condition function.

        Args:
            condition_func (Callable[[Metadata], bool]): A function that returns True for matching files.
        """
        filtered_objects = {}
        filtered_files = []

        for file, md in self.metadata_objects.items():
            if condition_func(md):
                filtered_objects[file] = md
                filtered_files.append(file)

        self.metadata_objects = filtered_objects
        self.file_list = filtered_files

    def filter_by_metadata(self, keyword_list: list[str], exact_match: bool,
                           all_keys_match: bool,
                           search_by: Literal["either", "value", "key"]) -> None:
        """
        Filter files by matching keywords in metadata keys/values.

        Args:
            keyword_list (list[str]): List of keywords to search for.
            exact_match (bool): Whether to use exact matching.
            all_keys_match (bool): Require all keywords to match.
            search_by (Literal): Where to search ("key", "value", or "either").
            
        """
        filtered_objects = {}
        filtered_files = []

        for file, md in self.metadata_objects.items():
            matches = []
            for keyword in keyword_list:
                if search_by == "key":
                    matches.append(md.contains_key(keyword,  exact_match))
                elif search_by == "value":
                    matches.append(md.contains_value(keyword,  exact_match))
                else:  # either
                    k = md.contains_key(keyword,  exact_match)
                    v = md.contains_value(keyword, exact_match)
                    matches.append(k or v)

            if all_keys_match and all(matches):
                filtered_objects[file] = md
                filtered_files.append(file)
            elif not all_keys_match and any(matches):
                filtered_objects[file] = md
                filtered_files.append(file)

        self.metadata_objects = filtered_objects
        self.file_list = filtered_files

    def prepare_rename(self, format_func: Callable[[Metadata], str]) -> None:
        """
        Prepare file rename dictionary using a formatting function.

        Args:
            format_func (Callable[[Metadata], str]): A function that generates base names from Metadata.
        """
        self.format_func = format_func

        def incrementer():
            count = 0
            def increment():
                nonlocal count
                count += 1
                return count
            return increment

        def add_duplicate_sequence_number(input_dict: dict):
            duplicate_count = {}
            renamed_files = {}
            i = incrementer()
            for key, value in tqdm(input_dict.items()):
                if value not in duplicate_count:
                    duplicate_count[value] = 0
                else:
                    duplicate_count[value] += 1
                n = i()
                renamed_files[key] = value + (duplicate_count[value], n)
            return renamed_files

        dir_path = os.path.dirname(self.file_list[0])
        all_files = glob.glob(os.path.join(dir_path, "*.*"))
        not_selected_files = [os.path.basename(n) for n in set(all_files) - set(self.file_list)]

        error_files = {}
        base_name_dict = {}
        new_name_dict = {}
        name_dict = {}

        for file, md_obj in self.metadata_objects.items():
            ext = os.path.splitext(file)[1].upper()
            if ext.lower() == ".jpg":
                ext = ".JPEG"
            try:
                base_name = self.format_func(md_obj)
                if Metadata.error_string in base_name:
                    error_files[file] = "Error"
                    continue
                for d in self.dup_seq_list:
                    if d in base_name:
                        r = re.search(r'重複連番(.+)桁', base_name).group(1)
                        count_digit = int(r)
                        base_name = base_name.replace(d, "<RN>")
                base_name_dict[file] = (base_name, ext)
            except Exception as e:
                error_files[file] = "Error"
                print(e)
                

        base_name_dict = dict(sorted(base_name_dict.items()))
        base_name_dict = add_duplicate_sequence_number(base_name_dict)

        for for_count, (file_path, (base_name, ext, dup_num, number)) in enumerate(base_name_dict.items()):
            count_is_file = 0
            new_name = f"{base_name}{ext}"

            if "連番" in new_name:
                new_name = new_name.replace("連番", str(number))

            if "<RN>" in new_name:
                new_name = new_name.replace("<RN>", str(dup_num).zfill(count_digit))
            
            if ("<RN>" not in base_name) and ("連番" not in base_name):
                raise ValueError("NUMBER or DUP_SEQ_1_DIGIT or DUP_SEQ_2_DIGIT or DUP_SEQ_3_DIGIT or DUP_SEQ_4_DIGIT not in format string")

            if os.path.basename(file_path) != new_name:
                while new_name in not_selected_files:
                    count_is_file += 1
                    new_name = f"{base_name.replace('<RN>', str(count_is_file).zfill(count_digit))}{ext}"
                    if os.path.basename(file_path) == new_name:
                        break

            if new_name == os.path.basename(file_path):
                error_files[file_path] = "Same name before and after renaming"
            else:
                name_dict[file_path] = new_name

        self.new_name_dict = name_dict
        self.error_files = error_files

    def rename_files(self) -> str:
        """
        Execute file renaming using prepared name dictionary.

        Returns:
            str: Result message.
        """
        total = len(self.new_name_dict) * 2
        t = tqdm(total=total)
        temp_dict = {}
        count = 0

        for file, new_name in self.new_name_dict.items():
            dir_name = os.path.dirname(file)
            temp_name = f"{uuid4()}{os.path.splitext(new_name)[1]}"
            temp_path = os.path.join(dir_name, temp_name)
            os.rename(file, temp_path)
            temp_dict[temp_path] = new_name
            count += 1
            t.update(count)
            if self.progress_func:
                self.progress_func((count * 100) // total)

        for temp_path, new_name in temp_dict.items():
            os.rename(temp_path, os.path.join(os.path.dirname(temp_path), new_name))
            count += 1
            t.update(count)
            if self.progress_func:
                self.progress_func((count * 100) // total)

        return "Renaming completed!"

    def copy(self) -> "MetadataBatchProcess":
        """
        Create a deep copy of the current MetadataBatchProcess instance.

        Returns:
            MetadataBatchProcess: A deep copy of the instance.
        """
        return copy.deepcopy(self)
    
    
        
    


    
        
    

    

        
        

        

        