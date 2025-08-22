Document Type: Net Metering Agreements
Folder: /document_types/net-metering-agreements/

1. Specialist Schema
File: net-metering-agreements.SS.json

JSON

{
  "title": "Net Metering Agreement Extraction",
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
          "role": { "type": "string", "enum": ["Customer-Generator", "Utility"] }
        },
        "required": ["name", "role"]
      }
    },
    "net_metering_details": {
      "type": "object",
      "properties": {
        "service_account_number": { "type": "string" },
        "generating_facility_address": { "type": "string" },
        "generator_type": { "type": "string" },
        "system_capacity_kw": { "type": "number" },
        "net_surplus_compensation_rate": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "net_metering_details"]
}
2. Few-Shot Example
File: net-metering-agreements.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
NET ENERGY METERING (NEM) AGREEMENT

This Agreement is made on January 15, 2028, between San Diego Gas & Electric ("Utility") and The Lofts at Market Street LLC ("Customer-Generator").

Service Account: 555-1234
Facility Location: 789 Market St, San Diego, CA
Generator Technology: Solar Photovoltaic
System Capacity: 75 kW

Any net surplus generation at the end of a 12-month period will be compensated at the net surplus compensation (NSC) rate as determined by the CPUC.

**JSON OUTPUT:**
{
  "contract_name": "Net Energy Metering (NEM) Agreement",
  "effective_date": "2028-01-15",
  "parties": [
    { "name": "San Diego Gas & Electric", "role": "Utility" },
    { "name": "The Lofts at Market Street LLC", "role": "Customer-Generator" }
  ],
  "net_metering_details": {
    "service_account_number": "555-1234",
    "generating_facility_address": "789 Market St, San Diego, CA",
    "generator_type": "Solar Photovoltaic",
    "system_capacity_kw": 75,
    "net_surplus_compensation_rate": "Net surplus compensation (NSC) rate as determined by the CPUC."
  }
}
3. Schema Additions
File: net-metering-agreements.SA.json

JSON

{
  "net_metering_details": {
    "type": "object",
    "description": "Details specific to a net energy metering (NEM) agreement for customer-owned power generation.",
    "properties": {
      "service_account_number": { "type": "string" },
      "generating_facility_address": { "type": "string" },
      "generator_type": { "type": "string" },
      "system_capacity_kw": { "type": "number" },
      "net_surplus_compensation_rate": { "type": "string" }
    }
  }
}
Document Type: Monument Records
Folder: /document_types/monument-records/

1. Specialist Schema
File: monument-records.SS.json

JSON

{
  "title": "Monument Record Extraction",
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
          "role": { "type": "string", "enum": ["Surveyor", "Public Agency"] }
        },
        "required": ["name", "role"]
      }
    },
    "survey_details": {
      "type": "object",
      "properties": {
        "monument_description": { "type": "string" },
        "monument_location": { "type": "string" },
        "surveyor_license_number": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "survey_details"]
}
2. Few-Shot Example
File: monument-records.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
CORNER RECORD - County of Sacramento
Document No. 2028-001234

A 2-inch brass cap in a monument well was found at the centerline intersection of Main Street and Oak Avenue, as shown on that certain map "Tract No. 500". The cap was found undisturbed and in good condition.

Statement of Surveyor:
This corner record was prepared by me on February 2, 2028.
James Peterson, PLS 8765

**JSON OUTPUT:**
{
  "contract_name": "Corner Record",
  "effective_date": "2028-02-02",
  "parties": [
    { "name": "James Peterson", "role": "Surveyor" },
    { "name": "County of Sacramento", "role": "Public Agency" }
  ],
  "survey_details": {
    "monument_description": "2-inch brass cap in a monument well.",
    "monument_location": "Centerline intersection of Main Street and Oak Avenue, as shown on map 'Tract No. 500'.",
    "surveyor_license_number": "PLS 8765"
  }
}
3. Schema Additions
File: monument-records.SA.json

JSON

{
  "survey_details": {
    "type": "object",
    "description": "Details specific to a land survey.",
    "properties": {
      "property_address": { "type": "string" },
      "property_legal_description": { "type": "string" },
      "apn": { "type": "string" },
      "survey_type": { "type": "string" },
      "monument_description": { "type": "string" },
      "monument_location": { "type": "string" },
      "surveyor_license_number": { "type": "string" }
    }
  }
}
Document Type: Meter Set Requests
Folder: /document_types/meter-set-requests/

1. Specialist Schema
File: meter-set-requests.SS.json

JSON

