"""
ISA Embedding Service

ISA reranking service using deployed Jina Reranker v2 via Modal
"""

import logging
from typing import Dict, Any, List, Optional

try:
    import modal
    MODAL_AVAILABLE = True
except ImportError:
    MODAL_AVAILABLE = False
    modal = None

from isa_model.inference.services.embedding.base_embed_service import BaseEmbedService

logger = logging.getLogger(__name__)

class ISAEmbedService(BaseEmbedService):
    """
    ISA Embedding Service - calls ISA deployed reranking models
    
    Supported features:
    - Document reranking (Jina Reranker v2 via Modal)
    - Future: embedding generation
    - Future: semantic similarity computation
    """
    
    def __init__(self, 
                 rerank_modal_app_name: str = "isa-embed-rerank",
                 timeout: int = 30):
        """
        Initialize ISA Embedding service
        
        Args:
            rerank_modal_app_name: Modal reranking app name
            timeout: Request timeout in seconds
        """
        # For now, skip BaseService initialization to avoid config validation
        # TODO: Properly configure ISA provider in config system
        self.provider_name = "isa"
        self.model_name = "isa-jina-reranker-v2-service"
        self.rerank_modal_app_name = rerank_modal_app_name
        self.timeout = timeout
        
        # Initialize Modal client
        if MODAL_AVAILABLE:
            try:
                # Get deployed Modal application
                self.modal_app = modal.App.lookup(rerank_modal_app_name)
                logger.info(f"Connected to Modal rerank app: {rerank_modal_app_name}")
                
                self.modal_service = True  # Mark service as available
                logger.info("Modal rerank app connection established")
                    
            except Exception as e:
                logger.warning(f"Failed to connect to Modal rerank app: {e}")
                self.modal_app = None
                self.modal_service = None
        else:
            logger.warning("Modal SDK not available")
            self.modal_app = None
            self.modal_service = None
        
        # Service statistics
        self.request_count = 0
        self.total_cost = 0.0

        # Store user_id for billing (will be set by invoke kwargs)
        self._current_user_id = None
        
    async def rerank_documents(
        self, 
        query: str, 
        documents: List[str], 
        top_k: Optional[int] = None,
        return_documents: bool = True
    ) -> Dict[str, Any]:
        """
        Rerank documents using Jina Reranker v2
        
        Args:
            query: Query string
            documents: List of documents to rerank
            top_k: Return top k results (None = all)
            return_documents: Whether to include document content in results
            
        Returns:
            Reranking results
        """
        try:
            if not self.modal_app or not self.modal_service:
                return {
                    'success': False,
                    'provider': 'ISA',
                    'service': 'isa-embed-rerank',
                    'error': 'Modal rerank app or service not available'
                }
            
            # Call reranking service directly via Modal SDK
            result = await self._call_rerank_service(query, documents, top_k, return_documents)
            
            if result and result.get('success', False):
                self.request_count += 1

                # Record cost
                if 'billing' in result:
                    cost = result['billing'].get('estimated_cost_usd', 0)
                    self.total_cost += cost

                # Publish billing event
                if self._current_user_id:
                    try:
                        await self._publish_billing_event(
                            user_id=self._current_user_id,
                            service_type="embedding",
                            operation="document_reranking",
                            input_units=float(len(documents)),  # Number of documents reranked
                            metadata={
                                "query_length": len(query),
                                "num_documents": len(documents),
                                "returned_count": result.get('returned_count', 0),
                                "processing_time": result.get('processing_time', 0),
                                "estimated_cost_usd": cost
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to publish billing event: {e}")

                # Format response to match expected structure
                formatted_result = {
                    'success': True,
                    'provider': 'ISA',
                    'service': 'isa-embed-rerank',
                    'result': {
                        'results': result.get('results', []),
                        'processing_time': result.get('processing_time'),
                        'billing': result.get('billing', {}),
                        'query': result.get('query'),
                        'num_documents': result.get('num_documents'),
                        'returned_count': result.get('returned_count')
                    },
                    'metadata': {
                        'model_used': result.get('model'),
                        'provider': result.get('provider', 'ISA'),
                        'billing': result.get('billing', {})
                    }
                }
                return formatted_result
            else:
                return {
                    'success': False,
                    'provider': 'ISA',
                    'service': 'isa-embed-rerank',
                    'error': f'Rerank service returned error: {result.get("error", "Unknown error") if result else "No response"}',
                    'details': result
                }
                
        except Exception as e:
            logger.error(f"ISA document reranking failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'provider': 'ISA',
                'service': 'isa-embed-rerank',
                'error': str(e)
            }
    
    async def _call_rerank_service(
        self, 
        query: str, 
        documents: List[str], 
        top_k: Optional[int], 
        return_documents: bool
    ) -> Dict[str, Any]:
        """
        Call reranking service via Modal SDK
        """
        try:
            import modal
            
            logger.info("Calling Jina Reranker v2 service via Modal SDK...")
            
            # Correct Modal SDK usage: call deployed class method
            ISAEmbedRerankService = modal.Cls.from_name(
                app_name=self.rerank_modal_app_name,
                name="ISAEmbedRerankService"
            )
            
            # Create instance and call method
            instance = ISAEmbedRerankService()
            result = instance.rerank_documents.remote(
                query=query,
                documents=documents,
                top_k=top_k,
                return_documents=return_documents
            )
            
            logger.info("Modal rerank SDK call successful")
            return result
                        
        except Exception as e:
            logger.error(f"Modal rerank SDK call failed: {e}")
            return {
                'success': False,
                'error': f'Modal rerank SDK error: {str(e)}'
            }
    
    # ==================== Unified invoke method ====================

    async def invoke(
        self,
        input_data: Optional[str] = None,
        task: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Unified invoke method for ISA embedding service.
        Handles rerank task (embeddings not supported).

        Args:
            input_data: Query string for reranking
            task: Task type ('rerank', 'rerank_documents', etc.)
            **kwargs: Additional parameters including:
                - documents: List of documents to rerank (required for rerank)
                - top_k: Number of top results to return
                - return_documents: Whether to include document text
        """
        # Check task type
        if task and task not in ['rerank', 'rerank_documents', 'document_ranking']:
            raise NotImplementedError(f"Task '{task}' not supported by ISA reranker service. Only 'rerank' is supported.")

        # For embed task, return error
        if task == 'embed':
            raise NotImplementedError("Text embedding not yet implemented in ISA service")

        # Rerank task
        if input_data is None:
            raise ValueError("Query text is required for reranking")

        # Extract documents from kwargs
        documents = kwargs.get('documents')
        if not documents:
            raise ValueError("rerank task requires documents parameter")

        # Call rerank_documents method
        return await self.rerank_documents(
            query=input_data,
            documents=documents,
            top_k=kwargs.get('top_k'),
            return_documents=kwargs.get('return_documents', True)
        )

    # ==================== Embedding methods (future implementation) ====================

    async def create_text_embedding(self, text: str) -> List[float]:
        """Create single text embedding - not yet implemented"""
        raise NotImplementedError("Text embedding not yet implemented in ISA service")
    
    async def create_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create multiple text embeddings - not yet implemented"""
        raise NotImplementedError("Text embeddings not yet implemented in ISA service")
    
    async def create_chunks(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """Create text chunks with embeddings - not yet implemented"""
        raise NotImplementedError("Text chunking not yet implemented in ISA service")
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute embedding similarity - not yet implemented"""
        raise NotImplementedError("Similarity computation not yet implemented in ISA service")
    
    async def find_similar_texts(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar texts - not yet implemented"""
        raise NotImplementedError("Similar text search not yet implemented in ISA service")
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension - not applicable for rerank-only service"""
        raise NotImplementedError("Embedding dimension not available for rerank-only service")
    
    def get_max_input_length(self) -> int:
        """Get maximum input length"""
        return 1024  # Jina Reranker v2 max length
    
    # ==================== Service management methods ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ISA reranking service health"""
        try:
            # Simple health check: call reranking service
            test_result = await self.rerank_documents(
                query="test",
                documents=["test document"],
                top_k=1,
                return_documents=False
            )
            
            return {
                'success': True,
                'provider': 'ISA',
                'service': 'isa-embed-rerank',
                'status': 'healthy' if test_result.get('success') else 'error',
                'rerank_service': test_result.get('success', False),
                'usage_stats': {
                    'total_requests': self.request_count,
                    'total_cost_usd': round(self.total_cost, 6)
                }
            }
                
        except Exception as e:
            return {
                'success': False,
                'provider': 'ISA',
                'service': 'isa-embed-rerank',
                'status': 'error',
                'error': str(e)
            }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        try:
            modal_stats = {}
            
            # Try to get Modal service statistics
            if self.modal_app:
                try:
                    # Can extend to get Modal service stats
                    pass
                except Exception as e:
                    logger.warning(f"Failed to get Modal stats: {e}")
            
            return {
                'provider': 'ISA',
                'service': 'isa-embed-rerank',
                'client_stats': {
                    'total_requests': self.request_count,
                    'total_cost_usd': round(self.total_cost, 6)
                },
                'modal_stats': modal_stats,
                'combined_cost': round(self.total_cost, 6)
            }
            
        except Exception as e:
            return {
                'provider': 'ISA', 
                'service': 'isa-embed-rerank',
                'error': str(e)
            }
    
    def get_supported_tasks(self) -> List[str]:
        """Get supported task list"""
        return [
            'rerank',           # Document reranking
            'rerank_documents', # Document reranking (alias)
            'document_ranking'  # Document ranking (alias)
        ]
    
    def get_supported_formats(self) -> List[str]:
        """Get supported formats"""
        return ['text']  # Text only

    async def _publish_billing_event(
        self,
        user_id: str,
        service_type: str,
        operation: str,
        input_units: float = None,
        metadata: dict = None
    ):
        """
        Publish billing event to NATS for ISA Embedding services

        Args:
            user_id: User ID for billing
            service_type: Service type (embedding)
            operation: Operation performed (document_reranking)
            input_units: Number of units consumed (documents processed)
            metadata: Additional metadata
        """
        try:
            from decimal import Decimal
            import os

            if input_units is None:
                logger.warning(f"No usage metrics provided for {user_id}")
                return

            usage_amount = Decimal(input_units)
            unit_type = "request"

            # Prepare usage details
            usage_details = {
                "provider": self.provider_name,
                "model": self.model_name,
                "operation": operation,
                "service_type": service_type,
            }

            if input_units is not None:
                usage_details["input_units"] = float(input_units)
            if metadata:
                usage_details.update(metadata)

            # Import and publish event
            try:
                from isa_common.events import publish_usage_event
                from isa_common.consul_client import ConsulRegistry

                # Try Consul discovery first for NATS service
                consul = None
                nats_host = None
                nats_port = None

                try:
                    consul_host = os.getenv('CONSUL_HOST', 'localhost')
                    consul_port = int(os.getenv('CONSUL_PORT', '8500'))
                    consul = ConsulRegistry(consul_host=consul_host, consul_port=consul_port)

                    # Try to discover NATS via Consul
                    nats_url = consul.get_nats_url()
                    if '://' in nats_url:
                        nats_url = nats_url.split('://', 1)[1]
                    nats_host, port_str = nats_url.rsplit(':', 1)
                    nats_port = int(port_str)
                    logger.info(f"Discovered NATS via Consul: {nats_host}:{nats_port}")
                except Exception as consul_err:
                    logger.debug(f"Consul discovery failed: {consul_err}, using environment variables")
                    nats_host = os.getenv('NATS_HOST', 'localhost')
                    nats_port = int(os.getenv('NATS_PORT', '50056'))

                success = await publish_usage_event(
                    user_id=user_id,
                    product_id=self.model_name,
                    usage_amount=usage_amount,
                    unit_type=unit_type,
                    usage_details=usage_details,
                    nats_host=nats_host,
                    nats_port=nats_port
                )

                if success:
                    logger.info(
                        f"Published billing event: user={user_id}, "
                        f"model={self.model_name}, usage={usage_amount} {unit_type}"
                    )
                else:
                    logger.warning(f"Failed to publish billing event for user {user_id}")

            except ImportError as ie:
                logger.error(
                    f"Cannot import billing events module: {ie}. "
                    f"Make sure isa_common package is installed."
                )
            except Exception as pe:
                logger.error(f"Error publishing billing event: {pe}", exc_info=True)

        except Exception as e:
            logger.warning(
                f"Failed to publish billing event: {e}",
                exc_info=True
            )

    async def close(self):
        """Cleanup resources"""
        # Modal client doesn't need explicit closure
        pass