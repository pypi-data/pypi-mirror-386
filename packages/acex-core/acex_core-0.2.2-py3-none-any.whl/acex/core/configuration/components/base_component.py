from ipaddress import IPv4Interface, IPv6Interface, IPv4Address
from pydantic import BaseModel
import json, hashlib
from typing import Dict, Any, Type, Union, Optional
from types import NoneType
from datetime import datetime
from acex.core.models import ExternalValue, SingleAttribute

"""
FIXA!

just nu wrappas även containers som AttributeValue, det är ju bara själva attributen som ska vara det.
Tex wrappas hela Interface som attributevalue, det är bara attributen på komponenterna som ska vara det. 

fixa det.

"""

class AttributeValue:
    """
    Simple wrapper for attributes to store in consistent format
    Each attribute of each ConfigComponent consists of:
     - type: str (concrete|externalValue)
     - value: str
     - _meta: dict
    """
    
    def __init__(self, data: Union[Any, ExternalValue, None] = None):
        self.data = data
    
    @property
    def value(self) -> str:
        if isinstance(self.data, (str, int, bool)):
            return self.data
        elif isinstance(self.data, ExternalValue):
            return self.data.value
        elif isinstance(self.data, IPv4Address):
            return str(self.data)
        else:
            return "Whoah! this was unexpected.."

    @value.setter
    def value(self, value):
        self.data.value = value

    @property
    def type(self) -> str:
        return self._get_type_repr()

    @property
    def meta(self) -> dict:
        return self._get_meta_repr()

    def to_json(self) -> dict:
        res = {
            "type": self.type,
            "value": self.value,
        }
        if self.meta is not None:
            res["_meta"] = self.meta

        return res

    def _get_type_repr(self) -> str:
        """
        Return self.type as a more informational representation
        """
        if isinstance(self.data, ExternalValue):
            return "externalValue"
        else:
            return "concrete" # Visar att attributet är satt specifikt i configMap.

    def _get_meta_repr(self):
        if self.type == "concrete":
           return None # No meta is necessary yet.
        elif self.type == "externalValue":
            return {
                "ref": self.data.ref,
                "query": self.data.query,
                "kind": self.data.kind,
                "ev_type": self.data.ev_type,
                "plugin": self.data.plugin,
                "resolved_at": self.data.resolved_at
            }
        else:
            return {"msg": "This is unexpected, let someone know plz"}


class ConfigComponent:
    type: str = "component"
    model_cls: Type[BaseModel] = None

    def __init__(self, *args, **kwargs):

        # This is where we store the config.
        self.config = {}

        # Check all values against the model
        self.model = self._validate_model(kwargs)

        # For singleattribute components:
        # - key is same as component classname
        # - value is first argument from init
        if isinstance(self.model, SingleAttribute):
            # self._key = self.__class__.__name__.lower()
            self._key = "value" # TODO: Går det att förenkla strukturen för singleattribte config?
            value = args[0]
            self.config[self._key] = AttributeValue(value)
        else:
            self._key = kwargs["name"]

            # Set all attributes as AttributeValue
            # for key, value in kwargs.items():
                # v = AttributeValue(value)
                # self.config[key] = v
            # Use getattr to preserve original types instead of model_dump()
            for field_name in self.model.model_fields.keys():
                value = getattr(self.model, field_name)
                if value is not None:
                    self.config[field_name] = AttributeValue(value)

    @property
    def path(self):
        return f"{self.type}.{self._key}"


    def _validate_model(self, kwargs) -> BaseModel:
        """
        Validate all kwargs against the model and set attribute
        types accordingly
        """
        if not self.__class__.model_cls:
            raise ValueError(f"No model_cls defined for {self.__class__.__name__}")
        try:
            # Create an instance of the model class with kwargs
            model_instance = self.__class__.model_cls(**kwargs)
            return model_instance
        except Exception as e:
            raise ValueError(f"Failed to validate kwargs against model {self.__class__.model_cls.__name__}: {e}")


    def attributes(self):
        """Get all AttributeValue attributes from config"""
        attributes = {}

        for k,v in self.config.items():
            attributes[k] = v
        return attributes

    def to_json(self):
        """Serialize to JSON with consistent structure."""
        result = {
            "name": self.path,
            "type": self.type,
            "config": {}, # This is where values is placed
            "_meta": {} # this is where stuff like external value ref etc is placed
        }
        for k, v in self.attributes().items():
            # Skip 'name' since it's already in the outer structure as "name": self.path
            # Only include attributes that have actual values (not None)
            if k not in ("type", "name", "config") and v.data is not None:
                result["config"][k] = v.to_json()
        return result


    def __repr__(self):
        return f"<{self.__class__.__name__}_pk=key>"

