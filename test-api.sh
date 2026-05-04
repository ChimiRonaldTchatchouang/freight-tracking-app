#!/bin/bash

# 🧪 SCRIPT DE TEST COMPLET API FREIGHT TRACKING
# Ce script teste TOUTES les routes du backend

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  🧪 TEST COMPLET DE TOUTES LES ROUTES API                     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
API_URL="${1:-http://localhost:3001}"
echo "🎯 Testing API at: $API_URL"
echo ""

# Couleurs pour output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

# Fonction pour tester une requête
test_endpoint() {
  local method=$1
  local endpoint=$2
  local data=$3
  local expected_status=$4
  
  test_count=$((test_count + 1))
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "TEST $test_count: $method $endpoint"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
  else
    response=$(curl -s -w "\n%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$API_URL$endpoint")
  fi
  
  status=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  echo "Status: $status (Expected: $expected_status)"
  echo "Response: $body"
  echo ""
  
  if [ "$status" = "$expected_status" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    pass_count=$((pass_count + 1))
  else
    echo -e "${RED}❌ FAIL${NC}"
    fail_count=$((fail_count + 1))
  fi
  echo ""
}

# ========================================
# TEST 1: PUBLIC ENDPOINTS
# ========================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "TEST SUITE 1: PUBLIC ENDPOINTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/" "null" "200"
test_endpoint "GET" "/health" "null" "200"

# ========================================
# TEST 2: AUTH ENDPOINTS
# ========================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "TEST SUITE 2: AUTH ENDPOINTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Valid login
test_endpoint "POST" "/api/v1/auth/login" '{"email":"admin@freight-tracking.com","password":"Admin123!@#"}' "200"

# Extract token for later tests
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{"email":"admin@freight-tracking.com","password":"Admin123!@#"}' "$API_URL/api/v1/auth/login" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Token extracted: ${TOKEN:0:20}..."
echo ""

# Invalid login
test_endpoint "POST" "/api/v1/auth/login" '{"email":"wrong@email.com","password":"WrongPassword"}' "401"

# Register new user
test_endpoint "POST" "/api/v1/auth/register" '{"email":"newuser@test.com","password":"Test123!@#","name":"Test User"}' "201"

# Verify token
if [ ! -z "$TOKEN" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "TEST: POST /api/v1/auth/verify"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" "$API_URL/api/v1/auth/verify")
  status=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  echo "Status: $status"
  echo "Response: $body"
  
  if [ "$status" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    pass_count=$((pass_count + 1))
  else
    echo -e "${RED}❌ FAIL${NC}"
    fail_count=$((fail_count + 1))
  fi
  test_count=$((test_count + 1))
  echo ""
fi

# ========================================
# TEST 3: BOATS ENDPOINTS
# ========================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "TEST SUITE 3: BOATS ENDPOINTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/boats" "null" "200"
test_endpoint "GET" "/api/v1/boats/1" "null" "200"
test_endpoint "GET" "/api/v1/boats/999" "null" "404"

test_endpoint "POST" "/api/v1/boats" '{"name":"New Ship","imoNumber":"9999999999","capacityKg":60000}' "201"
test_endpoint "PUT" "/api/v1/boats/1" '{"status":"en_mer"}' "200"
test_endpoint "DELETE" "/api/v1/boats/3" "null" "200"

# ========================================
# TEST 4: VEHICLES ENDPOINTS
# ========================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "TEST SUITE 4: VEHICLES ENDPOINTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/api/v1/vehicles" "null" "200"
test_endpoint "GET" "/api/v1/vehicles/1" "null" "200"
test_endpoint "GET" "/api/v1/vehicles/999" "null" "404"

test_endpoint "POST" "/api/v1/vehicles" '{"registrationPlate":"NEW-1111","type":"truck","weightEmptyKg":5000,"capacityKg":25000}' "201"
test_endpoint "PUT" "/api/v1/vehicles/1" '{"status":"maintenance"}' "200"
test_endpoint "DELETE" "/api/v1/vehicles/2" "null" "200"

# ========================================
# RÉSUMÉ
# ========================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "RÉSUMÉ DES TESTS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Total tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
  echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
  exit 0
else
  echo -e "${RED}❌ SOME TESTS FAILED${NC}"
  exit 1
fi
