"""Background monitor for camera configuration updates."""

import hashlib
import json
import logging
import threading
import time
from typing import Dict, Optional

from matrice_inference.server.stream.utils import CameraConfig


class CameraConfigMonitor:
    """Monitors and syncs camera configurations from app deployment API."""

    DEFAULT_CHECK_INTERVAL = 120  # seconds

    def __init__(
        self,
        app_deployment,
        streaming_pipeline,
        check_interval: int = DEFAULT_CHECK_INTERVAL
    ):
        """Initialize the camera config monitor.
        
        Args:
            app_deployment: AppDeployment instance to fetch configs
            streaming_pipeline: StreamingPipeline instance to update
            check_interval: Seconds between config checks
        """
        self.app_deployment = app_deployment
        self.streaming_pipeline = streaming_pipeline
        self.check_interval = max(10, int(check_interval))  # Minimum 10 seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        
        # Track camera configs by hash to detect changes (thread-safe access)
        self.camera_hashes: Dict[str, str] = {}
        self._hashes_lock = threading.Lock()

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self.running:
            self.logger.warning("Camera config monitor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            name="CameraConfigMonitor",
            daemon=False
        )
        self.thread.start()
        self.logger.info(f"Started camera config monitor (check interval: {self.check_interval}s)")

    def stop(self) -> None:
        """Stop the background monitoring thread."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            self.logger.info("Stopped camera config monitor")

    def _monitor_loop(self) -> None:
        """Main monitoring loop - periodically sync camera configs."""
        while self.running:
            try:
                self._sync_camera_configs()
            except Exception as e:
                self.logger.error(f"Error syncing camera configs: {e}")
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _sync_camera_configs(self) -> None:
        """Fetch latest configs from API and sync with pipeline."""
        try:
            # Fetch current configs from app deployment API
            latest_configs = self.app_deployment.get_camera_configs()
            
            if not latest_configs:
                self.logger.debug("No camera configs returned from API")
                return
            
            # Process each camera config
            for camera_id, camera_config in latest_configs.items():
                self._process_camera_config(camera_id, camera_config)
            
            # Optional: Remove cameras that are no longer in API
            # Uncomment if you want to auto-remove deleted cameras
            # self._remove_deleted_cameras(latest_configs)
            
        except Exception as e:
            self.logger.error(f"Failed to sync camera configs: {e}")

    def _process_camera_config(self, camera_id: str, camera_config: CameraConfig) -> None:
        """Process a single camera config - add new or update changed."""
        try:
            # Calculate config hash to detect changes
            config_hash = self._hash_camera_config(camera_config)
            
            # Thread-safe read of previous hash
            with self._hashes_lock:
                previous_hash = self.camera_hashes.get(camera_id)
            
            # Check if this is a new camera or config changed
            if previous_hash is None:
                # New camera - add it
                self._add_new_camera(camera_id, camera_config, config_hash)
            elif previous_hash != config_hash:
                # Config changed - update it
                self._update_changed_camera(camera_id, camera_config, config_hash)
            else:
                # No change - skip
                self.logger.debug(f"Camera {camera_id} config unchanged")
                
        except Exception as e:
            self.logger.error(f"Error processing camera {camera_id}: {e}")

    def _add_new_camera(self, camera_id: str, camera_config: CameraConfig, config_hash: str) -> None:
        """Add a new camera to the pipeline."""
        try:
            # Use asyncio to add camera config
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self.streaming_pipeline.add_camera_config(camera_config)
                )
                if success:
                    # Thread-safe write
                    with self._hashes_lock:
                        self.camera_hashes[camera_id] = config_hash
                    self.logger.info(f"Added new camera: {camera_id}")
                else:
                    self.logger.warning(f"Failed to add camera: {camera_id}")
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error adding camera {camera_id}: {e}")

    def _update_changed_camera(self, camera_id: str, camera_config: CameraConfig, config_hash: str) -> None:
        """Update an existing camera with changed config."""
        try:
            # Use asyncio to update camera config
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self.streaming_pipeline.update_camera_config(camera_config)
                )
                if success:
                    # Thread-safe write
                    with self._hashes_lock:
                        self.camera_hashes[camera_id] = config_hash
                    self.logger.info(f"Updated camera config: {camera_id}")
                else:
                    self.logger.warning(f"Failed to update camera: {camera_id}")
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error updating camera {camera_id}: {e}")

    def _remove_deleted_cameras(self, latest_configs: Dict[str, CameraConfig]) -> None:
        """Remove cameras that are no longer in the API response."""
        # Thread-safe read
        with self._hashes_lock:
            current_camera_ids = set(self.camera_hashes.keys())
        
        latest_camera_ids = set(latest_configs.keys())
        deleted_camera_ids = current_camera_ids - latest_camera_ids
        
        for camera_id in deleted_camera_ids:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(
                        self.streaming_pipeline.remove_camera_config(camera_id)
                    )
                    if success:
                        # Thread-safe delete
                        with self._hashes_lock:
                            del self.camera_hashes[camera_id]
                        self.logger.info(f"Removed deleted camera: {camera_id}")
                finally:
                    loop.close()
            except Exception as e:
                self.logger.error(f"Error removing camera {camera_id}: {e}")

    def _hash_camera_config(self, camera_config: CameraConfig) -> str:
        """Generate a hash of the camera config to detect changes."""
        try:
            # Create a dict with relevant config fields
            config_dict = {
                "camera_id": camera_config.camera_id,
                "input_topic": camera_config.input_topic,
                "output_topic": camera_config.output_topic,
                "stream_config": camera_config.stream_config,
                "enabled": camera_config.enabled
            }
            
            # Convert to JSON string (sorted for consistency) and hash
            config_str = json.dumps(config_dict, sort_keys=True)
            return hashlib.md5(config_str.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error hashing camera config: {e}")
            return ""

