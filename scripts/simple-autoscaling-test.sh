#!/bin/bash
# Simple Autoscaling Test

echo "🚀 Simple Autoscaling Test for Portfolio Demo"
echo "============================================="
echo ""

echo "📊 Current HPA Status:"
kubectl get hpa portfolio-demo-hpa
echo ""

echo "🐳 Current Pod Count:"
kubectl get pods -l app=portfolio-demo --no-headers | wc -l
echo ""

echo "⚡ Generating Load (30 seconds)..."
echo "Making multiple concurrent requests to trigger autoscaling..."

# Generate load for 30 seconds
for i in {1..30}; do
    {
        # Make multiple concurrent requests
        for j in {1..5}; do
            curl -s http://localhost:8080/health > /dev/null &
            curl -s http://localhost:8080/storage/status > /dev/null &
            curl -s http://localhost:8080/files > /dev/null &
        done
        wait
    } &
done

# Monitor for 30 seconds
for i in {1..6}; do
    echo "Check $i/6 - Time: $(date)"
    kubectl get hpa portfolio-demo-hpa -o custom-columns="NAME:.metadata.name,CPU:.status.currentCPUUtilizationPercentage%,MEM:.status.currentMemoryUtilizationPercentage%,REPLICAS:.status.currentReplicas"
    sleep 5
done

wait

echo ""
echo "📈 Final HPA Status:"
kubectl get hpa portfolio-demo-hpa
echo ""

echo "🐳 Final Pod Count:"
kubectl get pods -l app=portfolio-demo
echo ""

echo "✅ Autoscaling test completed!"
echo ""
echo "💡 Tips for better autoscaling testing:"
echo "1. Use the full test script: ./test-autoscaling.sh"
echo "2. Monitor with: kubectl get hpa -w"
echo "3. Check metrics: kubectl top pods -l app=portfolio-demo"
echo "4. View HPA events: kubectl describe hpa portfolio-demo-hpa"
