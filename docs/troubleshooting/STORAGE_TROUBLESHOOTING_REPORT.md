# Storage Troubleshooting Report - EFS PersistentVolume Issues

**Date:** October 9, 2025  
**Phase:** Storage Error Phase  
**Duration:** Approximately 40 minutes  
**Status:** In Progress - Requires Manual Intervention

---

## Executive Summary

Encountered persistent issues with Kubernetes PersistentVolumes (PV) and PersistentVolumeClaims (PVC) getting stuck in "Terminating" and "Released" states during AWS EFS CSI driver deployment. This report documents the root causes, troubleshooting steps taken, and recommendations for resolution.

---

## Problem Statement

### Primary Issues

1. **PersistentVolumeClaims stuck in "Terminating" state**
   - PVC `advanced-efs-pvc` remained in Terminating state indefinitely
   - Finalizers (`kubernetes.io/pv-protection`) preventing deletion
   - Even after finalizer removal, PVC recreation led to binding issues

2. **PersistentVolumes stuck in "Released" state**
   - After PVC deletion, PV `advanced-efs-pv` entered "Released" state
   - Released PVs cannot bind to new PVCs due to claimRef retention
   - Repeated cycle: Delete → Recreate → Released → Pending

3. **Binding Loop**
   - New PVC remains in "Pending" state
   - PV shows "Released" with old claimRef
   - Manual intervention required to break the cycle

---

## Timeline of Events

### Initial State (T+0)
```
PV: advanced-efs-pv → Bound
PVC: advanced-efs-pvc → Bound
Status: Working configuration
```

### Issue Discovery (T+10m)
```
Issue: Incorrect EFS File System ID and Access Point ID in PV definitions
Action: Updated volumeHandle with correct values
Problem: Pods stuck in ContainerCreating with mount errors
```

### First Troubleshooting Attempt (T+15m)
```
Error: MountVolume.SetUp failed - provisioningMode not supported
Action: Removed volumeAttributes from PV definitions
Result: Needed to recreate PVs with corrected configuration
```

### Deletion Phase (T+20m)
```
Action: kubectl delete pv advanced-efs-pv
Result: PV stuck in "Terminating" state
Cause: Finalizer kubernetes.io/pv-protection
```

### Finalizer Removal (T+25m)
```
Action: kubectl patch pv advanced-efs-pv -p '{"metadata":{"finalizers":null}}'
Result: PV deleted successfully
Problem: PVC also stuck in Terminating
```

### PVC Finalizer Issues (T+30m)
```
Action: kubectl patch pvc advanced-efs-pvc -p '{"metadata":{"finalizers":null}}'
Result: PVC deleted
Problem: Recreation leads to "Released" PV state
```

### Current State (T+40m)
```
PV: advanced-efs-pv → Released (has old claimRef)
PVC: advanced-efs-pvc → Pending (cannot bind)
Status: Stuck in loop requiring manual intervention
```

---

## Root Causes Analysis

### 1. **Kubernetes PV Lifecycle Management**

**Issue:** PersistentVolumes retain claimRef even after PVC deletion

**Technical Details:**
- When a PVC is deleted, the PV's `spec.claimRef` field retains reference to the deleted PVC
- PV transitions to "Released" state instead of "Available"
- New PVCs cannot bind because the PV still "claims" to be bound to old PVC
- This is by design to prevent accidental data loss

**Root Cause:**
- Reclaim Policy set to "Retain" (intentional for data safety)
- No automatic cleanup of claimRef on PVC deletion
- Manual intervention required to clear claimRef

### 2. **Finalizers Preventing Deletion**

**Issue:** Kubernetes finalizers block resource deletion

**Technical Details:**
- Finalizers: `kubernetes.io/pv-protection` and `kubernetes.io/pvc-protection`
- Purpose: Ensure orderly cleanup and prevent premature deletion
- Problem: In error scenarios, finalizers can cause infinite loops

**Root Cause:**
- EFS CSI driver or related controllers not properly releasing resources
- Finalizers waiting for cleanup that never completes
- Requires manual finalizer removal (dangerous but necessary)

### 3. **EFS CSI Driver Configuration Errors**

**Issue:** Initial configuration had incorrect parameters

**Technical Details:**
```yaml
# WRONG - Caused mount failures
volumeAttributes:
  provisioningMode: efs-ap
  accessPointId: fsap-xxxxx
```

**Root Cause:**
- `volumeAttributes` redundant when using `fs-id::ap-id` format in `volumeHandle`
- AWS EFS CSI driver v2.x doesn't support `provisioningMode` in volumeAttributes
- Documentation inconsistency across CSI driver versions

---

## Troubleshooting Steps Attempted

### Step 1: Identify Stuck Resources
```bash
kubectl get pv,pvc
# Identified: PVs in Terminating, PVCs in Pending/Released
```

### Step 2: Check Finalizers
```bash
kubectl get pv advanced-efs-pv -o yaml | grep finalizers
kubectl get pvc advanced-efs-pvc -o yaml | grep finalizers
```

