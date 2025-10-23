# coding: utf-8

"""
AvaTax Software Development Kit for Python.

   Copyright 2022 Avalara, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

    Avalara 1099 & W-9 API Definition
    ## 🔐 Authentication  Generate a **license key** from: *[Avalara Portal](https://www.avalara.com/us/en/signin.html) → Settings → License and API Keys*.  [More on authentication methods](https://developer.avalara.com/avatax-dm-combined-erp/common-setup/authentication/authentication-methods/)  [Test your credentials](https://developer.avalara.com/avatax/test-credentials/)  ## 📘 API & SDK Documentation  [Avalara SDK (.NET) on GitHub](https://github.com/avadev/Avalara-SDK-DotNet#avalarasdk--the-unified-c-library-for-next-gen-avalara-services)  [Code Examples – 1099 API](https://github.com/avadev/Avalara-SDK-DotNet/blob/main/docs/A1099/V2/Class1099IssuersApi.md#call1099issuersget) 

@author     Sachin Baijal <sachin.baijal@avalara.com>
@author     Jonathan Wenger <jonathan.wenger@avalara.com>
@copyright  2022 Avalara, Inc.
@license    https://www.apache.org/licenses/LICENSE-2.0
@version    25.8.3
@link       https://github.com/avadev/AvaTax-REST-V3-Python-SDK
"""

from __future__ import annotations
import json
import pprint
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError, field_validator
from typing import Any, List, Optional
from Avalara.SDK.models.A1099.V2.A1099.V2.A1099.V2.A1099.V2.w4_form_data_model import W4FormDataModel
from Avalara.SDK.models.A1099.V2.A1099.V2.A1099.V2.A1099.V2.w8_ben_form_data_model import W8BenFormDataModel
from Avalara.SDK.models.A1099.V2.A1099.V2.A1099.V2.A1099.V2.w8_bene_form_data_model import W8BeneFormDataModel
from Avalara.SDK.models.A1099.V2.A1099.V2.A1099.V2.A1099.V2.w8_imy_form_data_model import W8ImyFormDataModel
from Avalara.SDK.models.A1099.V2.A1099.V2.A1099.V2.A1099.V2.w9_form_data_model import W9FormDataModel
from pydantic import StrictStr, Field
from typing import Union, List, Set, Optional, Dict
from typing_extensions import Literal, Self

IW9FORMDATAMODELSONEOF_ONE_OF_SCHEMAS = ["W4FormDataModel", "W8BenFormDataModel", "W8BeneFormDataModel", "W8ImyFormDataModel", "W9FormDataModel"]

