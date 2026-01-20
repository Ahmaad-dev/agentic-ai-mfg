# Validation Errors - ESAROM Smart Planning Solver Engine

This document provides a comprehensive list of all validation checks that result in **error-level** messages in the validation endpoint `/validate-snapshot`. These errors lead to HTTP status code 260 (Business Validation Error) instead of 200.

## Overview

The validation system performs multiple checks to ensure data integrity and business rule compliance. Validation functions that produce error-level messages will prevent successful processing and require correction before the solver can run.

## Error-Level Validations

### 1. ID Uniqueness and Integrity (`validate_unique_ids`)

**Function:** `validate_unique_ids`  
**Scope:** All entity types  
**Error Conditions:**

- **Duplicate IDs:** When multiple entities have the same ID
- **Empty IDs:** When required ID fields are empty or null

**Affected Entity Types:**
- Demands (`demand_id`)
- Articles (`article_id`) 
- Work Plans (`work_plan_id`)
- Equipment (`equipment_id`)
- Worker Availability (`worker_id`)
- Worker Qualifications (`worker_id`)

**Example Error Messages:**
```
Demand IDs must be unique. Duplicates found: D001, D002.
Article IDs must not be empty. Empty IDs found: .
```

### 2. Reference Integrity Validations

#### 2.1 Work Plan References (`validate_work_plan_ids`)

**Function:** `validate_work_plan_ids`  
**Error Condition:** Article references a `work_plan_id` that doesn't exist in the work plans collection

**Example Error Message:**
```
Missing work plans for the following IDs: WP001, WP002
```

#### 2.2 Article References (`validate_demand_article_ids`)

**Function:** `validate_demand_article_ids`  
**Error Condition:** Demand references an `article_id` that doesn't exist in the articles collection

**Example Error Message:**
```
Missing articles for the following demand article IDs: A001, A002
```

### 3. Business Logic Validations

#### 3.1 Density Validation (`validate_density_values`)

**Function:** `validate_density_values`  
**Error Condition:** Article has `rel_density_min` ≤ 0 or null

**Example Error Message:**
```
Article A001 has invalid rel_density_min: 0.0. Must be greater than 0.
```

#### 3.2 Work Item Configuration Completeness (`validate_work_item_configs_completeness`)

**Function:** `validate_work_item_configs_completeness`  
**Error Condition:** Article missing work_item_configs for required work item keys from its work plan

**Work Plan Process Steps Checked:**
- preparation_aroma
- preparation_powder  
- waiting_time1
- manufacturing
- resting_filtering1
- quality_check1
- waiting_time2
- processing
- resting_filtering2
- quality_check2
- waiting_time3
- filling
- waiting_time4

**Example Error Message:**
```
Article A001 is missing work_item_configs for: HE01, BA01. Cannot process article.
```

#### 3.3 Start/End Operation Existence (`validate_start_end_operation_existence`)

**Function:** `validate_start_end_operation_existence`  
**Error Conditions:**
- Article missing HE01 or ABF01 work_item_config
- HE01 or ABF01 config has both `net_time_factor` ≤ 0 and `ramp_up_time` ≤ 0

**Example Error Messages:**
```
Article A001 is missing work_item_config for HE01. Cannot process article.
Article A001 has HE01 work_item_config with net_time_factor=0.0, ramp_up_time=0.0. At least one of net_time_factor or ramp_up_time must be > 0. This prevents a valid processing chain.
```

#### 3.4 Equipment Availability (`validate_work_item_equipment_availability`)

**Function:** `validate_work_item_equipment_availability`  
**Error Condition:** Required work item keys have no compatible equipment available

**Exempt Work Items:** QS01, QS02, WART01, WART02, WART03, WART04

**Example Error Message:**
```
Missing equipment for the following work item keys: BA01, FU01
```

#### 3.5 Equipment-Worker Qualification Compatibility (`validate_equipment_worker_qualification_compatibility`)

**Function:** `validate_equipment_worker_qualification_compatibility`  
**Error Conditions:**
- Equipment requires qualifications but no worker qualifications are defined
- Equipment requires a qualification that no worker possesses

**Example Error Messages:**
```
Equipment requires qualifications but no worker qualifications defined
Missing worker qualifications required by equipment: Mixing, Filling
```

#### 3.6 Equipment Predecessor References (`validate_equipment_predecessor_references`)

**Function:** `validate_equipment_predecessor_references`  
**Error Condition:** Equipment references a predecessor that doesn't exist in the equipment collection

**Example Error Message:**
```
Invalid equipment predecessor references: Equipment TANK01 references non-existent predecessor: MIXER99
```

#### 3.7 Packaging Equipment Compatibility References (`validate_packaging_equipment_compatibility_references`)

**Function:** `validate_packaging_equipment_compatibility_references`  
**Error Condition:** Packaging equipment compatibility references a predecessor that doesn't exist

**Example Error Message:**
```
Invalid packaging equipment compatibility predecessor references: Packaging P001 references non-existent equipment predecessor: TANK99
```

#### 3.8 Packaging References (`validate_packaging_references`)

**Function:** `validate_packaging_references`  
**Error Conditions:**
- Demand references non-existent packaging
- Article references non-existent standard packaging  
- Packaging has no predecessors defined

**Example Error Messages:**
```
Demand D001 references non-existent packaging: P999
Article A001 references non-existent packaging: P999
Packaging without predecessors found: P001
```

## Schema Validation Errors

**HTTP Status Code:** 422 (Unprocessable Entity)  
**Source:** FastAPI/Pydantic automatic validation  
**Error Condition:** Request JSON doesn't match the expected schema structure

These are handled automatically by FastAPI before reaching the business validation logic.

## Non-Error Validations

The following validation functions only produce **warnings** and do **not** result in error status:

- `validate_worker_consistency` - Warns about workers with availability but no qualifications, etc.
- `validate_equipment_unavailability_consistency` - Warns about equipment without unavailabilities
- `validate_equipment_connectivity` - Warns about isolated equipment in the production network

## Status Code Mapping

| Validation Result | HTTP Status Code | Description |
|------------------|------------------|-------------|
| All validations pass | 200 | Successful validation |
| Error-level messages present | 260 | Business validation errors |
| Schema validation fails | 422 | Invalid request format |
| Internal error | 500 | Server error |

## Usage

These validations are automatically executed when calling the `/validate-snapshot` endpoint. The response includes all validation messages filtered by the requested verbosity level (debug, info, warning, error).

**Example Request:**
```json
{
  "snapshot": { ... },
  "verbosity": "error"
}
```

**Example Error Response (Status 260):**
```json
{
  "validationMessages": [
    {
      "level": "error",
      "message": "Demand IDs must be unique. Duplicates found: D001."
    },
    {
      "level": "error", 
      "message": "Article A001 has invalid rel_density_min: 0.0. Must be greater than 0."
    }
  ]
}
```