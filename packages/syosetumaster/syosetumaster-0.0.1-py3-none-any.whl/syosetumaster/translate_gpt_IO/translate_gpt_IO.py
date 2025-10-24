

from .gpt_IO import GPT_IO
import dotenv
import time
from pydantic import BaseModel


class WordList(BaseModel):
    """ for consistancy/glossary process"""
    word_list: list[str]


class Episode(BaseModel):
    """ for translate process"""
    episode_title: str
    episode_text: str


def set_api_key(api_key: str) -> None:
    """ set api_key
    """
    
    dotenv.set_key(".env", "translate_gpt_api_key", api_key)
    return None

    
def messages(
    system_content: str,
    user_content: str
) -> list[dict[str, str]]:
    """ return input list for openAI API.
    """
    
    return [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": user_content
        }
    ]


def glossary_lightening(glossary: dict[str, str], episode: dict[str, str]) -> None:
    """ lightening given glossary. be careful to use
    """
    
    word_list = list(glossary.keys())
    for word in word_list:
        if word in episode["text"] or word in episode["title"]:
            continue
        glossary.pop(word) # execute pop to the original glossary


def consistancy_messages(
    source_lang: str,
    text: str
) -> list[dict[str, str]]:
    """ return input list for consistancy process.
    """
    
    return messages(
        system_content = (
            'You are an expert in key word extraction. You will get '
            f'{source_lang} text. Your goal is to extract only the expressions '
            'that require translation consistency across chapters, such as : \n'
            '- Names of character, place, organization, items, abilities or spells.\n'
            '- Uncommon idiomatic or figurative expressions.\n'
            '- Repeatedly used phrases.\n'
            '- '
            'Strictly follow these rules : \n'
            '- Extract ONLY terms that are crucial for maintaining translation consistency.\n'
            '- Do not add any explanations, annotations, or meanings.\n'
            '- Keep each terms exactly as written in the text.\n'
            '- Return the extracted word list only.\n'
            'Do not ask to do or not, just do.'
        ),
        user_content = text
    )


def glossary_messages(
    source_lang: str,
    target_lang: str,
    word_list: list[str]
) -> list[dict[str, str]]:
    """ return input list for glossary process.
    """
    
    return messages(
        system_content = (
            'You are a professional translator specialized in '
            f'{source_lang}-to-{target_lang} literary translation.'
            f'Translate each of the following {source_lang} terms into '
            f'natural {target_lang} terms. Strictly follow these rules : '
            '- If a term is written as [Kanji](Reading) (e.g. 散弾銃(ショットガン)), '
            'ignore the Kanji part and base the translation only on the Reading.\n'
            '- Do NOT include any explanations, examples, or notes.\n'
            '- Output only the translated expressions, maintaining order.'
        ),
        user_content = str(word_list)
    )


def translate_messages(
    source_lang: str,
    target_lang: str,
    glossary: dict[str, str],
    episode: dict[str, str]
) -> list[dict[str, str]]:
    """ return input list for translate process.
    """
    
    glossary_lightening(glossary, episode)
    
    return messages(
        system_content = (
           'You are a professional translator who specialized in '
           f'{source_lang}-to-{target_lang} translation. '
           'You will be given title and text. Translate these in natural and '
           f'fluent  {target_lang}. '
           'Preserve punctuation marks as much as possible.\n'
           'Refer to the provided glossary and use the specified translations '
           'whenever the corresponding terms appear.\n'
           'glossary : '
        ) + str(glossary) + (
            'Do not ask to do or not, just do.'
        ),
        user_content = str(episode)
    )


class Translate_GPT_IO(GPT_IO):
    def __init__(self) -> None:
        """ put available api_key from .env
        """
        
        api_key = dotenv.dotenv_values(".env").get("translate_gpt_api_key")
        GPT_IO.__init__(
            self,
            api_key = api_key
        )
        return None
    
    
    def consistancy_batch_request(
        self,
        source_lang: str,
        episode_text: str,
        novel_title: str,
        episode_id: str
    ) -> str:
        """
        request the batch for consistancy process.
        return batch id.
        """
        
        batch_id = self.batch_request(
            messages = consistancy_messages(
                source_lang = source_lang,
                text = episode_text
            ),
            custom_id = "consi_" + novel_title + "_" + episode_id + "_" + str(int(time.time())),
            response_format = WordList
        )
        return batch_id
    
    
    def consistancy_batch_response(
        self,
        batch_id: str
    ) -> list[str]:
        """
        get response from the batch for consistancy process.
        return word_list.
        """
        
        word_list = self.batch_response(
            batch_id = batch_id,
            response_format = WordList
        )
        return word_list.word_list
    
    
    def glossary_batch_request(
        self,
        source_lang: str,
        target_lang: str,
        word_list: list[str],
        novel_title: str,
        i: int
    ) -> str:
        """
        request the batch for glossary process.
        return batch id.
        """
        
        batch_id = self.batch_request(
            messages = glossary_messages(
                source_lang = source_lang,
                target_lang = target_lang,
                word_list = word_list
            ),
            custom_id = "gloss_" + novel_title + "_" + str(i) + "_" + str(int(time.time())),
            response_format = WordList
        )
        return batch_id
    
    def glossary_batch_response(
        self,
        batch_id: str
    ) -> list[str]:
        """
        get response from the batch for glossary process.
        return word_list.
        """
        
        translated_word_list = self.batch_response(
            batch_id = batch_id,
            response_format = WordList
        )
        return translated_word_list.word_list
    
    
    def translate_batch_request(
        self,
        source_lang: str,
        target_lang: str,
        glossary: dict,
        episode: list[str],
        novel_title: str,
        episode_id: str
    ) -> str:
        """
        request the batch for glossary process.
        return batch id.
        """
        
        batch_id = self.batch_request(
            messages = translate_messages(
                source_lang = source_lang,
                target_lang = target_lang,
                glossary = glossary,
                episode = episode
            ),
            custom_id = "trans_" + novel_title + "_" + episode_id + "_" + str(int(time.time())),
            response_format = Episode
        )
        return batch_id
    
    
    def translate_batch_response(
        self,
        batch_id: str
    ) -> list[str]:
        """
        get response from the batch for translate process.
        return text.
        """
        
        episode = self.batch_response(
            batch_id = batch_id,
            response_format = Episode
        )
        return [episode.episode_title, episode.episode_text]