from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from datetime import date

class ManagementChainLevel(BaseModel):
    """Model for a single level in the management chain"""
    organization_id: Optional[str]
    organization_name: Optional[str]
    manager_id: Optional[str]
    manager_name: Optional[str]

class Worker(BaseModel):
    """
    Pydantic model for a Workday worker record.
    `raw_data` holds the full SOAP response dict for any extra fields.
    """
    worker_id: str
    worker_wid: Optional[str]
    user_id: Optional[str]

    # Name
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    formatted_name: Optional[str]
    reporting_name: Optional[str]
    pref_formatted_name: Optional[str]
    pref_reporting_name: Optional[str]

    # Pronouns & demographics
    pronoun_id: Optional[str]
    birth_date: Optional[str]
    gender: Optional[str]
    hispanic_or_latino: Optional[bool]
    hispanic_or_latino_visual_survey: Optional[bool]
    ethnicity: Optional[str]
    tobacco_use: Optional[bool]

    # Email contact
    email: Optional[str]
    emails: Optional[List[str]]
    personal_email: Optional[str]  # Public=0 (personal email)
    corporate_email: Optional[str]  # Public=1 (work email)
    email_usage_public: Optional[bool]
    email_id: Optional[str]

    # Address contact
    address: Optional[str]
    address_effective_date: Optional[str]
    address_format_type: Optional[str]
    defaulted_business_site_address: Optional[bool]
    address_line: Optional[str]
    address_line_descriptor: Optional[str]
    municipality: Optional[str]
    country_region_descriptor: Optional[str]
    postal_code: Optional[str]
    address_usage_public: Optional[bool]
    address_number_of_days: Optional[int]
    address_id: Optional[str]
    state_code: Optional[str]
    country_code: Optional[str]

    # Phone contact
    phone: Optional[str]
    phone_area_code: Optional[str]
    phone_number_wo_area: Optional[str]
    phone_traditional: Optional[str]
    phone_national: Optional[str]
    phone_international: Optional[str]
    phone_tenant: Optional[str]
    phone_device_type_id: Optional[str]
    phone_usage_public: Optional[bool]
    phone_id: Optional[str]

    # Identification
    national_id: Optional[str]
    national_id_type_code: Optional[str]
    national_id_shared_reference: Optional[str]
    license_id: Optional[str]
    license_type_id: Optional[str]
    license_state_code: Optional[str]
    license_issued_date: Optional[str]
    license_expiration_date: Optional[str]
    custom_ids: Optional[Dict[str, Any]]
    custom_id_shared_references: Optional[Dict[str, str]]
    associate_oid: Optional[str]
    adp_payroll_id: Optional[str]
    adp_payroll_group: Optional[str]
    old_corporate_email: Optional[str]

    # Employment & benefits
    wage: Optional[float]
    benefit_enrollments: Optional[List[str]]
    roles: Optional[List[str]]
    worker_documents: Optional[List[str]]

    # Compensation
    compensation_effective_date: Optional[str]
    reason_references: Optional[Dict[str, str]]
    compensation_guidelines: Optional[Dict[str, Any]]
    salary_and_hourly: Optional[List[Dict[str, Any]]]
    compensation_summary: Optional[Dict[str, Any]]

    # Employment Data (New)
    position_id: Optional[str]
    position_title: Optional[str]
    business_title: Optional[str]
    start_date: Optional[date]
    end_employment_date: Optional[date]
    position_effective_date: Optional[date]
    worker_type: Optional[str]
    position_time_type: Optional[str]
    job_exempt: Optional[bool]
    scheduled_weekly_hours: Optional[float]
    default_weekly_hours: Optional[float]
    full_time_equivalent_percentage: Optional[float]
    pay_rate_type: Optional[str]
    job_profile_id: Optional[str]
    job_profile_name: Optional[str]
    management_level: Optional[str]
    job_family: Optional[List[str]]

    # Worker Status (New)
    active: Optional[bool]
    active_status_date: Optional[date]
    hire_date: Optional[date]
    original_hire_date: Optional[date]
    first_day_of_work: Optional[date]
    seniority_date: Optional[date]
    terminated: Optional[bool]
    termination_date: Optional[date]
    pay_through_date: Optional[date]
    termination_reason: Optional[str]
    termination_category: Optional[str]
    termination_involuntary: Optional[bool]
    eligible_for_hire: Optional[bool]
    regrettable_termination: Optional[bool]
    eligible_for_rehire: Optional[bool]
    termination_last_day_of_work: Optional[date]

    # Business Site Data (New)
    business_site_name: Optional[str]
    business_site_location_id: Optional[str]
    business_site_address: Optional[Dict[str, Any]]

    # Management Chain Data (New)
    management_chain: Optional[List[ManagementChainLevel]]
    direct_manager_id: Optional[str]
    direct_manager_name: Optional[str]
    matrix_management_chain: Optional[List[ManagementChainLevel]]

    # Payroll and Tax Data (New)
    federal_withholding_fein: Optional[str]
    workers_compensation_code: Optional[str]
    payroll_frequency: Optional[str]
    last_detected_manager_id: Optional[str]
    last_detected_manager_name: Optional[str]
    
    # Organizations
    organizations: Optional[List[Dict[str, Any]]]
    primary_organization_id: Optional[str]
    primary_organization_name: Optional[str]
    primary_organization_type: Optional[str]
    primary_organization_code: Optional[str]
    company_id: Optional[str]
    company_name: Optional[str]
    cost_center_id: Optional[str]
    cost_center_name: Optional[str]
    cost_center_hierarchy_name: Optional[str]
    pay_group_id: Optional[str]
    pay_group_name: Optional[str]
    supervisory_organization_id: Optional[str]
    supervisory_organization_name: Optional[str]

    # raw payload
    raw_data: Dict[str, Any] = Field(..., exclude=True)

    @validator("*", pre=True)
    def _convert_decimal(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v

    class Config:
        extra = "ignore" 