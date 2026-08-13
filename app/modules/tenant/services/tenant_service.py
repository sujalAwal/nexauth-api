"""Tenant Service - Business logic layer for tenant operations"""
import random
import re
import unicodedata
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tenant.models.tenant import Tenant
from app.modules.tenant.repositories.tenant_repository import TenantRepository
from app.modules.tenant.schemas.requests.tenant_request import (
    TenantCreateRequest,
    TenantUpdateRequest,
)
from app.modules.tenant.schemas.response.tenant_response import (
    TenantCollectionResponse,
    TenantResponse,
    TenantDetailResponse,
)
from app.schemas.pagination_response import PaginatedCollectionResponse
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler


def slugify(value: str) -> str:
    """Convert a name into a URL-safe slug (lowercase, hyphen-separated)."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().strip()
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    ascii_text = re.sub(r"[-\s]+", "-", ascii_text).strip("-_")
    return ascii_text or "tenant"


class TenantService:
    """Handles business logic for tenant operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TenantRepository(db)
        self.query_handler = PaginationQueryHandler(self.db)

    async def _generate_unique_slug(
        self,
        name: str,
        exclude_id: UUID | None = None,
    ) -> str:
        """
        Build a unique slug from `name`.
        If the base slug is taken, append -2, -3, ... until free.
        """
        base = slugify(name)
        slug = base
        counter = 2
        while await self.repo.slug_exists(slug, exclude_id=exclude_id):
            slug = f"{base}-{counter}"
            counter += 1
            if counter > 1000:
                raise ValueError(
                    f"Unable to generate a unique slug for name '{name}'. "
                    "Please try a different name."
                )
        return slug

    async def create_tenant(self, request: TenantCreateRequest) -> TenantResponse:
        """
        Create a new tenant with an auto-generated unique 4-digit code and slug.

        Strategy: attempt INSERT with a random code up to 5 times, catching
        DB-level UniqueViolation on the `code` column. This is 1 DB round-trip
        in the happy path instead of the previous approach of up to 10 SELECT
        existence checks before a single INSERT.
        """
        # Validate unique name first (human-facing, so give a clear error)
        if await self.repo.name_exists(request.name):
            raise ValueError(f"Tenant name '{request.name}' already exists")

        tenant_data = request.model_dump()
        tenant_data["slug"] = await self._generate_unique_slug(request.name)
        # TODO: Set created_by, updated_by from auth context when implemented

        for attempt in range(5):
            tenant_data["code"] = random.randint(1000, 9999)
            try:
                created_tenant = await self.repo.create(tenant_data)
                return TenantResponse.model_validate(created_tenant)
            except IntegrityError as exc:
                # Roll back the failed INSERT and retry only for code collisions
                await self.db.rollback()
                error_text = str(exc.orig).lower() if exc.orig else str(exc).lower()
                if "code" in error_text and attempt < 4:
                    continue
                if "slug" in error_text:
                    # Rare race: regenerate slug and retry remaining attempts
                    tenant_data["slug"] = await self._generate_unique_slug(request.name)
                    if attempt < 4:
                        continue
                raise ValueError(
                    "Unable to generate a unique tenant code/slug after 5 attempts. "
                    "Please try again."
                ) from exc

    async def get_tenant_by_id(self, tenant_id: UUID) -> TenantDetailResponse | None:
        tenant = await self.repo.get_by_id(tenant_id)
        if tenant:
            return TenantDetailResponse.model_validate(tenant)
        return None
    
    async def get_tenant_by_name(self, name: str) -> TenantResponse | None:
        tenant = await self.repo.get_by_name(name)
        if tenant:
            return TenantResponse.model_validate(tenant)
        return None
    
    async def get_tenant_by_code(self, code: int) -> TenantResponse | None:
        tenant = await self.repo.get_by_code(code)
        if tenant:
            return TenantResponse.model_validate(tenant)
        return None

    async def get_tenant_by_slug(self, slug: str) -> TenantResponse | None:
        tenant = await self.repo.get_by_slug(slug)
        if tenant:
            return TenantResponse.model_validate(tenant)
        return None
    
    async def update_tenant(
        self, 
        tenant_id: UUID, 
        request: TenantUpdateRequest
    ) -> TenantDetailResponse:
        """
        Note:
            TODO: Audit trail field (updated_by) will be populated from auth context in future.
            `updated_at` is set automatically by the ORM's `onupdate` hook — no manual assignment needed.
            When name changes, slug is regenerated from the new name to stay unique.
        """
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found with ID: {tenant_id}")
        
        # Validate unique name if being changed
        if request.name and request.name != tenant.name:
            if await self.repo.name_exists(request.name, exclude_id=tenant_id):
                raise ValueError(f"Tenant name '{request.name}' already exists")
        
        tenant_data = request.model_dump(exclude_unset=True)

        # Regenerate slug whenever the name changes
        if "name" in tenant_data and tenant_data["name"] != tenant.name:
            tenant_data["slug"] = await self._generate_unique_slug(
                tenant_data["name"],
                exclude_id=tenant_id,
            )

        # NOTE: updated_at is intentionally NOT set here.
        # The model's onupdate=lambda: datetime.now(timezone.utc) fires automatically on flush.
        # TODO: Set updated_by from auth context when implemented
        
        updated_tenant = await self.repo.update(tenant_id, tenant_data)
        return TenantDetailResponse.model_validate(updated_tenant)
    
    async def delete_tenant(self, tenant_id: UUID) -> TenantDetailResponse:
        """
        Soft delete a tenant.

        Note:
            TODO: Audit trail field (deleted_by) will be populated from auth context in future.
        """
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found with ID: {tenant_id}")
        
        # TODO: Pass auth user ID when implemented
        deleted_tenant = await self.repo.delete(tenant_id, None)
        return TenantDetailResponse.model_validate(deleted_tenant)
    
    async def restore_tenant(self, tenant_id: UUID) -> TenantDetailResponse:
        """
        Restore a soft-deleted tenant.

        Raises:
            ValueError: If tenant not found or not currently soft-deleted.
        """
        tenant = await self.repo.get_by_id_soft_deleted(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found with ID: {tenant_id}")
        
        restored_tenant = await self.repo.restore(tenant.id)
        return TenantDetailResponse.model_validate(restored_tenant)
    
    async def get_tenants_paginated(self, params: ListRequestFilters) -> PaginatedCollectionResponse[TenantCollectionResponse]:
        statement = select(Tenant)

        result = await self.query_handler.execute_paginated_query(
            query=statement,
            model=Tenant,
            params=params,
            searchable_fields=[
                Tenant.name,
                Tenant.slug,
                Tenant.industry,
                Tenant.contact_email,
                Tenant.domain,
            ],
            sortable_fields=[
                "created_at",
                "updated_at",
                "name",
                "slug",
                "code",
                "plan_tier",
            ],
        )
        return PaginatedCollectionResponse(
            data=result.data,
            pagination=result.pagination
        )

    async def get_active_tenants(self) -> list[TenantResponse]:
        """
        Get all active tenants.

        Returns:
            List of active TenantResponse objects
        """
        tenants = await self.repo.get_all_active()
        return [TenantResponse.model_validate(t) for t in tenants]
    
    async def toggle_tenant_status(self, tenant_id: UUID, is_active: bool) -> TenantDetailResponse:
        """
        Toggle tenant active/inactive status.

        Note:
            TODO: Audit trail field (updated_by) will be populated from auth context in future.
            `updated_at` is set automatically by the ORM's `onupdate` hook — no manual assignment needed.
        """
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found with ID: {tenant_id}")
        
        # NOTE: updated_at omitted intentionally — ORM onupdate handles it.
        # TODO: Set updated_by from auth context when implemented
        tenant_data = {"is_active": is_active}
        
        updated_tenant = await self.repo.update(tenant_id, tenant_data)
        return TenantDetailResponse.model_validate(updated_tenant)

