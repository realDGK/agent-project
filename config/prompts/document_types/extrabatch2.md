Document Type: Trustee's Deed
Folder: /document_types/trustee-s-deed/

1. Specialist Schema
File: trustee-s-deed.SS.json

JSON

{
  "title": "Trustee's Deed Upon Sale Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "effective_date": { "type": "string", "format": "date" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Trustee", "Grantee", "Purchaser"] }
        },
        "required": ["name", "role"]
      }
    },
    "deed_details": {
      "type": "object",
      "properties": {
        "deed_type": { "type": "string" },
        "property_legal_description": { "type": "string" },
        "apn": { "type": "string" },
        "sale_amount": { "type": "number" },
        "original_trustor": { "type": "string" },
        "original_beneficiary": { "type": "string" },
        "deed_of_trust_recording_info": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "deed_details"]
}
2. Few-Shot Example
File: trustee-s-deed.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
TRUSTEE'S DEED UPON SALE

This Trustee's Deed is made on October 20, 2027, by Quality Trustee Services, a California corporation, as Trustee, to Evergreen Investments, LLC, a Delaware limited liability company, the Purchaser.

This conveyance is made pursuant to a sale conducted under the Deed of Trust executed by Original Trustor, John Doe, recorded on June 1, 2020, as Instrument No. 2020-123456, Official Records of Alameda County, California. The property, APN 987-654-321, is described in Exhibit A. The amount of the successful bid was $850,000.

**JSON OUTPUT:**
{
  "contract_name": "Trustee's Deed Upon Sale",
  "effective_date": "2027-10-20",
  "parties": [
    { "name": "Quality Trustee Services", "role": "Trustee" },
    { "name": "Evergreen Investments, LLC", "role": "Purchaser" }
  ],
  "deed_details": {
    "deed_type": "Trustee's Deed Upon Sale",
    "property_legal_description": "Described in Exhibit A",
    "apn": "987-654-321",
    "sale_amount": 850000,
    "original_trustor": "John Doe",
    "original_beneficiary": null,
    "deed_of_trust_recording_info": "Instrument No. 2020-123456, Official Records of Alameda County, California"
  }
}
3. Schema Additions
File: trustee-s-deed.SA.json

JSON

{
    "deed_details": {
      "type": "object",
      "description": "Details specific to a deed transferring title to real property.",
      "properties": {
        "deed_type": { "type": "string" },
        "property_legal_description": { "type": "string" },
        "apn": { "type": "string" },
        "transfer_tax_amount": { "type": "number" },
        "sale_amount": { "type": "number" },
        "original_trustor": { "type": "string" },
        "original_beneficiary": { "type": "string" },
        "deed_of_trust_recording_info": { "type": "string" }
      }
    }
}
Document Type: Tree Protection Removal Plans
Folder: /document_types/tree-protection-removal-plans/

1. Specialist Schema
File: tree-protection-removal-plans.SS.json

JSON