{
  "title": "Meter Set Request Extraction",
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
          "role": { "type": "string", "enum": ["Applicant", "Utility"] }
        },
        "required": ["name", "role"]
      }
    },
    "utility_service_details": {
      "type": "object",
      "properties": {
        "service_address": { "type": "string" },
        "meter_type_requested": { "type": "string" },
        "service_type": { "type": "string", "description": "e.g., 'Electric', 'Water', 'Gas'" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "utility_service_details"]
}
2. Few-Shot Example
File: meter-set-requests.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
APPLICATION FOR WATER METER INSTALLATION
City of Pleasanton

Date: March 10, 2028
Applicant: Bright Homes LLC
Service Address: 123 New Development Circle, Lot 5, Pleasanton, CA

We hereby request the installation of one (1) 3/4-inch domestic water meter to serve the single-family residence at the above address.

**JSON OUTPUT:**
{
  "contract_name": "Application for Water Meter Installation",
  "effective_date": "2028-03-10",
  "parties": [
    { "name": "Bright Homes LLC", "role": "Applicant" },
    { "name": "City of Pleasanton", "role": "Utility" }
  ],
  "utility_service_details": {
    "service_address": "123 New Development Circle, Lot 5, Pleasanton, CA",
    "meter_type_requested": "3/4-inch domestic water meter",
    "service_type": "Water"
  }
}
3. Schema Additions
File: meter-set-requests.SA.json

JSON

{
  "utility_service_details": {
    "type": "object",
    "description": "Details specific to utility service letters and agreements.",
    "properties": {
      "utility_type": { "type": "string" },
      "project_name": { "type": "string" },
      "service_commitment": { "type": "string" },
      "conditions_of_service": { "type": "string" },
      "service_address": { "type": "string" },
      "meter_type_requested": { "type": "string" },
      "service_type": { "type": "string" }
    }
  }
}
Document Type: Mediation Arbitration Agreements
Folder: /document_types/mediation-arbitration-agreements/

1. Specialist Schema
File: mediation-arbitration-agreements.SS.json

JSON

{
  "title": "ADR Agreement Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "effective_date": { "type": "string", "format": "date" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": { "name": { "type": "string" } }
      }
    },
    "dispute_resolution_details": {
      "type": "object",
      "properties": {
        "adr_type": { "type": "string", "enum": ["Mediation", "Arbitration", "Mediation-Arbitration"] },
        "dispute_subject_matter": { "type": "string" },
        "is_binding": { "type": "boolean" },
        "governing_rules": { "type": "string", "description": "e.g., 'JAMS', 'AAA Commercial Rules'" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "dispute_resolution_details"]
}
2. Few-Shot Example
File: mediation-arbitration-agreements.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
AGREEMENT TO SUBMIT TO BINDING ARBITRATION

This Agreement is made April 20, 2028, between Riverstone Builders and the Parkside HOA.

The parties agree to submit their dispute concerning construction defects to final and binding arbitration. The arbitration shall be administered by JAMS pursuant to its Comprehensive Arbitration Rules and Procedures.

**JSON OUTPUT:**
{
  "contract_name": "Agreement to Submit to Binding Arbitration",
  "effective_date": "2028-04-20",
  "parties": [
    { "name": "Riverstone Builders" },
    { "name": "Parkside HOA" }
  ],
  "dispute_resolution_details": {
    "adr_type": "Arbitration",
    "dispute_subject_matter": "Construction defects",
    "is_binding": true,
    "governing_rules": "JAMS Comprehensive Arbitration Rules and Procedures"
  }
}
3. Schema Additions
File: mediation-arbitration-agreements.SA.json

JSON

{
  "dispute_resolution_details": {
    "type": "object",
    "description": "Details specific to alternative dispute resolution (ADR) agreements.",
    "properties": {
      "adr_type": { "type": "string", "enum": ["Mediation", "Arbitration", "Mediation-Arbitration"] },
      "dispute_subject_matter": { "type": "string" },
      "is_binding": { "type": "boolean" },
      "governing_rules": { "type": "string", "description": "e.g., 'JAMS', 'AAA Commercial Rules'" }
    }
  }
}
Document Type: Judgments
Folder: /document_types/judgments/

1. Specialist Schema
File: judgments.SS.json

JSON

{
  "title": "Judgment Extraction",
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
          "role": { "type": "string", "enum": ["Plaintiff", "Defendant", "Judgment Creditor", "Judgment Debtor"] }
        },
        "required": ["name", "role"]
      }
    },
    "litigation_details": {
      "type": "object",
      "properties": {
        "court_name": { "type": "string" },
        "case_number": { "type": "string" },
        "judgment_summary": { "type": "string" },
        "judgment_amount": { "type": "number" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "litigation_details"]
}
2. Few-Shot Example
File: judgments.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
JUDGMENT
Case Number: CIV-2027-9876
In the matter of: Prime Lenders, Plaintiff, vs. John Borrower, Defendant.

IT IS HEREBY ORDERED AND ADJUDGED that judgment is entered in favor of Plaintiff Prime Lenders and against Defendant John Borrower in the principal amount of $150,000.00, plus interest and costs.

Dated: May 5, 2028
(Signature)
Judge of the Superior Court

**JSON OUTPUT:**
{
  "contract_name": "Judgment",
  "effective_date": "2028-05-05",
  "parties": [
    { "name": "Prime Lenders", "role": "Plaintiff" },
    { "name": "John Borrower", "role": "Defendant" }
  ],
  "litigation_details": {
    "court_name": "Superior Court",
    "case_number": "CIV-2027-9876",
    "judgment_summary": "Judgment entered in favor of Plaintiff and against Defendant.",
    "judgment_amount": 150000
  }
}
3. Schema Additions
File: judgments.SA.json

JSON

{
  "litigation_details": {
    "type": "object",
    "description": "Details specific to litigation, court filings, and legal disputes.",
    "properties": {
      "court_name": { "type": "string" },
      "case_number": { "type": "string" },
      "judgment_summary": { "type": "string" },
      "judgment_amount": { "type": "number" }
    }
  }
}

Document Type: GIS Imagery 3D Models
Folder: /document_types/gis-imagery-3d-models/

1. Specialist Schema
File: gis-imagery-3d-models.SS.json

JSON

{
  "title": "GIS & Model Data Extraction",
  "type": "object",
  "properties": {
    "contract_name": {
      "type": "string",
      "description": "The name or title of the dataset."
    },
    "effective_date": {
      "type": "string",
      "format": "date",
      "description": "The creation or publication date of the data."
    },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": {
            "type": "string",
            "enum": ["Creator", "Owner", "Client"]
          }
        },
        "required": ["name", "role"]
      }
    },
    "gis_details": {
      "type": "object",
      "properties": {
        "data_type": {
          "type": "string",
          "enum": ["Aerial Photo", "LiDAR", "GIS Layer", "3D Model", "BIM"]
        },
        "project_name": { "type": "string" },
        "geographic_coverage": { "type": "string" },
        "coordinate_system": { "type": "string" },
        "file_format": { "type": "string", "description": "e.g., 'Shapefile', '.dwg', '.rvt', '.tif'" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "gis_details"]
}
2. Few-Shot Example
File: gis-imagery-3d-models.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
METADATA
Dataset: Riverbend Project - 2027 Aerial Imagery
Date of Capture: 2027-06-10
Description: 3-inch resolution orthorectified aerial imagery of the Riverbend project site.
Format: GeoTIFF
Projection: NAD 1983 StatePlane California III FIPS 0403 Feet
Source: Eagle Eye Aerials for Riverbend Development Corp.

**JSON OUTPUT:**
{
  "contract_name": "Riverbend Project - 2027 Aerial Imagery",
  "effective_date": "2027-06-10",
  "parties": [
    { "name": "Eagle Eye Aerials", "role": "Creator" },
    { "name": "Riverbend Development Corp.", "role": "Client" }
  ],
  "gis_details": {
    "data_type": "Aerial Photo",
    "project_name": "Riverbend Project",
    "geographic_coverage": "Riverbend project site",
    "coordinate_system": "NAD 1983 StatePlane California III FIPS 0403 Feet",
    "file_format": "GeoTIFF"
  }
}
3. Schema Additions
File: gis-imagery-3d-models.SA.json

JSON

{
  "gis_details": {
    "type": "object",
    "description": "Details specific to GIS data, imagery, or 3D models.",
    "properties": {
      "data_type": {
        "type": "string",
        "enum": ["Aerial Photo", "LiDAR", "GIS Layer", "3D Model", "BIM"]
      },
      "project_name": { "type": "string" },
      "geographic_coverage": { "type": "string" },
      "coordinate_system": { "type": "string" },
      "file_format": { "type": "string", "description": "e.g., 'Shapefile', '.dwg', '.rvt', '.tif'" }
    }
  }
}
Document Type: Geotech Reports Update Letters
Folder: /document_types/geotech-reports-update-letters/

1. Specialist Schema
File: geotech-reports-update-letters.SS.json

JSON

{
  "title": "Geotechnical Report Extraction",
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
          "role": { "type": "string", "enum": ["Client", "Geotechnical Engineer"] }
        },
        "required": ["name", "role"]
      }
    },
    "technical_report_details": {
      "type": "object",
      "properties": {
        "project_name": { "type": "string" },
        "report_type": { "type": "string", "enum": ["Geotechnical Investigation", "Soils Report", "Update Letter"] },
        "site_address": { "type": "string" },
        "key_findings": { "type": "string" },
        "recommendations_summary": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "technical_report_details"]
}
2. Few-Shot Example
File: geotech-reports-update-letters.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
GEOTECHNICAL INVESTIGATION UPDATE
Date: July 22, 2027
Project No: 12345
Project: Proposed Retail Center at 456 Commerce Way, Irvine, CA
To: Premier Properties

