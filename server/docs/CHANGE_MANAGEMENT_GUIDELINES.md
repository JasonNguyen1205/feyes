# Change Management Guidelines for Visual AOI Server

**Purpose:** Establish procedures for safely modifying code while preserving critical application logic  
**Reference:** [PROJECT_INSTRUCTIONS.md](./PROJECT_INSTRUCTIONS.md) - Core Logic Documentation

---

## 🚦 Change Classification System

### 🟢 Green Light Changes (Safe - No Review Required)
- **UI/Presentation**: Changing button colors, layout, labels
- **Logging**: Adding debug statements, improving log messages  
- **Documentation**: Updating comments, README, adding examples
- **Dependencies**: Adding new optional libraries (with fallbacks)
- **Performance**: Code optimizations that don't change logic
- **Testing**: Adding new test cases, improving test coverage

**Examples:**
```python
# ✅ Safe: Adding logging
logger.info(f"Processing ROI {roi_id} for device {device_id}")

# ✅ Safe: UI improvement
button.config(bg='#4CAF50', fg='white')

# ✅ Safe: Adding optional parameter with default
def process_roi(roi, img, product_name, debug_mode=False):
```

### 🟡 Yellow Light Changes (Moderate Risk - Peer Review Required)
- **Algorithm Improvements**: Enhancing ROI processing while preserving interface
- **New Features**: Adding optional functionality that doesn't break existing flows
- **Configuration**: Adding new product configuration fields with defaults
- **API Extensions**: Adding new optional parameters to existing endpoints
- **Error Handling**: Improving error messages and recovery mechanisms

**Examples:**
```python
# 🟡 Moderate: Adding new ROI type
elif roi_type == 4:  # New QR code type
    return process_qr_roi(...)

# 🟡 Moderate: Enhanced algorithm
def enhanced_golden_matching(roi_img, golden_images, threshold):
    # New algorithm but same return format
    return similarity_score, best_match
```

**Required Actions:**
1. Create feature branch
2. Write comprehensive tests
3. Get peer review
4. Test with existing product configurations
5. Update documentation if needed

### 🔴 Red Light Changes (High Risk - Full Review & Documentation Update Required)
- **Session Management**: Modifying session lifecycle, state management
- **Barcode Logic**: Changing device barcode priority/aggregation rules
- **API Contracts**: Modifying request/response formats
- **Database Schema**: Changing configuration file formats
- **Core Workflows**: Altering inspection pipeline, result aggregation
- **Backward Compatibility**: Removing support for legacy formats
- **ROI Structure**: Modifying ROI field definition (MUST update [ROI_DEFINITION_SPECIFICATION.md](./ROI_DEFINITION_SPECIFICATION.md) FIRST)
- **Result Structure**: Modifying inspection result format (MUST update [INSPECTION_RESULT_SPECIFICATION.md](./INSPECTION_RESULT_SPECIFICATION.md) FIRST)

**Examples:**
```python
# 🔴 High Risk: Changing session structure
class InspectionSession:
    def __init__(self, session_id, product_name, new_required_field):  # BREAKING

# 🔴 High Risk: Changing API response
return {
    'results': roi_results,  # Changed from 'roi_results'
    'summary': device_summaries  # Changed from 'device_summaries'
}

# 🔴 High Risk: Modifying barcode priority
def get_device_barcode(device_id):
    # Changed priority order - could break client expectations
```

**Required Actions:**
1. **STOP** - Review PROJECT_INSTRUCTIONS.md first
2. Create detailed design document
3. Update PROJECT_INSTRUCTIONS.md with new logic
4. Create comprehensive test suite
5. Multiple peer reviews
6. Backward compatibility plan
7. Migration strategy if needed
8. Update all related documentation

---

## 📋 Pre-Change Checklist

### Before Starting ANY Code Change:

