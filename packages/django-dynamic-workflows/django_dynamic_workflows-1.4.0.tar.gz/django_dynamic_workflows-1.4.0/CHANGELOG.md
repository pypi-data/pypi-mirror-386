# Changelog

All notable changes to django-dynamic-workflows will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2024-10-24

### ✨ Added

#### Email Notification System
- **Automatic Default Actions**: Workflows automatically get email notification actions for all events
  - AFTER_APPROVE: Notify creator when workflow approved
  - AFTER_REJECT: Notify creator when workflow rejected
  - AFTER_RESUBMISSION: Notify creator and current approver about resubmission
  - AFTER_DELEGATE: Notify delegated user and creator about delegation
  - AFTER_MOVE_STAGE: Notify creator about stage progression

- **Custom Actions via API**: Define custom actions when creating workflows, pipelines, or stages
  - Workflow-level actions (apply to entire workflow)
  - Pipeline-level actions (apply to specific pipeline)
  - Stage-level actions (apply to specific stage)
  - Action inheritance: Stage → Pipeline → Workflow → Default

- **Custom Email Integration**: Support for custom email services
  - Configure via `WORKFLOW_SEND_EMAIL_FUNCTION` setting
  - Compatible with SendGrid, Mailgun, AWS SES, etc.
  - Fallback to Django's EmailMultiAlternatives

- **Smart Recipient Resolution**: Automatic resolution of recipient types
  - `creator`: Object creator (object.created_by)
  - `current_approver`: Current approval step approver(s)
  - `delegated_to`: User receiving delegation
  - `workflow_starter`: User who started workflow
  - Direct email addresses
  - User objects or User IDs

- **Email Features**
  - Email deduplication to prevent duplicate sends
  - Bulk email processing for efficiency
  - HTML email templates with base template
  - Context-rich emails with workflow information

#### New Components (6 modules)
- `action_executor.py`: Execute workflow actions based on events
- `action_handlers.py`: Default email notification handlers
- `action_management.py`: Action creation, cloning, and management utilities
- `notifications.py`: Email sending service with context building
- `recipient_resolver.py`: Recipient type resolution
- `WorkflowActionInputSerializer`: Structured action input for Swagger/OpenAPI

#### Email Templates (6 templates)
- `base.html`: Base template for all workflow emails
- `workflow_approved.html`: Approval notification
- `workflow_rejected.html`: Rejection notification
- `workflow_action_required.html`: Stage progression notification
- `workflow_delegated.html`: Delegation notification
- `workflow_resubmission_required.html`: Resubmission notification

#### Configuration Settings
```python
WORKFLOW_AUTO_CREATE_ACTIONS = True  # Auto-create default actions
WORKFLOW_DISABLE_EMAILS = False      # Globally disable emails
WORKFLOW_SEND_EMAIL_FUNCTION = 'myapp.utils.send_email'  # Custom function
```

#### API Enhancements
- **WorkFlowSerializer**: Added optional `actions` field
- **PipelineSerializer**: Added optional `actions` field
- **StageSerializer**: Added optional `actions` field
- All action fields use `WorkflowActionInputSerializer` for clear API documentation

### 🎨 Changed

#### Admin Interface
- **Performance**: Removed workflow-related filters for better performance with large datasets
- **WorkflowAction Admin**: Enhanced scope display (Workflow/Pipeline/Stage)
- **Query Optimization**: Improved admin queries with select_related

### 📚 Documentation

- **README**: Added comprehensive "Email Notifications & Custom Actions" section
  - Configuration examples
  - Custom email function integration guide
  - Writing custom action handlers
  - Recipient types documentation
  - Testing with mocks
  - Best practices

### 🧪 Testing

- **New Tests**: 22 new tests (all passing)
  - 21 email notification tests
  - 1 workflow flow email integration test
- **Total Tests**: 307 (100% passing)
- **Test Coverage**: Comprehensive mocking for email testing

### 📊 Statistics

- **Files Added**: 12 (6 modules, 6 templates, 1 documentation)
- **Lines Added**: 3,798
- **Backwards Compatible**: Yes (all new features are optional)

### 🔄 Migration Notes

- **Existing Users**: No action required - all changes are backwards compatible
- **New Users**: Email notifications work out-of-the-box with default actions
- **Optional**: Configure custom email function or disable auto-creation as needed

## [1.3.1] - 2025-10-24

### 🐛 Fixed

- **Nested Conditional Forms**: Fixed type mismatch in `flatten_form_info` for nested form triggers
  - Resolves issue where nested forms were not being included when choice values had type mismatches
  - Now handles cases where `choice` is integer (e.g., `1`) but submitted value is string (e.g., `"1"`)
  - Properly normalizes both `trigger_choice` and `submitted_value` to strings for comparison
  - Fixes MULTI_CHOICE fields with integer choice values not triggering nested forms
  - Fixes DROP_DOWN fields with type mismatches between choice and submitted value
  - Example: Gender field with choice `1` (int) now correctly triggers when user submits `["1"]` (string array)

### 🧪 Testing

- **Nested Form Tests**: Added comprehensive test cases for nested conditional forms
  - Test MULTI_CHOICE with integer choice values triggering nested forms
  - Test DROP_DOWN with string choice values triggering nested forms
  - Test that nested forms are NOT triggered when different choice is selected
  - Test multi-level nested conditional forms (3+ levels deep)
  - All tests verify both flattening and answer enrichment work correctly

## [1.3.0] - 2025-10-24

### 🐛 Fixed

- **Form Enrichment**: Fixed `_enrich_form_data` to use current approval's form instead of stage.form_info
  - Ensures correct form is used when different approvers in the same stage have different forms
  - Form is now retrieved from `current_approval.form.form_info` instead of `stage.form_info`
  - Resolves issue where approval-specific forms were not being validated correctly

### ✨ Enhanced

- **Comprehensive Logging**: Added extensive logging to `WorkflowApprovalSerializer`
  - Info-level logs for major milestones and successful operations
  - Debug-level logs for detailed trace information and sub-steps
  - Warning-level logs for non-critical issues
  - Error-level logs for validation failures and errors
  - Logs include workflow ID, stage name, user ID, and object details for better debugging