This letter presents an update to our Geotechnical Investigation dated May 1, 2026. Based on a review of the revised grading plans, our original recommendations for foundation design and soil compaction remain valid. No significant changes are required.

**JSON OUTPUT:**
{
  "contract_name": "Geotechnical Investigation Update",
  "effective_date": "2027-07-22",
  "parties": [
    { "name": "Premier Properties", "role": "Client" }
  ],
  "technical_report_details": {
    "project_name": "Proposed Retail Center",
    "report_type": "Update Letter",
    "site_address": "456 Commerce Way, Irvine, CA",
    "key_findings": "Original recommendations remain valid after review of revised grading plans.",
    "recommendations_summary": "No significant changes are required."
  }
}
3. Schema Additions
File: geotech-reports-update-letters.SA.json

JSON

{
  "technical_report_details": {
    "type": "object",
    "description": "Details specific to a technical or engineering report.",
    "properties": {
      "project_name": { "type": "string" },
      "report_type": { "type": "string" },
      "recommendations_summary": { "type": "string" },
      "site_address": { "type": "string" },
      "key_findings": { "type": "string" }
    }
  }
}
Document Type: Eviction Unlawful Detainer Filings
Folder: /document_types/eviction-unlawful-detainer-filings/

1. Specialist Schema
File: eviction-unlawful-detainer-filings.SS.json

