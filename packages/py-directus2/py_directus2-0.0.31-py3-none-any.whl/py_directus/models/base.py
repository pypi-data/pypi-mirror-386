from pydantic import BaseModel, ConfigDict


class DirectusConfigDict(ConfigDict):
    collection: str


class DirectusModel(BaseModel):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        collection = cls.model_config.get('collection')
        if not collection:
            import re
            collection = "_".join([word.lower() for word in re.findall("[A-Z]?[a-z]+", cls.__name__)])
            cls.model_config["collection"] = collection