{
  "title": "Tree Plan Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "effective_date": { "type": "string", "format": "date" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Developer", "Arborist", "City"] }
        },
        "required": ["name", "role"]
      }
    },
    "plan_details": {
      "type": "object",
      "properties": {
        "project_name": { "type": "string" },
        "plan_type": { "type": "string" },
        "trees_to_be_removed_summary": { "type": "string" },
        "trees_to_be_protected_summary": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "plan_details"]
}
2. Few-Shot Example
File: tree-protection-removal-plans.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
ARBORIST REPORT & TREE PROTECTION PLAN
For: The Oak Knoll Subdivision Project
Date: November 5, 2027
Prepared by: Certified Arborist, Susan Jones (#WE-1234A)

This report details the survey of 50 trees on the project site.
Trees to be Removed: A total of 5 trees are designated for removal as shown on the plan, including three (3) Coast Live Oaks and two (2) Monterey Pines.
Trees to be Preserved: All remaining 45 trees shall be protected. Fencing shall be installed at the designated tree protection zone (TPZ) prior to any grading.

**JSON OUTPUT:**
{
  "contract_name": "Arborist Report & Tree Protection Plan",
  "effective_date": "2027-11-05",
  "parties": [
    { "name": "Susan Jones", "role": "Arborist" }
  ],
  "plan_details": {
    "project_name": "The Oak Knoll Subdivision Project",
    "plan_type": "Tree Protection and Removal",
    "trees_to_be_removed_summary": "5 trees total: three (3) Coast Live Oaks and two (2) Monterey Pines.",
    "trees_to_be_protected_summary": "45 trees shall be protected with fencing at the tree protection zone (TPZ)."
  }
}
3. Schema Additions
File: tree-protection-removal-plans.SA.json

JSON

{
  "plan_details": {
    "type": "object",
    "description": "Details specific to engineering, architectural, or site plans.",
    "properties": {
      "project_name": { "type": "string" },
      "plan_type": { "type": "string" },
      "engineer_of_record": { "type": "string" },
      "approval_date": { "type": "string", "format": "date" },
      "plan_sheet_count": { "type": "integer" },
      "trees_to_be_removed_summary": { "type": "string" },
      "trees_to_be_protected_summary": { "type": "string" }
    }
  }
}
Document Type: Topographic Boundary Surveys
Folder: /document_types/topographic-boundary-surveys/

1. Specialist Schema
File: topographic-boundary-surveys.SS.json

JSON

{
  "title": "Survey Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "effective_date": { "type": "string", "format": "date" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Client", "Surveyor"] }
        },
        "required": ["name", "role"]
      }
    },
    "survey_details": {
      "type": "object",
      "properties": {
        "property_address": { "type": "string" },
        "property_legal_description": { "type": "string" },
        "apn": { "type": "string" },
        "survey_type": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "survey_details"]
}
2. Few-Shot Example
File: topographic-boundary-surveys.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
TOPOGRAPHIC & BOUNDARY SURVEY
A survey of Lot 5 of the Evergreen Tract, in the City of Walnut Creek, County of Contra Costa, State of California.
APN: 123-456-005
Job No: 27-042
Date: December 1, 2027
Prepared for: Westpark Homes
Prepared by: Apex Land Surveying, Inc. PLS 9876

**JSON OUTPUT:**
{
  "contract_name": "Topographic & Boundary Survey",
  "effective_date": "2027-12-01",
  "parties": [
    { "name": "Westpark Homes", "role": "Client" },
    { "name": "Apex Land Surveying, Inc.", "role": "Surveyor" }
  ],
  "survey_details": {
    "property_address": null,
    "property_legal_description": "Lot 5 of the Evergreen Tract, in the City of Walnut Creek, County of Contra Costa, State of California.",
    "apn": "123-456-005",
    "survey_type": "Topographic & Boundary"
  }
}
3. Schema Additions
File: topographic-boundary-surveys.SA.json

JSON

{
  "survey_details": {
    "type": "object",
    "description": "Details specific to a land survey.",
    "properties": {
      "property_address": { "type": "string" },
      "property_legal_description": { "type": "string" },
      "apn": { "type": "string" },
      "flood_zone_information": { "type": "string" },
      "zoning_classification": { "type": "string" },
      "table_a_items": {
        "type": "array",
        "items": { "type": "string" },
        "description": "A list of the optional ALTA Table A items included in the survey."
      },
      "survey_type": { "type": "string" }
    }
  }
}
Document Type: Notice of Trustee's Sale
Folder: /document_types/notice-of-trustee-s-sale/

1. Specialist Schema
File: notice-of-trustee-s-sale.SS.json

JSON

{
  "title": "Notice of Trustee's Sale Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Trustor", "Beneficiary", "Trustee"] }
        },
        "required": ["name", "role"]
      }
    },
    "foreclosure_details": {
      "type": "object",
      "properties": {
        "property_address": { "type": "string" },
        "apn": { "type": "string" },
        "sale_date": { "type": "string", "format": "date" },
        "sale_time": { "type": "string" },
        "sale_location": { "type": "string" },
        "unpaid_balance": { "type": "number" }
      }
    }
  },
  "required": ["contract_name", "parties", "foreclosure_details"]
}
2. Few-Shot Example
File: notice-of-trustee-s-sale.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
NOTICE OF TRUSTEE'S SALE
TS No. 12345-CA APN: 111-222-333