JSON

{
  "title": "Unlawful Detainer Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string", "description": "e.g., 'Complaint for Unlawful Detainer'" },
    "effective_date": { "type": "string", "format": "date", "description": "The date the filing was submitted to the court." },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Plaintiff", "Defendant", "Landlord", "Tenant"] }
        },
        "required": ["name", "role"]
      }
    },
    "litigation_details": {
      "type": "object",
      "properties": {
        "court_name": { "type": "string" },
        "case_number": { "type": "string" },
        "property_address": { "type": "string" },
        "reason_for_eviction": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "litigation_details"]
}
2. Few-Shot Example
File: eviction-unlawful-detainer-filings.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
COMPLAINT - UNLAWFUL DETAINER
Case Number: 28-UC-12345
Court: Superior Court of California, County of Orange

Plaintiff: Oak Tree Apartments, LLC
Defendant: Robert Miller

1. Plaintiff is the owner of the property at 100 Main St, Apt 2B, Irvine, CA.
2. Defendant is in possession of the premises.
3. Defendant has failed to pay rent due for the month of August 2028.
Dated: August 20, 2028

**JSON OUTPUT:**
{
  "contract_name": "Complaint - Unlawful Detainer",
  "effective_date": "2028-08-20",
  "parties": [
    { "name": "Oak Tree Apartments, LLC", "role": "Plaintiff" },
    { "name": "Robert Miller", "role": "Defendant" }
  ],
  "litigation_details": {
    "court_name": "Superior Court of California, County of Orange",
    "case_number": "28-UC-12345",
    "property_address": "100 Main St, Apt 2B, Irvine, CA",
    "reason_for_eviction": "Failure to pay rent for August 2028."
  }
}
3. Schema Additions
File: eviction-unlawful-detainer-filings.SA.json

JSON

{
  "litigation_details": {
    "type": "object",
    "description": "Details specific to litigation, court filings, and legal disputes.",
    "properties": {
      "court_name": { "type": "string" },
      "case_number": { "type": "string" },
      "property_address": { "type": "string" },
      "reason_for_eviction": { "type": "string" }
    }
  }
}
Document Type: Encroachment Maintenance Agreements
Folder: /document_types/encroachment-maintenance-agreements/

1. Specialist Schema
File: encroachment-maintenance-agreements.SS.json

JSON