### 🌍 Internationalization

- **Arabic Translations**: Updated Arabic translations for new serializer validation messages
  - "Reason is required for rejection" → "السبب مطلوب للرفض"
  - "Reason is required for resubmission" → "السبب مطلوب لإعادة التقديم"
  - "Stage does not belong to current workflow" → "المرحلة لا تنتمي إلى سير العمل الحالي"
  - "Invalid stage ID" → "معرف المرحلة غير صالح"
  - "Invalid user ID" → "معرف المستخدم غير صالح"
  - "Form data is required for this approval step" → "بيانات النموذج مطلوبة لهذه خطوة الموافقة"
  - "Object instance is required for workflow approval" → "مثيل الكائن مطلوب للموافقة على سير العمل"
  - "Failed to process approval action" → "فشل في معالجة إجراء الموافقة"

### 🧪 Testing

- **Nested Form Tests**: Added comprehensive test cases for nested conditional forms
  - Test MULTI_CHOICE with integer choice values triggering nested forms
  - Test DROP_DOWN with string choice values triggering nested forms
  - Test that nested forms are NOT triggered when different choice is selected
  - Test multi-level nested conditional forms (3+ levels deep)
  - All tests verify both flattening and answer enrichment work correctly
- **Test Improvements**: Fixed file upload test to avoid creating test files in workflows directory
  - Changed `save_files=True` to `save_files=False` in file upload tests
  - Updated test assertions to check for uploaded file object instead of URL
- **Mock Approval**: Updated form enrichment integration test to use mock approval object
  - Test now properly mocks approval instance with form containing form_info

## [1.2.9] - 2025-10-18

### 🔧 Resubmission Step Numbering Fix

This release fixes a critical bug in resubmission step numbering to ensure steps continue cumulatively across the workflow instead of restarting from 1.

### Fixed

- **Resubmission Step Numbering**: Steps now continue from the current step number instead of restarting from 1
  - Example: If at step 5 during resubmission, new steps start from 6, 7, 8, etc.
  - Prevents "Step number already exists in the flow" errors
  - Maintains cumulative step tracking across the entire workflow journey
  - Properly handles multiple resubmissions without step number conflicts

### Added

- **`start_step` Parameter**: Added to `build_approval_steps()` function in `utils.py`
  - Allows continuing step numbering from a specific point
  - Default value of 1 maintains backward compatibility
  - Essential for resubmission flows and workflow extensions

- **Step Number Calculation**: Enhanced `_prepare_resubmission_steps()` in `serializers.py`
  - Calculates starting step as `current_step_number + 1`
  - Ensures proper step continuation after resubmission
  - Adds comprehensive logging for debugging

- **Handler Hook**: Added `on_resubmission()` method to `WorkflowApprovalHandler`
  - Implements newer approval_workflow API
  - Delegates to `after_resubmission()` for backward compatibility
  - Fixes missing method errors during resubmission

### Enhanced

- **`ApprovalStepBuilder.build_steps()`**: Now accepts `start_step` parameter
  - Passes through to `build_approval_steps()` utility function
  - Enables step number continuation for resubmission scenarios
  - Maintains backward compatibility with default value

- **Step Enumeration**: Updated to use `enumerate(approvals, start=start_step)`
  - Dynamically starts numbering from specified step
  - Replaces hardcoded `start=1` with configurable parameter
  - Supports complex workflow progression patterns

### Technical Details

- **Backward Compatible**: Existing workflows continue to work unchanged
- **No Breaking Changes**: Default parameter values maintain current behavior
- **Smart Calculation**: Uses current approval step number to determine continuation point
- **Comprehensive Logging**: Added info-level logs to track step number calculations

### Benefits

- ✅ **Fixes resubmission errors**: No more "step already exists" errors
- ✅ **Cumulative tracking**: Step numbers track entire workflow journey, not per-stage
- ✅ **Multiple resubmissions**: Supports multiple resubmission cycles without conflicts
- ✅ **Better audit trail**: Sequential step numbers provide clear workflow history
- ✅ **Delegation support**: Works seamlessly with delegation (which keeps same step number)

### Files Changed

- `django_workflow_engine/utils.py`: Added `start_step` parameter to `build_approval_steps()` (lines 102-209)
- `django_workflow_engine/handlers.py`: Added `start_step` parameter to `ApprovalStepBuilder.build_steps()` and `on_resubmission()` hook (lines 165-177, 314-316)
- `django_workflow_engine/serializers.py`: Enhanced `_prepare_resubmission_steps()` with step calculation logic (lines 293-369)

### Migration Notes

- **No action required**: This is a bug fix with backward compatibility
- **Automatic**: Resubmissions will automatically use new numbering
- **Testing**: Verify resubmission flows work correctly in your workflow stages

---

## [1.2.8] - 2025-10-12

### 🔧 Pipeline Order Auto-Generation

This release adds intelligent automatic order generation for pipelines when order values are not provided.

### Added

- **Automatic Pipeline Order Generation**: `create_workflow()` now detects when all pipelines have `order=0` or `order=None`
  - Automatically generates incremental order values (0, 1, 2, etc.)
  - Prevents manual ordering errors for apps that don't send proper order values
  - Maintains existing order values when at least one pipeline has a non-zero order
  - Adds info logging when auto-generation occurs for debugging

### Enhanced

- **`create_workflow()` Function**: Enhanced pipeline creation logic
  - Checks all pipeline orders before creation
  - Auto-assigns sequential orders when all orders are 0 or null
  - Preserves explicit order values when provided
  - First pipeline gets order 0, second gets 1, third gets 2, etc.

### Technical Details

- **Backward Compatible**: Existing workflows with explicit orders continue to work unchanged
- **No Breaking Changes**: Only activates when all pipelines have order 0 or None
- **Smart Detection**: Uses `all()` to check if auto-generation should occur
- **Performance**: Minimal overhead, single pass through pipeline data

### Benefits

