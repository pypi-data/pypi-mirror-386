from syosetu import Syosetu, PROG_STATUS, BASE_DIR
from crawl import Crawler
from translate_gpt_IO import Translate_GPT_IO as Client, set_api_key as _set_api_key
from local import BaseLocal, normalize_brackets, split_list
import os


GLOSSARY_CHUNK_SIZE = 100


def load_syosetu(syosetu_title: str, target_lang: str) -> Syosetu:
    """ load syosetu if exists.
    """
    
    syosetu = Syosetu()
    syosetu.load_data(syosetu_title, target_lang)
    return syosetu


def syosetu_list_dump_to_json(syosetu_list: list[Syosetu]) -> list[str]:
    """ dump syosetu_list to json form.
    """
    
    data_list = []
    for syosetu in syosetu_list:
        data_list.append({
            "syosetu_title": syosetu.get_syosetu_title(),
            "target_lang": syosetu.get_target_lang()
        })
    return data_list

    
def crawl_syosetu(syosetu: Syosetu) -> None:
    """ crawl the syosetu syosetu episodes.
    """
    
    syosetu_id = syosetu.get_syosetu_id()
    episode_id_list = syosetu.get_episode_id_list()
    
    if episode_id_list == []:
        episode_id = "1"
    else:
        episode_id = episode_id_list[-1]
        episode_id = Crawler.crawl_syosetu_episode(syosetu_id, episode_id)[1]
    
    Crawler._open()
    
    while True:
        [
            episode_data,
            next_episode_id
        ] = Crawler.crawl_syosetu_episode(
            syosetu_id,
            episode_id
        )
        print("crawled")
        
        syosetu.update_episode_info(
            episode_id = episode_id
        )
        syosetu.save_episode_data(
            lang = syosetu.get_source_lang(),
            episode_id = episode_id,
            episode_data = episode_data
        )
        
        if next_episode_id == None:
            syosetu.set_crawl_status(PROG_STATUS[2])
            print(f"{syosetu.get_syosetu_id()} crawl finished")
            break
        episode_id = next_episode_id
    
    Crawler._close()
    
    return None


def normalize_text(syosetu: Syosetu) -> None:
    """ normalize episode chapter, title, text of the syosetu.
    """
    
    normalized_episode_data = {}
    episode_id_list = syosetu.get_episode_id_list()
    for episode_id in episode_id_list:
        episode_data = syosetu.load_episode_data(
            lang = syosetu.get_source_lang(),
            episode_id = episode_id
        )
        normalized_episode_data["chapter"] = normalize_brackets(
            episode_data["chapter"]
        )
        normalized_episode_data["title"] = normalize_brackets(
            episode_data["title"]
        )
        normalized_episode_data["text"] = normalize_brackets(
            episode_data["text"]
        )
        syosetu.save_episode_data(
            lang = "normalized",
            episode_id = episode_id,
            episode_data = normalized_episode_data
        )
    return None


##########################################################################


def _consistancy_batch_request(
    client: Client,
    syosetu: Syosetu,
    episode_id: str
) -> None:
    """ request batch of consistancy process of episode in the syosetu.
    """
    
    consistancy_batch_id = client.consistancy_batch_request(
        source_lang = syosetu.get_source_lang(),
        episode_text = syosetu.load_episode_data(
            lang = "normalized",
            episode_id = episode_id
        )["text"],
        syosetu_title = syosetu.get_syosetu_title(),
        episode_id = episode_id
    )
    syosetu.set_consistancy_batch_id(episode_id, consistancy_batch_id)
    syosetu.set_consistancy_status(episode_id, PROG_STATUS[1])
    
    return None


def _consistancy_batch_response(
    client: Client,
    syosetu: Syosetu,
    episode_id: str,
    batch_id: str
) -> None:
    """ retrieve batch of consistancy process of episode in the syosetu.
    """
    
    new_word_list = client.consistancy_batch_response(batch_id)
    syosetu.append_new_word_list_list(new_word_list)
    syosetu.set_consistancy_status(episode_id, PROG_STATUS[2])
    syosetu.set_glossary_status(episode_id, PROG_STATUS[0])
    
    return None