#### 1. Classification Check ✅
- [ ] Classified change risk level (Green/Yellow/Red)
- [ ] Identified affected systems and components  
- [ ] Reviewed PROJECT_INSTRUCTIONS.md for relevant critical logic
- [ ] Reviewed ROI_DEFINITION_SPECIFICATION.md if touching ROI handling
- [ ] Reviewed INSPECTION_RESULT_SPECIFICATION.md if touching result format
- [ ] Confirmed no violations of "NEVER CHANGE" rules

#### 2. Planning Check ✅
- [ ] Created feature branch from latest main
- [ ] Defined clear acceptance criteria
- [ ] Planned rollback strategy
- [ ] Identified test scenarios
- [ ] Estimated impact on existing functionality

#### 3. Documentation Check ✅
- [ ] PROJECT_INSTRUCTIONS.md reviewed for affected logic
- [ ] API documentation impact assessed
- [ ] Configuration changes documented
- [ ] Breaking changes identified and documented

---

## 🔧 Implementation Guidelines

### Safe Coding Practices

#### 1. Preserve Critical Function Signatures
```python
# ✅ Good: Adding optional parameters with defaults
def process_roi(roi, img, product_name, optimization_level=1):
    
# ❌ Bad: Changing required parameters
def process_roi(roi, img, product_name, required_new_param):
```

#### 2. Maintain Backward Compatibility
```python
# ✅ Good: Supporting both old and new formats
def decode_image_data(data):
    if isinstance(data, dict) and 'image' in data:
        return data['image']  # New format
    return data  # Legacy format

# ❌ Bad: Breaking existing clients
def decode_image_data(data):
    return data['image']  # Assumes new format only
```

#### 3. Add Graceful Fallbacks
```python
# ✅ Good: Fallback on feature failure
try:
    result = new_ai_algorithm(image)
except Exception as e:
    logger.warning(f"New algorithm failed: {e}, using fallback")
    result = original_algorithm(image)

# ❌ Bad: Failing on new feature errors
result = new_ai_algorithm(image)  # No fallback
```

### Code Review Requirements

#### Green Light Changes
- **Self Review**: Code style, basic functionality
- **Automated Tests**: Must pass existing test suite
- **Deployment**: Can deploy directly to staging

#### Yellow Light Changes  
- **Peer Review**: One senior developer approval
- **Integration Tests**: Test with real product configurations
- **Staging Validation**: Full functionality testing
- **Documentation**: Update relevant docs

#### Red Light Changes
- **Architecture Review**: Lead developer + senior team member
- **Complete Test Suite**: Unit + integration + regression tests
- **Multiple Environments**: Test in dev, staging, and sandbox
- **Documentation**: Update PROJECT_INSTRUCTIONS.md + API docs
- **Migration Plan**: If changing data formats or APIs

---

## 🧪 Testing Requirements

### Mandatory Tests for All Changes

#### Core Functionality Tests
```python
def test_session_lifecycle():
    """Test complete session create -> inspect -> close flow"""
    
def test_device_barcode_priority():
    """Test barcode selection logic: ROI -> manual -> legacy -> default"""
    
def test_roi_processing_by_type():
    """Test each ROI type processes correctly"""
    
def test_device_aggregation():
    """Test results grouped correctly by device_id"""
```

#### API Contract Tests  
```python
def test_api_response_format():
    """Ensure all API responses match documented schemas"""
    
def test_backward_compatibility():
    """Test legacy request formats still work"""
    
def test_error_handling():
    """Test all error scenarios return proper HTTP codes"""
```

#### Configuration Tests
```python
def test_product_loading():
    """Test all product configuration formats load correctly"""
    
def test_roi_config_validation():
    """Test ROI configs validate and auto-upgrade properly"""
    
def test_golden_image_management():
    """Test golden image file operations"""
```

### Risk-Level Specific Tests

#### Yellow Light Additional Tests
- Performance regression tests
- Memory leak detection
- Concurrent session testing
- Product configuration compatibility

#### Red Light Additional Tests
- Complete end-to-end workflow testing
- Data migration testing (if applicable)
- Load testing with multiple scenarios
- Disaster recovery testing
- Client compatibility testing

---

## 📊 Change Review Process