class IW9FormDataModelsOneOf(BaseModel):
    """
    Interface representing a union of W4FormDataModel, W8BeneFormDataModel, W8BenFormDataModel, W8ImyFormDataModel, or W9FormDataModel.  Used only for OpenAPI documentation.
    """
    # data type: W4FormDataModel
    oneof_schema_1_validator: Optional[W4FormDataModel] = None
    # data type: W8BeneFormDataModel
    oneof_schema_2_validator: Optional[W8BeneFormDataModel] = None
    # data type: W8BenFormDataModel
    oneof_schema_3_validator: Optional[W8BenFormDataModel] = None
    # data type: W8ImyFormDataModel
    oneof_schema_4_validator: Optional[W8ImyFormDataModel] = None
    # data type: W9FormDataModel
    oneof_schema_5_validator: Optional[W9FormDataModel] = None
    actual_instance: Optional[Union[W4FormDataModel, W8BenFormDataModel, W8BeneFormDataModel, W8ImyFormDataModel, W9FormDataModel]] = None
    one_of_schemas: Set[str] = { "W4FormDataModel", "W8BenFormDataModel", "W8BeneFormDataModel", "W8ImyFormDataModel", "W9FormDataModel" }

    model_config = ConfigDict(
        validate_assignment=True,
        protected_namespaces=(),
    )


    def __init__(self, *args, **kwargs) -> None:
        if args:
            if len(args) > 1:
                raise ValueError("If a position argument is used, only 1 is allowed to set `actual_instance`")
            if kwargs:
                raise ValueError("If a position argument is used, keyword arguments cannot be used.")
            super().__init__(actual_instance=args[0])
        else:
            super().__init__(**kwargs)

    @field_validator('actual_instance')
    def actual_instance_must_validate_oneof(cls, v):
        instance = IW9FormDataModelsOneOf.model_construct()
        error_messages = []
        match = 0
        # validate data type: W4FormDataModel
        if not isinstance(v, W4FormDataModel):
            error_messages.append(f"Error! Input type `{type(v)}` is not `W4FormDataModel`")
        else:
            match += 1
        # validate data type: W8BeneFormDataModel
        if not isinstance(v, W8BeneFormDataModel):
            error_messages.append(f"Error! Input type `{type(v)}` is not `W8BeneFormDataModel`")
        else:
            match += 1
        # validate data type: W8BenFormDataModel
        if not isinstance(v, W8BenFormDataModel):
            error_messages.append(f"Error! Input type `{type(v)}` is not `W8BenFormDataModel`")
        else:
            match += 1
        # validate data type: W8ImyFormDataModel
        if not isinstance(v, W8ImyFormDataModel):
            error_messages.append(f"Error! Input type `{type(v)}` is not `W8ImyFormDataModel`")
        else:
            match += 1
        # validate data type: W9FormDataModel
        if not isinstance(v, W9FormDataModel):
            error_messages.append(f"Error! Input type `{type(v)}` is not `W9FormDataModel`")
        else:
            match += 1
        if match > 1:
            # more than 1 match
            raise ValueError("Multiple matches found when setting `actual_instance` in IW9FormDataModelsOneOf with oneOf schemas: W4FormDataModel, W8BenFormDataModel, W8BeneFormDataModel, W8ImyFormDataModel, W9FormDataModel. Details: " + ", ".join(error_messages))
        elif match == 0:
            # no match
            raise ValueError("No match found when setting `actual_instance` in IW9FormDataModelsOneOf with oneOf schemas: W4FormDataModel, W8BenFormDataModel, W8BeneFormDataModel, W8ImyFormDataModel, W9FormDataModel. Details: " + ", ".join(error_messages))
        else:
            return v

    @classmethod
    def from_dict(cls, obj: Union[str, Dict[str, Any]]) -> Self:
        return cls.from_json(json.dumps(obj))

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Returns the object represented by the json string"""
        instance = cls.model_construct()
        error_messages = []
        match = 0

        # deserialize data into W4FormDataModel
        try:
            instance.actual_instance = W4FormDataModel.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into W8BeneFormDataModel
        try:
            instance.actual_instance = W8BeneFormDataModel.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into W8BenFormDataModel
        try:
            instance.actual_instance = W8BenFormDataModel.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into W8ImyFormDataModel
        try:
            instance.actual_instance = W8ImyFormDataModel.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into W9FormDataModel
        try:
            instance.actual_instance = W9FormDataModel.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))

        if match > 1:
            # more than 1 match
            raise ValueError("Multiple matches found when deserializing the JSON string into IW9FormDataModelsOneOf with oneOf schemas: W4FormDataModel, W8BenFormDataModel, W8BeneFormDataModel, W8ImyFormDataModel, W9FormDataModel. Details: " + ", ".join(error_messages))
        elif match == 0:
            # no match
            raise ValueError("No match found when deserializing the JSON string into IW9FormDataModelsOneOf with oneOf schemas: W4FormDataModel, W8BenFormDataModel, W8BeneFormDataModel, W8ImyFormDataModel, W9FormDataModel. Details: " + ", ".join(error_messages))
        else:
            return instance

    def to_json(self) -> str:
        """Returns the JSON representation of the actual instance"""
        if self.actual_instance is None:
            return "null"

        if hasattr(self.actual_instance, "to_json") and callable(self.actual_instance.to_json):
            return self.actual_instance.to_json()
        else:
            return json.dumps(self.actual_instance)

    def to_dict(self) -> Optional[Union[Dict[str, Any], W4FormDataModel, W8BenFormDataModel, W8BeneFormDataModel, W8ImyFormDataModel, W9FormDataModel]]:
        """Returns the dict representation of the actual instance"""
        if self.actual_instance is None:
            return None

        if hasattr(self.actual_instance, "to_dict") and callable(self.actual_instance.to_dict):
            return self.actual_instance.to_dict()
        else:
            # primitive type
            return self.actual_instance

    def to_str(self) -> str:
        """Returns the string representation of the actual instance"""
        return pprint.pformat(self.model_dump())