{
  "title": "Encroachment Maintenance Agreement Extraction",
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
          "role": { "type": "string", "enum": ["Property Owner", "Encroaching Party", "Public Agency"] }
        },
        "required": ["name", "role"]
      }
    },
    "encroachment_details": {
      "type": "object",
      "properties": {
        "description_of_encroachment": { "type": "string" },
        "location_of_encroachment": { "type": "string" },
        "maintenance_responsibility": { "type": "string" },
        "is_revocable": { "type": "boolean" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "encroachment_details"]
}
2. Few-Shot Example
File: encroachment-maintenance-agreements.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
ENCROACHMENT MAINTENANCE AND REMOVAL AGREEMENT
This Agreement is made on September 5, 2028, between the City of Walnut Creek ("City") and Maplewood Center LLC ("Owner").

Owner desires to install and maintain a decorative sign and landscaping which will encroach into the public right-of-way adjacent to its property at 123 Maple St. Owner agrees to maintain the encroachment in good condition at its sole expense. The City reserves the right to revoke this permit at any time.

**JSON OUTPUT:**
{
  "contract_name": "Encroachment Maintenance and Removal Agreement",
  "effective_date": "2028-09-05",
  "parties": [
    { "name": "City of Walnut Creek", "role": "Public Agency" },
    { "name": "Maplewood Center LLC", "role": "Owner" }
  ],
  "encroachment_details": {
    "description_of_encroachment": "Decorative sign and landscaping.",
    "location_of_encroachment": "Public right-of-way adjacent to 123 Maple St.",
    "maintenance_responsibility": "Owner shall maintain the encroachment at its sole expense.",
    "is_revocable": true
  }
}
3. Schema Additions
File: encroachment-maintenance-agreements.SA.json

JSON

{
  "encroachment_details": {
    "type": "object",
    "description": "Details specific to an encroachment agreement.",
    "properties": {
      "encroaching_property_owner": { "type": "string" },
      "encroached_upon_property_owner": { "type": "string" },
      "description_of_encroachment": { "type": "string" },
      "permission_granted": { "type": "string" },
      "is_revocable": { "type": "boolean" },
      "location_of_encroachment": { "type": "string" },
      "maintenance_responsibility": { "type": "string" }
    }
  }
}
Document Type: Easement Sketches Legal Exhibits
Folder: /document_types/easement-sketches-legal-exhibits/

1. Specialist Schema
File: easement-sketches-legal-exhibits.SS.json

JSON

{
  "title": "Easement Exhibit Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string", "description": "e.g., 'Exhibit A', 'Legal Description of Easement'" },
    "effective_date": { "type": "string", "format": "date" },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Surveyor", "Engineer"] }
        }
      }
    },
    "map_details": {
      "type": "object",
      "properties": {
        "property_legal_description": { "type": "string" },
        "apn": { "type": "string" },
        "purpose_of_exhibit": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "map_details"]
}
2. Few-Shot Example
File: easement-sketches-legal-exhibits.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
EXHIBIT 'B'
LEGAL DESCRIPTION OF PUBLIC UTILITY EASEMENT

A strip of land, 10 feet in width, over a portion of Lot 2 as shown on that certain map entitled "Tract 9000", filed for record in Book 123 of Maps, at Page 45, Official Records of Orange County, California.
APN: 987-654-002

Prepared by: Compass Land Surveying
Date: October 1, 2028

**JSON OUTPUT:**
{
  "contract_name": "Exhibit 'B' - Legal Description of Public Utility Easement",
  "effective_date": "2028-10-01",
  "parties": [
    { "name": "Compass Land Surveying", "role": "Surveyor" }
  ],
  "map_details": {
    "property_legal_description": "A strip of land, 10 feet in width, over a portion of Lot 2 as shown on that certain map entitled \"Tract 9000\", filed for record in Book 123 of Maps, at Page 45, Official Records of Orange County, California.",
    "apn": "987-654-002",
    "purpose_of_exhibit": "Legal Description of Public Utility Easement"
  }
}
3. Schema Additions
File: easement-sketches-legal-exhibits.SA.json

JSON

{
  "map_details": {
    "type": "object",
    "description": "Details specific to maps, plats, and legal descriptions.",
    "properties": {
      "property_legal_description": { "type": "string" },
      "apn": { "type": "string" },
      "purpose_of_exhibit": { "type": "string" }
    }
  }
}


Document Type: Discovery (RFPs/ROGs/RFAs)
Folder: /document_types/discovery-rfps-rogs-rfas/

1. Specialist Schema
File: discovery-rfps-rogs-rfas.SS.json

JSON