### Review Checklist Template

#### For Reviewers:

**Functional Review:**
- [ ] Change classification is correct
- [ ] No violation of critical logic preservation rules
- [ ] Backward compatibility maintained
- [ ] Error handling is comprehensive
- [ ] Performance impact is acceptable

**Code Quality Review:**
- [ ] Code follows existing patterns and style
- [ ] Proper logging and error messages
- [ ] No hardcoded values or magic numbers
- [ ] Thread safety considerations addressed
- [ ] Resource cleanup is proper

**Testing Review:**
- [ ] Adequate test coverage for changes
- [ ] Tests cover both success and failure scenarios
- [ ] Integration tests validate end-to-end flows
- [ ] Performance tests show no regression

**Documentation Review:**
- [ ] PROJECT_INSTRUCTIONS.md updated if logic changed
- [ ] API documentation reflects any changes
- [ ] Code comments explain complex logic
- [ ] README updated if needed

---

## 🚨 Emergency Change Procedures

### When Production is Broken:

#### Immediate Response (0-15 minutes)
1. **Assess Impact**: Determine scope of failure
2. **Communicate**: Notify team and stakeholders  
3. **Decide**: Hotfix vs. rollback
4. **Execute**: Implement chosen solution
5. **Verify**: Confirm system is operational

#### Hotfix Process (High Risk Changes Only)
1. **Create hotfix branch** from production
2. **Minimal change scope** - fix only the critical issue
3. **Emergency review** - one senior developer approval
4. **Fast-track testing** - critical path only
5. **Deploy and monitor** closely
6. **Follow-up**: Proper review and testing post-deployment

#### Post-Emergency Review
- Root cause analysis
- Process improvement recommendations
- Documentation updates
- Additional monitoring implementation

---

## 📈 Continuous Improvement

### Monthly Logic Review Process

1. **Review PROJECT_INSTRUCTIONS.md** for accuracy
2. **Check for technical debt** in critical logic areas
3. **Assess change management effectiveness**
4. **Update procedures** based on lessons learned
5. **Plan refactoring** for risky legacy code

### Key Metrics to Monitor

- **Change Success Rate**: % of changes that don't require rollback
- **Time to Recovery**: Average time to fix broken functionality  
- **Backward Compatibility**: % of legacy clients still working
- **Test Coverage**: % of critical logic covered by tests
- **Documentation Freshness**: Last update date vs. code changes

---

## 🏆 Best Practices Summary

### Golden Rules for Code Changes

1. **Read First**: Always review PROJECT_INSTRUCTIONS.md before changing core logic
2. **Test Everything**: No change is too small for proper testing
3. **Document Changes**: Update docs BEFORE merging, not after
4. **Preserve Compatibility**: Never break existing clients
5. **Plan Rollbacks**: Always have a way to undo changes quickly
6. **Review Thoroughly**: Get appropriate level of review for change risk
7. **Monitor Post-Deploy**: Watch for issues after deployment

### Common Pitfalls to Avoid

❌ **Don't**: Modify session management without understanding full impact  
❌ **Don't**: Change API response formats without versioning  
❌ **Don't**: Remove backward compatibility "because it's old"  
❌ **Don't**: Skip testing with real product configurations  
❌ **Don't**: Deploy critical changes without rollback plan  
❌ **Don't**: Assume error handling will prevent all failures  
❌ **Don't**: Modify critical logic without updating documentation  

✅ **Do**: Add new features as optional extensions  
✅ **Do**: Preserve existing interfaces and add new ones  
✅ **Do**: Test extensively with legacy configurations  
✅ **Do**: Plan for graceful degradation on failures  
✅ **Do**: Document all logic changes immediately  

---

## 📝 Change Log: ROI Structure Updates

### Version 3.0 - Field 10: is_device_barcode (October 3, 2025)

**Change Type:** 🔴 Red Light - Structure Change  
**Status:** Completed with full backward compatibility

#### What Changed

