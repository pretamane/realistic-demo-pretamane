#!/bin/bash

###############################################################################
# DEPLOYMENT MONITORING SCRIPT
###############################################################################
# Purpose: Real-time monitoring of deployment progress and health
###############################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REFRESH_INTERVAL=10
AWS_REGION="${AWS_REGION:-ap-southeast-1}"

clear

echo "============================================================================"
echo "DEPLOYMENT MONITORING DASHBOARD"
echo "============================================================================"
echo "Refresh interval: ${REFRESH_INTERVAL} seconds"
echo "Press Ctrl+C to exit"
echo ""

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "Last Updated: ${TIMESTAMP}"
    echo "----------------------------------------------------------------------------"
    
    echo ""
    echo "[1] KUBERNETES PODS STATUS"
    kubectl get pods -o wide 2>/dev/null || echo "Cluster not accessible yet"
    
    echo ""
    echo "[2] KUBERNETES SERVICES"
    kubectl get svc 2>/dev/null | head -10
    
    echo ""
    echo "[3] PERSISTENT VOLUME CLAIMS"
    kubectl get pvc 2>/dev/null
    
    echo ""
    echo "[4] HORIZONTAL POD AUTOSCALERS"
    kubectl get hpa 2>/dev/null
    
    echo ""
    echo "[5] INGRESS STATUS"
    kubectl get ingress 2>/dev/null
    
    echo ""
    echo "[6] POD HEALTH SUMMARY"
    RUNNING=$(kubectl get pods --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    PENDING=$(kubectl get pods --field-selector=status.phase=Pending --no-headers 2>/dev/null | wc -l)
    FAILED=$(kubectl get pods --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l)
    TOTAL=$(kubectl get pods --no-headers 2>/dev/null | wc -l)
    
    echo "Running: ${RUNNING} | Pending: ${PENDING} | Failed: ${FAILED} | Total: ${TOTAL}"
    
    echo ""
    echo "[7] RECENT EVENTS (Last 5)"
    kubectl get events --sort-by='.lastTimestamp' 2>/dev/null | tail -6 | head -5
    
    echo ""
    echo "----------------------------------------------------------------------------"
    echo "Next refresh in ${REFRESH_INTERVAL} seconds..."
    echo ""
    
    sleep "$REFRESH_INTERVAL"
    
    # Clear screen for next iteration
    clear
    echo "============================================================================"
    echo "DEPLOYMENT MONITORING DASHBOARD"
    echo "============================================================================"
    echo "Refresh interval: ${REFRESH_INTERVAL} seconds"
    echo "Press Ctrl+C to exit"
    echo ""
done