### Step 3: Remove PV Finalizers
```bash
kubectl patch pv advanced-efs-pv -p '{"metadata":{"finalizers":null}}'
kubectl patch pv shared-efs-pv -p '{"metadata":{"finalizers":null}}'
kubectl patch pv secure-efs-pv -p '{"metadata":{"finalizers":null}}'
```
**Result:** PVs deleted successfully

### Step 4: Remove PVC Finalizers
```bash
kubectl patch pvc advanced-efs-pvc -p '{"metadata":{"finalizers":null}}'
```
**Result:** PVC deleted but recreation leads to Released PV

### Step 5: Delete and Recreate Cycle (Multiple Iterations)
```bash
# Iteration 1
kubectl delete pv advanced-efs-pv
kubectl delete pvc advanced-efs-pvc
kubectl apply -f k8s/storage/
# Result: PV Released, PVC Pending

# Iteration 2
kubectl delete pv advanced-efs-pv
kubectl apply -f k8s/storage/02-efs-persistent-volumes.yaml
kubectl apply -f k8s/storage/03-efs-claims.yaml
# Result: Same - PV Released, PVC Pending

# Iteration 3+
# Got interrupted, process hangs
```

### Step 6: Current Blocker
- Commands hang during deletion phase
- Likely waiting for controller to release resources
- Manual intervention cycle becoming inefficient

---

## Technical Insights

### Why PVs Get "Released" Instead of "Available"

When a PVC is deleted:
1. PV's `status.phase` changes from `Bound` → `Released`
2. PV retains `spec.claimRef` pointing to deleted PVC
3. PV cannot bind to new PVC due to claimRef mismatch
4. New PVC stays `Pending` waiting for available PV

**Solution Required:**
```bash
# Must manually clear claimRef from PV
kubectl patch pv <pv-name> -p '{"spec":{"claimRef":null}}'
```

### Finalizer Protection Mechanism

Finalizers serve important purposes:
- **pv-protection**: Prevents PV deletion while bound to PVC
- **pvc-protection**: Prevents PVC deletion while mounted by pods

**When They Cause Issues:**
- Controllers offline or malfunctioning
- Resource state inconsistencies
- Race conditions during rapid create/delete cycles

**Safe Removal Process:**
1. Ensure no pods are using the PVC
2. Verify controller health
3. Remove finalizers only as last resort
4. Document actions for audit trail

### EFS CSI Driver Version Compatibility

**Key Learning:**
- AWS EFS CSI Driver v2.4.8+ uses simplified configuration
- `volumeHandle` format: `fs-<file-system-id>::fsap-<access-point-id>`
- No `volumeAttributes` needed for basic access point mounting
- Legacy formats from v1.x cause compatibility issues

**Correct Configuration:**
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: advanced-efs-pv
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: efs-sc-advanced
  csi:
    driver: efs.csi.aws.com
    volumeHandle: fs-0b3a076e9c8805489::fsap-03631d1b648d4b51c
    # NO volumeAttributes needed
```

---

## Current Infrastructure State

### EFS Resources (AWS)
```
File System: fs-0b3a076e9c8805489
Access Point: fsap-03631d1b648d4b51c
Status: Active and healthy
Mount Targets: Available in all subnets
```

### Kubernetes Resources
```
PersistentVolumes:
  - advanced-efs-pv: Released (stuck)
  - shared-efs-pv: Bound (working)
  - secure-efs-pv: Bound (working)

PersistentVolumeClaims:
  - advanced-efs-pvc: Pending (waiting for PV)
  - shared-efs-pvc: Bound (working)
  - secure-efs-pvc: Bound (working)

StorageClasses:
  - efs-sc-advanced: Created
  - efs-sc-shared: Created
  - efs-sc-secure: Created
  - efs-sc-performance: Created
