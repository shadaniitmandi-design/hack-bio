"""
Backend API Tests for ADMET Prediction Service
Tests all backend endpoints per test_result.md requirements
"""

import requests
import json
import os
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
# TEST 1: GET /api/health
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: GET /api/health")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("Health endpoint returns 200")
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check status field
        if data.get("status") == "ok":
            log_pass("Health status is 'ok'")
        else:
            log_fail("Health status check", f"Expected 'ok', got '{data.get('status')}'")
        
        # Check model_loaded field
        if "model_loaded" in data:
            if data["model_loaded"] is True:
                log_pass("model_loaded is true")
            else:
                log_fail("model_loaded check", f"Expected true, got {data['model_loaded']}")
        else:
            log_fail("model_loaded field missing", "Response does not contain 'model_loaded' field")
        
        # Check endpoints array
        if "endpoints" in data:
            endpoints = data["endpoints"]
            expected_endpoints = ["HIA", "BBB", "CYP2D6", "Solubility", "VDss"]
            
            if isinstance(endpoints, list):
                log_pass("endpoints field is an array")
                
                missing = set(expected_endpoints) - set(endpoints)
                extra = set(endpoints) - set(expected_endpoints)
                
                if not missing and not extra:
                    log_pass(f"All 5 expected endpoints present: {endpoints}")
                else:
                    if missing:
                        log_fail("Missing endpoints", f"Missing: {missing}")
                    if extra:
                        log_warning("Extra endpoints", f"Extra: {extra}")
            else:
                log_fail("endpoints field type", f"Expected list, got {type(endpoints)}")
        else:
            log_fail("endpoints field missing", "Response does not contain 'endpoints' field")
            
    else:
        log_fail("Health endpoint status code", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("Health endpoint request", f"Exception: {str(e)}")

# ============================================================================
# TEST 2: POST /api/predict with valid SMILES (caffeine)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: POST /api/predict with valid SMILES (caffeine)")
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
        log_pass("Predict endpoint returns 200 for valid SMILES")
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Check smiles field
        if data.get("smiles") == caffeine_smiles:
            log_pass("Response smiles matches input")
        else:
            log_fail("SMILES mismatch", f"Expected '{caffeine_smiles}', got '{data.get('smiles')}'")
        
        # Check results field
        if "results" in data:
            results = data["results"]
            expected_keys = ["HIA", "BBB", "CYP2D6", "Solubility", "VDss"]
            
            if all(key in results for key in expected_keys):
                log_pass("All 5 ADMET endpoints present in results")
                
                # Check classification endpoints (HIA, BBB, CYP2D6)
                for endpoint in ["HIA", "BBB", "CYP2D6"]:
                    endpoint_data = results[endpoint]
                    
                    if "probability" in endpoint_data:
                        prob = endpoint_data["probability"]
                        if isinstance(prob, (int, float)) and 0 <= prob <= 1:
                            log_pass(f"{endpoint} probability is valid float (0..1): {prob}")
                        else:
                            log_fail(f"{endpoint} probability", f"Expected float 0..1, got {prob}")
                    else:
                        log_fail(f"{endpoint} probability missing", "No 'probability' field")
                    
                    if "prediction" in endpoint_data:
                        pred = endpoint_data["prediction"]
                        if isinstance(pred, str) and len(pred) > 0:
                            log_pass(f"{endpoint} prediction is non-empty string: '{pred}'")
                        else:
                            log_fail(f"{endpoint} prediction", f"Expected non-empty string, got '{pred}'")
                    else:
                        log_fail(f"{endpoint} prediction missing", "No 'prediction' field")
                
                # Check regression endpoints (Solubility, VDss)
                for endpoint in ["Solubility", "VDss"]:
                    endpoint_data = results[endpoint]
                    
                    if "value" in endpoint_data:
                        val = endpoint_data["value"]
                        if isinstance(val, (int, float)):
                            log_pass(f"{endpoint} value is numeric: {val}")
                        else:
                            log_fail(f"{endpoint} value", f"Expected numeric, got {val}")
                    else:
                        log_fail(f"{endpoint} value missing", "No 'value' field")
                    
                    if "unit" in endpoint_data:
                        unit = endpoint_data["unit"]
                        if isinstance(unit, str):
                            log_pass(f"{endpoint} unit is string: '{unit}'")
                        else:
                            log_fail(f"{endpoint} unit", f"Expected string, got {unit}")
                    else:
                        log_fail(f"{endpoint} unit missing", "No 'unit' field")
                        
            else:
                missing = set(expected_keys) - set(results.keys())
                log_fail("Missing ADMET endpoints", f"Missing: {missing}")
        else:
            log_fail("results field missing", "Response does not contain 'results' field")
        
        # Check descriptors field
        if "descriptors" in data:
            descriptors = data["descriptors"]
            expected_desc = ["mw", "heavy", "rings", "logp"]
            
            if all(key in descriptors for key in expected_desc):
                log_pass("All descriptor fields present (mw, heavy, rings, logp)")
                
                # Validate caffeine descriptors (approximate values)
                mw = descriptors.get("mw")
                heavy = descriptors.get("heavy")
                rings = descriptors.get("rings")
                
                if mw and 190 <= mw <= 200:
                    log_pass(f"Caffeine MW is reasonable: {mw} (expected ~194)")
                else:
                    log_warning("Caffeine MW", f"Expected ~194, got {mw}")
                
                if heavy == 14:
                    log_pass(f"Caffeine heavy atoms correct: {heavy}")
                else:
                    log_warning("Caffeine heavy atoms", f"Expected 14, got {heavy}")
                
                if rings == 2:
                    log_pass(f"Caffeine rings correct: {rings}")
                else:
                    log_warning("Caffeine rings", f"Expected 2, got {rings}")
                    
            else:
                missing = set(expected_desc) - set(descriptors.keys())
                log_fail("Missing descriptor fields", f"Missing: {missing}")
        else:
            log_fail("descriptors field missing", "Response does not contain 'descriptors' field")
        
        # Check latency_ms field
        if "latency_ms" in data:
            latency = data["latency_ms"]
            if isinstance(latency, int) and latency > 0:
                log_pass(f"latency_ms is positive integer: {latency}")
            else:
                log_fail("latency_ms", f"Expected positive integer, got {latency}")
        else:
            log_fail("latency_ms field missing", "Response does not contain 'latency_ms' field")
        
        # Check source field
        if data.get("source") == "model":
            log_pass("source is 'model'")
        else:
            log_fail("source field", f"Expected 'model', got '{data.get('source')}'")
            
    else:
        log_fail("Predict endpoint status code", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("Predict endpoint request (caffeine)", f"Exception: {str(e)}")

# ============================================================================
# TEST 3: POST /api/predict with empty SMILES
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: POST /api/predict with empty SMILES")
print("=" * 80)

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"smiles": ""},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        log_pass("Empty SMILES returns 400")
        
        data = response.json()
        if "detail" in data:
            log_pass(f"Error detail provided: '{data['detail']}'")
        else:
            log_warning("Error detail missing", "No 'detail' field in error response")
    else:
        log_fail("Empty SMILES status code", f"Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("Empty SMILES request", f"Exception: {str(e)}")

# ============================================================================
# TEST 4: POST /api/predict with invalid SMILES
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: POST /api/predict with invalid SMILES")
print("=" * 80)

invalid_smiles = "not_a_molecule!!"
print(f"SMILES: {invalid_smiles}")

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"smiles": invalid_smiles},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 422:
        log_pass("Invalid SMILES returns 422")
        
        data = response.json()
        if "detail" in data:
            detail = str(data["detail"]).lower()
            if "smiles" in detail or "invalid" in detail:
                log_pass(f"Error detail mentions invalid SMILES: '{data['detail']}'")
            else:
                log_warning("Error detail content", f"Detail doesn't mention SMILES: '{data['detail']}'")
        else:
            log_warning("Error detail missing", "No 'detail' field in error response")
    else:
        log_fail("Invalid SMILES status code", f"Expected 422, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("Invalid SMILES request", f"Exception: {str(e)}")

# ============================================================================
# TEST 5: POST /api/predict with another valid SMILES (aspirin)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: POST /api/predict with another valid SMILES (aspirin)")
print("=" * 80)

aspirin_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
print(f"SMILES: {aspirin_smiles}")

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json={"smiles": aspirin_smiles},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("Predict endpoint returns 200 for aspirin")
        
        data = response.json()
        
        # Check all 5 endpoints present
        if "results" in data:
            results = data["results"]
            expected_keys = ["HIA", "BBB", "CYP2D6", "Solubility", "VDss"]
            
            if all(key in results for key in expected_keys):
                log_pass("All 5 ADMET endpoints present for aspirin")
            else:
                missing = set(expected_keys) - set(results.keys())
                log_fail("Missing ADMET endpoints (aspirin)", f"Missing: {missing}")
        else:
            log_fail("results field missing (aspirin)", "Response does not contain 'results' field")
        
        # Check descriptors are not null
        if "descriptors" in data:
            descriptors = data["descriptors"]
            if all(descriptors.get(k) is not None for k in ["mw", "heavy", "rings", "logp"]):
                log_pass(f"All descriptors non-null for aspirin: {descriptors}")
            else:
                log_fail("Null descriptors (aspirin)", f"Some descriptors are null: {descriptors}")
        else:
            log_fail("descriptors field missing (aspirin)", "Response does not contain 'descriptors' field")
            
    else:
        log_fail("Predict endpoint status code (aspirin)", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("Predict endpoint request (aspirin)", f"Exception: {str(e)}")

# ============================================================================
# TEST 6: GET /api/history
# ============================================================================
print("\n" + "=" * 80)
print("TEST 6: GET /api/history?limit=5")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/history?limit=5", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        log_pass("History endpoint returns 200")
        
        data = response.json()
        
        if isinstance(data, list):
            log_pass(f"History returns a list with {len(data)} items")
            
            if len(data) > 0:
                # Check structure of first item
                item = data[0]
                required_fields = ["smiles", "latency_ms", "timestamp"]
                
                if all(field in item for field in required_fields):
                    log_pass(f"History items have required fields: {required_fields}")
                    print(f"Sample item: {json.dumps(item, indent=2)}")
                else:
                    missing = set(required_fields) - set(item.keys())
                    log_fail("Missing history item fields", f"Missing: {missing}")
            else:
                log_warning("Empty history", "History is empty (may be expected if no predictions made)")
        else:
            log_fail("History response type", f"Expected list, got {type(data)}")
            
    else:
        log_fail("History endpoint status code", f"Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    log_fail("History endpoint request", f"Exception: {str(e)}")

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
else:
    print("\n🎉 ALL CRITICAL TESTS PASSED!")

print("\n" + "=" * 80)
