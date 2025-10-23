# dsf_quantum_sdk/client.py
"""DSF Quantum SDK - Lightweight client with async support"""

import requests
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
import time
from functools import wraps
import logging

from . import __version__
from .exceptions import ValidationError, APIError, RateLimitError
from .models import QuantumConfig, QuantumResult, JobStatus, Block

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator with rate limit awareness"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited. Retrying after {e.retry_after}s...")
                        time.sleep(e.retry_after)
                    last_exception = e
                except (requests.RequestException, APIError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            raise last_exception
        return wrapper
    return decorator


class QuantumSDK:
    """
    DSF Quantum SDK Client
    
    Lightweight client for adaptive quantum scoring with:
    - Local QAE simulator (API uses qiskit-aer)
    - IBM Quantum hardware (user provides credentials)
    - Async job processing for long-running evaluations
    
    Examples:
        >>> # Evaluación síncrona (simulador rápido)
        >>> sdk = QuantumSDK(license_key='PRO-2025-12-31-abc')
        >>> result = sdk.evaluate(
        ...     data={'flujo_caja': [0.5, 0.8, 0.6]},
        ...     config={'blocks': [...]},
        ...     backend='simulator'
        ... )
        
        >>> # Evaluación asíncrona (IBM hardware)
        >>> job_id = sdk.submit_async(
        ...     data={'flujo_caja': [0.5, 0.8, 0.6]},
        ...     config={'blocks': [...]},
        ...     backend='ibm_quantum',
        ...     ibm_credentials={'token': '...', 'backend_name': 'ibm_brisbane'}
        ... )
        >>> result = sdk.wait_for_result(job_id, timeout=600)
    """
    
    BASE_URL = "https://dsf-quantum-a4bohi7n8-api-dsfuptech.vercel.app/api/evaluate"
    
    def __init__(
        self,
        license_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        verify_ssl: bool = True
    ):
        """
        Initialize Quantum SDK client.
        
        Args:
            license_key: License key for premium features
            base_url: Override default API endpoint
            timeout: Request timeout (default 120s for quantum jobs)
            max_retries: Maximum retry attempts
            verify_ssl: Verify SSL certificates
        """
        self.license_key = license_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'DSF-Quantum-SDK/{__version__}'
        })
    
    def _validate_config(self, config: Dict) -> None:
        """Validate hierarchical config structure"""
        if not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary")
        
        if 'blocks' not in config:
            raise ValidationError("Config must contain 'blocks' key")
        
        blocks = config['blocks']
        if not isinstance(blocks, list) or len(blocks) == 0:
            raise ValidationError("'blocks' must be a non-empty list")
        
        for idx, block in enumerate(blocks):
            required = ['name', 'influence', 'priority']
            for field in required:
                if field not in block:
                    raise ValidationError(f"Block {idx} missing required field: {field}")
    
    def _validate_data(self, data: Dict, config: Dict) -> None:
        """Validate data matches config blocks"""
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        block_names = {b['name'] for b in config['blocks']}
        data_keys = set(data.keys())
        
        missing = block_names - data_keys
        if missing:
            raise ValidationError(f"Missing data for blocks: {missing}")
        
        for name, values in data.items():
            if not isinstance(values, list):
                raise ValidationError(f"Data for '{name}' must be a list")
            if len(values) == 0:
                raise ValidationError(f"Data for '{name}' cannot be empty")
    
    @retry_on_failure(max_retries=3, delay=1.5)
    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """Make HTTP request with retry logic"""
        base = self.base_url.rstrip("/") + "/"
        ep = endpoint.strip().lstrip("/")
        
        if ep in ("", "evaluate"):
            url = base.rstrip("/")
        else:
            url = urljoin(base, ep)
        
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
        
        # Handle rate limiting
        if resp.status_code == 429:
            try:
                err = resp.json()
            except ValueError:
                err = {}
            retry_after = err.get("retry_after") or resp.headers.get("Retry-After", "60")
            try:
                retry_after_int = int(retry_after)
            except (ValueError, TypeError):
                retry_after_int = 60
            raise RateLimitError(
                err.get("error", "Rate limited"),
                retry_after=retry_after_int,
                limit=err.get("limit")
            )
        
        # Parse response
        try:
            j = resp.json()
        except ValueError:
            j = {}
        
        if resp.status_code >= 400:
            msg = j.get("error", f"API returned HTTP {resp.status_code}")
            raise APIError(msg, status_code=resp.status_code)
        
        return j
    
    def evaluate(
        self,
        data: Dict[str, List[float]],
        config: Union[Dict[str, Any], QuantumConfig],
        backend: str = 'simulator',
        shots: int = 1024,
        num_eval_qubits: int = 6,
        ibm_credentials: Optional[Dict[str, str]] = None
    ) -> QuantumResult:
        """
        Synchronous evaluation (blocks until result).
        
        Best for:
        - Simulator backend (fast ~5-15s)
        - Development/testing
        - Single evaluations
        
        Limitations:
        - IBM hardware NOT supported (use submit_async instead)
        - May timeout for complex circuits (>50s)
        - Subject to Vercel timeout limits
        
        Args:
            data: Dict mapping block names to value lists
            config: Hierarchical configuration (dict or QuantumConfig)
            backend: 'simulator' only (IBM requires async)
            shots: Number of quantum measurements
            num_eval_qubits: Evaluation qubits for QAE
            ibm_credentials: Not used for sync (raises error if backend='ibm_quantum')
        
        Returns:
            QuantumResult with score and metadata
            
        Raises:
            ValueError: If backend='ibm_quantum' (must use async)
            
        Example:
            >>> # Fast simulator evaluation
            >>> result = sdk.evaluate(
            ...     data={'flujo': [0.5, 0.8]},
            ...     config=config,
            ...     backend='simulator'
            ... )
            >>> print(f"Score: {result.score:.4f}")
        """
        # Convert QuantumConfig to dict if needed
        if isinstance(config, QuantumConfig):
            config = config.to_dict()
        
        # Validate inputs
        self._validate_config(config)
        self._validate_data(data, config)
        
        if backend not in ['simulator', 'ibm_quantum']:
            raise ValidationError("backend must be 'simulator' or 'ibm_quantum'")
        
        # Sync only supports simulator
        if backend == 'ibm_quantum':
            raise ValueError(
                "Synchronous evaluation does not support IBM Quantum hardware. "
                "Use submit_async() or evaluate_async() instead."
            )
        
        # Build payload
        payload = {
            'data': data,
            'config': config,
            'backend': backend,
            'shots': shots,
            'num_eval_qubits': num_eval_qubits
        }
        
        if self.license_key:
            payload['license_key'] = self.license_key
        
        # Make sync request (POST /)
        response = self._make_request('', payload)
        
        # Handle 202 Accepted (job taking longer, switched to async)
        if 'job_id' in response and response.get('status') in ('processing', 'queued'):
            job_id = response['job_id']
            logger.warning(f"Evaluation exceeded sync timeout, polling job {job_id}...")
            return self.wait_for_result(job_id, poll_interval=2, timeout=120)
        
        return QuantumResult.from_response(response)
    
    # ----------------------------------
    # ASYNC METHODS
    # ----------------------------------
    
    def submit_async(
        self,
        data: Dict[str, List[float]],
        config: Union[Dict[str, Any], QuantumConfig],
        backend: str = 'simulator',
        shots: int = 1024,
        num_eval_qubits: int = 6,
        ibm_credentials: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Submit job to async queue (non-blocking).
        
        Best for:
        - IBM Quantum hardware (REQUIRED)
        - Complex simulator circuits (>50s)
        - Batch processing
        - Long-running evaluations
        
        Advantages:
        - No timeout limits
        - Non-blocking (returns job_id immediately)
        - Can process multiple jobs in parallel
        
        Args:
            data: Dict mapping block names to value lists
            config: Hierarchical configuration (dict or QuantumConfig)
            backend: 'simulator' or 'ibm_quantum'
            shots: Number of measurements
            num_eval_qubits: QAE qubits (simulator only)
            ibm_credentials: Required for IBM backend
                Example: {'token': '...', 'backend_name': 'ibm_brisbane'}
        
        Returns:
            job_id for status polling
            
        Example:
            >>> # Submit IBM job
            >>> job_id = sdk.submit_async(
            ...     data=data,
            ...     config=config,
            ...     backend='ibm_quantum',
            ...     ibm_credentials={'token': '...', 'backend_name': 'ibm_brisbane'}
            ... )
            >>> print(f"Job ID: {job_id}")
            >>> 
            >>> # Poll manually
            >>> status = sdk.get_job_status(job_id)
            >>> if status.is_completed:
            ...     print(f"Score: {status.result.score:.4f}")
            >>> 
            >>> # Or wait automatically
            >>> result = sdk.wait_for_result(job_id, timeout=600)
        """
        # Convert QuantumConfig to dict if needed
        if isinstance(config, QuantumConfig):
            config = config.to_dict()
        
        # Validate inputs
        self._validate_config(config)
        self._validate_data(data, config)
        
        if backend not in ['simulator', 'ibm_quantum']:
            raise ValidationError("backend must be 'simulator' or 'ibm_quantum'")
        
        if backend == 'ibm_quantum' and not ibm_credentials:
            raise ValidationError("ibm_credentials required for IBM backend")
        
        if ibm_credentials:
            if not isinstance(ibm_credentials, dict) or 'token' not in ibm_credentials:
                raise ValidationError("ibm_credentials must contain 'token'")
        
        # Build payload
        payload = {
            'data': data,
            'config': config,
            'backend': backend,
            'shots': shots
        }
        
        if backend == 'simulator':
            payload['num_eval_qubits'] = num_eval_qubits
        
        if self.license_key:
            payload['license_key'] = self.license_key
        
        if ibm_credentials:
            payload['ibm_credentials'] = ibm_credentials
        
        # Submit to async queue (POST /enqueue)
        response = self._make_request('enqueue', payload)
        job_id = response.get('job_id')
        
        if not job_id:
            raise APIError("Server did not return job_id")
        
        logger.info(f"Quantum job submitted: {job_id} (backend: {backend})")
        return job_id
    
    def get_job_status(self, job_id: str) -> JobStatus:
        """
        Check status of async job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            JobStatus object with current state
        """
        # Try GET first (more efficient)
        base = self.base_url.rstrip("/")
        url = f"{base}/status/{job_id}"
        
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code == 200:
                result = resp.json()
                logger.debug(f"Job {job_id} status: {result.get('status')}")
                return JobStatus.from_response(result)
        except:
            pass
        
        # Fallback to POST
        response = self._make_request('status', {'job_id': job_id})
        return JobStatus.from_response(response)
    
    def wait_for_result(
        self,
        job_id: str,
        poll_interval: int = 5,
        timeout: int = 600
    ) -> QuantumResult:
        """
        Wait for async job to complete with polling.
        
        Args:
            job_id: Job ID to wait for
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds
            
        Returns:
            QuantumResult with score and metadata
            
        Raises:
            TimeoutError: If timeout exceeded
            APIError: If job fails
        """
        start = time.time()
        
        while True:
            job_status = self.get_job_status(job_id)
            
            if job_status.is_completed:
                if job_status.result is None:
                    raise APIError("Job completed but no result returned")
                return job_status.result
            
            elif job_status.is_failed:
                error_msg = job_status.error or 'Unknown error'
                raise APIError(f"Job failed: {error_msg}")
            
            elif job_status.is_running:
                elapsed = time.time() - start
                if elapsed > timeout:
                    raise TimeoutError(f"Job {job_id} timed out after {timeout}s")
                
                # Warning if approaching timeout
                if elapsed > timeout * 0.8:
                    pct = int((elapsed/timeout)*100)
                    logger.warning(f"Job {job_id} running >{pct}% of timeout ({elapsed:.1f}s/{timeout}s)")
                
                logger.info(f"Job {job_id} status: {job_status.status}, waiting {poll_interval}s...")
                time.sleep(poll_interval)
            
            else:
                raise APIError(f"Unknown job status: {job_status.status}")
    
    def evaluate_async(
        self,
        data: Dict[str, List[float]],
        config: Union[Dict[str, Any], QuantumConfig],
        backend: str = 'simulator',
        shots: int = 1024,
        num_eval_qubits: int = 6,
        ibm_credentials: Optional[Dict[str, str]] = None,
        poll_interval: int = 5,
        timeout: int = 600
    ) -> QuantumResult:
        """
        Convenience method: submit + wait in one call.
        
        Returns:
            QuantumResult with score and metadata
        """
        job_id = self.submit_async(
            data, config, backend, shots, num_eval_qubits, ibm_credentials
        )
        logger.info(f"Quantum job submitted: {job_id}, polling every {poll_interval}s")
        return self.wait_for_result(job_id, poll_interval, timeout)
    
    def healthcheck(self) -> Dict[str, Any]:
        """Check API health status"""
        url = urljoin(self.base_url, 'health')
        response = self.session.get(url, timeout=10)
        return response.json()
    
    def create_config(self) -> QuantumConfig:
        """
        Create a new quantum configuration builder.
        
        Returns:
            QuantumConfig object for fluent configuration building
            
        Example:
            >>> config = sdk.create_config() \\
            ...     .add_block('flujo_caja', 
            ...                influence=[0.5, 0.3, 0.2],
            ...                priority=[1.4, 1.2, 1.0]) \\
            ...     .add_block('comportamiento',
            ...                influence=[0.2, 0.3, 0.5],
            ...                priority=[1.8, 1.4, 1.0]) \\
            ...     .set_global_adjustment(0.01)
        """
        return QuantumConfig()
    
    def close(self):
        """Close session and cleanup"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __repr__(self):
        return f"QuantumSDK(url='{self.base_url}', backend='simulator|ibm_quantum')"


# ----------------------------------
# HELPER FUNCTIONS
# ----------------------------------

def create_block(
    name: str,
    influence: List[float],
    priority: List[float],
    risk_adjustment: float = 0.0,
    block_influence: float = 1.0,
    block_priority: float = 1.0
) -> Block:
    """
    Create a block configuration object.
    
    Args:
        name: Block identifier (must match data keys)
        influence: Weight per value in block
        priority: Criticality per value in block
        risk_adjustment: Penalty factor (0.0-1.0)
        block_influence: Global weight for this block
        block_priority: Global criticality for this block
    
    Returns:
        Block object
        
    Example:
        >>> block = create_block(
        ...     'flujo_caja',
        ...     influence=[0.5, 0.3, 0.2],
        ...     priority=[1.4, 1.2, 1.0],
        ...     risk_adjustment=0.1
        ... )
    """
    return Block(
        name=name,
        influence=influence,
        priority=priority,
        risk_adjustment=risk_adjustment,
        block_influence=block_influence,
        block_priority=block_priority
    )


def create_config(blocks: List[Block], global_adjustment: float = 0.0) -> QuantumConfig:
    """
    Create full hierarchical quantum config from blocks.
    
    Args:
        blocks: List of Block objects
        global_adjustment: Global penalty factor (0.0-1.0)
    
    Returns:
        QuantumConfig object
        
    Example:
        >>> b1 = create_block('flujo', [0.5, 0.3], [1.4, 1.2])
        >>> b2 = create_block('comportamiento', [0.3, 0.7], [1.8, 1.0])
        >>> config = create_config([b1, b2], global_adjustment=0.01)
    """
    config = QuantumConfig()
    for block in blocks:
        config.add_block(
            name=block.name,
            influence=block.influence,
            priority=block.priority,
            risk_adjustment=block.risk_adjustment,
            block_influence=block.block_influence,
            block_priority=block.block_priority
        )
    config.set_global_adjustment(global_adjustment)
    return config