"""
Bulk operation coordinator - Single entry point for all bulk operations.

This facade hides the complexity of wiring up multiple services and provides
a clean, simple API for the QuerySet to use.
"""

import logging
from django.db import transaction
from django.db.models import QuerySet as BaseQuerySet

from django_bulk_hooks.helpers import (
    build_changeset_for_create,
    build_changeset_for_update,
    build_changeset_for_delete,
)

logger = logging.getLogger(__name__)


class BulkOperationCoordinator:
    """
    Single entry point for coordinating bulk operations.

    This coordinator manages all services and provides a clean facade
    for the QuerySet. It wires up services and coordinates the hook
    lifecycle for each operation type.

    Services are created lazily and cached.
    """

    def __init__(self, queryset):
        """
        Initialize coordinator for a queryset.

        Args:
            queryset: Django QuerySet instance
        """
        self.queryset = queryset
        self.model_cls = queryset.model

        # Lazy initialization
        self._analyzer = None
        self._mti_handler = None
        self._executor = None
        self._dispatcher = None

    @property
    def analyzer(self):
        """Get or create ModelAnalyzer"""
        if self._analyzer is None:
            from django_bulk_hooks.operations.analyzer import ModelAnalyzer

            self._analyzer = ModelAnalyzer(self.model_cls)
        return self._analyzer

    @property
    def mti_handler(self):
        """Get or create MTIHandler"""
        if self._mti_handler is None:
            from django_bulk_hooks.operations.mti_handler import MTIHandler

            self._mti_handler = MTIHandler(self.model_cls)
        return self._mti_handler

    @property
    def executor(self):
        """Get or create BulkExecutor"""
        if self._executor is None:
            from django_bulk_hooks.operations.bulk_executor import BulkExecutor

            self._executor = BulkExecutor(
                queryset=self.queryset,
                analyzer=self.analyzer,
                mti_handler=self.mti_handler,
            )
        return self._executor

    @property
    def dispatcher(self):
        """Get or create Dispatcher"""
        if self._dispatcher is None:
            from django_bulk_hooks.dispatcher import get_dispatcher

            self._dispatcher = get_dispatcher()
        return self._dispatcher

    # ==================== PUBLIC API ====================

    @transaction.atomic
    def create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        bypass_hooks=False,
        bypass_validation=False,
    ):
        """
        Execute bulk create with hooks.

        Args:
            objs: List of model instances to create
            batch_size: Number of objects per batch
            ignore_conflicts: Ignore conflicts if True
            update_conflicts: Update on conflict if True
            update_fields: Fields to update on conflict
            unique_fields: Fields to check for conflicts
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            List of created objects
        """
        if not objs:
            return objs

        # Validate
        self.analyzer.validate_for_create(objs)

        # Build initial changeset
        changeset = build_changeset_for_create(
            self.model_cls,
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

        # Execute with hook lifecycle
        def operation():
            return self.executor.bulk_create(
                objs,
                batch_size=batch_size,
                ignore_conflicts=ignore_conflicts,
                update_conflicts=update_conflicts,
                update_fields=update_fields,
                unique_fields=unique_fields,
            )

        return self._execute_with_mti_hooks(
            changeset=changeset,
            operation=operation,
            event_prefix="create",
            bypass_hooks=bypass_hooks,
            bypass_validation=bypass_validation,
        )

    @transaction.atomic
    def update(
        self,
        objs,
        fields,
        batch_size=None,
        bypass_hooks=False,
        bypass_validation=False,
    ):
        """
        Execute bulk update with hooks.

        Args:
            objs: List of model instances to update
            fields: List of field names to update
            batch_size: Number of objects per batch
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            Number of objects updated
        """
        if not objs:
            return 0

        # Validate
        self.analyzer.validate_for_update(objs)

        # Fetch old records using analyzer (single source of truth)
        old_records_map = self.analyzer.fetch_old_records_map(objs)

        # Build changeset
        from django_bulk_hooks.changeset import ChangeSet, RecordChange

        changes = [
            RecordChange(
                new_record=obj,
                old_record=old_records_map.get(obj.pk),
                changed_fields=fields,
            )
            for obj in objs
        ]
        changeset = ChangeSet(self.model_cls, changes, "update", {"fields": fields})

        # Execute with hook lifecycle
        def operation():
            return self.executor.bulk_update(objs, fields, batch_size=batch_size)

        return self._execute_with_mti_hooks(
            changeset=changeset,
            operation=operation,
            event_prefix="update",
            bypass_hooks=bypass_hooks,
            bypass_validation=bypass_validation,
        )

    @transaction.atomic
    def update_queryset(
        self, update_kwargs, bypass_hooks=False, bypass_validation=False
    ):
        """
        Execute queryset update with hooks.
        
        ARCHITECTURE: Application-Layer Update with Expression Resolution
        ===================================================================
        
        When hooks are enabled, queryset.update() is transformed into bulk_update()
        to allow BEFORE hooks to modify records. This is a deliberate design choice:
        
        1. Fetch instances from the queryset (we need them for hooks anyway)
        2. Resolve SQL expressions (F(), Subquery, Case, etc.) to concrete values
        3. Apply resolved values to instances
        4. Run BEFORE hooks (which can now modify the instances)
        5. Use bulk_update() to persist the (possibly modified) instances
        6. Run AFTER hooks with final state
        
        This approach:
        - ✅ Allows BEFORE hooks to modify values (feature request)
        - ✅ Preserves SQL expression semantics (materializes them correctly)
        - ✅ Eliminates the double-fetch (was fetching before AND after)
        - ✅ More efficient than previous implementation
        - ✅ Maintains Salesforce-like hook contract
        
        SQL expressions are resolved per-instance using Django's annotate(),
        which ensures correct evaluation of:
        - F() expressions: F('balance') + 100
        - Subquery: Subquery(related.aggregate(...))
        - Case/When: Case(When(...))
        - Database functions: Upper(), Concat(), etc.
        - Any other Django Expression
        
        Trade-off:
        - Uses bulk_update() internally (slightly different SQL than queryset.update)
        - Expression resolution may add overhead for complex expressions
        - But eliminates the refetch, so overall more efficient

        Args:
            update_kwargs: Dict of fields to update
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            Number of objects updated
        """
        # Fetch instances from queryset
        instances = list(self.queryset)
        if not instances:
            return 0

        # Check both parameter and context for bypass_hooks
        from django_bulk_hooks.context import get_bypass_hooks
        should_bypass = bypass_hooks or get_bypass_hooks()
        
        if should_bypass:
            # No hooks - use original queryset.update() for max performance
            return BaseQuerySet.update(self.queryset, **update_kwargs)

        # Resolve expressions and apply to instances
        # Delegate to analyzer for expression resolution and value application
        fields_to_update = self.analyzer.apply_update_values(instances, update_kwargs)
        
        # Now instances have the resolved values applied
        # Fetch old records for comparison (single bulk query)
        old_records_map = self.analyzer.fetch_old_records_map(instances)

        # Detect FK fields being updated to prevent @select_related conflicts
        fk_fields_being_updated = self._get_fk_fields_being_updated(update_kwargs)

        # Build changeset for VALIDATE and BEFORE hooks
        # instances now have the "intended" values from update_kwargs
        changeset = build_changeset_for_update(
            self.model_cls,
            instances,
            update_kwargs,
            old_records_map=old_records_map,
        )

        # Add FK field info to changeset meta for dispatcher to use
        if fk_fields_being_updated:
            changeset.operation_meta['fk_fields_being_updated'] = fk_fields_being_updated

        # Execute VALIDATE and BEFORE hooks
        # Hooks can now modify the instances and changes will persist
        if not bypass_validation:
            self.dispatcher.dispatch(changeset, "validate_update", bypass_hooks=False)
        self.dispatcher.dispatch(changeset, "before_update", bypass_hooks=False)

        # COORDINATION LOGIC: Determine all fields to persist
        # Hooks may have modified fields beyond the original update_kwargs.
        # We need to detect those changes and include them in bulk_update.
        # This is coordination between: hooks → field detection → executor
        additional_changed_fields = self.analyzer.detect_changed_fields(instances)
        all_fields_to_update = list(set(fields_to_update) | set(additional_changed_fields))
        
        # Use bulk_update with all modified fields (original + hook modifications)
        result = self.executor.bulk_update(instances, all_fields_to_update, batch_size=None)

        # Build changeset for AFTER hooks
        # No refetch needed! instances already have final state from bulk_update
        changeset_after = build_changeset_for_update(
            self.model_cls,
            instances,
            update_kwargs,
            old_records_map=old_records_map,
        )

        # Execute AFTER hooks with final state
        self.dispatcher.dispatch(changeset_after, "after_update", bypass_hooks=False)

        return result

    @transaction.atomic
    def delete(self, bypass_hooks=False, bypass_validation=False):
        """
        Execute delete with hooks.

        Args:
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True

        Returns:
            Tuple of (count, details dict)
        """
        # Get objects
        objs = list(self.queryset)
        if not objs:
            return 0, {}

        # Validate
        self.analyzer.validate_for_delete(objs)

        # Build changeset
        changeset = build_changeset_for_delete(self.model_cls, objs)

        # Execute with hook lifecycle
        def operation():
            # Call base Django QuerySet.delete() to avoid recursion
            return BaseQuerySet.delete(self.queryset)

        return self._execute_with_mti_hooks(
            changeset=changeset,
            operation=operation,
            event_prefix="delete",
            bypass_hooks=bypass_hooks,
            bypass_validation=bypass_validation,
        )

    def clean(self, objs, is_create=None):
        """
        Execute validation hooks only (no database operations).

        This is used by Django's clean() method to hook VALIDATE_* events
        without performing the actual operation.

        Args:
            objs: List of model instances to validate
            is_create: True for create, False for update, None to auto-detect

        Returns:
            None
        """
        if not objs:
            return

        # Auto-detect if is_create not specified
        if is_create is None:
            is_create = objs[0].pk is None

        # Build changeset based on operation type
        if is_create:
            changeset = build_changeset_for_create(self.model_cls, objs)
            event = "validate_create"
        else:
            # For update validation, no old records needed - hooks handle their own queries
            changeset = build_changeset_for_update(self.model_cls, objs, {})
            event = "validate_update"

        # Dispatch validation event only
        self.dispatcher.dispatch(changeset, event, bypass_hooks=False)

    # ==================== MTI PARENT HOOK SUPPORT ====================

    def _build_changeset_for_model(self, original_changeset, target_model_cls):
        """
        Build a changeset for a specific model in the MTI inheritance chain.
        
        This allows parent model hooks to receive the same instances but with
        the correct model_cls for hook registration matching.
        
        Args:
            original_changeset: The original changeset (for child model)
            target_model_cls: The model class to build changeset for (parent model)
            
        Returns:
            ChangeSet for the target model
        """
        from django_bulk_hooks.changeset import ChangeSet
        
        # Create new changeset with target model but same record changes
        return ChangeSet(
            model_cls=target_model_cls,
            changes=original_changeset.changes,
            operation_type=original_changeset.operation_type,
            operation_meta=original_changeset.operation_meta,
        )

    def _execute_with_mti_hooks(
        self, 
        changeset, 
        operation, 
        event_prefix, 
        bypass_hooks=False, 
        bypass_validation=False
    ):
        """
        Execute operation with hooks for entire MTI inheritance chain.
        
        This method dispatches hooks for both child and parent models when
        dealing with MTI models, ensuring parent model hooks fire when
        child instances are created/updated/deleted.
        
        Args:
            changeset: ChangeSet for the child model
            operation: Callable that performs the actual DB operation
            event_prefix: 'create', 'update', or 'delete'
            bypass_hooks: Skip all hooks if True
            bypass_validation: Skip validation hooks if True
            
        Returns:
            Result of operation
        """
        if bypass_hooks:
            return operation()

        # Get all models in inheritance chain
        models_in_chain = [changeset.model_cls]
        if self.mti_handler.is_mti_model():
            parent_models = self.mti_handler.get_parent_models()
            models_in_chain.extend(parent_models)

        # VALIDATE phase - for all models in chain
        if not bypass_validation:
            for model_cls in models_in_chain:
                model_changeset = self._build_changeset_for_model(changeset, model_cls)
                self.dispatcher.dispatch(model_changeset, f"validate_{event_prefix}", bypass_hooks=False)

        # BEFORE phase - for all models in chain
        for model_cls in models_in_chain:
            model_changeset = self._build_changeset_for_model(changeset, model_cls)
            self.dispatcher.dispatch(model_changeset, f"before_{event_prefix}", bypass_hooks=False)

        # Execute the actual operation
        result = operation()

        # AFTER phase - for all models in chain
        # Use result if operation returns modified data (for create operations)
        if result and isinstance(result, list) and event_prefix == "create":
            # Rebuild changeset with assigned PKs for AFTER hooks
            from django_bulk_hooks.helpers import build_changeset_for_create
            changeset = build_changeset_for_create(changeset.model_cls, result)

        for model_cls in models_in_chain:
            model_changeset = self._build_changeset_for_model(changeset, model_cls)
            self.dispatcher.dispatch(model_changeset, f"after_{event_prefix}", bypass_hooks=False)

        return result

    def _get_fk_fields_being_updated(self, update_kwargs):
        """
        Get the relationship names for FK fields being updated.

        This helps @select_related avoid preloading relationships that are
        being modified, which can cause cache conflicts.

        Args:
            update_kwargs: Dict of fields being updated

        Returns:
            Set of relationship names (e.g., {'business'}) for FK fields being updated
        """
        fk_relationships = set()

        for field_name in update_kwargs.keys():
            try:
                field = self.model_cls._meta.get_field(field_name)
                if (field.is_relation and
                    not field.many_to_many and
                    not field.one_to_many and
                    hasattr(field, 'attname') and
                    field.attname == field_name):
                    # This is a FK field being updated by its attname (e.g., business_id)
                    # Add the relationship name (e.g., 'business') to skip list
                    fk_relationships.add(field.name)
            except Exception:
                # If field lookup fails, skip it
                continue

        return fk_relationships
