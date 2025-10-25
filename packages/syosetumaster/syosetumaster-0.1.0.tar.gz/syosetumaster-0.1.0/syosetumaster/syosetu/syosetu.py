

import os
from local import BaseLocal
from pydantic import BaseModel, Field
from pathlib import Path
from copy import deepcopy


BASE_DIR = "C:\\Task\\Translate" # DIR 1


PROG_STATUS = [
    "ready",
    "in_progress",
    "completed"
]


class Episode(BaseModel):
    chapter: str
    title: str
    text: str


class BatchInfo(BaseModel):
    batch_id: str = ""
    batch_status: str = PROG_STATUS[0]
    batch_start_time: float = 0.


class SyosetuData(BaseModel):
    syosetu_title: str = ""
    syosetu_id: str = ""
    source_lang: str = ""
    target_lang: str = ""
    episode_id_list: list[str] = Field(default_factory=list)
    consistancy_batch_info_dict: list[BatchInfo] = Field(default_factory=list)
    glossary_batch_info_list: list[BatchInfo] = Field(default_factory=list)
    translate_batch_info_dict: list[BatchInfo] = Field(default_factory=list)
    post_translate_batch_info: BatchInfo = Field(default_factory=BatchInfo)
    keyword_list_list: list[list[str]] = Field(default_factory=list)
    new_word_list_list: list[list[str]] = Field(default_factory=list)
    glossary: dict[str, str] = Field(default_factory=dict)
    chapter_list: list[str] = Field(default_factory=list)
    is_end: bool = False


def _set_base_dir(base_dir: str) -> None:
    """ set BASE_DIR.
    """

    BASE_DIR = base_dir
    return None


def if_new(
    syosetu_title: str,
    target_lang: str
) -> bool:
    """ check the syosetu is new or not.
    """
    
    path = BASE_DIR + "\\" + syosetu_title + "\\" + target_lang
    return Path(path).is_dir()


