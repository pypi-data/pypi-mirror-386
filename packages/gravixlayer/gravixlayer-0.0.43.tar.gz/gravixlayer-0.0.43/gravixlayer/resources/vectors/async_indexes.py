"""
Async vector index management for GravixLayer SDK
"""
from typing import Optional, Dict, Any, List
from ...types.vectors import (
    VectorIndex, VectorIndexList, CreateIndexRequest, UpdateIndexRequest,
    SUPPORTED_METRICS, SUPPORTED_VECTOR_TYPES
)


class AsyncVectorIndexes:
    """Async version of vector index management"""
    
    def __init__(self, client):
        self.client = client
        # Use client's base URL and replace inference with vectors
        self.base_url = client.base_url.replace("/v1/inference", "/v1/vectors")
    
    async def create(
        self,
        name: str,
        dimension: int,
        metric: str,
        cloud_provider: str,
        region: str,
        index_type: str,
        vector_type: str = "dense",
        metadata: Optional[Dict[str, Any]] = None,
        delete_protection: bool = False
    ) -> VectorIndex:
        """
        Create a new vector index
        
        Args:
            name: Index name (1-255 characters)
            dimension: Vector dimension (1-2000)
            metric: Similarity metric (cosine, euclidean, dotproduct)
            cloud_provider: Cloud provider (AWS, GCP, Azure, Gravix)
            region: Region ID (e.g., us-east-1, us-central1, eastus)
            index_type: Index type (serverless, dedicated)
            vector_type: Vector type (dense)
            metadata: Additional metadata
            delete_protection: Prevent accidental deletion
            
        Returns:
            VectorIndex: Created index information
        """
        if metric not in SUPPORTED_METRICS:
            raise ValueError(f"Metric must be one of: {SUPPORTED_METRICS}")
        
        if vector_type not in SUPPORTED_VECTOR_TYPES:
            raise ValueError(f"Vector type must be one of: {SUPPORTED_VECTOR_TYPES}")
        
        if not (1 <= dimension <= 2000):
            raise ValueError("Dimension must be between 1 and 2000")
        
        if not (1 <= len(name) <= 255):
            raise ValueError("Name must be between 1 and 255 characters")
        
        # Validate required fields
        valid_providers = ["AWS", "GCP", "Azure", "Gravix"]
        valid_index_types = ["serverless", "dedicated"]
        
        if cloud_provider not in valid_providers:
            raise ValueError(f"Cloud provider must be one of: {valid_providers}")
        
        if index_type not in valid_index_types:
            raise ValueError(f"Index type must be one of: {valid_index_types}")
        
        data = {
            "name": name,
            "dimension": dimension,
            "metric": metric,
            "vector_type": vector_type,
            "cloud_provider": cloud_provider,
            "region": region,
            "index_type": index_type,
            "metadata": metadata or {},
            "delete_protection": delete_protection
        }
        
        response = await self.client._make_request(
            "POST",
            f"{self.base_url}/indexes",
            data=data
        )
        
        result = response.json()
        return VectorIndex(**result)
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> VectorIndexList:
        """
        List all vector indexes
        
        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 20, max: 1000)
            
        Returns:
            VectorIndexList: List of indexes with pagination info
        """
        if page_size > 1000:
            raise ValueError("Page size cannot exceed 1000")
        
        # Build query parameters into URL for GET request
        endpoint = f"{self.base_url}/indexes?page={page}&page_size={page_size}"
        
        response = await self.client._make_request(
            "GET",
            endpoint
        )
        
        result = response.json()
        indexes = [VectorIndex(**idx) for idx in result["indexes"]]
        
        # Handle pagination field - may not be present in all API responses
        pagination = result.get("pagination", {
            "page": page,
            "page_size": page_size,
            "total": len(indexes)
        })
        
        return VectorIndexList(
            indexes=indexes,
            pagination=pagination
        )
    
    async def get(self, index_id: str) -> VectorIndex:
        """
        Get a specific vector index by ID
        
        Args:
            index_id: The index ID
            
        Returns:
            VectorIndex: Index information
        """
        response = await self.client._make_request(
            "GET",
            f"{self.base_url}/indexes/{index_id}"
        )
        
        result = response.json()
        return VectorIndex(**result)
    
    async def update(
        self,
        index_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        delete_protection: Optional[bool] = None
    ) -> VectorIndex:
        """
        Update a vector index
        
        Args:
            index_id: The index ID
            metadata: Updated metadata
            delete_protection: Enable/disable delete protection
            
        Returns:
            VectorIndex: Updated index information
        """
        data = {}
        if metadata is not None:
            data["metadata"] = metadata
        if delete_protection is not None:
            data["delete_protection"] = delete_protection
        
        if not data:
            raise ValueError("At least one field must be provided for update")
        
        response = await self.client._make_request(
            "PUT",
            f"{self.base_url}/indexes/{index_id}",
            data=data
        )
        
        result = response.json()
        
        # If the update response doesn't include all fields, fetch the complete index
        if "created_at" not in result:
            return await self.get(index_id)
        
        return VectorIndex(**result)
    
    async def delete(self, index_id: str, force: bool = False) -> None:
        """
        Delete a vector index and all its vectors
        
        Args:
            index_id: The index ID
            force: Force delete even if index has delete protection enabled
        """
        if force:
            # First, try to disable delete protection
            try:
                await self.update(index_id, delete_protection=False)
            except Exception:
                # If update fails, continue with delete attempt anyway
                pass
        
        await self.client._make_request(
            "DELETE",
            f"https://api.gravixlayer.com/v1/vectors/indexes/{index_id}"
        )