- ✅ **Prevents ordering issues**: Apps that forget to send order values get automatic ordering
- ✅ **Reduces errors**: No more pipelines with identical orders causing confusion
- ✅ **Developer friendly**: Works automatically without configuration
- ✅ **Preserves control**: Apps can still specify custom orders when needed

### Files Changed

- `django_workflow_engine/services.py`: Enhanced `create_workflow()` with auto-order generation logic (lines 134-146)

---

## [1.2.7] - 2025-10-12

### 🎯 Automatic Status Updates on Workflow Completion/Rejection

This release introduces intelligent automatic status management for your models based on workflow outcomes.

### Added

- **Completion Status Updates**: `WorkflowConfiguration.completion_status_value` field
  - Automatically updates model's status field when workflow completes successfully
  - Example: Set Opportunity status to "won" when deal approval completes

- **Rejection Status Updates**: `WorkflowConfiguration.rejection_status_value` field
  - Automatically updates model's status field when workflow is rejected
  - Example: Set Opportunity status to "lost" when deal is rejected

- **Smart Status Update Function**: `update_object_status()` in services.py
  - Validates field existence before updating
  - Uses efficient `update_fields` for performance
  - Comprehensive logging for audit trail
  - Graceful handling of missing configurations

### Enhanced

- **`complete_workflow()` Function**: Now automatically updates object status on completion
  - Checks for `completion_status_value` configuration
  - Updates content object's status field if configured
  - Maintains backward compatibility (no updates if not configured)

- **`reject_workflow_stage()` Function**: Now automatically updates object status on rejection
  - Checks for `rejection_status_value` configuration
  - Updates content object's status field if configured
  - Maintains backward compatibility (no updates if not configured)

### Migration

- **Migration 0004**: Adds `completion_status_value` and `rejection_status_value` fields to `WorkflowConfiguration`
  - Both fields are optional (blank=True)
  - CharField with max_length=100
  - Includes helpful documentation in help_text

### Documentation

- **Comprehensive README Section**: Added "Automatic Status Updates on Workflow Completion/Rejection"
  - Configuration examples for multiple use cases
  - Real-world examples: CRM Opportunities, Support Tickets, Purchase Requests
  - Django Admin configuration guide
  - Best practices and logging information
  - Migration instructions

### Use Cases

**Example 1: CRM Opportunity**
```python
config.completion_status_value = 'won'   # Deal closed successfully
config.rejection_status_value = 'lost'   # Deal failed
```

**Example 2: Support Ticket**
```python
config.completion_status_value = 'closed'      # Ticket resolved
config.rejection_status_value = 'cancelled'    # Ticket cancelled
```

**Example 3: Purchase Request**
```python
config.completion_status_value = 'approved'  # Purchase approved
config.rejection_status_value = 'denied'     # Purchase denied
```

### Technical Details

- **Backward Compatible**: Completely optional feature, existing code works unchanged
- **No Breaking Changes**: All status updates only happen if explicitly configured
- **Efficient Updates**: Uses `update_fields` to only update the status field
- **Comprehensive Logging**:
  - Info logs on successful updates
  - Warning logs if configured field doesn't exist
  - Debug logs when not configured

### Benefits

- ✅ **Eliminates manual status management**: No need to update status in custom code
- ✅ **Ensures consistency**: Model status always reflects workflow state
- ✅ **Audit trail**: All status updates are logged automatically
- ✅ **Flexible**: Configure different status values for different models
- ✅ **Optional**: Fully backward compatible, only works when configured

### Files Changed

- `django_workflow_engine/models.py`: Added `completion_status_value` and `rejection_status_value` fields
- `django_workflow_engine/services.py`: Added `update_object_status()` function and updated workflow completion/rejection logic
- `django_workflow_engine/migrations/0004_add_status_values_to_workflowconfiguration.py`: New migration
- `README.md`: Added comprehensive documentation section with examples
- `django_workflow_engine/__init__.py`: Version bump to 1.2.7
- `pyproject.toml`: Version bump to 1.2.7

---

## [1.2.6] - 2025-10-06

### 🚀 Handler Discovery Integration & Workflow Compatibility Update

### Changed
- **Dependency Upgrade:** Updated `django-approval-workflow` to version **0.8.5**
  - Adds `APPROVAL_HANDLER_DISCOVERY_FUNCTION` for flexible handler resolution
  - Maintains backward compatibility with `APPROVAL_HANDLERS` list
  - Improves SUBMIT type validation for consistent behavior

### Added
- **Handler Discovery Compatibility:**
  - Integrated new discovery mechanism for automatic handler detection via app label and model name
  - Retained legacy `OpportunityApprovalHandler` fallback for CRM workflows
  - Added detailed debug logs for discovery order and fallback resolution
  - Compatible with both custom discovery functions and built-in handlers

### Fixed
- **Automatic Handler Resolution:**
  - Ensured all workflow progression tests continue to work with automatic handlers
  - Preserved multi-pipeline transitions without requiring manual handler registration
  - Prevented handler import errors when CRM app not installed
  - Added safe import guards and structured debug logging

### Improved
- Unified logging format for handler discovery and fallback resolution
- Simplified compatibility layer ensuring smooth transition to handler discovery in v0.8.5
- Verified compatibility with `WorkflowApprovalHandler` auto-progression and pipeline synchronization

### Technical
- Updated `handlers.py` with custom discovery and safe fallback mechanism
- Updated `requirements.txt` to use `django-approval-workflow==0.8.5`
- All workflow progression and multi-pipeline tests passing successfully

### Impact
Developers can now leverage advanced handler discovery patterns introduced in `django-approval-workflow v0.8.5`
while retaining seamless workflow progression and multi-pipeline support with zero configuration changes required.

## [1.2.5] - 2025-10-05

### Fixed
- **Progress Calculation**: Fixed `progress_percentage` returning 0 when workflow is completed. Now correctly returns 100% for completed workflows.
- **Pipeline Synchronization**: Added automatic synchronization of `current_pipeline` with `current_stage.pipeline` to prevent inconsistencies.

