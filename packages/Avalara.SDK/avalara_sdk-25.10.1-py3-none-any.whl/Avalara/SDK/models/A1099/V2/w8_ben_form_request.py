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
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing import Optional, Set
from typing_extensions import Self

class W8BenFormRequest(BaseModel):
    """
    W8BenFormRequest
    """ # noqa: E501
    type: Optional[StrictStr] = Field(default=None, description="The form type (always \"w8ben\" for this model).")
    name: StrictStr = Field(description="The name of the individual or entity associated with the form.")
    citizenship_country: StrictStr = Field(description="The country of citizenship.. Allowed values: US, AF, AX, AL, AG, AQ, AN, AO, AV, AY (and 248 more)", alias="citizenshipCountry")
    residence_address: Optional[StrictStr] = Field(default=None, description="The residential address of the individual or entity.", alias="residenceAddress")
    residence_city: Optional[StrictStr] = Field(default=None, description="The city of residence.", alias="residenceCity")
    residence_state: Optional[StrictStr] = Field(default=None, description="The state of residence. Required for US and Canada.. Allowed values: AA, AE, AK, AL, AP, AR, AS, AZ, CA, CO (and 65 more)", alias="residenceState")
    residence_zip: Optional[StrictStr] = Field(default=None, description="The ZIP code of the residence.", alias="residenceZip")
    residence_country: StrictStr = Field(description="The country of residence.. Allowed values: US, AF, AX, AL, AG, AQ, AN, AO, AV, AY (and 248 more)", alias="residenceCountry")
    residence_is_mailing: Optional[StrictBool] = Field(default=None, description="Indicates whether the residence address is the mailing address.", alias="residenceIsMailing")
    mailing_address: Optional[StrictStr] = Field(default=None, description="The mailing address.", alias="mailingAddress")
    mailing_city: Optional[StrictStr] = Field(default=None, description="The city of the mailing address.", alias="mailingCity")
    mailing_state: Optional[StrictStr] = Field(default=None, description="The state of the mailing address. Required for US and Canada.. Allowed values: AA, AE, AK, AL, AP, AR, AS, AZ, CA, CO (and 65 more)", alias="mailingState")
    mailing_zip: Optional[StrictStr] = Field(default=None, description="The ZIP code of the mailing address.", alias="mailingZip")
    mailing_country: Optional[StrictStr] = Field(description="The country of the mailing address.. Allowed values: US, AF, AX, AL, AG, AQ, AN, AO, AV, AY (and 248 more)", alias="mailingCountry")
    tin: Optional[StrictStr] = Field(default=None, description="The taxpayer identification number (TIN).")
    foreign_tin_not_required: Optional[StrictBool] = Field(default=None, description="Indicates whether a foreign TIN is not legally required.", alias="foreignTinNotRequired")
    foreign_tin: Optional[StrictStr] = Field(default=None, description="The foreign taxpayer identification number (TIN).", alias="foreignTin")
    reference_number: Optional[StrictStr] = Field(default=None, description="A reference number for the form.", alias="referenceNumber")
    birthday: Optional[date] = Field(default=None, description="The birthday of the individual associated with the form.")
    treaty_country: Optional[StrictStr] = Field(default=None, description="The country for which the treaty applies.. Allowed values: US, AF, AX, AL, AG, AQ, AN, AO, AV, AY (and 248 more)", alias="treatyCountry")
    treaty_article: Optional[StrictStr] = Field(default=None, description="The specific article of the treaty being claimed.", alias="treatyArticle")
    treaty_reasons: Optional[StrictStr] = Field(default=None, description="The reasons for claiming treaty benefits.", alias="treatyReasons")
    withholding_rate: Optional[StrictStr] = Field(default=None, description="The withholding rate applied as per the treaty. Must be a percentage with up to two decimals (e.g., 12.50, 0).. Allowed values: 0, 0.0, 0.00, 5, 5.5, 10, 12.50, 15, 20, 25 (and 1 more)", alias="withholdingRate")
    income_type: Optional[StrictStr] = Field(default=None, description="The type of income covered by the treaty.", alias="incomeType")
    signer_name: Optional[StrictStr] = Field(default=None, description="The name of the signer of the form.", alias="signerName")
    e_delivery_consented_at: Optional[datetime] = Field(default=None, description="The date when e-delivery was consented.", alias="eDeliveryConsentedAt")
    signature: Optional[StrictStr] = Field(default=None, description="The signature of the form.")
    company_id: Optional[StrictStr] = Field(default=None, description="The ID of the associated company. Required when creating a form.", alias="companyId")
    reference_id: Optional[StrictStr] = Field(default=None, description="A reference identifier for the form.", alias="referenceId")
    email: Optional[StrictStr] = Field(default=None, description="The email address of the individual associated with the form.")
    __properties: ClassVar[List[str]] = ["eDeliveryConsentedAt", "signature", "type", "companyId", "referenceId", "email"]

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['W4', 'W8Ben', 'W8BenE', 'W8Imy', 'W9']):
            raise ValueError("must be one of enum values ('W4', 'W8Ben', 'W8BenE', 'W8Imy', 'W9')")
        return value

    @field_validator('citizenship_country')
    def citizenship_country_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI']):
            raise ValueError("must be one of enum values ('US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI')")
        return value

    @field_validator('residence_state')
    def residence_state_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['AA', 'AE', 'AK', 'AL', 'AP', 'AR', 'AS', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'FM', 'GA', 'GU', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MH', 'MI', 'MN', 'MO', 'MP', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'PW', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VI', 'VT', 'WA', 'WI', 'WV', 'WY', 'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']):
            raise ValueError("must be one of enum values ('AA', 'AE', 'AK', 'AL', 'AP', 'AR', 'AS', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'FM', 'GA', 'GU', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MH', 'MI', 'MN', 'MO', 'MP', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'PW', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VI', 'VT', 'WA', 'WI', 'WV', 'WY', 'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT')")
        return value

    @field_validator('residence_country')
    def residence_country_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI']):
            raise ValueError("must be one of enum values ('US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI')")
        return value

    @field_validator('mailing_state')
    def mailing_state_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['AA', 'AE', 'AK', 'AL', 'AP', 'AR', 'AS', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'FM', 'GA', 'GU', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MH', 'MI', 'MN', 'MO', 'MP', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'PW', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VI', 'VT', 'WA', 'WI', 'WV', 'WY', 'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']):
            raise ValueError("must be one of enum values ('AA', 'AE', 'AK', 'AL', 'AP', 'AR', 'AS', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'FM', 'GA', 'GU', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MH', 'MI', 'MN', 'MO', 'MP', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'PW', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VI', 'VT', 'WA', 'WI', 'WV', 'WY', 'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT')")
        return value

    @field_validator('mailing_country')
    def mailing_country_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI']):
            raise ValueError("must be one of enum values ('US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI')")
        return value

    @field_validator('treaty_country')
    def treaty_country_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI']):
            raise ValueError("must be one of enum values ('US', 'AF', 'AX', 'AL', 'AG', 'AQ', 'AN', 'AO', 'AV', 'AY', 'AC', 'AR', 'AM', 'AA', 'AT', 'AS', 'AU', 'AJ', 'BF', 'BA', 'FQ', 'BG', 'BB', 'BO', 'BE', 'BH', 'BN', 'BD', 'BT', 'BL', 'BK', 'BC', 'BV', 'BR', 'IO', 'VI', 'BX', 'BU', 'UV', 'BM', 'BY', 'CB', 'CM', 'CA', 'CV', 'CJ', 'CT', 'CD', 'CI', 'CH', 'KT', 'IP', 'CK', 'CO', 'CN', 'CF', 'CG', 'CW', 'CR', 'CS', 'IV', 'HR', 'CU', 'UC', 'CY', 'EZ', 'DA', 'DX', 'DJ', 'DO', 'DR', 'TT', 'EC', 'EG', 'ES', 'EK', 'ER', 'EN', 'ET', 'FK', 'FO', 'FM', 'FJ', 'FI', 'FR', 'FP', 'FS', 'GB', 'GA', 'GG', 'GM', 'GH', 'GI', 'GR', 'GL', 'GJ', 'GQ', 'GT', 'GK', 'GV', 'PU', 'GY', 'HA', 'HM', 'VT', 'HO', 'HK', 'HQ', 'HU', 'IC', 'IN', 'ID', 'IR', 'IZ', 'EI', 'IS', 'IT', 'JM', 'JN', 'JA', 'DQ', 'JE', 'JQ', 'JO', 'KZ', 'KE', 'KQ', 'KR', 'KN', 'KS', 'KV', 'KU', 'KG', 'LA', 'LG', 'LE', 'LT', 'LI', 'LY', 'LS', 'LH', 'LU', 'MC', 'MK', 'MA', 'MI', 'MY', 'MV', 'ML', 'MT', 'IM', 'RM', 'MR', 'MP', 'MX', 'MQ', 'MD', 'MN', 'MG', 'MJ', 'MH', 'MO', 'MZ', 'WA', 'NR', 'BQ', 'NP', 'NL', 'NC', 'NZ', 'NU', 'NG', 'NI', 'NE', 'NF', 'CQ', 'NO', 'MU', 'OC', 'PK', 'PS', 'LQ', 'PM', 'PP', 'PF', 'PA', 'PE', 'RP', 'PC', 'PL', 'PO', 'RQ', 'QA', 'RO', 'RS', 'RW', 'TB', 'RN', 'WS', 'SM', 'TP', 'SA', 'SG', 'RI', 'SE', 'SL', 'SN', 'NN', 'LO', 'SI', 'BP', 'SO', 'SF', 'SX', 'SP', 'PG', 'CE', 'SH', 'SC', 'ST', 'SB', 'VC', 'SU', 'NS', 'SV', 'WZ', 'SW', 'SZ', 'SY', 'TW', 'TI', 'TZ', 'TH', 'TO', 'TL', 'TN', 'TD', 'TS', 'TU', 'TX', 'TK', 'TV', 'UG', 'UP', 'AE', 'UK', 'UY', 'UZ', 'NH', 'VE', 'VM', 'VQ', 'WQ', 'WF', 'WI', 'YM', 'ZA', 'ZI')")
        return value

    @field_validator('withholding_rate')
    def withholding_rate_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['0', '0.0', '0.00', '5', '5.5', '10', '12.50', '15', '20', '25', '30']):
            raise ValueError("must be one of enum values ('0', '0.0', '0.00', '5', '5.5', '10', '12.50', '15', '20', '25', '30')")
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
        """Create an instance of W8BenFormRequest from a JSON string"""
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
        # set to None if e_delivery_consented_at (nullable) is None
        # and model_fields_set contains the field
        if self.e_delivery_consented_at is None and "e_delivery_consented_at" in self.model_fields_set:
            _dict['eDeliveryConsentedAt'] = None

        # set to None if signature (nullable) is None
        # and model_fields_set contains the field
        if self.signature is None and "signature" in self.model_fields_set:
            _dict['signature'] = None

        # set to None if reference_id (nullable) is None
        # and model_fields_set contains the field
        if self.reference_id is None and "reference_id" in self.model_fields_set:
            _dict['referenceId'] = None

        # set to None if email (nullable) is None
        # and model_fields_set contains the field
        if self.email is None and "email" in self.model_fields_set:
            _dict['email'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of W8BenFormRequest from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "eDeliveryConsentedAt": obj.get("eDeliveryConsentedAt"),
            "signature": obj.get("signature"),
            "type": obj.get("type"),
            "companyId": obj.get("companyId"),
            "referenceId": obj.get("referenceId"),
            "email": obj.get("email")
        })
        return _obj


