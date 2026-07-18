"""
Backend API Tests for ADMET Prediction Service - Enhanced Schema Testing
Tests all backend endpoints per test_result.md requirements including new features
"""

import requests
import json
import io
from pathlib import Path

# Load backend URL from frontend/.env
def get_backend_url():
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    base_url = line.split("=", 1)[1].strip()
                    return f"{base_url}/api"
    return "http://localhost:8001/api"

BASE_URL = get_backend_url()

print(f"Testing backend at: {BASE_URL}")
print("=" * 80)

# Test Results Storage
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_pass(test_name, details=""):
    test_results["passed"].append(f"✅ {test_name}")
    print(f"✅ PASS: {test_name}")
    if details:
        print(f"   {details}")

def log_fail(test_name, details=""):
    test_results["failed"].append(f"❌ {test_name}: {details}")
    print(f"❌ FAIL: {test_name}")
    if details:
        print(f"   {details}")

def log_warning(test_name, details=""):
    test_results["warnings"].append(f"⚠️  {test_name}: {details}")
    print(f"⚠️  WARNING: {test_name}")
    if details:
        print(f"   {details}")

# ============================================================================
# TEST A: POST /api/predict - Enhanced Schema Verification
# ============================================================================
print("\n" + "=" * 80)
print("TEST A: POST /api/predict - Enhanced Schema with Scaffold, CI, Confidence")
print("=" * 80)