YOU ARE IN DEFAULT UNDER A DEED OF TRUST DATED 1/15/2020.
NOTICE IS HEREBY GIVEN that a public auction will be held on 1/10/2028, at 10:00 AM at the main entrance to the County Courthouse, 123 Main Street, Anytown, CA. The property to be sold is commonly known as 456 Oak Lane, Anytown, CA. The unpaid balance of the obligation secured by the property is $550,000.00. The original Trustor was John Borrower.

**JSON OUTPUT:**
{
  "contract_name": "Notice of Trustee's Sale",
  "parties": [
    { "name": "John Borrower", "role": "Trustor" }
  ],
  "foreclosure_details": {
    "property_address": "456 Oak Lane, Anytown, CA",
    "apn": "111-222-333",
    "sale_date": "2028-01-10",
    "sale_time": "10:00 AM",
    "sale_location": "The main entrance to the County Courthouse, 123 Main Street, Anytown, CA",
    "unpaid_balance": 550000
  }
}
3. Schema Additions
File: notice-of-trustee-s-sale.SA.json

JSON

{
  "foreclosure_details": {
    "type": "object",
    "description": "Details specific to a foreclosure proceeding.",
    "properties": {
      "property_address": { "type": "string" },
      "apn": { "type": "string" },
      "sale_date": { "type": "string", "format": "date" },
      "sale_time": { "type": "string" },
      "sale_location": { "type": "string" },
      "unpaid_balance": { "type": "number" }
    }
  }
}
Document Type: Notice of Tax Sale
Folder: /document_types/notice-of-tax-sale/

1. Specialist Schema
File: notice-of-tax-sale.SS.json

JSON

{
  "title": "Notice of Tax Sale Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Assessee", "Taxing Authority"] }
        },
        "required": ["name", "role"]
      }
    },
    "tax_sale_details": {
      "type": "object",
      "properties": {
        "property_address": { "type": "string" },
        "apn": { "type": "string" },
        "sale_date": { "type": "string", "format": "date" },
        "sale_location": { "type": "string" },
        "minimum_bid": { "type": "number" }
      }
    }
  },
  "required": ["contract_name", "parties", "tax_sale_details"]
}
2. Few-Shot Example
File: notice-of-tax-sale.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
NOTICE OF PUBLIC AUCTION FOR TAX-DEFAULTED PROPERTY
Sale No. 2028-01. County of Marin Tax Collector.

Notice is hereby given that on February 15, 2028, the Tax Collector will sell the property assessed to Jane Owner, APN 444-555-666, at public auction. The minimum bid for the property, located at 789 Pine Street, Sausalito, CA, is $52,100.00. The sale will be conducted online at www.marintax.com.

**JSON OUTPUT:**
{
  "contract_name": "Notice of Public Auction for Tax-Defaulted Property",
  "parties": [
    { "name": "Jane Owner", "role": "Assessee" },
    { "name": "County of Marin Tax Collector", "role": "Taxing Authority" }
  ],
  "tax_sale_details": {
    "property_address": "789 Pine Street, Sausalito, CA",
    "apn": "444-555-666",
    "sale_date": "2028-02-15",
    "sale_location": "Online at www.marintax.com",
    "minimum_bid": 52100
  }
}
3. Schema Additions
File: notice-of-tax-sale.SA.json

JSON

{
  "tax_sale_details": {
    "type": "object",
    "description": "Details specific to a sale of property for delinquent taxes.",
    "properties": {
      "property_address": { "type": "string" },
      "apn": { "type": "string" },
      "sale_date": { "type": "string", "format": "date" },
      "sale_location": { "type": "string" },
      "minimum_bid": { "type": "number" }
    }
  }
}