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
@version    25.10.1
@link       https://github.com/avadev/AvaTax-REST-V3-Python-SDK
"""

from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from Avalara.SDK.models.A1099.V2.entry_status_response import EntryStatusResponse
from Avalara.SDK.models.A1099.V2.tin_match_status_response import TinMatchStatusResponse
from typing import Optional, Set
from typing_extensions import Self

class W9FormResponse(BaseModel):
    """
    W9FormResponse
    """ # noqa: E501
    type: Optional[StrictStr] = Field(default=None, description="The form type (always \"W9\" for this model).")
    name: Optional[StrictStr] = Field(default=None, description="The name of the individual or entity associated with the form.")
    business_name: Optional[StrictStr] = Field(default=None, description="The name of the business associated with the form.", alias="businessName")
    business_classification: Optional[StrictStr] = Field(default=None, description="The classification of the business.", alias="businessClassification")
    business_other: Optional[StrictStr] = Field(default=None, description="The classification description when \"businessClassification\" is \"Other\".", alias="businessOther")
    foreign_partner_owner_or_beneficiary: Optional[StrictBool] = Field(default=None, description="Indicates whether the individual is a foreign partner, owner, or beneficiary.", alias="foreignPartnerOwnerOrBeneficiary")
    exempt_payee_code: Optional[StrictStr] = Field(default=None, description="The exempt payee code.", alias="exemptPayeeCode")
    exempt_fatca_code: Optional[StrictStr] = Field(default=None, description="The exemption from FATCA reporting code.", alias="exemptFatcaCode")
    foreign_country_indicator: Optional[StrictBool] = Field(default=None, description="Indicates whether the individual or entity is in a foreign country.", alias="foreignCountryIndicator")
    address: Optional[StrictStr] = Field(default=None, description="The address of the individual or entity.")
    foreign_address: Optional[StrictStr] = Field(default=None, description="The foreign address of the individual or entity.", alias="foreignAddress")
    city: Optional[StrictStr] = Field(default=None, description="The city of the address.")
    state: Optional[StrictStr] = Field(default=None, description="The state of the address.")
    zip: Optional[StrictStr] = Field(default=None, description="The ZIP code of the address.")
    account_number: Optional[StrictStr] = Field(default=None, description="The account number associated with the form.", alias="accountNumber")
    tin_type: Optional[StrictStr] = Field(default=None, description="Tax Identification Number (TIN) type.", alias="tinType")
    tin: Optional[StrictStr] = Field(default=None, description="The taxpayer identification number (TIN).")
    backup_withholding: Optional[StrictBool] = Field(default=None, description="Indicates whether backup withholding applies.", alias="backupWithholding")
    is1099able: Optional[StrictBool] = Field(default=None, description="Indicates whether the individual or entity should be issued a 1099 form.")
    tin_match_status: Optional[TinMatchStatusResponse] = Field(default=None, description="The TIN Match status from IRS.", alias="tinMatchStatus")
    id: Optional[StrictStr] = Field(default=None, description="The unique identifier for the form.")
    entry_status: Optional[EntryStatusResponse] = Field(default=None, description="The entry status information for the form.", alias="entryStatus")
    reference_id: Optional[StrictStr] = Field(default=None, description="A reference identifier for the form.", alias="referenceId")
    company_id: Optional[StrictStr] = Field(default=None, description="The ID of the associated company.", alias="companyId")
    display_name: Optional[StrictStr] = Field(default=None, description="The display name associated with the form.", alias="displayName")
    email: Optional[StrictStr] = Field(default=None, description="The email address of the individual associated with the form.")
    archived: Optional[StrictBool] = Field(default=None, description="Indicates whether the form is archived.")
    ancestor_id: Optional[StrictStr] = Field(default=None, description="Form ID of previous version.", alias="ancestorId")
    signature: Optional[StrictStr] = Field(default=None, description="The signature of the form.")
    signed_date: Optional[datetime] = Field(default=None, description="The date the form was signed.", alias="signedDate")
    e_delivery_consented_at: Optional[datetime] = Field(default=None, description="The date when e-delivery was consented.", alias="eDeliveryConsentedAt")
    created_at: Optional[datetime] = Field(default=None, description="The creation date of the form.", alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, description="The last updated date of the form.", alias="updatedAt")
    __properties: ClassVar[List[str]] = ["type", "id", "entryStatus", "referenceId", "companyId", "displayName", "email", "archived", "ancestorId", "signature", "signedDate", "eDeliveryConsentedAt", "createdAt", "updatedAt"]

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['W4', 'W8Ben', 'W8BenE', 'W8Imy', 'W9']):
            raise ValueError("must be one of enum values ('W4', 'W8Ben', 'W8BenE', 'W8Imy', 'W9')")
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        protected_namespaces=(),
    )


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Optional[Self]:
        """Create an instance of W9FormResponse from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        * OpenAPI `readOnly` fields are excluded.
        """
        excluded_fields: Set[str] = set([
            "type",
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of entry_status
        if self.entry_status:
            _dict['entryStatus'] = self.entry_status.to_dict()
        # set to None if reference_id (nullable) is None
        # and model_fields_set contains the field
        if self.reference_id is None and "reference_id" in self.model_fields_set:
            _dict['referenceId'] = None

        # set to None if email (nullable) is None
        # and model_fields_set contains the field
        if self.email is None and "email" in self.model_fields_set:
            _dict['email'] = None

        # set to None if ancestor_id (nullable) is None
        # and model_fields_set contains the field
        if self.ancestor_id is None and "ancestor_id" in self.model_fields_set:
            _dict['ancestorId'] = None

        # set to None if signature (nullable) is None
        # and model_fields_set contains the field
        if self.signature is None and "signature" in self.model_fields_set:
            _dict['signature'] = None

        # set to None if signed_date (nullable) is None
        # and model_fields_set contains the field
        if self.signed_date is None and "signed_date" in self.model_fields_set:
            _dict['signedDate'] = None

        # set to None if e_delivery_consented_at (nullable) is None
        # and model_fields_set contains the field
        if self.e_delivery_consented_at is None and "e_delivery_consented_at" in self.model_fields_set:
            _dict['eDeliveryConsentedAt'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of W9FormResponse from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "type": obj.get("type"),
            "id": obj.get("id"),
            "entryStatus": EntryStatusResponse.from_dict(obj["entryStatus"]) if obj.get("entryStatus") is not None else None,
            "referenceId": obj.get("referenceId"),
            "companyId": obj.get("companyId"),
            "displayName": obj.get("displayName"),
            "email": obj.get("email"),
            "archived": obj.get("archived"),
            "ancestorId": obj.get("ancestorId"),
            "signature": obj.get("signature"),
            "signedDate": obj.get("signedDate"),
            "eDeliveryConsentedAt": obj.get("eDeliveryConsentedAt"),
            "createdAt": obj.get("createdAt"),
            "updatedAt": obj.get("updatedAt")
        })
        return _obj


