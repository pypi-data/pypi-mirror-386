


from openai import OpenAI
import tiktoken
from local import BaseLocal
import random, string
import os
import json
from pydantic import BaseModel
from typing import Type, Any


BATCH_DIR = "C:\\task\\batch" # DIR 2


BATCH_END = [
    "completed",
    "failed",
    "cancelled",
    "expired"
]


DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_TOKEN_LIMIT = 200000


def _set_batch_dir(batch_dir: str) -> None:
    """ set BATCH_DIR.
    """

    BATCH_DIR = batch_dir
    return None


def random_custom_id(length: int = 20) -> str:
    """ create random id string with certain length.
    """

    chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choice(chars) for _ in range(length))


def count_token(content: Any) -> int:
    """ count token for GPT.
    """
    
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(str(content))
    count = len(tokens)
    return count


def is_over_limit(
    content: Any,
    limit: int = DEFAULT_TOKEN_LIMIT
) -> bool:
    """ check whether input token count over the limit or not.
    """
    
    if count_token(content) > limit:
        print(f"content has over {limit} tokens")
        return True
    return False


def remove_titles(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively removed the 'title' key within JSON schema
    Note that models with the key 'title' cannot be used
    """
    
    if isinstance(schema, dict):
        return {
            k: remove_titles(v)
            for k, v in schema.items()
            if k != "title"
        }
    elif isinstance(schema, list):
        return [remove_titles(i) for i in schema]
    else:
        return schema 


def json_schema_format(model: Type[BaseModel]) -> dict[str, Any]:
    
    """ Returns the format fits to text.format required by the openAI API
    """
    
    json_schema = remove_titles(model.model_json_schema())
    json_schema["additionalProperties"] = False
    return {
        "type": "json_schema",
        "name": model.__name__,
        "schema": json_schema,
        "strict": True
    }


def str_to_model(model: Type[BaseModel], data_str: str) -> BaseModel:
    """ parse data string to given model class instance.
    """
    
    try:
        data_dict = json.loads(data_str)  # str → dict
        return model(**data_dict)     # dict → instance
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Model parsing failed: {e}")


class GPT_IO(OpenAI):
    def __init__(
        self,
        api_key: str
    ) -> None:
        """ initialize with api_key.
        """
        
        OpenAI.__init__(
            self,
            api_key = api_key
        )
        return None
    
    
    ###########################################################################
    
    
    def response(
        self,
        messages: list[str],
        model: str = DEFAULT_MODEL,
        limit: int|None = None,
        response_format: Type[BaseModel]|None = None,
        top_p: float = 1.
    ) -> list[str]|None:
        """ get output from responses.
        """
        
        if is_over_limit(messages, limit):
            raise Exception("Token limit over")
        
        if response_format:
            response = self.responses.create(
                model = model,
                input = messages,
                top_p = top_p,
                text = {"format": json_schema_format(response_format)}
            )
            response = response.output_parsed
        
        else:
            response = self.responses.create(
                model = model,
                input = messages,
                top_p = top_p
            )
            response = response.output_text
        
        return response
    
    
    ###########################################################################
    
    
    def batch_request(
        self,
        messages: list[str],
        custom_id: str = random_custom_id(),
        model: str = DEFAULT_MODEL,
        limit: int|None = None,
        response_format: Type[BaseModel]|None = None,
        top_p: float = 1.
    ) -> str:
        """ request with batch, to responses.
        """
        
        if is_over_limit(messages, limit):
            raise Exception("Token limit over")
        
        batch_data = [{
            "method": "POST",
            "custom_id": custom_id,
            "url": "/v1/responses",
            "body": {
                "model": model,
                "input": messages,
                "top_p": top_p
            }
        }]
        
        if response_format:
            schema = json_schema_format(response_format)
            batch_data[0]["body"].update(
                {"text": {"format": schema}}
            )
        
        os.makedirs(BATCH_DIR, exist_ok = True)
        batch_file = os.path.join(
            BATCH_DIR,
            custom_id + ".jsonl"
        )
        BaseLocal.write_jsonl(batch_file, batch_data)
        
        with open(batch_file, "rb") as f:
            batch_input_file = self.files.create(
                file = f,
                purpose = "batch"
            )
        batch = self.batches.create(
            input_file_id = batch_input_file.id,
            endpoint = "/v1/responses",
            completion_window = "24h"
        )
        
        return batch.id
    
    
    def batch_status(
        self,
        batch_id: str
    ) -> str:
        """ check status of the batch, with batch_id. 
        """
        
        status = self.batches.retrieve(batch_id).status
        return status
    
    
    def batch_response(
        self,
        batch_id: str,
        response_format: Type[BaseModel]|None = None
    ) -> Any:
        """ get batch response, with batch_id.
        """
        
        try:
            response = None
            output_file_id = self.batches.retrieve(batch_id).output_file_id
            output_file = self.files.content(output_file_id)
            # print(output_file.text)
            batch = json.loads(output_file.text)
            output_list = batch["response"]["body"]["output"]
            for output in output_list:
                if output["type"] == "message":
                    response = output["content"][0]["text"]
            
            if response_format:
                response = str_to_model(
                    model = response_format,
                    data_str = response
                )
        
        except Exception as e:
            print("Exception\n" + e)
        
        finally:
            return response
    
    
    def batch_cancel(
        self,
        batch_id: str
    ) -> None:
        """ cancel batch if not ended.
        """
        
        if self.batch_status(batch_id) in ["validating", "in_progress"]:
            self.batches.cancel(batch_id)
    
    