{
  "title": "Discovery Request Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string", "description": "e.g., 'Request for Production of Documents', 'Interrogatories'" },
    "effective_date": { "type": "string", "format": "date", "description": "The date the request was served." },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Propounding Party", "Responding Party"] }
        },
        "required": ["name", "role"]
      }
    },
    "litigation_details": {
      "type": "object",
      "properties": {
        "court_name": { "type": "string" },
        "case_number": { "type": "string" }
      }
    },
    "discovery_details": {
      "type": "object",
      "properties": {
        "discovery_type": { "type": "string", "enum": ["Request for Production", "Special Interrogatories", "Request for Admissions"] },
        "response_due_date": { "type": "string", "format": "date" },
        "number_of_requests": { "type": "integer" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "discovery_details"]
}
2. Few-Shot Example
File: discovery-rfps-rogs-rfas.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
SUPERIOR COURT OF CALIFORNIA, COUNTY OF SAN FRANCISCO
Case No. CGC-28-123456

PROPOUNDING PARTY: WESTWOOD DEVELOPMENT, LLC
RESPONDING PARTY: CITY AND COUNTY OF SAN FRANCISCO
SET NO.: ONE

PLAINTIFF'S FIRST SET OF REQUESTS FOR PRODUCTION OF DOCUMENTS

Pursuant to the Code of Civil Procedure, Plaintiff requests that Defendant produce the documents described below for inspection and copying within 30 days. This set contains 25 requests.

Dated: June 10, 2028

**JSON OUTPUT:**
{
  "contract_name": "Plaintiff's First Set of Requests for Production of Documents",
  "effective_date": "2028-06-10",
  "parties": [
    { "name": "WESTWOOD DEVELOPMENT, LLC", "role": "Propounding Party" },
    { "name": "CITY AND COUNTY OF SAN FRANCISCO", "role": "Responding Party" }
  ],
  "litigation_details": {
    "court_name": "Superior Court of California, County of San Francisco",
    "case_number": "CGC-28-123456"
  },
  "discovery_details": {
    "discovery_type": "Request for Production",
    "response_due_date": null,
    "number_of_requests": 25
  }
}
3. Schema Additions
File: discovery-rfps-rogs-rfas.SA.json

JSON

{
  "discovery_details": {
    "type": "object",
    "description": "Details specific to a formal discovery request in litigation.",
    "properties": {
      "discovery_type": { "type": "string", "enum": ["Request for Production", "Special Interrogatories", "Request for Admissions"] },
      "response_due_date": { "type": "string", "format": "date" },
      "number_of_requests": { "type": "integer" }
    }
  }
}
Document Type: Declarations
Folder: /document_types/declarations/

1. Specialist Schema
File: declarations.SS.json

JSON

{
  "title": "Declaration Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string", "description": "e.g., 'Declaration of John Smith in Support of Motion'" },
    "effective_date": { "type": "string", "format": "date", "description": "The date the declaration was signed." },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Declarant", "Attorney"] }
        },
        "required": ["name", "role"]
      }
    },
    "litigation_details": {
      "type": "object",
      "properties": {
        "court_name": { "type": "string" },
        "case_number": { "type": "string" },
        "supporting": { "type": "string", "description": "The motion or purpose the declaration supports." }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "litigation_details"]
}
2. Few-Shot Example
File: declarations.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
DECLARATION OF JANE DOE
Case No. 12345

I, Jane Doe, declare as follows:
1. I am the project manager for the plaintiff in this action and have personal knowledge of the facts stated herein.
2. On May 1, 2028, I personally witnessed the defendant operating heavy machinery on the disputed property line.

I declare under penalty of perjury under the laws of the State of California that the foregoing is true and correct.
Executed on July 1, 2028, at San Jose, California.
(Signature)
Jane Doe

**JSON OUTPUT:**
{
  "contract_name": "Declaration of Jane Doe",
  "effective_date": "2028-07-01",
  "parties": [
    { "name": "Jane Doe", "role": "Declarant" }
  ],
  "litigation_details": {
    "court_name": null,
    "case_number": "12345",
    "supporting": null
  }
}
3. Schema Additions
File: declarations.SA.json

JSON

{
  "litigation_details": {
    "type": "object",
    "description": "Details specific to litigation, court filings, and legal disputes.",
    "properties": {
      "court_name": { "type": "string" },
      "case_number": { "type": "string" },
      "supporting": { "type": "string", "description": "The motion or purpose the declaration supports." }
    }
  }
}

Document Type: Abstracts of Judgment
Folder: /document_types/abstracts-of-judgment/

1. Specialist Schema
File: abstracts-of-judgment.SS.json

JSON