### Added
- **Form Enrichment**: Added `flatten_form_info()` and `enrich_answers()` utilities for handling nested/conditional forms with proper answer key integration.
- **Enhanced Tests**: Added comprehensive tests for:
  - Form enrichment with nested forms (dropdown, multi-choice triggers)
  - Progress calculation across single and multiple pipelines (16 new tests)
  - Complete workflow flow from start to completion
  - Pipeline movement and synchronization

### Changed
- WorkflowAttachment now auto-syncs `current_pipeline` on save to ensure data consistency
- WorkflowApprovalSerializer now enriches form data with answer keys automatically

## [1.2.4] - 2025-10-05

### 🚀 Major Enhancement: Zero-Configuration Workflow Progression

**The Big Win**: Developers no longer need to create custom approval handlers! The package now handles everything automatically.

#### What Changed

- **Eliminated UNIQUE constraint violations**: `move_to_next_stage()` now uses `extend_flow()` instead of `start_flow()`
- **Automatic workflow progression**: Built-in `WorkflowApprovalHandler` handles stage transitions seamlessly
- **No manual handler registration needed**: Handler auto-detects when workflow is attached to an object

#### Before (Manual Handler Required)

Previously, developers had to create custom approval handlers like this:

```python
# OLD WAY - Required custom handler in your project
class OpportunityApprovalHandler(BaseApprovalHandler):
    def on_final_approve(self, approval_instance):
        # Manually update WorkflowAttachment
        # Manually extend approval flow
        # Manually handle step numbering
        # ~120 lines of boilerplate code
```

And register it in settings:
```python
APPROVAL_HANDLERS = [
    "myapp.approval.OpportunityApprovalHandler",
]
```

#### After (Simple Configuration)

Now, just register the built-in handler and attach workflows:

```python
# settings.py - One-time setup
APPROVAL_HANDLERS = [
    "django_workflow_engine.handlers.WorkflowApprovalHandler",
]

# In your code - No custom handler code needed!
from django_workflow_engine.services import attach_workflow_to_object

attachment = attach_workflow_to_object(
    obj=opportunity,
    workflow=workflow,
    user=request.user,
    auto_start=True
)

# Approvals automatically progress through stages
# Pipeline transitions happen seamlessly
# Workflow completes when reaching final stage
```

### 🔧 Technical Improvements

- **Fixed ApprovalFlow.DoesNotExist error**: Using `extend_flow()` prevents UNIQUE constraint violations
- **Proper step numbering**: New approval steps continue from the last step number
- **Enhanced logging**: Added detailed logs for flow extension operations
- **Seamless flow continuation**: Single approval flow spans all stages and pipelines

### 📋 Files Changed

- `django_workflow_engine/services.py`: Updated `move_to_next_stage()` to use `extend_flow()`
- `tests/test_services.py`: Updated test to mock `extend_flow()` instead of `start_flow()`
- Dependency: Now requires `django-approval-workflow>=0.8.4` for `extend_flow()` support

### ✅ Migration Notes

**No breaking changes!** Existing code continues to work.

If you previously created custom approval handlers (like `OpportunityApprovalHandler`), you can now:
1. **Delete your custom handler file** (e.g., `crm/approval.py`)
2. **Update `APPROVAL_HANDLERS`** to use the built-in handler:
   ```python
   # settings.py
   APPROVAL_HANDLERS = [
       "django_workflow_engine.handlers.WorkflowApprovalHandler",  # Built-in handler
   ]
   ```
3. Keep using `attach_workflow_to_object()` as before

The built-in `WorkflowApprovalHandler` now handles everything automatically!

### 🎯 What This Means for You

- ✅ **Less boilerplate**: No need to write ~120 lines of handler code per model
- ✅ **Fewer bugs**: Package handles all edge cases internally
- ✅ **Easier maintenance**: Updates to workflow logic happen in the package, not your code
- ✅ **Faster development**: One-line setup in settings, then just attach workflows!

### 📝 Required Configuration

**Important**: You must register the built-in handler in your settings:

```python
# settings.py
APPROVAL_HANDLERS = [
    "django_workflow_engine.handlers.WorkflowApprovalHandler",
]
```

This tells the `approval-workflow` package to use the built-in handler for workflow progression.

---

## [1.2.3] - 2025-10-05

### 🐛 Critical Bug Fixes
- **Fixed workflow completion not clearing stage/pipeline references**:
  - `complete_workflow()` now sets `current_stage` and `current_pipeline` to None
  - Prevents confusion about workflow state when checking if workflow is complete
  - Ensures proper cleanup when workflow reaches final stage

- **Fixed pipeline change detection crash**:
  - Added null checks to `pipeline_changed` logic in `move_to_next_stage()`
  - Previously crashed when `current_pipeline` was None
  - Now properly handles: `pipeline_changed = current_pipeline and next_pipeline and current_pipeline.id != next_pipeline.id`

- **Fixed inconsistent user handling in workflow progression**:
  - Created centralized `get_user_for_approval()` utility function
  - Consistent user fallback logic: user parameter → obj.created_by → obj.started_by → attachment.started_by
  - Both `start_workflow_for_object()` and `move_to_next_stage()` now use same user resolution strategy
  - Prevents failures when user is not provided

### ⚡ Performance & Debugging Enhancements
- **Added comprehensive logging system**:
  - Created centralized `ERROR_MESSAGES` and `LOG_MESSAGES` constants
  - Added debug logging for stage transitions and pipeline changes
  - Workflow progression now has detailed logging for troubleshooting
  - Better visibility into approval flow creation and stage movements

- **Enhanced error messages**:
  - Replaced hardcoded error strings with constants
  - Clearer messages for workflow not found, no next stage, etc.
  - Improved developer experience when debugging workflow issues

### 🎯 ApprovalType Integration
- **Full ApprovalType support** (from v1.2.2):
  - APPROVE: Standard approval with optional form
  - SUBMIT: Requires form, typically for initial submission
  - CHECK_IN_VERIFY: Physical verification type with optional form
  - MOVE: Automatic stage transition without form
  - Case-insensitive validation for all approval types