```

---

## Recommendations

### Immediate Actions (to resolve current issue)

1. **Clear PV ClaimRef Manually**
```bash
kubectl patch pv advanced-efs-pv -p '{"spec":{"claimRef":null}}'
```

2. **Verify PV is Available**
```bash
kubectl get pv advanced-efs-pv
# Should show STATUS: Available
```

3. **Allow PVC to Bind**
```bash
kubectl get pvc advanced-efs-pvc
# Should transition from Pending → Bound
```

4. **Verify Binding**
```bash
kubectl get pv,pvc | grep advanced
# Both should show Bound status
```

### Short-Term Improvements

1. **Add Health Checks Before Deletion**
```bash
# Check for pods using PVC before deletion
kubectl get pods -o json | jq '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName=="advanced-efs-pvc")'
```

2. **Use Cascade Deletion Carefully**
```bash
# Delete PVC first (safer order)
kubectl delete pvc advanced-efs-pvc --wait=true
# Then delete PV
kubectl delete pv advanced-efs-pv --wait=true
```

3. **Implement Timeout Handling**
```bash
# Set timeout for delete operations
kubectl delete pv advanced-efs-pv --timeout=60s
```

### Long-Term Solutions

1. **Implement Dynamic Provisioning**
   - Use StorageClass with dynamic provisioning
   - Let EFS CSI driver create PVs automatically
   - Eliminates manual PV/PVC management

2. **Automated Cleanup Scripts**
   - Create scripts to detect and fix Released PVs
   - Implement pre-flight checks before deletion
   - Add retry logic with exponential backoff

3. **Better Resource Lifecycle Management**
   - Document PV/PVC creation/deletion procedures
   - Implement GitOps for storage resources
   - Use Helm charts for bundled deployments

4. **Monitoring and Alerting**
   - Monitor PV/PVC states with Prometheus
   - Alert on stuck Terminating resources
   - Dashboard for storage resource health

---

## Lessons Learned

### 1. **Kubernetes Storage is Stateful and Complex**
- PVs and PVCs have intricate lifecycle dependencies
- Deletion order matters: Pods → PVC → PV
- Finalizers are protection mechanisms, not bugs
- Understanding Reclaim Policies is critical

### 2. **CSI Driver Documentation Must Match Version**
- Always verify CSI driver version before configuring
- API changes between major versions are significant
- Test configurations in dev before production
- Keep driver documentation links versioned

### 3. **Manual Interventions Should Be Documented**
- Every `kubectl patch` to remove finalizers is risky
- Document reasons and results for audit trail
- Create runbooks for common stuck states
- Implement proper change management

### 4. **Testing PV/PVC Changes Requires Care**
- Rapid create/delete cycles cause race conditions
- Allow time for controllers to reconcile state
- Use `--wait=true` flags for synchronous operations
- Verify state transitions before next action

### 5. **Infrastructure as Code Benefits**
- GitOps approach would prevent manual drift
- Declarative configs easier to troubleshoot
- Version control provides rollback capability
- Automated testing catches config errors early

---

## Prevention Strategies

### 1. **Use Dynamic Provisioning Where Possible**
```yaml
# StorageClass with automatic provisioning
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc-dynamic
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-0b3a076e9c8805489
  directoryPerms: "755"
```

### 2. **Implement Proper Testing Pipeline**
- Lint Kubernetes manifests before apply
- Use `kubectl diff` to preview changes
- Test in staging environment first
- Implement canary deployments for storage changes

### 3. **Resource Naming Conventions**
- Include version or timestamp in resource names
- Use labels for lifecycle management
- Implement proper tagging strategy
- Document naming standards

### 4. **Backup and Recovery Procedures**
- Regular EFS backups via AWS Backup
- Export Kubernetes resource definitions
- Test restore procedures regularly
- Document recovery time objectives (RTO)

---

## Next Steps

### Immediate (Today)
1. Execute claimRef patch to resolve current stuck state
2. Verify all PVs and PVCs reach Bound state
3. Test pod mounting with corrected configuration
4. Document successful resolution steps

### Short-Term (This Week)
1. Create automated cleanup script for Released PVs
2. Implement pre-deletion health checks
3. Document standard operating procedures (SOPs)
4. Add monitoring for storage resource states

### Long-Term (This Month)
1. Migrate to dynamic provisioning where appropriate
2. Implement GitOps for storage resources
3. Create comprehensive testing suite
4. Conduct storage disaster recovery drill

---

## References

### Kubernetes Documentation
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [Using Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/)

### AWS EFS CSI Driver
- [GitHub Repository](https://github.com/kubernetes-sigs/aws-efs-csi-driver)
- [Installation Guide](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html)
- [Volume Parameters](https://github.com/kubernetes-sigs/aws-efs-csi-driver/blob/master/docs/README.md)

### Troubleshooting Resources
- [Debugging PVCs](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pvc/)
- [Storage Troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/debug-statefulset/)

---

## Conclusion

This storage error phase revealed the complexities of Kubernetes PersistentVolume lifecycle management and the importance of understanding CSI driver version compatibility. While the immediate issue (stuck PVs/PVCs) can be resolved with manual intervention, the root causes point to deeper needs:

1. **Better Understanding of Kubernetes Storage Primitives** - The stateful nature of PVs requires careful lifecycle management
2. **Improved Testing and Validation** - Configuration errors should be caught before deployment
3. **Automation and Monitoring** - Manual interventions are error-prone and don't scale
4. **Documentation and Knowledge Sharing** - Complex systems require comprehensive documentation

**Key Takeaway:** Kubernetes storage is not "fire and forget" - it requires ongoing management, monitoring, and understanding of underlying mechanisms. This incident provides valuable lessons for building more robust storage infrastructure.

---

**Report Prepared By:** AI Assistant  
**Review Status:** Pending Human Review  
**Action Items:** See Next Steps section  
**Severity:** Medium (Development Environment)  
**Impact:** Deployment blocked pending resolution  

---

*End of Report*


