"""Collection service for pgvector MCP server."""

import re
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..exceptions import CollectionError, DatabaseError
from ..models.collection import Collection

# Initialize logger - note: we'll use basic logging for now, structured logger can be added later
import logging

logger = logging.getLogger("collection_service")


class CollectionService:
    """Service for managing collections."""

    def __init__(self, session: Session):
        self.session = session

    def get_collections(self) -> List[Collection]:
        """Get all active collections."""
        try:
            collections = self.session.query(Collection).filter(Collection.is_active).all()
            logger.debug(f"Retrieved {len(collections)} collections")
            return collections
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve collections: {e}")
            raise DatabaseError(f"Failed to retrieve collections: {e}") from e

    def get_collection(self, collection_id: int) -> Optional[Collection]:
        """Get collection by ID."""
        return (
            self.session.query(Collection)
            .filter(Collection.id == collection_id, Collection.is_active)
            .first()
        )

    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        """Get collection by name."""
        return (
            self.session.query(Collection)
            .filter(Collection.name == name, Collection.is_active)
            .first()
        )

    def create_collection(
        self, name: str, dimension: int = 1536, description: Optional[str] = None
    ) -> Collection:
        """Create a new collection."""
        try:
            # Check if collection name already exists
            existing = self.get_collection_by_name(name)
            if existing:
                logger.warning(f"Attempt to create duplicate collection: {name}")
                raise CollectionError(
                    f"Collection with name '{name}' already exists", code="DUPLICATE_NAME"
                )

            # Create the collection record
            collection = Collection(name=name, description=description, dimension=dimension)
            self.session.add(collection)
            self.session.commit()
            self.session.refresh(collection)

            logger.info(
                f"Created collection record: {name} (ID: {collection.id}, dim: {dimension})"
            )

            logger.info(f"Successfully created collection: {name} (ID: {collection.id})")
            return collection

        except CollectionError:
            # Re-raise collection-specific errors
            raise
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Database integrity error creating collection {name}: {e}")
            raise CollectionError(
                f"Failed to create collection '{name}': integrity constraint violation"
            ) from e
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating collection {name}: {e}")
            raise DatabaseError(f"Failed to create collection '{name}': {e}") from e
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error creating collection {name}: {e}")
            raise CollectionError(f"Failed to create collection '{name}': {e}") from e

    def update_collection(
        self, collection_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Collection]:
        """Update collection."""
        collection = self.get_collection(collection_id)
        if not collection:
            return None

        # If name is being changed, rename the vector table
        old_name = collection.name

        if name and name != old_name:
            # Check if new name already exists
            existing = self.get_collection_by_name(name)
            if existing and existing.id != collection_id:
                raise ValueError(f"Collection with name '{name}' already exists")

            collection.name = name

        if description is not None:
            collection.description = description

        self.session.commit()
        self.session.refresh(collection)

        return collection

    def rename_collection(self, old_name: str, new_name: str) -> Optional[Collection]:
        """
        Rename a collection atomically.

        Args:
            old_name: Current collection name
            new_name: New collection name

        Returns:
            Updated collection object if successful, None if collection not found

        Raises:
            CollectionError: If new name already exists or rename operation fails
            DatabaseError: If database operation fails
        """
        try:
            # Start transaction - will be committed/rolled back by caller
            collection = self.get_collection_by_name(old_name)
            if not collection:
                raise CollectionError(f"Collection '{old_name}' not found", code="NOT_FOUND")

            # Check if new name already exists
            existing_collection = self.get_collection_by_name(new_name)
            if existing_collection and existing_collection.id != collection.id:
                raise CollectionError(
                    f"Collection with name '{new_name}' already exists", code="DUPLICATE_NAME"
                )

            # Validate new name format
            if not re.match(r"^[a-zA-Z0-9_]{1,64}$", new_name):
                raise CollectionError(
                    f"Invalid collection name '{new_name}'. Must contain only letters, numbers, and underscores, max 64 characters.",
                    code="INVALID_NAME",
                )

            # If names are the same, no operation needed
            if old_name == new_name:
                logger.info(f"Collection name unchanged: {old_name}")
                return collection

            # Update collection record (less likely to fail after table rename succeeds)
            from sqlalchemy.sql import func

            collection.name = new_name
            collection.updated_at = func.now()

            self.session.commit()
            self.session.refresh(collection)

            logger.info(
                f"Successfully renamed collection from '{old_name}' to '{new_name}' (ID: {collection.id})"
            )
            return collection

        except CollectionError:
            # Re-raise collection-specific errors
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to rename collection from '{old_name}' to '{new_name}': {e}")
            raise DatabaseError(f"Failed to rename collection: {e}") from e

    def delete_collection(self, collection_id: int) -> bool:
        """Delete collection."""
        collection = self.get_collection(collection_id)
        if not collection:
            return False

        # Soft delete the collection record
        self.session.query(Collection).filter(Collection.id == collection_id).delete()
        self.session.commit()

        return True
        