- **Enhanced serializer validation**:
  - `StageSerializer` validates ApprovalType configuration
  - SUBMIT type enforces required_form presence
  - MOVE type prevents form assignment
  - Clear validation error messages at serializer level

### 🧪 Testing Improvements
- **Added 12 new comprehensive test files**:
  - `test_approval_types.py`: Validates all ApprovalType behaviors and validation rules
  - `test_pipeline_approval_type_integration.py`: Multi-pipeline workflows with mixed approval types
  - `test_pipeline_transitions.py`: Pipeline and stage transition logic
  - `test_handlers_coverage.py`: Handler method coverage
  - `test_models_coverage.py`: Model method coverage
  - `test_services_coverage.py`: Service function coverage
  - `test_utils.py`: Utility function coverage
  - Additional coverage tests for edge cases

- **264 tests now passing**: Comprehensive test coverage for all workflow scenarios
- **Test execution time**: ~2.3 seconds (highly optimized)
- **Coverage includes**:
  - Final stage approval completing workflow successfully
  - Multi-pipeline transitions with proper event triggering
  - Workflow completion setting stage/pipeline to None
  - User fallback logic in approval step creation
  - All ApprovalType validation scenarios

### 📋 Technical Details
- **Files changed**:
  - `django_workflow_engine/services.py`: Fixed move_to_next_stage and complete_workflow
  - `django_workflow_engine/handlers.py`: Enhanced on_final_approve workflow progression
  - `django_workflow_engine/utils.py`: Added get_user_for_approval utility
  - `django_workflow_engine/constants.py`: Added ERROR_MESSAGES and LOG_MESSAGES
  - `django_workflow_engine/models.py`: Enhanced ApprovalType validation
  - `django_workflow_engine/serializers.py`: Added ApprovalType serializer validation

- **Backward compatible**: All changes maintain full backward compatibility
- **No breaking changes**: Existing code continues to work without modifications
- **No migrations required**: All changes are code-level only

### ✅ Verified Scenarios
- ✅ Final stage approval completes workflow and clears stage/pipeline
- ✅ Multi-pipeline transitions work correctly with proper event firing
- ✅ Pipeline change detection handles None values gracefully
- ✅ User fallback works consistently across all workflow operations
- ✅ All ApprovalTypes (APPROVE, SUBMIT, CHECK_IN_VERIFY, MOVE) validated correctly
- ✅ Comprehensive logging helps with debugging workflow issues

---

## [1.2.0] - 2025-10-02

### 🎯 New Features
- **Added `is_hidden` field to WorkFlow, Pipeline, and Stage models**:
  - Main workflows, pipelines, and stages have `is_hidden=False` by default
  - Cloned workflows, pipelines, and stages automatically have `is_hidden=True`
  - Enables hiding cloned objects from UI listings while maintaining database records
  - Useful for workflow versioning and template management
  - Migration 0003_add_is_hidden_to_workflow included

### ⚡ Performance Optimizations
- **Stage.save() performance improvements**:
  - Added `skip_workflow_update=True` parameter to Stage.save() method
  - Prevents expensive workflow validation on every stage save
  - **8-13x performance improvement** when creating multiple stages
  - Recommended for bulk operations and test suites

### 🧪 Testing Enhancements
- **Added comprehensive test for is_hidden field**:
  - `WorkflowCloneHiddenFieldTest.test_main_workflow_is_not_hidden_and_cloned_is_hidden()`
  - Validates is_hidden behavior for all three models (WorkFlow, Pipeline, Stage)
  - Verifies cloned_from relationships are maintained
- **Added performance demonstration test**:
  - `tests/test_performance_demo.py` shows 13.8x speedup with optimization
  - Includes performance comparison output for developers
  - Run with: `pytest tests/test_performance_demo.py -v -s`

### 🔧 Code Quality
- **Optimized test suite performance**:
  - Updated test_models.py to use skip_workflow_update where appropriate
  - Test suite improved from 14.17s to 13.36s (5.7% faster)
  - Individual stage operations up to 13.8x faster with optimization

### 📋 Technical Details
- **Backward compatible**: All changes maintain backward compatibility
- **No breaking changes**: Existing code continues to work without modifications
- **Migration included**: 0003_add_is_hidden_to_workflow adds is_hidden to all three models
- **Performance gains**: Optional optimization available for bulk operations

### 🎯 Use Cases
- **Workflow versioning**: Hide old workflow versions while keeping them for audit
- **Template management**: Create workflow templates and hide cloned instances
- **Bulk operations**: Significantly faster when creating multiple stages
- **Test performance**: Faster test execution with skip_workflow_update

---

## [1.1.0] - 2025-10-01

### 🐛 Critical Bug Fixes
- **Fixed build_approval_steps conflict**: Resolved "cannot have both 'assigned_to' and 'assigned_role'" error
  - Removed initialization of `assigned_to` and `role_selection_strategy` in base step dictionary
  - Now only relevant keys are added based on approval type (user-based OR role-based)
  - Prevents approval workflow package from rejecting steps with conflicting keys
  - This was causing workflow start failures for role-based approvals

### 🎯 Enhanced User Handling
- **Robust approval_user processing**: Now handles multiple input formats seamlessly
  - Supports integer user IDs: `approval_user: 123`
  - Supports dict format with "val" key: `approval_user: {"val": 123}`
  - Supports direct User objects: `approval_user: user_instance`
  - Automatic fallback to `created_by_user` when user not found
  - Error logging for debugging when user lookup fails
  - Consistent User object output regardless of input format

### 🎯 Code Quality Improvements
- **Replaced all hardcoded strings with enum constants**:
  - `ApprovalTypes.ROLE`, `ApprovalTypes.USER`, `ApprovalTypes.SELF` instead of strings
  - `RoleSelectionStrategy.ROUND_ROBIN`, `RoleSelectionStrategy.ANYONE`, `RoleSelectionStrategy.CONSENSUS` instead of strings
  - Updated README examples to use enum constants
  - Updated all test files to use enum constants
  - Better type safety and IDE support
