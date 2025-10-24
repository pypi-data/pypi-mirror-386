"""
Run object for managing experiment runs.
"""

import time
from typing import Any, Dict, List, Optional, Union
from .api import APIClient
from .config import Config
from .exceptions import ValidationError, RunNotFoundError
from .image_utils import detect_image_type, convert_to_bytes, ImageConversionError


class Run:
    """
    Represents an active experiment run.
    
    Similar to wandb.run, this object provides methods for logging
    metrics, configurations, and managing the run lifecycle.
    """
    
    def __init__(
        self,
        api_client: APIClient,
        run_id: str,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        group_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.api_client = api_client
        self.run_id = run_id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.group_id = group_id
        self.config = Config(config or {})
        self._finished = False
        self._start_time = time.time()
        
        # Log initial configuration if provided
        if config:
            self._log_configs(config)
    
    def log(
        self, 
        data: Dict[str, Any], 
        step: Optional[int] = None
    ) -> None:
        """
        Log metrics and other data.
        
        Args:
            data: Dictionary of metrics to log
            step: Step number (optional)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        # Convert data to metrics format and handle images
        metrics = []
        for key, value in data.items():
            # Check if value is a dict with metadata
            if isinstance(value, dict) and 'value' in value:
                # Extract actual value and metadata
                actual_value = value['value']
                title = value.get('title')
                description = value.get('description')
                
                # Check if it's an image
                if detect_image_type(actual_value):
                    try:
                        self._upload_image(
                            actual_value,
                            key,
                            step=step,
                            title=title,
                            description=description
                        )
                    except ImageConversionError as e:
                        print(f"Warning: Failed to log image '{key}': {e}")
                    continue
                
                # Otherwise treat as numeric or config
                if isinstance(actual_value, (int, float)):
                    metric = {"key": key, "value": actual_value}
                    if step is not None:
                        metric["step"] = step
                    metrics.append(metric)
                else:
                    self.config[key] = str(actual_value)
            
            # Check if value itself is an image
            elif detect_image_type(value):
                try:
                    self._upload_image(value, key, step=step)
                except ImageConversionError as e:
                    print(f"Warning: Failed to log image '{key}': {e}")
            
            # Handle numeric metrics
            elif isinstance(value, (int, float)):
                metric = {"key": key, "value": value}
                if step is not None:
                    metric["step"] = step
                metrics.append(metric)
            
            # For non-numeric values, convert to string and log as config
            else:
                self.config[key] = str(value)
        
        if metrics:
            self.api_client.log_metrics(self.run_id, metrics)
    
    def log_metric(
        self, 
        key: str, 
        value: Union[int, float], 
        step: Optional[int] = None
    ) -> None:
        """
        Log a single metric.
        
        Args:
            key: Metric name
            value: Metric value
            step: Step number (optional)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        self.api_client.log_metric(self.run_id, key, value, step)
    
    def log_metrics(
        self, 
        metrics: List[Dict[str, Any]]
    ) -> None:
        """
        Log multiple metrics.
        
        Args:
            metrics: List of metric dictionaries with 'key' and 'value' fields
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        self.api_client.log_metrics(self.run_id, metrics)
    
    def log_config(self, key: str, value: Any) -> None:
        """
        Log a configuration parameter.
        
        Args:
            key: Configuration key
            value: Configuration value (will be converted to string)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        self.config[key] = str(value)
        self.api_client.log_config(self.run_id, key, str(value))
    
    def log_configs(self, configs: Dict[str, Any]) -> None:
        """
        Log multiple configuration parameters.
        
        Args:
            configs: Dictionary of configuration parameters
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        # Update local config
        self.config.update(configs)
        
        # Convert all values to strings for API
        string_configs = {k: str(v) for k, v in configs.items()}
        self.api_client.log_configs(self.run_id, string_configs)
    
    def finish(self, status: str = "FINISHED") -> None:
        """
        Finish the run.
        
        Args:
            status: Run status ("FINISHED", "FAILED", or "CANCELLED")
        """
        if self._finished:
            return
        
        self._finished = True
        self.api_client.finish_run(self.run_id, status)
    
    def get_metrics(
        self, 
        metric_key: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get metrics for this run.
        
        Args:
            metric_key: Filter by specific metric key
            limit: Number of metrics to return
            offset: Number of metrics to skip
            
        Returns:
            List of metric dictionaries
        """
        return self.api_client.get_metrics(
            self.run_id, metric_key, limit, offset
        )
    
    def get_run_data(self) -> Dict[str, Any]:
        """
        Get the full run data including metrics and configurations.
        
        Returns:
            Dictionary containing run information
        """
        return self.api_client.get_run(self.run_id)
    
    def _log_configs(self, configs: Dict[str, Any]) -> None:
        """Internal method to log initial configurations."""
        string_configs = {k: str(v) for k, v in configs.items()}
        self.api_client.log_configs(self.run_id, string_configs)
    
    def _upload_image(
        self,
        image: Any,
        name: str,
        step: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Internal method to upload an image.
        
        Args:
            image: Image object (PIL, numpy, path, or matplotlib figure)
            name: Name/key for the image
            step: Optional step number
            title: Optional title
            description: Optional description
            
        Returns:
            Media log record
        """
        # Convert image to bytes
        file_bytes, mime_type, filename = convert_to_bytes(image)
        
        # Use name as filename if not from path
        if not filename or filename.startswith('image.') or filename.startswith('plot.'):
            ext = filename.split('.')[-1] if '.' in filename else 'png'
            filename = f"{name}.{ext}"
        
        # Prepare metadata
        metadata = {
            'step': step,
            'title': title or name,
            'description': description,
        }
        
        # Upload via API
        return self.api_client.upload_media(
            self.run_id,
            file_bytes,
            filename,
            mime_type,
            metadata
        )
    
    def log_image(
        self,
        image: Any,
        name: str,
        step: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Log an image to the run.
        
        Supports PIL Images, numpy arrays, file paths, and matplotlib figures.
        
        Args:
            image: Image object (PIL.Image, numpy array, file path, or matplotlib figure)
            name: Name/key for the image
            step: Optional step number
            title: Optional title (defaults to name)
            description: Optional description
            
        Example:
            >>> import numpy as np
            >>> from PIL import Image
            >>> 
            >>> # Log a PIL image
            >>> img = Image.open("photo.jpg")
            >>> run.log_image(img, "input_photo", step=0)
            >>> 
            >>> # Log a numpy array
            >>> array = np.random.rand(100, 100, 3)
            >>> run.log_image(array, "random_pattern", step=1)
            >>> 
            >>> # Log a matplotlib figure
            >>> import matplotlib.pyplot as plt
            >>> fig, ax = plt.subplots()
            >>> ax.plot([1, 2, 3], [1, 4, 9])
            >>> run.log_image(fig, "loss_curve", step=2)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        try:
            self._upload_image(image, name, step, title, description)
        except ImageConversionError as e:
            raise ValidationError(f"Failed to log image: {e}")
    
    @property
    def id(self) -> str:
        """Get the run ID."""
        return self.run_id
    
    @property
    def project(self) -> str:
        """Get the project ID."""
        return self.project_id
    
    @property
    def is_finished(self) -> bool:
        """Check if the run is finished."""
        return self._finished
    
    @property
    def duration(self) -> float:
        """Get the run duration in seconds."""
        if self._finished:
            return time.time() - self._start_time
        return time.time() - self._start_time
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically finish the run."""
        if not self._finished:
            status = "FAILED" if exc_type else "FINISHED"
            self.finish(status)
    
    def __repr__(self) -> str:
        status = "finished" if self._finished else "running"
        return f"Run(id='{self.run_id}', name='{self.name}', status='{status}')" 