def _glossary_batch_request(
    client: Client,
    syosetu: Syosetu,
    i: int
) -> None:
    """ request batch of glossary process of episode in the syosetu.
    """
    
    glossary_batch_id = client.glossary_batch_request(
        source_lang = syosetu.get_source_lang(),
        target_lang = syosetu.get_target_lang(),
        word_list = syosetu.get_keyword_list_list()[i],
        syosetu_title = syosetu.get_syosetu_title(),
        i = i
    )
    syosetu.set_glossary_batch_id(i, glossary_batch_id)
    syosetu.set_glossary_status(i, PROG_STATUS[1])
    return None


def _glossary_batch_response(
    client: Client,
    syosetu: Syosetu,
    i: int,
    batch_id: str
) -> None:
    """ retrieve batch of glossary process of episode in the syosetu.
    """
    
    translated_keyword_list = client.glossary_batch_response(batch_id)
    keyword_list = syosetu.get_keyword_list_list()[i]
    new_glossary = dict(zip(keyword_list, translated_keyword_list))
    syosetu.update_glossary(new_glossary)
    syosetu.set_glossary_status(i, PROG_STATUS[2])
    syosetu.set_translate_status(i, PROG_STATUS[0])
    
    return None


def _translate_batch_request(
    client: Client,
    syosetu: Syosetu,
    episode_id: str
) -> None:
    """ request batch of translate process of episode in the syosetu.
    """
    
    episode_data = syosetu.load_episode_data(
        lang = "normalized",
        episode_id = episode_id
    )
    translate_batch_id = client.translate_batch_request(
        source_lang = syosetu.get_source_lang(),
        target_lang = syosetu.get_target_lang(),
        glossary = syosetu.get_glossary(),
        episode = {
            k:episode_data.get(k)
            for k in ["title", "text"]
        },
        syosetu_title = syosetu.get_syosetu_title(),
        episode_id = episode_id
    )
    syosetu.set_translate_batch_id(episode_id, translate_batch_id)
    syosetu.set_translate_status(episode_id, PROG_STATUS[1])
    
    return None


def _translate_batch_response(
    client: Client,
    syosetu: Syosetu,
    episode_id: str,
    batch_id: str
) -> None:
    """ retrieve batch of translate process of episode in the syosetu.
    """
    
    [title, text] = client.translate_batch_response(batch_id)
    episode_data = syosetu.load_episode_data(
        lang = syosetu.get_source_lang(), 
        episode_id = episode_id
    )
    episode_data["title"] = title
    episode_data["text"] = text
    syosetu.save_episode_data(
        lang = syosetu.get_target_lang(),
        episode_id = episode_id,
        episode_data = episode_data
    )
    syosetu.set_translate_status(episode_id, PROG_STATUS[2])
    syosetu.set_post_translate_status(PROG_STATUS[0])
    
    return None


########################################################################




def export_episodes_txt(syosetu: Syosetu) -> None:
    """ export syosetu episodes to txt.
    """
    
    episode_id_list = syosetu.get_episode_id_list()
    for episode_id in episode_id_list:
        syosetu.export_episode_txt(episode_id)


def export_syosetu_txt(syosetu: Syosetu) -> None:
    """ export whole syosetu in a txt.
    """
    
    whole_txt = (
        "이 번역본은 gpt-5 모델을 활용한 syosetumaster 패키지를 통해 제작되었습니다."
        "\n\n\n\n"
    )
    temp_chapter_list = []
    target_lang = syosetu.get_target_lang()
    episode_id_list = syosetu.get_episode_id_list()
    for episode_id in episode_id_list:
        episode_data = syosetu.load_episode_data(target_lang, episode_id)
        chapter = episode_data["chapter"]
        if chapter != "" and chapter not in temp_chapter_list:
            whole_txt += (
                "--- " + episode_data["chapter"] + " ---\n\n"
            )
            temp_chapter_list.append(episode_data["chapter"])
        whole_txt += (
            episode_data["title"] + "\n\n" + episode_data["text"] + "\n\n\n\n"
        )
    file_path = os.path.join(
        BASE_DIR,
        syosetu.get_syosetu_title(),
        target_lang,
        syosetu.get_syosetu_title() + ".txt"
    )
    BaseLocal.write_txt(file_path, whole_txt)