- **Fixed type hint warnings**:
  - Resolved "Expected type 'int | dict[str, Any]'" warning for role_selection_strategy
  - Changed from `.get()` with default to explicit None check for better type safety
  - Cleaner code that satisfies static type checkers

### ⚙️ Dynamic Validation
- **Validation now uses enum choices dynamically**:
  - `valid_approval_types` generated from `ApprovalTypes.choices`
  - `valid_strategies` generated from `RoleSelectionStrategy.choices`
  - Automatically stays in sync with enum definitions
  - Removed hardcoded validation lists

### 📚 Documentation Enhancements
- **Added comprehensive Approval Package setup guide in README**:
  - Step-by-step model configuration instructions
  - Three implementation options (Django Group, Custom Role, Dynamic Forms)
  - Complete settings examples with best practices
  - Proper placement in Quick Start guide for better discoverability

### ✅ Testing
- **Added 3 new test cases for build_approval_steps**:
  - `test_build_approval_steps_role_based_no_assigned_to_conflict`: Verifies role-based approvals don't have `assigned_to`
  - `test_build_approval_steps_user_based_no_role_conflict`: Verifies user-based approvals don't have `assigned_role`
  - `test_build_approval_steps_mixed_approvals_no_conflicts`: Verifies mixed approval types work correctly
- **Updated stage configuration examples in README**:
  - Added `name_en`, `name_ar`, `pipeline_id` as stage-level fields
  - Clarified distinction between Stage model fields and `stage_info` JSON configuration
- **All 150 tests passing**: Full test coverage maintained

### 📋 Technical Details
- **Backward compatible**: No breaking changes to existing API
- **Bug fix priority**: Resolves critical workflow start failures
- **Best practices**: Following Django/Python enum patterns throughout
- **Improved maintainability**: Code is more maintainable with enum constants

---

## [1.0.9] - 2025-10-01

### 🐛 Bug Fixes
- **Fixed department_generic_fk setting**: `create_pipeline` now correctly sets department generic foreign key
  - Fixed `set_pipeline_department` to use lowercase model name for ContentType lookup
  - ContentType model field is always stored in lowercase in Django
  - Previously failed silently when department_id was provided

### ⚙️ Configuration
- **Added DJANGO_WORKFLOW_ENGINE settings**: Proper configuration support for department model mapping
  - Added `DEPARTMENT_MODEL` setting in sandbox/settings.py for testing
  - Ensures department mapping works correctly across different environments

### ✅ Testing
- **Added comprehensive test coverage for pipeline department functionality**:
  - `test_create_pipeline_with_department`: Verifies department_generic_fk is set correctly when department_id is provided
  - `test_create_pipeline_without_department`: Ensures pipeline creation works without department_id
  - `test_set_pipeline_department`: Validates set_pipeline_department function directly
- **All 18 service tests passing**: Complete test coverage for department-related functionality

### 📋 Technical Details
- **Backward compatible**: No breaking changes to existing API
- **Bug fix only**: Resolves issue where department was not being set when using create_pipeline service
- **Better error handling**: Silent failures now properly addressed with correct ContentType lookup

---

## [1.0.8] - 2025-09-30

### 🎯 ApprovalTypes Enhancements
- **Updated ApprovalTypes enum**: Added new approval type choices with translation support
  - `SELF = "self-approved"` - Self approval type
  - `ROLE = "role"` - Role-based approval
  - `USER = "user"` - User-specific approval
  - `TEAM_HEAD = "team_head"` - Team head approval (reserved for future use)
  - `DEPARTMENT_HEAD = "department_head"` - Department head approval (reserved for future use)
- **Dynamic validation**: Stage model now validates approval types against ApprovalTypes enum dynamically
- **Translation ready**: All approval type labels now use `gettext_lazy` for internationalization

### 🌍 Translation Improvements
- **Complete model translation**: All `help_text` and `verbose_name` strings now wrapped with `_()` for translation
- **BaseCompanyModel translations**: Company, name fields fully translatable
- **Pipeline model translations**: Department fields with proper translation support
- **Stage model translations**: Form and stage info fields translated
- **WorkflowAttachment translations**: All workflow state fields translatable
- **WorkflowConfiguration translations**: Hook and field mapping descriptions translated
- **WorkflowAction translations**: Action configuration fields fully translated

### 🔧 StageSerializer Enhancements
- **Pipeline validation**: Added smart pipeline detection from URL or request body
- **URL parameter support**: Automatically extracts `pipeline` or `pipeline_pk` from URL kwargs
- **Body parameter support**: Falls back to pipeline from request body if not in URL
- **Clear error messages**: Descriptive validation error when pipeline is missing
- **Create vs Update logic**: Pipeline validation only required for create operations

### ✅ Testing
- **Added stage update test**: New test case `test_update_stage_info_with_role_approval`
- **Validates name fields**: Tests confirm Stage has `name_en` and `name_ar` fields
- **Approval configuration test**: Verifies role-based approval with all required fields
- **11/11 tests passing**: All serializer tests pass with new changes

### 🗄️ Database Migrations
- **Migration 0002**: Created migration for model option changes
- **Index optimization**: Renamed indexes for better clarity
- **Field updates**: Updated cloned_from fields with proper help text
- **Status choices**: Updated WorkflowStatus and WorkflowAttachmentStatus choices

### 📋 Technical Details
- **Backward compatible**: All changes maintain backward compatibility
- **No breaking changes**: Existing code continues to work without modifications
- **Enhanced validation**: More robust approval type validation using enum
- **Better DX**: Improved developer experience with clearer error messages

---

## [1.0.7] - 2025-09-30

### 🚀 New Workflow Serializers
- **Added WorkFlowSerializer**: Complete nested creation of workflows with pipelines and stages in a single API call
- **Added PipelineSerializer**: Create pipelines with automatic stage generation based on `number_of_stages` parameter
- **Added StageSerializer**: Create and update stages with approval configuration validation
- **Nested serialization support**: Create entire workflow hierarchies in one request with proper validation
- **README examples now functional**: All serializer examples in documentation are now fully working

