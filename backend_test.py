#!/usr/bin/env python3
"""
Backend test for POST /api/scaffold endpoint - Invalid SMILES fix verification
"""
import requests
import json

# Base URL from frontend/.env
BASE_URL = "https://smiles-predictor.preview.emergentagent.com/api"

def test_scaffold_invalid_smiles_1():
    """Test case 1: POST /api/scaffold with {"smiles":"???"} should return 422"""
    print("\n" + "="*80)
    print("TEST 1: POST /api/scaffold with invalid SMILES '???'")
    print("="*80)
    
    url = f"{BASE_URL}/scaffold"
    payload = {"smiles": "???"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            try:
                data = response.json()
                if "detail" in data:
                    detail_str = str(data["detail"]).lower()
                    if "invalid" in detail_str and "smiles" in detail_str:
                        print("✅ PASS: Returns 422 with 'detail' field mentioning invalid SMILES")
                        return True
                    else:
                        print(f"❌ FAIL: Returns 422 but detail doesn't mention invalid SMILES: {data['detail']}")
                        return False
                else:
                    print(f"❌ FAIL: Returns 422 but no 'detail' field in response: {data}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ FAIL: Returns 422 but response is not valid JSON")
                return False
        else:
            print(f"❌ FAIL: Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_scaffold_invalid_smiles_2():
    """Test case 2: POST /api/scaffold with {"smiles":"not_a_molecule!!"} should return 422"""
    print("\n" + "="*80)
    print("TEST 2: POST /api/scaffold with invalid SMILES 'not_a_molecule!!'")
    print("="*80)
    
    url = f"{BASE_URL}/scaffold"
    payload = {"smiles": "not_a_molecule!!"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ PASS: Returns 422 for invalid SMILES")
            return True
        else:
            print(f"❌ FAIL: Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_scaffold_valid_smiles_regression():
    """Test case 3: POST /api/scaffold with aspirin SMILES should still return 200 with scaffold + descriptors"""
    print("\n" + "="*80)
    print("TEST 3: POST /api/scaffold with valid SMILES (aspirin) - Regression test")
    print("="*80)
    
    url = f"{BASE_URL}/scaffold"
    payload = {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check for required fields
            checks = []
            
            # Check smiles field
            if "smiles" in data:
                print(f"✓ smiles: {data['smiles']}")
                checks.append(True)
            else:
                print("✗ Missing 'smiles' field")
                checks.append(False)
            
            # Check scaffold object
            if "scaffold" in data and isinstance(data["scaffold"], dict):
                scaffold = data["scaffold"]
                print(f"✓ scaffold object present with keys: {list(scaffold.keys())}")
                
                # Check scaffold fields
                required_scaffold_fields = ["scaffold", "complexity", "applicability", "novelty_tier"]
                for field in required_scaffold_fields:
                    if field in scaffold:
                        print(f"  ✓ scaffold.{field}: {scaffold[field]}")
                        checks.append(True)
                    else:
                        print(f"  ✗ Missing scaffold.{field}")
                        checks.append(False)
            else:
                print("✗ Missing or invalid 'scaffold' object")
                checks.append(False)
            
            # Check descriptors object
            if "descriptors" in data and isinstance(data["descriptors"], dict):
                descriptors = data["descriptors"]
                print(f"✓ descriptors object present with keys: {list(descriptors.keys())}")
                checks.append(True)
            else:
                print("✗ Missing or invalid 'descriptors' object")
                checks.append(False)
            
            if all(checks):
                print("✅ PASS: Returns 200 with populated scaffold + descriptors")
                return True
            else:
                print(f"❌ FAIL: Returns 200 but missing required fields ({sum(checks)}/{len(checks)} checks passed)")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_scaffold_empty_smiles_regression():
    """Test case 4: POST /api/scaffold with empty SMILES should still return 400"""
    print("\n" + "="*80)
    print("TEST 4: POST /api/scaffold with empty SMILES - Regression test")
    print("="*80)
    
    url = f"{BASE_URL}/scaffold"
    payload = {"smiles": ""}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ PASS: Returns 400 for empty SMILES")
            return True
        else:
            print(f"❌ FAIL: Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    print("\n" + "="*80)
    print("POST /api/scaffold - Invalid SMILES Fix Verification")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    
    results = []
    
    # Run all 4 test cases
    results.append(("Invalid SMILES '???'", test_scaffold_invalid_smiles_1()))
    results.append(("Invalid SMILES 'not_a_molecule!!'", test_scaffold_invalid_smiles_2()))
    results.append(("Valid SMILES (aspirin) regression", test_scaffold_valid_smiles_regression()))
    results.append(("Empty SMILES regression", test_scaffold_empty_smiles_regression()))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Invalid SMILES fix verified!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