class Syosetu():
    def __init__(self) -> None:
        self._modified = False
        return None
    
    
    def create_new_syosetu(
        self,
        syosetu_title: str,
        syosetu_id: str,
        source_lang: str,
        target_lang: str
    ) -> None:
        """ create new syosetu data file
        """
        
        if if_new(syosetu_title, target_lang):      
            self.data = SyosetuData(
                syosetu_title = syosetu_title,
                syosetu_id = syosetu_id,
                source_lang = source_lang,
                target_lang = target_lang
            )
            self.modified()
        return None
    
    
    def clear(self) -> None:
        """ clear self as new syosetu.
        """
        
        syosetu_title = self.get_syosetu_title()
        syosetu_id = self.get_syosetu_id()
        source_lang = self.get_source_lang()
        target_lang = self.get_target_lang()
        episode_id_list = self.get_episode_id_list()
        self.data = SyosetuData(
            syosetu_title = syosetu_title,
            syosetu_id = syosetu_id,
            source_lang = source_lang,
            target_lang = target_lang,
            episode_id_list = episode_id_list
        )
        
        self.modified()
        return None
    
    
    def load_data(
        self,
        syosetu_title: str,
        target_lang: str
    ) -> None:
        """ load syosetu data from local
        """
        
        file_path = os.path.join(
            BASE_DIR,
            syosetu_title,
            target_lang,
            "data.json"
        )
        data_dict = BaseLocal.read_json(file_path)
        self.data = SyosetuData.model_validate(data_dict)
        return None
    
    
    def save_data(self) -> None:
        """ save syosetu data to local
        """
        
        file_path = os.path.join(
            BASE_DIR,
            self.data.syosetu_title,
            self.data.target_lang,
            "data.json"
        )
        data_json = self.data.model_dump()
        BaseLocal.write_json(file_path, data_json)
        return None
    
    
    def modified(self) -> None:
        """ set _modified True.
        """
        
        self._modified = True
        return None
    
    
    def save_if_modified(self) -> None:
        """ save syosetu data if modified.
        """
        
        if self._modified:
            self.save_data()
        return None
    
    
    def load_episode_data(
        self,
        lang: str,
        episode_id: str
    ) -> dict[str, str]:
        """ load episode_data from \\{syosetu_title}\\{lang}\\{episode_id}.json
        """
        
        path = os.path.join(
            BASE_DIR,
            self.data.syosetu_title,
            lang,
            episode_id + ".json"
        )
        
        return BaseLocal.read_json(path)
    
    
    def save_episode_data(
        self,
        lang: str,
        episode_id: str,
        episode_data: dict[str, str]
    ) -> None:
        """ save episode_data at \\{syosetu_title}\\{lang}\\{episode_id}.json
        """
        
        path = os.path.join(
            BASE_DIR,
            self.data.syosetu_title,
            lang,
            episode_id + ".json"
        )
        
        BaseLocal.write_json(path, episode_data)
        return None
    
    
    def export_episode_txt(
        self,
        episode_id: str,
    ) -> None:
        """ save episode_data as txt at \\{syosetu_title}\\{lang}\\{episode_id}.txt
        """
        
        lang = self.get_target_lang()
        path = os.path.join(
            BASE_DIR,
            self.data.syosetu_title,
            lang,
            episode_id + ".txt"
        )
        episode_data = self.load_episode_data(lang, episode_id)
        episode_txt = (
            episode_data["chapter"] + "\n" +episode_data["title"]
            + "\n\n" + episode_data["text"]
        )
        BaseLocal.write_txt(path, episode_txt)
        return None
    
    
    ##########################################################################
    
    
    def get_syosetu_title(self) -> str:
        """ get syosetu_title
        """
        
        return self.data.syosetu_title
    
    
    def set_syosetu_title(self, syosetu_title: str) -> None:
        """ set syosetu_title
        """
        
        self.data.syosetu_title = syosetu_title
        self.modified()
        return None
    
    
    def get_syosetu_id(self) -> str:
        """ get syosetu_id
        """
        
        return self.data.syosetu_id
    
    
    def set_syosetu_id(self, syosetu_id: str) -> None:
        """ set syosetu_id
        """
        
        self.data.syosetu_id = syosetu_id
        self.modified()
        return None
    
    
    def get_source_lang(self) -> str:
        """ get source_lang
        """
        
        return self.data.source_lang
    
    
    def set_source_lang(self, source_lang: str) -> None:
        """ set source_lang
        """
        
        self.data.source_lang = source_lang
        self.modified()
        return None
    
    
    def get_target_lang(self) -> str:
        """ get target_lang
        """
        
        return deepcopy(self.data.target_lang)
    
    
    def set_target_lang(self, target_lang: str) -> None:
        """ set target_lang
        """
        
        self.data.target_lang = target_lang
        self.modified()
        return None
    
    
    def get_episode_id_list(self) -> list[str]:
        """ get episode_id list
        """
        
        return deepcopy(self.data.episode_id_list)
    
    
    def update_consistancy_batch_info(self, episode_id: str) -> None:
        """ update consistancy_batch_info_dict
        """
        
        self.data.consistancy_batch_info_dict[episode_id] = BatchInfo()
        self.modified()
        return None
    
    
    def get_consistancy_batch_id(self, episode_id: str) -> str:
        """ get consistancy_batch_id of episode_id
        """
        
        if episode_id not in self.data.consistancy_batch_info_dict.keys():
            return PROG_STATUS[0]
        return self.data.consistancy_batch_info_dict[episode_id].batch_id
    
    
    def set_consistancy_batch_id(self, episode_id: str, batch_id: str) -> None:
        """ set consistancy_batch_id of episode_id
        """
        
        if episode_id not in self.data.consistancy_batch_info_dict.keys():
            return None
        self.data.consistancy_batch_info_dict[episode_id].batch_id = batch_id
        self.modified()
        return None
    
    
    def get_consistancy_status(self, episode_id: str) -> str:
        """ get consistancy_status of episode_id
        """
        
        return self.data.consistancy_batch_info_dict[episode_id].batch_status
    
    
    def set_consistancy_status(self, episode_id: str, status: str) -> None:
        """ set consistancy_status of episode_id
        """
        
        self.data.consistancy_batch_info_dict[episode_id].batch_status = status
        self.modified()
        return None
    
    
    def append_glossary_batch_info(self) -> None:
        """ append glossary_batch_info_list
        """
        
        self.data.glossary_batch_info_list.append(BatchInfo())
        self.modified()
        return None
    
    
    def get_glossary_batch_id(self, i: int) -> str:
        """ get i-th glossary_batch_id
        """
        
        return self.data.glossary_batch_info_dict[i].batch_id
    
    
    def set_glossary_batch_id(self, i: int, batch_id: str) -> None:
        """ set i-th glossary_batch_id
        """
        
        self.data.glossary_batch_info_dict[i].batch_id = batch_id
        self.modified()
        return None
    
    
    def get_glossary_status(self, i: int) -> str:
        """ get i-th glossary_status
        """
        
        return self.data.glossary_batch_info_dict[i].batch_status
    
    
    def set_glossary_status(self, i: int, status: str) -> None:
        """ set consistancy_status of episode_id
        """
        
        self.data.glossary_batch_info_dict[i].batch_status= status
        self.modified()
        return None
    
    
    def get_glossary_batch_count(self) -> int:
        """ get length of glossary_batch_info_list
        """
        
        return len(self.data.glossary_batch_info_list)
    
    
    def update_translate_batch_info(self, episode_id: str) -> None:
        """ update translate_batch_info_dict
        """
        
        self.data.translate_batch_info_dict[episode_id] = BatchInfo()
        self.modified()
        return None
    
    
    def get_translate_batch_id(self, episode_id: str) -> str:
        """ get translate_batch_id of episode_id
        """
        
        if episode_id not in self.data.translate_batch_info_dict.keys():
            return PROG_STATUS[0]
        return self.data.translate_batch_info_dict[episode_id].batch_id
        
    
    def set_translate_batch_id(self, episode_id: str, batch_id: str) -> None:
        """ set translate_batch_id of episode_id
        """
        
        if episode_id not in self.data.translate_batch_info_dict.keys():
            return None
        self.data.translate_batch_info_dict[episode_id].batch_id = batch_id
        self.modified()
        return None
    
    
    def get_post_translate_batch_id(self) -> str:
        """ get post_translate_batch_id
        """
        
        return self.data.post_translate_batch_info.batch_id
    
    
    def set_post_translate_batch_id(self, batch_id: str) -> None:
        """ set post_translate_batch_id
        """
        
        self.data.post_translate_batch_info.batch_id = batch_id
        self.modified()
        return None
    
    
    def get_post_translate_status(self) -> str:
        """ get post_translate_status
        """
        
        return self.data.post_translate_batch_info.batch_status
    
    
    def set_post_translate_status(self, status: str) -> None:
        """ set post_translate_status
        """
        
        self.data.post_translate_batch_info.batch_status = status
        self.modified()
        return None
    
    
    def get_keyword_list_list(self) -> list[str]:
        """ get keyword_list_list.
        """
        
        return deepcopy(self.data.keyword_list_list)
    
    
    def append_keyword_list_list(self, keyword_list: list[str]) -> None:
        """ append keyword_list on keyword_list_list.
        """
        
        self.data.keyword_list_list.append(keyword_list)
        self.modified()
        return None
    
    
    def get_new_word_list_list(self) -> None:
        """ get new_word_list_list.
        """
        
        return deepcopy(self.data.new_word_list_list)
    
    
    def set_new_word_list_list(self, new_word_list_list) -> None:
        """ set new_word_list_list.
        """
        
        self.data.new_word_list_list = new_word_list_list
        self.modified()
        return None
    
    
    def append_new_word_list_list(self, new_word_list: list[str]) -> None:
        """ append new_word_list on new_word_list_list.
        """
        
        self.data.new_word_list_list.append(new_word_list)
        self.modified()
        return None
    
    
    def clear_new_word_list(self) -> None:
        """ clear new_word_list.
        """
        
        self.data.new_word_list_list = []
        self.modified()
        return None
    
    
    def validated_new_word_list(self) -> list[str]:
        """ return validated keyword list from new_word_list_list.
        """
        
        keyword_list_list = self.get_keyword_list()
        new_word_list_list = self.get_new_word_list_list()
        
        validated_new_word_list = []
        for word_list in new_word_list_list:
            for word in word_list:
                if word not in validated_new_word_list:
                    validated_new_word_list.append(word)
        
        for word in validated_new_word_list:
            for keyword_list in keyword_list_list:
                if word in keyword_list:
                    validated_new_word_list.remove(word)
        
        return validated_new_word_list
    
    
    def get_glossary(self) -> dict[str, str]:
        """ get glossary.
        """
        
        return deepcopy(self.data.glossary)
    
    
    def update_glossary(self, new_glossary: dict[str, str]) -> None:
        """ update glossary with new_glossary.
        """
        
        self.data.glossary.update(new_glossary)
        self.modified()
        return None
    
    
    def get_chapter_list(self) -> list[str]:
        """ get chapter_list.
        """
        
        return deepcopy(self.data.chapter_list)
    
    
    def append_chapter_list(self, chapter: str) -> None:
        """ append chapter to chapter_list.
        """
        
        self.data.chapter_list.append(chapter)
        self.modified()
        return None
    
    