### ⚡ Workflow Auto-Activation System
- **Intelligent stage activation**: Stages automatically activate when approval configurations are added
- **Auto-deactivation**: Stages deactivate when all approvals are removed
- **Workflow-level activation**: Workflows automatically activate when all stages are properly configured
- **Real-time validation**: Stage and workflow status updates happen automatically on configuration changes
- **Performance optimized**: Added `skip_workflow_update` parameter to Stage.save() for bulk operations

### 🔧 Serializer Improvements
- **Refactored WorkflowApprovalSerializer**: Now uses standard DRF `self.instance` pattern instead of custom `object_instance` parameter
- **Developer flexibility**: All serializers now use `fields = "__all__"` in Meta, allowing easy customization by subclassing
- **Better context handling**: Automatic `company` extraction from context when not provided
- **Standard DRF patterns**: Simplified serializer initialization following Django Rest Framework conventions
- **Comprehensive logging**: Added structured logging throughout all serializers using WorkflowLogger

### 🎯 Validation & Error Handling
- **Case-insensitive approval types**: Approval types ('user', 'role', 'self') now validated case-insensitively
- **Case-insensitive strategies**: Role selection strategies ('anyone', 'consensus', etc.) validated case-insensitively
- **Stage completion validation**: Stages require proper approval configuration to be considered complete
- **Better error messages**: Clear validation errors with helpful guidance for developers

### 🚀 Performance Optimizations
- **Query optimization**: Added `prefetch_related` to workflow validation to prevent N+1 queries
- **Bulk operation support**: Stage.save() accepts `skip_workflow_update` flag for bulk operations
- **Reduced redundant validation**: Workflow active status only updates when necessary
- **Optimized test fixtures**: Test setup optimized to reduce unnecessary workflow validations

### 📚 Documentation Updates
- **Fixed README examples**: Updated all code examples to use correct lowercase approval types and strategies
- **Added comprehensive tests**: 10 new tests validating all README serializer examples work correctly
- **Better developer guidance**: Enhanced documentation with working examples and best practices

### 🧪 Testing Improvements
- **All tests passing**: 143/143 tests passing with new validation requirements
- **Updated test fixtures**: All test stages now include proper `stage_info` with approvals
- **README example tests**: New test file validates all documentation examples work correctly
- **Improved test patterns**: Tests now follow standard DRF patterns with `instance=` parameter

### 🛠 Technical Details
- **Migration path**: Existing workflows need stages updated with approval configurations to activate
- **Backward compatible**: No breaking changes to existing API or data structures
- **Standard DRF usage**: WorkflowApprovalSerializer now follows standard serializer patterns
- **Proper field configuration**: Read-only and write-only fields properly configured across all serializers

### 📋 Migration Notes
- Existing stages without approval configurations will be inactive until approvals are added
- WorkflowApprovalSerializer usage changed from `object_instance=obj` to `instance=obj` (standard DRF)
- All serializers can be customized by subclassing and overriding `fields` in Meta
- Test execution time: ~84 seconds for 143 tests (integration tests with full database setup)

---

## [1.0.6] - 2025-09-28

### 🔧 DRF Spectacular Compatibility Fixes
- **Fixed type hint warnings**: Added `@extend_schema_field` decorators to all SerializerMethodField methods in serializers
- **Resolved GenericForeignKey warnings**: Created custom `GenericForeignKeyField` to properly handle Pipeline.department field serialization
- **Enhanced API documentation**: All serializer method fields now have proper type annotations for OpenAPI schema generation
- **Improved field resolution**: Replaced direct department field usage with department_detail field using custom serializer

### 📋 Technical Improvements
- **Added drf-spectacular import**: Imported extend_schema_field decorator for type hint support
- **Custom field implementation**: Created GenericForeignKeyField class for consistent GenericForeignKey serialization
- **Type safety**: All SerializerMethodField methods now have explicit return type declarations
- **Schema compliance**: Full compatibility with drf-spectacular OpenAPI schema generation

### 🚫 Resolved Warnings
- Fixed "unable to resolve type hint" warnings for all serializer method fields
- Resolved Pipeline.department model field resolution issues
- Eliminated DRF Spectacular W001 warnings across all serializers

## [1.0.5] - 2025-09-28

### 🚀 Complete Resubmission & Delegation Implementation
- **Enhanced resubmission logic**: Implemented proper `after_resubmission` handler with stage transitions and workflow event triggers
- **Added delegation logic**: New `after_delegate` handler with delegate user assignment and workflow event integration
- **WorkflowApprovalSerializer integration**: All approval actions (approve, reject, delegate, resubmission) now use `advance_flow` with proper parameter passing
- **Comprehensive test coverage**: Completely rewritten flow tests using WorkflowApprovalSerializer instead of manual assignment

### 🔧 Workflow Engine Improvements
- **Handler integration**: Added `ActionType.AFTER_DELEGATE` and `ActionType.AFTER_RESUBMISSION` workflow event triggers
- **Stage transition logic**: Resubmission properly updates workflow attachment to target resubmission stage
- **Metadata tracking**: Resubmission steps include `resubmission_stage_id` in extra_fields for audit trail
- **Error handling**: Improved error handling and validation in serializer save method

### 📋 Testing & Validation
- **advance_flow integration tests**: Added comprehensive mocking tests to verify correct parameter passing to approval workflow
- **End-to-end flow tests**: New tests validate complete approval progression using proper serializer patterns
- **Real workflow simulation**: Tests now use actual WorkflowApprovalSerializer patterns from production implementations

### 📚 Documentation Updates
- **Feature highlights**: Updated README with new resubmission and delegation capabilities
- **Implementation notes**: Added documentation about workflow event triggers and stage transitions
- **Known limitations**: Documented step number conflict issue in approval workflow package for resubmission edge cases

## [1.0.4] - 2025-09-27

### 🔄 Clone Tracking & API Improvements
- **Added `cloned_from` field**: All workflow models (WorkFlow, Pipeline, Stage) now automatically track their clone origin
- **Enhanced clone functionality**: Base clone method automatically sets clone relationships and handles field copying
- **Improved API consistency**: Renamed `department_object_id` to `department_id` for cleaner, more intuitive API

