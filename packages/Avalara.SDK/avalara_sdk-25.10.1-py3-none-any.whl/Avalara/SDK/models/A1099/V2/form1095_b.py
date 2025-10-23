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

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from Avalara.SDK.models.A1099.V2.covered_individual import CoveredIndividual
from Avalara.SDK.models.A1099.V2.form1099_status_detail import Form1099StatusDetail
from Avalara.SDK.models.A1099.V2.state_and_local_withholding import StateAndLocalWithholding
from Avalara.SDK.models.A1099.V2.state_efile_status_detail import StateEfileStatusDetail
from Avalara.SDK.models.A1099.V2.validation_error import ValidationError
from typing import Optional, Set
from typing_extensions import Self

class Form1095B(BaseModel):
    """
    Form 1095-B: Health Coverage
    """ # noqa: E501
    employee_first_name: Optional[StrictStr] = Field(description="Employee's first name", alias="employeeFirstName")
    employee_middle_name: Optional[StrictStr] = Field(default=None, description="Employee's middle name", alias="employeeMiddleName")
    employee_last_name: Optional[StrictStr] = Field(description="Employee's last name", alias="employeeLastName")
    employee_name_suffix: Optional[StrictStr] = Field(default=None, description="Employee's name suffix", alias="employeeNameSuffix")
    employee_date_of_birth: Optional[date] = Field(default=None, description="Employee's date of birth", alias="employeeDateOfBirth")
    origin_of_health_coverage_code: Optional[StrictStr] = Field(description="Origin of health coverage code.    Available values:  - A: Small Business Health Options Program (SHOP)  - B: Employer-sponsored coverage  - C: Government-sponsored program  - D: Individual market insurance  - E: Multiemployer plan  - F: Other designated minimum essential coverage  - G: Employer-sponsored coverage that is an individual coverage HRA (valid for tax years 2020 and later)", alias="originOfHealthCoverageCode")
    covered_individuals: Optional[List[CoveredIndividual]] = Field(default=None, description="Covered individuals information - At least one month of coverage must be entered if it's not a correction.", alias="coveredIndividuals")
    type: StrictStr = Field(description="Form type.")
    id: Optional[StrictStr] = Field(default=None, description="Form ID. Unique identifier set when the record is created.")
    issuer_id: Optional[StrictStr] = Field(default=None, description="Issuer ID - only required when creating forms", alias="issuerId")
    issuer_reference_id: Optional[StrictStr] = Field(default=None, description="Issuer Reference ID - only required when creating forms via $bulk-upsert", alias="issuerReferenceId")
    issuer_tin: Optional[StrictStr] = Field(default=None, description="Issuer TIN - readonly", alias="issuerTin")
    tax_year: Optional[StrictInt] = Field(default=None, description="Tax Year - only required when creating forms via $bulk-upsert", alias="taxYear")
    reference_id: Optional[StrictStr] = Field(default=None, description="Internal reference ID. Never shown to any agency or recipient.", alias="referenceId")
    tin: Optional[StrictStr] = Field(default=None, description="Recipient's Federal Tax Identification Number (TIN).")
    recipient_name: Optional[StrictStr] = Field(description="Recipient name", alias="recipientName")
    tin_type: Optional[StrictStr] = Field(default=None, description="Tax Identification Number (TIN) type.  Available values: - EIN: Employer Identification Number - SSN: Social Security Number - ITIN: Individual Taxpayer Identification Number - ATIN: Adoption Taxpayer Identification Number", alias="tinType")
    recipient_second_name: Optional[StrictStr] = Field(default=None, description="Recipient second name", alias="recipientSecondName")
    address: Optional[StrictStr] = Field(description="Address.")
    address2: Optional[StrictStr] = Field(default=None, description="Address line 2.")
    city: Optional[StrictStr] = Field(description="City.")
    state: Optional[StrictStr] = Field(default=None, description="Two-letter US state or Canadian province code (required for US/CA addresses).")
    zip: Optional[StrictStr] = Field(default=None, description="ZIP/postal code.")
    email: Optional[StrictStr] = Field(default=None, description="Recipient's Contact email address.")
    account_number: Optional[StrictStr] = Field(default=None, description="Account number", alias="accountNumber")
    office_code: Optional[StrictStr] = Field(default=None, description="Office code", alias="officeCode")
    non_us_province: Optional[StrictStr] = Field(default=None, description="Province or region for non-US/CA addresses.", alias="nonUsProvince")
    country_code: Optional[StrictStr] = Field(description="Two-letter IRS country code (e.g., 'US', 'CA'), as defined at https://www.irs.gov/e-file-providers/country-codes.", alias="countryCode")
    federal_efile_date: Optional[date] = Field(default=None, description="Date when federal e-filing should be scheduled. If set between current date and beginning of blackout period, scheduled to that date. If in the past or blackout period, scheduled to next available date. For blackout period information, see https://www.track1099.com/info/IRS_info. Set to null to leave unscheduled.", alias="federalEfileDate")
    postal_mail: Optional[StrictBool] = Field(default=None, description="Boolean indicating that postal mailing to the recipient should be scheduled for this form", alias="postalMail")
    state_efile_date: Optional[date] = Field(default=None, description="Date when state e-filing should be scheduled. Must be on or after federalEfileDate. If set between current date and beginning of blackout period, scheduled to that date. If in the past or blackout period, scheduled to next available date. For blackout period information, see https://www.track1099.com/info/IRS_info. Set to null to leave unscheduled.", alias="stateEfileDate")
    recipient_edelivery_date: Optional[date] = Field(default=None, description="Date when recipient e-delivery should be scheduled. If set between current date and beginning of blackout period, scheduled to that date. If in the past or blackout period, scheduled to next available date. For blackout period information, see https://www.track1099.com/info/IRS_info. Set to null to leave unscheduled.", alias="recipientEdeliveryDate")
    tin_match: Optional[StrictBool] = Field(default=None, description="Boolean indicating that TIN Matching should be scheduled for this form", alias="tinMatch")
    no_tin: Optional[StrictBool] = Field(default=None, description="No TIN indicator", alias="noTin")
    address_verification: Optional[StrictBool] = Field(default=None, description="Boolean indicating that address verification should be scheduled for this form", alias="addressVerification")
    state_and_local_withholding: Optional[StateAndLocalWithholding] = Field(default=None, description="State and local withholding information", alias="stateAndLocalWithholding")
    second_tin_notice: Optional[StrictBool] = Field(default=None, description="Second TIN notice", alias="secondTinNotice")
    federal_efile_status: Optional[Form1099StatusDetail] = Field(default=None, description="Federal e-file status.  Available values:  - unscheduled: Form has not been scheduled for federal e-filing  - scheduled: Form is scheduled for federal e-filing  - airlock: Form is in process of being uploaded to the IRS (forms exist in this state for a very short period and cannot be updated while in this state)  - sent: Form has been sent to the IRS  - accepted: Form was accepted by the IRS  - corrected_scheduled: Correction is scheduled to be sent  - corrected_airlock: Correction is in process of being uploaded to the IRS (forms exist in this state for a very short period and cannot be updated while in this state)  - corrected: A correction has been sent to the IRS  - corrected_accepted: Correction was accepted by the IRS  - rejected: Form was rejected by the IRS  - corrected_rejected: Correction was rejected by the IRS  - held: Form is held and will not be submitted to IRS (used for certain forms submitted only to states)", alias="federalEfileStatus")
    state_efile_status: Optional[List[StateEfileStatusDetail]] = Field(default=None, description="State e-file status.  Available values:  - unscheduled: Form has not been scheduled for state e-filing  - scheduled: Form is scheduled for state e-filing  - airlocked: Form is in process of being uploaded to the state  - sent: Form has been sent to the state  - rejected: Form was rejected by the state  - accepted: Form was accepted by the state  - corrected_scheduled: Correction is scheduled to be sent  - corrected_airlocked: Correction is in process of being uploaded to the state  - corrected_sent: Correction has been sent to the state  - corrected_rejected: Correction was rejected by the state  - corrected_accepted: Correction was accepted by the state", alias="stateEfileStatus")
    postal_mail_status: Optional[Form1099StatusDetail] = Field(default=None, description="Postal mail to recipient status.  Available values:  - unscheduled: Postal mail has not been scheduled  - pending: Postal mail is pending to be sent  - sent: Postal mail has been sent  - delivered: Postal mail has been delivered", alias="postalMailStatus")
    tin_match_status: Optional[Form1099StatusDetail] = Field(default=None, description="TIN Match status.  Available values:  - none: TIN matching has not been performed  - pending: TIN matching request is pending  - matched: Name/TIN combination matches IRS records  - unknown: TIN is missing, invalid, or request contains errors  - rejected: Name/TIN combination does not match IRS records or TIN not currently issued", alias="tinMatchStatus")
    address_verification_status: Optional[Form1099StatusDetail] = Field(default=None, description="Address verification status.  Available values:  - unknown: Address verification has not been checked  - pending: Address verification is in progress  - failed: Address verification failed  - incomplete: Address verification is incomplete  - unchanged: User declined address changes  - verified: Address has been verified and accepted", alias="addressVerificationStatus")
    e_delivery_status: Optional[Form1099StatusDetail] = Field(default=None, description="EDelivery status.  Available values:  - unscheduled: E-delivery has not been scheduled  - scheduled: E-delivery is scheduled to be sent  - sent: E-delivery has been sent to recipient  - bounced: E-delivery bounced back (invalid email)  - refused: E-delivery was refused by recipient  - bad_verify: E-delivery failed verification  - accepted: E-delivery was accepted by recipient  - bad_verify_limit: E-delivery failed verification limit reached  - second_delivery: Second e-delivery attempt  - undelivered: E-delivery is undelivered (temporary state allowing resend)", alias="eDeliveryStatus")
    validation_errors: Optional[List[ValidationError]] = Field(default=None, description="Validation errors", alias="validationErrors")
    created_at: Optional[datetime] = Field(default=None, description="Date time when the record was created.", alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, description="Date time when the record was last updated.", alias="updatedAt")
    __properties: ClassVar[List[str]] = ["type", "id", "issuerId", "issuerReferenceId", "issuerTin", "taxYear", "referenceId", "tin", "recipientName", "tinType", "recipientSecondName", "address", "address2", "city", "state", "zip", "email", "accountNumber", "officeCode", "nonUsProvince", "countryCode", "federalEfileDate", "postalMail", "stateEfileDate", "recipientEdeliveryDate", "tinMatch", "noTin", "addressVerification", "stateAndLocalWithholding", "secondTinNotice", "federalEfileStatus", "stateEfileStatus", "postalMailStatus", "tinMatchStatus", "addressVerificationStatus", "eDeliveryStatus", "validationErrors", "createdAt", "updatedAt"]

    @field_validator('origin_of_health_coverage_code')
    def origin_of_health_coverage_code_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['A', 'B', 'C', 'D', 'E', 'F', 'G']):
            raise ValueError("must be one of enum values ('A', 'B', 'C', 'D', 'E', 'F', 'G')")
        return value

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['Form1099Nec', 'Form1099Misc', 'Form1099Div', 'Form1099R', 'Form1099K', 'Form1095B', 'Form1042S', 'Form1095C', 'Form1099Int']):
            raise ValueError("must be one of enum values ('Form1099Nec', 'Form1099Misc', 'Form1099Div', 'Form1099R', 'Form1099K', 'Form1095B', 'Form1042S', 'Form1095C', 'Form1099Int')")
        return value

    @field_validator('tin_type')
    def tin_type_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['EIN', 'SSN', 'ITIN', 'ATIN']):
            raise ValueError("must be one of enum values ('EIN', 'SSN', 'ITIN', 'ATIN')")
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
        """Create an instance of Form1095B from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        * OpenAPI `readOnly` fields are excluded.
        """
        excluded_fields: Set[str] = set([
            "id",
            "federal_efile_status",
            "state_efile_status",
            "postal_mail_status",
            "tin_match_status",
            "address_verification_status",
            "e_delivery_status",
            "validation_errors",
            "created_at",
            "updated_at",
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of state_and_local_withholding
        if self.state_and_local_withholding:
            _dict['stateAndLocalWithholding'] = self.state_and_local_withholding.to_dict()
        # override the default output from pydantic by calling `to_dict()` of federal_efile_status
        if self.federal_efile_status:
            _dict['federalEfileStatus'] = self.federal_efile_status.to_dict()
        # override the default output from pydantic by calling `to_dict()` of each item in state_efile_status (list)
        _items = []
        if self.state_efile_status:
            for _item in self.state_efile_status:
                if _item:
                    _items.append(_item.to_dict())
            _dict['stateEfileStatus'] = _items
        # override the default output from pydantic by calling `to_dict()` of postal_mail_status
        if self.postal_mail_status:
            _dict['postalMailStatus'] = self.postal_mail_status.to_dict()
        # override the default output from pydantic by calling `to_dict()` of tin_match_status
        if self.tin_match_status:
            _dict['tinMatchStatus'] = self.tin_match_status.to_dict()
        # override the default output from pydantic by calling `to_dict()` of address_verification_status
        if self.address_verification_status:
            _dict['addressVerificationStatus'] = self.address_verification_status.to_dict()
        # override the default output from pydantic by calling `to_dict()` of e_delivery_status
        if self.e_delivery_status:
            _dict['eDeliveryStatus'] = self.e_delivery_status.to_dict()
        # override the default output from pydantic by calling `to_dict()` of each item in validation_errors (list)
        _items = []
        if self.validation_errors:
            for _item in self.validation_errors:
                if _item:
                    _items.append(_item.to_dict())
            _dict['validationErrors'] = _items
        # set to None if id (nullable) is None
        # and model_fields_set contains the field
        if self.id is None and "id" in self.model_fields_set:
            _dict['id'] = None

        # set to None if issuer_id (nullable) is None
        # and model_fields_set contains the field
        if self.issuer_id is None and "issuer_id" in self.model_fields_set:
            _dict['issuerId'] = None

        # set to None if issuer_reference_id (nullable) is None
        # and model_fields_set contains the field
        if self.issuer_reference_id is None and "issuer_reference_id" in self.model_fields_set:
            _dict['issuerReferenceId'] = None

        # set to None if issuer_tin (nullable) is None
        # and model_fields_set contains the field
        if self.issuer_tin is None and "issuer_tin" in self.model_fields_set:
            _dict['issuerTin'] = None

        # set to None if tax_year (nullable) is None
        # and model_fields_set contains the field
        if self.tax_year is None and "tax_year" in self.model_fields_set:
            _dict['taxYear'] = None

        # set to None if reference_id (nullable) is None
        # and model_fields_set contains the field
        if self.reference_id is None and "reference_id" in self.model_fields_set:
            _dict['referenceId'] = None

        # set to None if tin (nullable) is None
        # and model_fields_set contains the field
        if self.tin is None and "tin" in self.model_fields_set:
            _dict['tin'] = None

        # set to None if recipient_name (nullable) is None
        # and model_fields_set contains the field
        if self.recipient_name is None and "recipient_name" in self.model_fields_set:
            _dict['recipientName'] = None

        # set to None if tin_type (nullable) is None
        # and model_fields_set contains the field
        if self.tin_type is None and "tin_type" in self.model_fields_set:
            _dict['tinType'] = None

        # set to None if recipient_second_name (nullable) is None
        # and model_fields_set contains the field
        if self.recipient_second_name is None and "recipient_second_name" in self.model_fields_set:
            _dict['recipientSecondName'] = None

        # set to None if address (nullable) is None
        # and model_fields_set contains the field
        if self.address is None and "address" in self.model_fields_set:
            _dict['address'] = None

        # set to None if address2 (nullable) is None
        # and model_fields_set contains the field
        if self.address2 is None and "address2" in self.model_fields_set:
            _dict['address2'] = None

        # set to None if city (nullable) is None
        # and model_fields_set contains the field
        if self.city is None and "city" in self.model_fields_set:
            _dict['city'] = None

        # set to None if state (nullable) is None
        # and model_fields_set contains the field
        if self.state is None and "state" in self.model_fields_set:
            _dict['state'] = None

        # set to None if zip (nullable) is None
        # and model_fields_set contains the field
        if self.zip is None and "zip" in self.model_fields_set:
            _dict['zip'] = None

        # set to None if email (nullable) is None
        # and model_fields_set contains the field
        if self.email is None and "email" in self.model_fields_set:
            _dict['email'] = None

        # set to None if account_number (nullable) is None
        # and model_fields_set contains the field
        if self.account_number is None and "account_number" in self.model_fields_set:
            _dict['accountNumber'] = None

        # set to None if office_code (nullable) is None
        # and model_fields_set contains the field
        if self.office_code is None and "office_code" in self.model_fields_set:
            _dict['officeCode'] = None

        # set to None if non_us_province (nullable) is None
        # and model_fields_set contains the field
        if self.non_us_province is None and "non_us_province" in self.model_fields_set:
            _dict['nonUsProvince'] = None

        # set to None if country_code (nullable) is None
        # and model_fields_set contains the field
        if self.country_code is None and "country_code" in self.model_fields_set:
            _dict['countryCode'] = None

        # set to None if federal_efile_date (nullable) is None
        # and model_fields_set contains the field
        if self.federal_efile_date is None and "federal_efile_date" in self.model_fields_set:
            _dict['federalEfileDate'] = None

        # set to None if postal_mail (nullable) is None
        # and model_fields_set contains the field
        if self.postal_mail is None and "postal_mail" in self.model_fields_set:
            _dict['postalMail'] = None

        # set to None if state_efile_date (nullable) is None
        # and model_fields_set contains the field
        if self.state_efile_date is None and "state_efile_date" in self.model_fields_set:
            _dict['stateEfileDate'] = None

        # set to None if recipient_edelivery_date (nullable) is None
        # and model_fields_set contains the field
        if self.recipient_edelivery_date is None and "recipient_edelivery_date" in self.model_fields_set:
            _dict['recipientEdeliveryDate'] = None

        # set to None if tin_match (nullable) is None
        # and model_fields_set contains the field
        if self.tin_match is None and "tin_match" in self.model_fields_set:
            _dict['tinMatch'] = None

        # set to None if no_tin (nullable) is None
        # and model_fields_set contains the field
        if self.no_tin is None and "no_tin" in self.model_fields_set:
            _dict['noTin'] = None

        # set to None if address_verification (nullable) is None
        # and model_fields_set contains the field
        if self.address_verification is None and "address_verification" in self.model_fields_set:
            _dict['addressVerification'] = None

        # set to None if state_and_local_withholding (nullable) is None
        # and model_fields_set contains the field
        if self.state_and_local_withholding is None and "state_and_local_withholding" in self.model_fields_set:
            _dict['stateAndLocalWithholding'] = None

        # set to None if second_tin_notice (nullable) is None
        # and model_fields_set contains the field
        if self.second_tin_notice is None and "second_tin_notice" in self.model_fields_set:
            _dict['secondTinNotice'] = None

        # set to None if federal_efile_status (nullable) is None
        # and model_fields_set contains the field
        if self.federal_efile_status is None and "federal_efile_status" in self.model_fields_set:
            _dict['federalEfileStatus'] = None

        # set to None if state_efile_status (nullable) is None
        # and model_fields_set contains the field
        if self.state_efile_status is None and "state_efile_status" in self.model_fields_set:
            _dict['stateEfileStatus'] = None

        # set to None if postal_mail_status (nullable) is None
        # and model_fields_set contains the field
        if self.postal_mail_status is None and "postal_mail_status" in self.model_fields_set:
            _dict['postalMailStatus'] = None

        # set to None if tin_match_status (nullable) is None
        # and model_fields_set contains the field
        if self.tin_match_status is None and "tin_match_status" in self.model_fields_set:
            _dict['tinMatchStatus'] = None

        # set to None if address_verification_status (nullable) is None
        # and model_fields_set contains the field
        if self.address_verification_status is None and "address_verification_status" in self.model_fields_set:
            _dict['addressVerificationStatus'] = None

        # set to None if e_delivery_status (nullable) is None
        # and model_fields_set contains the field
        if self.e_delivery_status is None and "e_delivery_status" in self.model_fields_set:
            _dict['eDeliveryStatus'] = None

        # set to None if validation_errors (nullable) is None
        # and model_fields_set contains the field
        if self.validation_errors is None and "validation_errors" in self.model_fields_set:
            _dict['validationErrors'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Form1095B from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "type": obj.get("type"),
            "id": obj.get("id"),
            "issuerId": obj.get("issuerId"),
            "issuerReferenceId": obj.get("issuerReferenceId"),
            "issuerTin": obj.get("issuerTin"),
            "taxYear": obj.get("taxYear"),
            "referenceId": obj.get("referenceId"),
            "tin": obj.get("tin"),
            "recipientName": obj.get("recipientName"),
            "tinType": obj.get("tinType"),
            "recipientSecondName": obj.get("recipientSecondName"),
            "address": obj.get("address"),
            "address2": obj.get("address2"),
            "city": obj.get("city"),
            "state": obj.get("state"),
            "zip": obj.get("zip"),
            "email": obj.get("email"),
            "accountNumber": obj.get("accountNumber"),
            "officeCode": obj.get("officeCode"),
            "nonUsProvince": obj.get("nonUsProvince"),
            "countryCode": obj.get("countryCode"),
            "federalEfileDate": obj.get("federalEfileDate"),
            "postalMail": obj.get("postalMail"),
            "stateEfileDate": obj.get("stateEfileDate"),
            "recipientEdeliveryDate": obj.get("recipientEdeliveryDate"),
            "tinMatch": obj.get("tinMatch"),
            "noTin": obj.get("noTin"),
            "addressVerification": obj.get("addressVerification"),
            "stateAndLocalWithholding": StateAndLocalWithholding.from_dict(obj["stateAndLocalWithholding"]) if obj.get("stateAndLocalWithholding") is not None else None,
            "secondTinNotice": obj.get("secondTinNotice"),
            "federalEfileStatus": Form1099StatusDetail.from_dict(obj["federalEfileStatus"]) if obj.get("federalEfileStatus") is not None else None,
            "stateEfileStatus": [StateEfileStatusDetail.from_dict(_item) for _item in obj["stateEfileStatus"]] if obj.get("stateEfileStatus") is not None else None,
            "postalMailStatus": Form1099StatusDetail.from_dict(obj["postalMailStatus"]) if obj.get("postalMailStatus") is not None else None,
            "tinMatchStatus": Form1099StatusDetail.from_dict(obj["tinMatchStatus"]) if obj.get("tinMatchStatus") is not None else None,
            "addressVerificationStatus": Form1099StatusDetail.from_dict(obj["addressVerificationStatus"]) if obj.get("addressVerificationStatus") is not None else None,
            "eDeliveryStatus": Form1099StatusDetail.from_dict(obj["eDeliveryStatus"]) if obj.get("eDeliveryStatus") is not None else None,
            "validationErrors": [ValidationError.from_dict(_item) for _item in obj["validationErrors"]] if obj.get("validationErrors") is not None else None,
            "createdAt": obj.get("createdAt"),
            "updatedAt": obj.get("updatedAt")
        })
        return _obj