class SyosetuMaster():
    def __init__(self) -> None:
        """ initiate SyosetuMaster.
        """

        self.syosetu_list = []
        self.select_syosetu_list = []
        return None
    
    
    def set_api_key(api_key: str) -> None:
        """ set openai api_key.
        """

        _set_api_key(api_key)
        return None
    

    def client_open(self) -> None:
        """ open client.
        """
        
        self.client = Client()
        return None
    
    
    def client_close(self) -> None:
        """ close client.
        """
        
        self.client.close()
    
    
    def create_new_syosetu(
        self,
        syosetu_title: str,
        syosetu_id: str,
        source_lang: str,
        target_lang: str
    ) -> None:
        """ create new Syosetu instance with given data.
        """
        
        syosetu = Syosetu()
        syosetu.create_new_syosetu(syosetu_title, syosetu_id, source_lang, target_lang)
        self.syosetu_list.append(syosetu)
        return None
    
    
    def create_new_syosetus(
        self,
        data_list: list[dict[str, str]]
    ) -> None:
        """ create new Syosetu instances with given data_list.
        """
        
        for data in data_list:
            self.create_new_syosetu(**data)
        
        return None
    
    
    def append_to_syosetu_list(self, syosetu_title: str, target_lang: str) -> None:
        """ append syosetu to syosetu_list, with syosetu_title & target_lang.
        """
        
        syosetu = load_syosetu(syosetu_title, target_lang)
        self.syosetu_list.append(syosetu)
        return None
    
    
    def load_syosetu_list(self) -> None:
        """ load syosetu_list from local.
        """
        
        file_path = os.path.join(
            BASE_DIR,
            "syosetu_list.json"
        )
        data_list = BaseLocal.read_json(file_path)
        
        for data in data_list:
            syosetu = Syosetu()
            print(str(data))
            syosetu.load_data(**data)
            self.syosetu_list.append(syosetu)
        
        return None
    
    
    def save_syosetu_list(self) -> None:
        """ save syosetu_list to local.
        """
        
        data_list = syosetu_list_dump_to_json(self.syosetu_list)
        file_path = os.path.join(
            BASE_DIR,
            "syosetu_list.json"
        )
        BaseLocal.write_json(file_path, data_list)
        
        return None
    
    
    def print_syosetu_list(self) -> None:
        """ print syosetu_list.
        """
        
        for syosetu in self.syosetu_list:
            print("title : " + syosetu.get_syosetu_title())
            print("syosetu_id : " + syosetu.get_syosetu_id())
            print("-------------------------")
        return None
    
    
    def select_syosetu(self, syosetu: Syosetu) -> None:
        """ append syosetu in select_syosetu_list
        """
        
        self.select_syosetu_list.append(syosetu)
        return None
    

    def crawl_syosetsu(self, mode: str = "all") -> None:
        """ crawl the all syosetu syosetu episodes of all syosetu in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        for syosetu in syosetu_list:
            crawl_syosetu(syosetu)
        return None
    
    
    def normalize_text(self, mode: str = "all") -> None:
        """ normalize episode data of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        for syosetu in syosetu_list:
            normalize_text(syosetu)
        return None
    
    
    def clear_syosetu(self, mode: str = "all") -> None:
        """
        clear all syosetus in syosetu_list.
        use only if the data has contamianated.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        for syosetu in syosetu_list:
            syosetu.clear()
        return None
    
    
    ###################################################################################################
    
    
    def consistancy_batches_request(self, syosetu: Syosetu) -> None:
        """ request batches of consistancy process of the syosetu.
        """
                
        episode_id_list = syosetu.get_episode_id_list()
        
        for episode_id in episode_id_list:
            status = syosetu.get_consistancy_status(episode_id)
            if status == PROG_STATUS[0]:
                _consistancy_batch_request(self.client, syosetu, episode_id)
                print(
                    "request consi_" + syosetu.get_syosetu_title() 
                    + "_" + episode_id
                )
            elif status == PROG_STATUS[1]:
                print(
                    "processing consi_" + syosetu.get_syosetu_title() 
                    + "_" + episode_id
                )
            elif status == PROG_STATUS[2]:
                print(
                    "end consi_" + syosetu.get_syosetu_title() 
                    + "_" + episode_id
                )
        
        syosetu.save_if_modified()
        return None


    def consistancy_batches_response(self, syosetu: Syosetu) -> bool:
        """ 
        retrieve batch responses of consistancy process of the syosetu.
        if there is not-completed-batch, print 'not yet'.
        return is_completed; all batches has completed, or made error.
        """
                
        episode_id_list = syosetu.get_episode_id_list()
        
        is_completed = True
        for episode_id in episode_id_list:
            if syosetu.get_consistancy_status(episode_id) == PROG_STATUS[1]:
                batch_id = syosetu.get_consistancy_batch_id(episode_id)
                status = self.client.batch_status(batch_id)
                if status == "completed":
                    _consistancy_batch_response(self.client, syosetu, episode_id, batch_id)
                    print(
                        "retrieve consi_" + syosetu.get_syosetu_title() 
                        + "_" + episode_id
                    )
                elif status == "finalizing":
                    is_completed = False
                    print(
                        "finalize consi_" + syosetu.get_syosetu_title() 
                        + "_" + episode_id
                    )
                else:
                    is_completed = False
                    self.client.batch_cancel(batch_id)
                    _consistancy_batch_request(self.client, syosetu, episode_id)
                    print(
                        "re-request consi_" + syosetu.get_syosetu_title() 
                        + "_" + episode_id
                    )
            elif syosetu.get_consistancy_status(episode_id) == PROG_STATUS[0]:
                is_completed = False
                print("request first")
        
        self.client.close()
        syosetu.save_if_modified()
        return is_completed

        
    def glossary_batches_request(self, syosetu: Syosetu) -> None:
        """ request batches of glossary process of the syosetu.
        """
                
        validated_keyword_list = syosetu.validated_new_word_list()
        count = len(validated_keyword_list) / GLOSSARY_CHUNK_SIZE
        split_keyword_list = split_list(validated_keyword_list, GLOSSARY_CHUNK_SIZE)
        for keyword_list in split_keyword_list:
            syosetu.append_keyword_list_list(keyword_list)
        
        for i in count:
            syosetu.append_glossary_batch_info()
        
        for i in range(syosetu.get_glossary_batch_count()):
            status = syosetu.get_glossary_status(i)
            if status == PROG_STATUS[0]:
                _glossary_batch_request(self.client, syosetu, i, split_keyword_list[i])
                print(
                    "request gloss_" + syosetu.get_syosetu_title() 
                    + "_" + f"{i:2d}/{count:2d}"
                )
            elif status == PROG_STATUS[1]:
                print(
                    "processing gloss_" + syosetu.get_syosetu_title() 
                    + "_" + f"{i:2d}/{count:2d}"
                )
            elif status == PROG_STATUS[2]:
                print(
                    "end gloss_" + syosetu.get_syosetu_title() 
                    + "_" + f"{i:2d}/{count:2d}"
                )
        
        syosetu.clear_new_word_list()
        syosetu.save_if_modified()
        return None


    def glossary_batches_response(self, syosetu: Syosetu) -> bool:
        """ 
        retrieve batch responses of glossary process of the syosetu.
        if there is not-completed-batch, re-request it.
        return is_completed; all batches has completed, or made error.
        """
                
        count = syosetu.get_glossary_batch_count()
        
        is_completed = True
        for i in range(count):
            if syosetu.get_glossary_status(i) == PROG_STATUS[1]:
                batch_id = syosetu.get_glossary_batch_id(i)
                status = self.client.batch_status(batch_id)
                if status == "completed":
                    _glossary_batch_response(self.client, syosetu, i, batch_id)
                    print(
                        "retrieve gloss_" + syosetu.get_syosetu_title() 
                        + "_" + f"{i:2d}/{count:2d}"
                    )
                elif status == "finalizing":
                    is_completed = False
                    print(
                        "finalize gloss_" + syosetu.get_syosetu_title() 
                        + "_" + f"{i:2d}/{count:2d}"
                    )
                else:
                    is_completed = False
                    self.client.batch_cancel(batch_id)
                    _glossary_batch_request(self.client, syosetu, i, batch_id)
                    print(
                        "re-request gloss_" + syosetu.get_syosetu_title() 
                        + "_" + f"{i:2d}/{count:2d}"
                    )
            elif syosetu.get_glossary_status(i) == PROG_STATUS[0]:
                is_completed = False
                print(f"{i:2d}/{count:2d} : request first")
            elif syosetu.get_glossary_status(i) == PROG_STATUS[2]:
                print(f"{i:2d}/{count:2d} : completed")
        
        if is_completed:
            syosetu.set_new_word_list([])
        syosetu.save_if_modified()
        return is_completed


    def translate_batches_request(self, syosetu: Syosetu) -> None:
        """ request batches of translate process of the syosetu.
        """
                
        episode_id_list = syosetu.get_episode_id_list()
        
        for episode_id in episode_id_list:
            status = syosetu.get_translate_status(episode_id)
            if status == PROG_STATUS[0]:
                _translate_batch_request(self.client, syosetu, episode_id)
                print(
                    "request trans_" + syosetu.get_syosetu_title() 
                    + "_" + episode_id
                )
            elif status == PROG_STATUS[1]:
                print(
                    "processing trans_" + syosetu.get_syosetu_title() 
                    + "_" + episode_id
                )
            elif status == PROG_STATUS[2]:
                print(
                    "end trans_" + syosetu.get_syosetu_title() 
                    + "_" + episode_id
                )
        
        syosetu.save_if_modified()
        return None


    def translate_batches_response(self, syosetu: Syosetu) -> bool:
        """ retrieve batch responses of translate process of the syosetu.
        """
                
        episode_id_list = syosetu.get_episode_id_list()
        
        is_completed = True
        for episode_id in episode_id_list:
            if syosetu.get_translate_status(episode_id) == PROG_STATUS[1]:
                batch_id = syosetu.get_translate_batch_id(episode_id)
                status = self.client.batch_status(batch_id)
                if status == "completed":
                    _translate_batch_response(self.client, syosetu, episode_id, batch_id)
                    print(
                        "retrieve trans_" + syosetu.get_syosetu_title() 
                        + "_" + episode_id
                    )
                elif status == "finalizing":
                    is_completed = False
                    print(
                        "finalize trans_" + syosetu.get_syosetu_title() 
                        + "_" + episode_id
                    )
                else:
                    is_completed = False
                    self.client.batch_cancel(batch_id)
                    _translate_batch_request(self.client, syosetu, episode_id)
                    print(
                        "re-request trans_" + syosetu.get_syosetu_title() 
                        + "_" + episode_id
                    )
            elif syosetu.get_translate_status(episode_id) == PROG_STATUS[0]:
                is_completed = False
                print("request first")
        
        if is_completed:
            syosetu.set_post_translate_status(PROG_STATUS[0])
        syosetu.save_if_modified()
        return is_completed


    def post_translate_batch_request(self, syosetu: Syosetu) -> None:
        """ request batches of post-translate process of the syosetu.
        """
        
        episode_id_list = syosetu.get_episode_id_list()
        for episode_id in episode_id_list:
            episode_data = syosetu.load_episode_data(
                lang = syosetu.get_source_lang(),
                episode_id = episode_id
            )
            if episode_data["chapter"] not in syosetu.get_chapter_list():
                syosetu.append_chapter_list(episode_data["chapter"])
        
        if syosetu.get_chapter_list() == [""]:
            syosetu.set_post_translate_status(PROG_STATUS[2])
            print(syosetu.get_syosetu_title() + " passed post_trans")
            return None
        elif syosetu.get_post_translate_status() == PROG_STATUS[0]:
            batch_id = self.client.glossary_batch_request(
                source_lang = syosetu.get_source_lang(),
                target_lang = syosetu.get_target_lang(),
                word_list = syosetu.get_chapter_list(),
                syosetu_title = syosetu.get_syosetu_title(),
                episode_id = "post_translate"
            )
            syosetu.set_post_translate_batch_id(batch_id)
            syosetu.set_post_translate_status(PROG_STATUS[1])
            print("request post_trans_" + syosetu.get_syosetu_title())
        
        syosetu.save_if_modified()
        return None


    def post_translate_batch_response(self, syosetu: Syosetu) -> bool:
        """ retrieve batches of post-translate process of the syosetu.
        """
        
        is_completed = False
        if syosetu.get_post_translate_status() == PROG_STATUS[0]:
            print("request first")
            return None
        elif syosetu.get_post_translate_status() == PROG_STATUS[1]:
            batch_id = syosetu.get_post_translate_batch_id()
            status = self.client.batch_status(batch_id)
            if status == "completed":
                chapter_list = syosetu.get_chapter_list()
                translated_chapter_list = self.client.glossary_batch_response(batch_id)
                chapter_translate_dict = dict(zip(
                    chapter_list, translated_chapter_list
                ))
                
                episode_id_list = syosetu.get_episode_id_list()
                for episode_id in episode_id_list:
                    episode_data = syosetu.load_episode_data(
                        lang = syosetu.get_target_lang(),
                        episode_id = episode_id
                    )
                    chapter = episode_data["chapter"]
                    episode_data["chapter"] = chapter_translate_dict[chapter]
                    syosetu.save_episode_data(
                        lang = syosetu.get_target_lang(),
                        episode_id = episode_id,
                        episode_data = episode_data
                    )
                syosetu.set_post_translate_status(PROG_STATUS[2])
                print("retrieve post_trans_" + syosetu.get_syosetu_title())
                is_completed = True
        elif syosetu.get_post_translate_status() == PROG_STATUS[2]:
            print("end post_trans_" + syosetu.get_syosetu_title())
            is_completed = True
        
        syosetu.save_if_modified()
        return is_completed
    

    ###################################################################################################
    
    
    def consistancy_batches_request(self, mode: str = "all") -> None:
        """ request batches of consistancy process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        for syosetu in syosetu_list:
            self.consistancy_batches_request(syosetu)
        self.client_close()
        return None
    
    
    def consistancy_batches_response(self, mode: str = "all") -> bool:
        """ retrieve batches of consistancy process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        is_completed = True
        for syosetu in syosetu_list:
            is_completed = self.consistancy_batches_response(syosetu) and is_completed
        self.client_close()
        return is_completed
    
    
    def glossary_batch_request(self, mode: str = "all") -> None:
        """ request batch of glossary process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        for syosetu in syosetu_list:
            self.glossary_batches_request(syosetu)
        self.client_close()
        return None
    
    
    def glossary_batch_response(self, mode: str = "all") -> bool:
        """ retrieve batch of glossary process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        is_completed = True
        for syosetu in syosetu_list:
            is_completed = self.glossary_batches_response(syosetu) and is_completed
        self.client_close()
        return is_completed
    
    
    def translate_batches_request(self, mode: str = "all") -> None:
        """ request batches of translate process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        for syosetu in syosetu_list:
            self.translate_batches_request(syosetu)
        self.client_close()
        return None
    
    
    def translate_batches_response(self, mode: str = "all") -> bool:
        """ retrieve batches of translate process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        is_completed = True
        for syosetu in syosetu_list:
            is_completed = self.translate_batches_response(syosetu) and is_completed
        self.client_close()
        return is_completed
    
    
    def post_translate_batch_request(self, mode: str = "all") -> None:
        """ request batch of post-translate process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        for syosetu in syosetu_list:
            self.post_translate_batch_request(syosetu)
        self.client_close()
        return None
    
    
    def post_translate_batch_response(self, mode: str = "all") -> bool:
        """ retrieve batch of translate process of all syosetus in syosetu_list.
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        
        self.client_open()
        is_completed = True
        for syosetu in syosetu_list:
            is_completed = self.post_translate_batch_response(syosetu) and is_completed
        self.client_close()
        return is_completed
    
    
    def export_txt(self, mode: str = "all") -> None:
        """ export txt files
        """
        
        if mode == "all":
            syosetu_list = self.syosetu_list
        elif mode == "selected":
            syosetu_list = self.select_syosetu_list
        else:
            return None
        for syosetu in syosetu_list:
            export_syosetu_txt(syosetu)
        return None