### 📚 Configuration Documentation
- **Comprehensive configuration guide**: Added detailed DEPARTMENT_MODEL setting documentation to README
- **Flexible department mapping**: Document support for mapping departments to any model (custom models, auth.Group, etc.)
- **Developer-friendly examples**: Enhanced configuration examples with real-world use cases

### 🛠 Technical Improvements
- **Optimized service functions**: Enhanced workflow data retrieval functions with better performance
- **Updated migrations**: Clean field renaming with proper migration handling
- **Code quality**: Applied formatting improvements with isort and black

### 📋 Migration Notes
- **Seamless upgrade**: Field rename handled transparently in migrations
- **No breaking changes**: All existing functionality preserved
- **130 tests passing**: Full test coverage maintained

---

## [1.0.3] - 2025-09-27

### 🔧 Model Updates
- Allowed `null=True` on timestamp and related fields to improve migration flexibility
- Ensures smoother installation on existing databases without requiring defaults

### 🛠 Migration Notes
- If upgrading from `1.0.2`, run migrations to apply the `null=True` changes
- New installs are not affected

---

## [1.0.2] - 2025-07-15

### 🚀 Enhancements
- **Refactored Department** to be fully generic and non-blocking for developer usage
- **Updated Company model**: defaults to `AUTH_USER_MODEL` for better integration
- **Optimized service helpers**: added utilities such as `get_detailed_workflow_data` with focus on performance
- **Developer support APIs**: ready-made endpoints to simplify implementation and accelerate onboarding

### 🛠 Technical Improvements
- Refined model structure for clarity and future-proofing
- Improved separation between workflow orchestration and developer integration layers

### 📋 Migration Notes
- Fully backward compatible
- Developers can now use generic departments without schema changes

---

## [1.0.1] - 2024-12-27

### 🎉 Production-Ready Release
This release marks the completion of extensive testing, optimization, and internationalization work, making django-dynamic-workflows fully production-ready for enterprise deployment.

### ✅ Test Coverage & Quality Improvements
- **Achieved 100% test pass rate**: Fixed all 58 failing tests, now 69/69 tests pass
- **Added comprehensive test mocking**: Optimized test execution speed by 43% (70s → 40s)
- **Enhanced test reliability**: Added proper fixtures and database optimization
- **Improved error handling**: Better validation and error messages throughout

### 🌍 Internationalization & Localization
- **Full Arabic translation support**: Complete translation of all user-facing text
- **Enhanced English translations**: Refined and standardized all English text
- **RTL support**: Right-to-left text rendering for Arabic interface
- **Dynamic language switching**: API responses adapt to request language headers
- **Translated components**:
  - Model verbose names and field labels
  - Validation error messages and API responses
  - Email templates and notifications
  - Admin interface and help text

### 📊 Advanced Logging & Monitoring
- **Structured logging system**: Comprehensive workflow operation tracking
- **Performance monitoring**: Execution time tracking for optimization
- **Contextual logging**: Rich metadata for debugging and analysis
- **Workflow event tracking**: Complete audit trail of all workflow operations
- **Error tracking**: Detailed error logging with context information

### 🚀 Performance Optimizations
- **Faster test execution**: Comprehensive mocking strategy for slow operations
- **Database optimizations**: Reduced query count and improved caching
- **Email backend mocking**: Eliminated slow email operations in tests
- **Memory usage improvements**: Optimized object creation and cleanup

### 🔧 Developer Experience Enhancements
- **Better error messages**: Clear, actionable error descriptions in both languages
- **Improved documentation**: Enhanced README with clearer examples
- **Translation management**: Added management commands for translation compilation
- **Development tools**: Optimized pytest configuration and test fixtures

### 📦 Package Improvements
- **Updated dependencies**: Removed version pinning for latest compatibility
- **Enhanced metadata**: Improved package description and keywords
- **Better structure**: Organized code with clear separation of concerns
- **Documentation updates**: Added TRANSLATIONS.md with comprehensive i18n guide

### 🛠 Technical Improvements
- **Serializer enhancements**: Better validation logic and error handling
- **Service layer optimization**: More efficient workflow operations
- **Model improvements**: Enhanced progress calculation and status management
- **API refinements**: More robust request/response handling

### 📋 Migration Notes
- All existing functionality remains backward compatible
- New translation files need to be compiled: `python manage.py compilemessages`
- Recommended to update to latest dependency versions
- Enhanced logging may increase log volume (configure appropriately)

### 🎯 Use Case Validation
Successfully tested for:
- CRM workflow replacement scenarios
- Multi-tenant enterprise applications
- High-volume workflow processing
- International deployments requiring Arabic/English support
- Complex approval processes with multiple stages

---

## [1.0.0] - 2024-09-26

### Added
- Initial release of Django Dynamic Workflows
- Generic workflow attachment system for any Django model
- Database-stored configurable actions with inheritance system
- Integration with django-approval-workflow package
- WorkFlow, Pipeline, Stage hierarchical structure
- WorkflowAction model with database-stored function paths
- Action inheritance: Stage → Pipeline → Workflow → Default
- Default email actions for all workflow events
- WorkflowAttachment model for generic model binding
- WorkflowConfiguration for model registration
- Comprehensive admin interface
- Action types: AFTER_APPROVE, AFTER_REJECT, AFTER_RESUBMISSION, AFTER_DELEGATE, AFTER_MOVE_STAGE, AFTER_MOVE_PIPELINE, ON_WORKFLOW_START, ON_WORKFLOW_COMPLETE
- Dynamic function execution system
- Rich context passing to action functions
- Progress tracking and status management
- API serializers for workflow approval actions
- Comprehensive usage examples and documentation

### Features
- Attach workflows to any model without hardcoded relationships
- Configure workflow actions dynamically in database
- Execute Python functions by database-stored paths
- Smart email notifications with automatic recipient detection
- Workflow progression through approval actions only
- Error resilient action execution with logging
- Django admin integration with rich interfaces
- Support for metadata and custom parameters

### Dependencies
- Django >= 4.0
- django-approval-workflow >= 0.8.0
