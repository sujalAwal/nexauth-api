# nexauth-api
Multi-tenant Identity-as-a-Service platform providing centralized authentication, authorization, and access management for enterprise applications.

## Model Convention

ORM tables should use shared mixins for the base audit fields:

- `SoftDeleteMixin` for `deleted_at`
- `AuditMixin` for `created_by`, `updated_by`, and `deleted_by`

This keeps soft-delete filtering and user-action tracking consistent across the codebase.