Added Field 10 (`is_device_barcode`) to ROI structure:
- **Type:** `bool` or `None`
- **Purpose:** Mark specific barcode ROI as device's main identifier
- **Priority:** Highest priority in barcode selection logic
- **Default:** `None` (backward compatible)

#### Files Modified

1. **Specification Documents:**
   - `docs/ROI_DEFINITION_SPECIFICATION.md` - Updated to 11-field format
   - `docs/INSPECTION_RESULT_SPECIFICATION.md` - Updated barcode priority logic
   - `docs/PROJECT_INSTRUCTIONS.md` - Updated ROI format references
   - `README.md` - Updated ROI format documentation
   - `.github/copilot-instructions.md` - Updated ROI format

2. **Core Implementation:**
   - `src/roi.py` - Updated `normalize_roi()` for 11-field support
   - `src/roi.py` - Updated `load_rois_from_config()` for field 10
   - `server/simple_api_server.py` - Updated barcode priority logic

#### Backward Compatibility

- ✅ All legacy formats (3-10 fields) still supported
- ✅ Automatic upgrade to 11-field format with `is_device_barcode=None`
- ✅ Existing configurations work without modification
- ✅ Default behavior unchanged when field not specified

#### New Barcode Priority Logic

```
Priority 0: ROI with is_device_barcode=True (NEW - HIGHEST)
Priority 1: Any ROI barcode detected
Priority 2: Manual device_barcodes[device_id]
Priority 3: Legacy single device_barcode
Priority 4: Default "N/A"
```

#### Migration Notes

- **No action required** for existing systems
- **Optional adoption** of new field for multi-barcode scenarios
- **Use case:** When device has multiple barcodes, explicitly mark the device identifier
- **Example:** Product barcode vs. Device serial number - mark serial as `is_device_barcode=True`

#### Testing Performed

- ✅ Legacy 10-field configurations load correctly
- ✅ New 11-field configurations with `is_device_barcode=True` prioritize correctly
- ✅ New 11-field configurations with `is_device_barcode=None` behave as before
- ✅ Multiple barcode ROIs per device handled correctly
- ✅ Backward compatible auto-upgrade from all legacy formats

#### Documentation Updated

All specification documents updated to reflect v3.0 structure:
- Field definitions and constraints
- JSON configuration examples
- Priority logic documentation
- Implementation guidelines
- Common mistakes section
✅ **Do**: Get appropriate review for change risk level  
✅ **Do**: Monitor production after deployment  

---

## 📚 Essential Documentation References

### Before Making Changes - Read These:
1. **[PROJECT_INSTRUCTIONS.md](./PROJECT_INSTRUCTIONS.md)** - Core application logic and API behavior
2. **[ROI_DEFINITION_SPECIFICATION.md](./ROI_DEFINITION_SPECIFICATION.md)** - ROI structure format (v3.0, 11-field)
3. **[INSPECTION_RESULT_SPECIFICATION.md](./INSPECTION_RESULT_SPECIFICATION.md)** - Result structure format (v2.0)
4. **[SHARED_FOLDER_CONFIGURATION.md](./SHARED_FOLDER_CONFIGURATION.md)** - File exchange architecture (if working with file I/O)

### Infrastructure Documentation:
5. **[SWAGGER_DOCUMENTATION.md](./SWAGGER_DOCUMENTATION.md)** - API documentation system
6. **[SWAGGER_EXTERNAL_ACCESS.md](./SWAGGER_EXTERNAL_ACCESS.md)** - External access configuration
7. **[SCHEMA_API_ENDPOINTS.md](./SCHEMA_API_ENDPOINTS.md)** - Programmatic schema access

### After Making Changes - Update These:
1. ✅ Update relevant documentation files
2. ✅ Update Swagger documentation if API changes
3. ✅ Test thoroughly with all legacy formats
4. ✅ Update this change log (CHANGE_MANAGEMENT_GUIDELINES.md)
5. ✅ Verify all tests pass

---

**Remember: The goal is not to prevent change, but to change safely while preserving the critical business logic that makes the Visual AOI system reliable and trusted by production users.**