caffeine_smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
print(f"SMILES: {caffeine_smiles}")

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"smiles": caffeine_smiles},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("POST /api/predict returns 200")
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # A.1: Check top-level scaffold object
        if "scaffold" in data:
            scaffold = data["scaffold"]
            log_pass("Top-level 'scaffold' object present")
            
            # Check scaffold fields
            required_scaffold_fields = ["scaffold", "complexity", "applicability", "novelty_tier"]
            if all(field in scaffold for field in required_scaffold_fields):
                log_pass(f"Scaffold has all required fields: {required_scaffold_fields}")
                
                # Validate scaffold field (string, can be empty)
                if isinstance(scaffold.get("scaffold"), str):
                    log_pass(f"scaffold.scaffold is string: '{scaffold['scaffold']}'")
                else:
                    log_fail("scaffold.scaffold type", f"Expected string, got {type(scaffold.get('scaffold'))}")
                
                # Validate complexity (float 0..1)
                complexity = scaffold.get("complexity")
                if isinstance(complexity, (int, float)) and 0 <= complexity <= 1:
                    log_pass(f"scaffold.complexity is float 0..1: {complexity}")
                else:
                    log_fail("scaffold.complexity", f"Expected float 0..1, got {complexity}")
                
                # Validate applicability (float 0..1)
                applicability = scaffold.get("applicability")
                if isinstance(applicability, (int, float)) and 0 <= applicability <= 1:
                    log_pass(f"scaffold.applicability is float 0..1: {applicability}")
                else:
                    log_fail("scaffold.applicability", f"Expected float 0..1, got {applicability}")
                
                # Validate novelty_tier
                novelty_tier = scaffold.get("novelty_tier")
                valid_tiers = ["in-domain", "borderline", "out-of-domain"]
                if novelty_tier in valid_tiers:
                    log_pass(f"scaffold.novelty_tier is valid: '{novelty_tier}'")
                else:
                    log_fail("scaffold.novelty_tier", f"Expected one of {valid_tiers}, got '{novelty_tier}'")
            else:
                missing = set(required_scaffold_fields) - set(scaffold.keys())
                log_fail("Missing scaffold fields", f"Missing: {missing}")
        else:
            log_fail("scaffold object missing", "Response does not contain top-level 'scaffold' object")
        
        # A.2: Check enhanced results with CI, confidence, sigma
        if "results" in data:
            results = data["results"]
            expected_endpoints = ["HIA", "BBB", "CYP2D6", "Solubility", "VDss"]
            
            if all(key in results for key in expected_endpoints):
                log_pass("All 5 ADMET endpoints present in results")
                
                # Check classifiers (HIA, BBB, CYP2D6)
                for endpoint in ["HIA", "BBB", "CYP2D6"]:
                    endpoint_data = results[endpoint]
                    print(f"\n  Checking {endpoint}:")
                    
                    # Check ci_low
                    if "ci_low" in endpoint_data:
                        ci_low = endpoint_data["ci_low"]
                        if isinstance(ci_low, (int, float)) and 0 <= ci_low <= 1:
                            log_pass(f"{endpoint}.ci_low is valid: {ci_low}")
                        else:
                            log_fail(f"{endpoint}.ci_low", f"Expected float 0..1, got {ci_low}")
                    else:
                        log_fail(f"{endpoint}.ci_low missing", "No 'ci_low' field")
                    
                    # Check ci_high
                    if "ci_high" in endpoint_data:
                        ci_high = endpoint_data["ci_high"]
                        if isinstance(ci_high, (int, float)) and 0 <= ci_high <= 1:
                            log_pass(f"{endpoint}.ci_high is valid: {ci_high}")
                            
                            # Check ci_high >= ci_low
                            if "ci_low" in endpoint_data:
                                if ci_high >= endpoint_data["ci_low"]:
                                    log_pass(f"{endpoint}.ci_high >= ci_low: {ci_high} >= {endpoint_data['ci_low']}")
                                else:
                                    log_fail(f"{endpoint}.ci_high < ci_low", f"{ci_high} < {endpoint_data['ci_low']}")
                        else:
                            log_fail(f"{endpoint}.ci_high", f"Expected float 0..1, got {ci_high}")
                    else:
                        log_fail(f"{endpoint}.ci_high missing", "No 'ci_high' field")
                    
                    # Check probability bounds
                    if "probability" in endpoint_data:
                        prob = endpoint_data["probability"]
                        ci_low = endpoint_data.get("ci_low", 0)
                        ci_high = endpoint_data.get("ci_high", 1)
                        if ci_low <= prob <= ci_high:
                            log_pass(f"{endpoint}: ci_low <= probability <= ci_high: {ci_low} <= {prob} <= {ci_high}")
                        else:
                            log_fail(f"{endpoint} probability bounds", f"Expected {ci_low} <= {prob} <= {ci_high}")
                    
                    # Check confidence
                    if "confidence" in endpoint_data:
                        confidence = endpoint_data["confidence"]
                        valid_confidence = ["high", "moderate", "low"]
                        if confidence in valid_confidence:
                            log_pass(f"{endpoint}.confidence is valid: '{confidence}'")
                        else:
                            log_fail(f"{endpoint}.confidence", f"Expected one of {valid_confidence}, got '{confidence}'")
                    else:
                        log_fail(f"{endpoint}.confidence missing", "No 'confidence' field")
                    
                    # Check sigma
                    if "sigma" in endpoint_data:
                        sigma = endpoint_data["sigma"]
                        if isinstance(sigma, (int, float)) and sigma >= 0:
                            log_pass(f"{endpoint}.sigma is valid: {sigma}")
                        else:
                            log_fail(f"{endpoint}.sigma", f"Expected float >= 0, got {sigma}")
                    else:
                        log_fail(f"{endpoint}.sigma missing", "No 'sigma' field")
                
                # Check regressors (Solubility, VDss)
                for endpoint in ["Solubility", "VDss"]:
                    endpoint_data = results[endpoint]
                    print(f"\n  Checking {endpoint}:")
                    
                    # Check ci_low
                    if "ci_low" in endpoint_data:
                        ci_low = endpoint_data["ci_low"]
                        if isinstance(ci_low, (int, float)):
                            log_pass(f"{endpoint}.ci_low is numeric: {ci_low}")
                        else:
                            log_fail(f"{endpoint}.ci_low", f"Expected number, got {ci_low}")
                    else:
                        log_fail(f"{endpoint}.ci_low missing", "No 'ci_low' field")
                    
                    # Check ci_high
                    if "ci_high" in endpoint_data:
                        ci_high = endpoint_data["ci_high"]
                        if isinstance(ci_high, (int, float)):
                            log_pass(f"{endpoint}.ci_high is numeric: {ci_high}")
                            
                            # Check ci_high >= ci_low
                            if "ci_low" in endpoint_data:
                                if ci_high >= endpoint_data["ci_low"]:
                                    log_pass(f"{endpoint}.ci_high >= ci_low: {ci_high} >= {endpoint_data['ci_low']}")
                                else:
                                    log_fail(f"{endpoint}.ci_high < ci_low", f"{ci_high} < {endpoint_data['ci_low']}")
                        else:
                            log_fail(f"{endpoint}.ci_high", f"Expected number, got {ci_high}")
                    else:
                        log_fail(f"{endpoint}.ci_high missing", "No 'ci_high' field")
                    
                    # Check value bounds
                    if "value" in endpoint_data:
                        value = endpoint_data["value"]
                        ci_low = endpoint_data.get("ci_low", float('-inf'))
                        ci_high = endpoint_data.get("ci_high", float('inf'))
                        if ci_low <= value <= ci_high:
                            log_pass(f"{endpoint}: ci_low <= value <= ci_high: {ci_low} <= {value} <= {ci_high}")
                        else:
                            log_fail(f"{endpoint} value bounds", f"Expected {ci_low} <= {value} <= {ci_high}")
                    
                    # Check confidence
                    if "confidence" in endpoint_data:
                        confidence = endpoint_data["confidence"]
                        valid_confidence = ["high", "moderate", "low"]
                        if confidence in valid_confidence:
                            log_pass(f"{endpoint}.confidence is valid: '{confidence}'")
                        else:
                            log_fail(f"{endpoint}.confidence", f"Expected one of {valid_confidence}, got '{confidence}'")
                    else:
                        log_fail(f"{endpoint}.confidence missing", "No 'confidence' field")
                    
                    # Check sigma
                    if "sigma" in endpoint_data:
                        sigma = endpoint_data["sigma"]
                        if isinstance(sigma, (int, float)) and sigma >= 0:
                            log_pass(f"{endpoint}.sigma is valid: {sigma}")
                        else:
                            log_fail(f"{endpoint}.sigma", f"Expected float >= 0, got {sigma}")
                    else:
                        log_fail(f"{endpoint}.sigma missing", "No 'sigma' field")
                        
            else:
                missing = set(expected_endpoints) - set(results.keys())
                log_fail("Missing ADMET endpoints", f"Missing: {missing}")
        else:
            log_fail("results field missing", "Response does not contain 'results' field")
        
        # A.3: Check extended descriptors
        if "descriptors" in data:
            descriptors = data["descriptors"]
            expected_desc = ["mw", "heavy", "rings", "logp", "tpsa", "rotatable", "hbd", "hba"]
            
            if all(key in descriptors for key in expected_desc):
                log_pass(f"All extended descriptor fields present: {expected_desc}")
                
                # Validate each descriptor is numeric
                for desc in expected_desc:
                    val = descriptors.get(desc)
                    if isinstance(val, (int, float)):
                        log_pass(f"descriptors.{desc} is numeric: {val}")
                    else:
                        log_fail(f"descriptors.{desc}", f"Expected numeric, got {val}")
            else:
                missing = set(expected_desc) - set(descriptors.keys())
                log_fail("Missing extended descriptor fields", f"Missing: {missing}")
        else:
            log_fail("descriptors field missing", "Response does not contain 'descriptors' field")
            
    else:
        log_fail("POST /api/predict status code", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict request", f"Exception: {str(e)}")

# ============================================================================
# TEST B: POST /api/scaffold
# ============================================================================
print("\n" + "=" * 80)
print("TEST B: POST /api/scaffold")
print("=" * 80)

# B.1: Valid SMILES (aspirin)
print("\nB.1: Valid SMILES (aspirin)")
aspirin_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
print(f"SMILES: {aspirin_smiles}")

try:
    response = requests.post(
        f"{BASE_URL}/scaffold",
        json={"smiles": aspirin_smiles},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("POST /api/scaffold returns 200 for valid SMILES")
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Check scaffold object
        if "scaffold" in data:
            log_pass("scaffold object present")
            scaffold = data["scaffold"]
            if all(k in scaffold for k in ["scaffold", "complexity", "applicability", "novelty_tier"]):
                log_pass("scaffold object has all required fields")
            else:
                log_fail("scaffold fields incomplete", f"Got: {list(scaffold.keys())}")
        else:
            log_fail("scaffold object missing", "Response does not contain 'scaffold' object")
        
        # Check descriptors
        if "descriptors" in data:
            log_pass("descriptors object present")
            descriptors = data["descriptors"]
            expected_desc = ["mw", "heavy", "rings", "logp", "tpsa", "rotatable", "hbd", "hba"]
            if all(k in descriptors for k in expected_desc):
                log_pass("descriptors object has all required fields")
            else:
                missing = set(expected_desc) - set(descriptors.keys())
                log_fail("descriptors fields incomplete", f"Missing: {missing}")
        else:
            log_fail("descriptors object missing", "Response does not contain 'descriptors' object")
            
    else:
        log_fail("POST /api/scaffold status code (valid)", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/scaffold request (valid)", f"Exception: {str(e)}")

# B.2: Empty SMILES
print("\nB.2: Empty SMILES")
try:
    response = requests.post(
        f"{BASE_URL}/scaffold",
        json={"smiles": ""},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("POST /api/scaffold returns 400 for empty SMILES")
    else:
        log_fail("POST /api/scaffold status code (empty)", f"Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/scaffold request (empty)", f"Exception: {str(e)}")

# B.3: Invalid SMILES
print("\nB.3: Invalid SMILES")
try:
    response = requests.post(
        f"{BASE_URL}/scaffold",
        json={"smiles": "???"},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 422:
        log_pass("POST /api/scaffold returns 422 for invalid SMILES")
        
        data = response.json()
        if "detail" in data:
            detail = str(data["detail"]).lower()
            if "invalid" in detail and "smiles" in detail:
                log_pass(f"Error detail mentions 'Invalid SMILES': '{data['detail']}'")
            else:
                log_warning("Error detail content", f"Detail: '{data['detail']}'")
    else:
        log_fail("POST /api/scaffold status code (invalid)", f"Expected 422, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/scaffold request (invalid)", f"Exception: {str(e)}")

# ============================================================================
# TEST C: POST /api/predict/batch
# ============================================================================
print("\n" + "=" * 80)
print("TEST C: POST /api/predict/batch")
print("=" * 80)

# C.1: Mixed valid/invalid SMILES
print("\nC.1: Batch with mixed valid/invalid SMILES")
batch_items = [
    {"smiles": "CCO"},  # Ethanol - valid
    {"smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"},  # Caffeine - valid
    {"smiles": "???"}  # Invalid
]

try:
    response = requests.post(
        f"{BASE_URL}/predict/batch",
        json={"items": batch_items},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("POST /api/predict/batch returns 200")
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Check count
        if data.get("count") == 3:
            log_pass("count = 3")
        else:
            log_fail("count field", f"Expected 3, got {data.get('count')}")
        
        # Check ok
        if data.get("ok") == 2:
            log_pass("ok = 2")
        else:
            log_fail("ok field", f"Expected 2, got {data.get('ok')}")
        
        # Check failed
        if data.get("failed") == 1:
            log_pass("failed = 1")
        else:
            log_fail("failed field", f"Expected 1, got {data.get('failed')}")
        
        # Check latency_ms
        if "latency_ms" in data and isinstance(data["latency_ms"], int) and data["latency_ms"] >= 0:
            log_pass(f"latency_ms is valid: {data['latency_ms']}")
        else:
            log_fail("latency_ms field", f"Expected int >= 0, got {data.get('latency_ms')}")
        
        # Check items array
        if "items" in data and isinstance(data["items"], list):
            items = data["items"]
            if len(items) == 3:
                log_pass("items array has 3 elements")
                
                # Check third item has error
                third_item = items[2]
                if "error" in third_item and third_item["error"]:
                    log_pass(f"Third item has non-empty error field: '{third_item['error']}'")
                else:
                    log_fail("Third item error", "Expected non-empty 'error' field")
                
                # Check first two items have results
                for i in [0, 1]:
                    item = items[i]
                    if "results" in item and item["results"]:
                        log_pass(f"Item {i+1} has results")
                    else:
                        log_fail(f"Item {i+1} results", "Expected non-empty 'results' field")
            else:
                log_fail("items array length", f"Expected 3, got {len(items)}")
        else:
            log_fail("items field", "Expected list")
            
    else:
        log_fail("POST /api/predict/batch status code", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict/batch request", f"Exception: {str(e)}")

# C.2: Empty items array
print("\nC.2: Empty items array")
try:
    response = requests.post(
        f"{BASE_URL}/predict/batch",
        json={"items": []},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("POST /api/predict/batch returns 400 for empty items")
    else:
        log_fail("POST /api/predict/batch status code (empty)", f"Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict/batch request (empty)", f"Exception: {str(e)}")

# ============================================================================
# TEST D: POST /api/predict/batch/upload
# ============================================================================
print("\n" + "=" * 80)
print("TEST D: POST /api/predict/batch/upload")
print("=" * 80)

# D.1: Valid CSV with mixed valid/invalid SMILES
print("\nD.1: Valid CSV with mixed SMILES")
csv_content = """smiles,name
CCO,Ethanol
CN1C=NC2=C1C(=O)N(C(=O)N2C)C,Caffeine
CC(=O)OC1=CC=CC=C1C(=O)O,Aspirin
not_a_mol,Bogus"""

try:
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    response = requests.post(
        f"{BASE_URL}/predict/batch/upload",
        files=files,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("POST /api/predict/batch/upload returns 200")
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Check count
        if data.get("count") == 4:
            log_pass("count = 4")
        else:
            log_fail("count field", f"Expected 4, got {data.get('count')}")
        
        # Check ok
        if data.get("ok") == 3:
            log_pass("ok = 3")
        else:
            log_fail("ok field", f"Expected 3, got {data.get('ok')}")
        
        # Check failed
        if data.get("failed") == 1:
            log_pass("failed = 1")
        else:
            log_fail("failed field", f"Expected 1, got {data.get('failed')}")
        
        # Check items and names
        if "items" in data and isinstance(data["items"], list):
            items = data["items"]
            if len(items) == 4:
                log_pass("items array has 4 elements")
                
                # Check names propagate
                expected_names = ["Ethanol", "Caffeine", "Aspirin", "Bogus"]
                actual_names = [item.get("name", "") for item in items]
                if actual_names == expected_names:
                    log_pass(f"Names propagate correctly: {actual_names}")
                else:
                    log_fail("Name propagation", f"Expected {expected_names}, got {actual_names}")
            else:
                log_fail("items array length", f"Expected 4, got {len(items)}")
        else:
            log_fail("items field", "Expected list")
        
        # Store items for export test
        global export_items
        export_items = data.get("items", [])
            
    else:
        log_fail("POST /api/predict/batch/upload status code", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict/batch/upload request", f"Exception: {str(e)}")

# D.2: Empty file
print("\nD.2: Empty file")
try:
    files = {'file': ('empty.csv', '', 'text/csv')}
    response = requests.post(
        f"{BASE_URL}/predict/batch/upload",
        files=files,
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("POST /api/predict/batch/upload returns 400 for empty file")
    else:
        log_fail("POST /api/predict/batch/upload status code (empty)", f"Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict/batch/upload request (empty)", f"Exception: {str(e)}")

# D.3: CSV with no SMILES data
print("\nD.3: CSV with no SMILES data")
try:
    files = {'file': ('no_data.csv', 'smiles,name\n', 'text/csv')}
    response = requests.post(
        f"{BASE_URL}/predict/batch/upload",
        files=files,
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    # Accept 400 or 422 for this case
    if response.status_code in [400, 422]:
        log_pass(f"POST /api/predict/batch/upload returns {response.status_code} for CSV with no data")
    else:
        log_fail("POST /api/predict/batch/upload status code (no data)", f"Expected 400 or 422, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict/batch/upload request (no data)", f"Exception: {str(e)}")

# ============================================================================
# TEST E: POST /api/predict/batch/export
# ============================================================================
print("\n" + "=" * 80)
print("TEST E: POST /api/predict/batch/export")
print("=" * 80)

# E.1: Export with items from upload test
print("\nE.1: Export with items")
try:
    if 'export_items' in globals() and export_items:
        response = requests.post(
            f"{BASE_URL}/predict/batch/export",
            json={"items": export_items},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            log_pass("POST /api/predict/batch/export returns 200")
            
            # Check Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'text/csv' in content_type:
                log_pass(f"Content-Type is text/csv: {content_type}")
            else:
                log_fail("Content-Type", f"Expected text/csv, got {content_type}")
            
            # Check CSV content
            csv_text = response.text
            lines = csv_text.strip().split('\n')
            
            if len(lines) > 0:
                header = lines[0]
                print(f"CSV Header: {header}")
                
                # Check required columns
                required_cols = [
                    "row_idx", "name", "smiles", "mw", "heavy", "rings", "logp",
                    "HIA_prob", "HIA_pred", "BBB_prob", "BBB_pred",
                    "CYP2D6_prob", "CYP2D6_pred", "Solubility_logS", "VDss_Lkg", "error"
                ]
                
                header_lower = header.lower()
                missing_cols = [col for col in required_cols if col.lower() not in header_lower]
                
                if not missing_cols:
                    log_pass(f"CSV header contains all required columns")
                else:
                    log_fail("CSV header missing columns", f"Missing: {missing_cols}")
                
                # Check we have data rows
                if len(lines) > 1:
                    log_pass(f"CSV has {len(lines)-1} data rows")
                else:
                    log_warning("CSV data rows", "No data rows in CSV")
            else:
                log_fail("CSV content", "CSV is empty")
                
        else:
            log_fail("POST /api/predict/batch/export status code", f"Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
    else:
        log_warning("Export test skipped", "No items from upload test")
        
except Exception as e:
    log_fail("POST /api/predict/batch/export request", f"Exception: {str(e)}")

# E.2: Empty items array
print("\nE.2: Empty items array")
try:
    response = requests.post(
        f"{BASE_URL}/predict/batch/export",
        json={"items": []},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("POST /api/predict/batch/export returns 400 for empty items")
    else:
        log_fail("POST /api/predict/batch/export status code (empty)", f"Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("POST /api/predict/batch/export request (empty)", f"Exception: {str(e)}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

print(f"\n✅ PASSED: {len(test_results['passed'])}")
for result in test_results['passed']:
    print(f"  {result}")

if test_results['warnings']:
    print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
    for result in test_results['warnings']:
        print(f"  {result}")

if test_results['failed']:
    print(f"\n❌ FAILED: {len(test_results['failed'])}")
    for result in test_results['failed']:
        print(f"  {result}")
    print(f"\nTotal failures: {len(test_results['failed'])}")
else:
    print("\n🎉 ALL CRITICAL TESTS PASSED!")

print("\n" + "=" * 80)