{
  "title": "Abstract of Judgment Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string", "description": "The name of the document, typically 'Abstract of Judgment'." },
    "effective_date": { "type": "string", "format": "date", "description": "The date the judgment was entered." },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Judgment Creditor", "Judgment Debtor"] }
        },
        "required": ["name", "role"]
      }
    },
    "litigation_details": {
      "type": "object",
      "properties": {
        "court_name": { "type": "string" },
        "case_number": { "type": "string" },
        "judgment_amount": { "type": "number" }
      }
    },
    "legal_recording_details": {
      "type": "object",
      "properties": {
        "county": { "type": "string" },
        "recording_date": { "type": "string", "format": "date" },
        "instrument_number": { "type": "string" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "litigation_details"]
}
2. Few-Shot Example
File: abstracts-of-judgment.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
RECORDING REQUESTED BY: ABC Law Group
WHEN RECORDED MAIL TO: ABC Law Group

ABSTRACT OF JUDGMENT
Case Number: 2027CV12345
Court: Superior Court of California, County of San Mateo

Judgment Creditor: Apex Supplies, Inc.
Judgment Debtor: Bayview Builders, LLC

Total Amount of Judgment as Entered: $75,450.25
Judgment Entered on: September 10, 2028
Recorded in the Official Records of San Mateo County on Sep 15, 2028, Doc # 2028-98765.

**JSON OUTPUT:**
{
  "contract_name": "Abstract of Judgment",
  "effective_date": "2028-09-10",
  "parties": [
    { "name": "Apex Supplies, Inc.", "role": "Judgment Creditor" },
    { "name": "Bayview Builders, LLC", "role": "Judgment Debtor" }
  ],
  "litigation_details": {
    "court_name": "Superior Court of California, County of San Mateo",
    "case_number": "2027CV12345",
    "judgment_amount": 75450.25
  },
  "legal_recording_details": {
    "county": "San Mateo",
    "recording_date": "2028-09-15",
    "instrument_number": "2028-98765"
  }
}
3. Schema Additions
File: abstracts-of-judgment.SA.json

JSON

{
  "litigation_details": {
    "type": "object",
    "description": "Details specific to litigation, court filings, and legal disputes.",
    "properties": {
      "court_name": { "type": "string" },
      "case_number": { "type": "string" },
      "judgment_amount": { "type": "number" }
    }
  }
}
Document Type: ALTA Surveys
Folder: /document_types/alta-surveys/

1. Specialist Schema
File: alta-surveys.SS.json

JSON

{
  "title": "ALTA/NSPS Land Title Survey Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "effective_date": { "type": "string", "format": "date", "description": "The date of the surveyor's certification." },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Client", "Surveyor", "Title Company"] }
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
        "survey_type": { "type": "string" },
        "table_a_items": {
          "type": "array",
          "items": { "type": "string" },
          "description": "A list of the optional ALTA Table A items included in the survey."
        }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "survey_details"]
}
2. Few-Shot Example
File: alta-surveys.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
ALTA/NSPS LAND TITLE SURVEY
A survey of Lot 10, Block B, of the Sunnyside Estates, City of Austin, Travis County, Texas.
For: Big Tex Development
Title Company: First American Title, GF No. 12345

Surveyor's Certification:
I hereby certify that this map or plat and the survey on which it is based were made in accordance with the 2021 Minimum Standard Detail Requirements for ALTA/NSPS Land Title Surveys, jointly established and adopted by ALTA and NSPS, and includes items 1, 5, 8, and 11 of Table A thereof.
Date of Certification: August 30, 2028
John Surveyor, RPLS No. 1234

**JSON OUTPUT:**
{
  "contract_name": "ALTA/NSPS Land Title Survey",
  "effective_date": "2028-08-30",
  "parties": [
    { "name": "Big Tex Development", "role": "Client" },
    { "name": "John Surveyor, RPLS No. 1234", "role": "Surveyor" },
    { "name": "First American Title", "role": "Title Company" }
  ],
  "survey_details": {
    "property_address": null,
    "property_legal_description": "Lot 10, Block B, of the Sunnyside Estates, City of Austin, Travis County, Texas.",
    "apn": null,
    "survey_type": "ALTA/NSPS Land Title Survey",
    "table_a_items": ["1", "5", "8", "11"]
  }
}
3. Schema Additions
File: alta-surveys.SA.json

JSON

{
  "survey_details": {
    "type": "object",
    "description": "Details specific to a land survey.",
    "properties": {
      "property_address": { "type": "string" },
      "property_legal_description": { "type": "string" },
      "apn": { "type": "string" },
      "survey_type": { "type": "string" },
      "table_a_items": {
        "type": "array",
        "items": { "type": "string" },
        "description": "A list of the optional ALTA Table A items included in the survey."
      }
    }
  }
}
Document Type: Writs of Possession
Folder: /document_types/writs-of-possession/

1. Specialist Schema
File: writs-of-possession.SS.json

JSON

{
  "title": "Writ of Possession Extraction",
  "type": "object",
  "properties": {
    "contract_name": { "type": "string" },
    "effective_date": { "type": "string", "format": "date", "description": "The date the writ was issued by the court." },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string", "enum": ["Plaintiff", "Defendant", "Sheriff", "Clerk of the Court"] }
        },
        "required": ["name", "role"]
      }
    },
    "litigation_details": {
      "type": "object",
      "properties": {
        "court_name": { "type": "string" },
        "case_number": { "type": "string" },
        "property_address": { "type": "string" },
        "judgment_date": { "type": "string", "format": "date" }
      }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "litigation_details"]
}
2. Few-Shot Example
File: writs-of-possession.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
WRIT OF POSSESSION (REAL PROPERTY)
Case Number: UD-2028-555

TO THE SHERIFF OF THE COUNTY OF LOS ANGELES:
You are directed to enforce the judgment entered on September 15, 2028, in the above-entitled action. You are ordered to restore possession of the premises located at 987 Tenant Ave, Los Angeles, CA to the Plaintiff, Property Management Inc.

Issued on: September 20, 2028
Clerk of the Court

**JSON OUTPUT:**
{
  "contract_name": "Writ of Possession (Real Property)",
  "effective_date": "2028-09-20",
  "parties": [
    { "name": "Property Management Inc.", "role": "Plaintiff" },
    { "name": "Sheriff of the County of Los Angeles", "role": "Sheriff" },
    { "name": "Clerk of the Court", "role": "Clerk of the Court" }
  ],
  "litigation_details": {
    "court_name": null,
    "case_number": "UD-2028-555",
    "property_address": "987 Tenant Ave, Los Angeles, CA",
    "judgment_date": "2028-09-15"
  }
}
3. Schema Additions
File: writs-of-possession.SA.json

JSON

{
  "litigation_details": {
    "type": "object",
    "description": "Details specific to litigation, court filings, and legal disputes.",
    "properties": {
      "court_name": { "type": "string" },
      "case_number": { "type": "string" },
      "property_address": { "type": "string" },
      "judgment_date": { "type": "string", "format": "date" }
    }
  }
}


Document Type: Utility Easements
Folder: /document_types/utility-easements/

1. Specialist Schema
File: utility-easements.SS.json

JSON

{
  "title": "Utility Easement Extraction",
  "type": "object",
  "properties": {
    "contract_name": {
      "type": "string",
      "description": "The name of the document, e.g., 'Grant of Easement for Public Utilities'."
    },
    "effective_date": {
      "type": "string",
      "format": "date",
      "description": "The date the easement was granted or recorded."
    },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": {
            "type": "string",
            "enum": ["Grantor", "Grantee"]
          }
        },
        "required": ["name", "role"]
      }
    },
    "parcels": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "apn": { "type": "string" },
                "legal_description": { "type": "string" }
            }
        }
    },
    "easement_details": {
      "type": "object",
      "properties": {
        "easement_type": {
          "type": "string",
          "description": "The type of utility the easement is for (e.g., 'Electric', 'Water', 'Sewer', 'Communications')."
        },
        "purpose": {
          "type": "string",
          "description": "The specific purpose of the easement (e.g., 'install, maintain, and operate underground electric lines')."
        },
        "easement_area_description": {
          "type": "string",
          "description": "A description of the specific portion of the property affected by the easement."
        },
        "is_perpetual": {
          "type": "boolean"
        }
      }
    },
    "discovered_entities": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "entity_name": { "type": "string" },
                "entity_value": { "type": "string" },
                "context_summary": { "type": "string" }
            }
        }
    }
  },
  "required": ["contract_name", "effective_date", "parties", "easement_details"]
}
2. Few-Shot Example
File: utility-easements.FSE.txt

Plaintext

**INPUT DOCUMENT TEXT:**
EASEMENT FOR PUBLIC UTILITIES

This Grant of Easement is made on April 5, 2026, by John and Jane Smith, Trustees of the Smith Family Trust ("Grantor"), to Pacific Gas & Electric Company, a California corporation ("Grantee").

Grantor hereby grants to Grantee a perpetual easement to install, construct, maintain, and operate underground electric and gas lines over, under, and across that certain real property described in Exhibit A, APN 123-456-789.

The easement shall be a strip of land ten (10) feet in width, the location of which is depicted on the map attached as Exhibit B.

**JSON OUTPUT:**
{
  "contract_name": "Easement for Public Utilities",
  "effective_date": "2026-04-05",
  "parties": [
    {
      "name": "John and Jane Smith, Trustees of the Smith Family Trust",
      "role": "Grantor"
    },
    {
      "name": "Pacific Gas & Electric Company",
      "role": "Grantee"
    }
  ],
  "parcels": [
    {
      "apn": "123-456-789",
      "legal_description": "Described in Exhibit A"
    }
  ],
  "easement_details": {
    "easement_type": "Electric and Gas",
    "purpose": "To install, construct, maintain, and operate underground electric and gas lines.",
    "easement_area_description": "A strip of land ten (10) feet in width, as depicted on the map attached as Exhibit B.",
    "is_perpetual": true
  },
  "discovered_entities": []
}
3. Schema Additions
File: utility-easements.SA.json

JSON

{
  "easement_details": {
    "type": "object",
    "description": "Details specific to an easement agreement.",
    "properties": {
      "easement_type": {
        "type": "string",
        "description": "The type of utility or purpose the easement is for (e.g., 'Electric', 'Water', 'Access')."
      },
      "purpose": {
        "type": "string",
        "description": "The specific purpose of the easement."
      },
      "easement_area_description": {
        "type": "string",
        "description": "A description of the specific portion of the property affected by the easement."
      },
      "is_perpetual": {
        "type": "boolean"
      }
    }
  }
}
