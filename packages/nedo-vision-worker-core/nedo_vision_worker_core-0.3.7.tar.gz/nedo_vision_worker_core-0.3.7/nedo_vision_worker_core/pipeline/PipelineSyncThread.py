import json
import logging
import time
import threading
from typing import Dict, Set, Optional
from ..repositories.WorkerSourcePipelineDebugRepository import WorkerSourcePipelineDebugRepository
from ..repositories.WorkerSourcePipelineRepository import WorkerSourcePipelineRepository
from .PipelineManager import PipelineManager
from .ModelManager import ModelManager
from ..streams.VideoStreamManager import VideoStreamManager


class PipelineSyncThread(threading.Thread):
    """Thread responsible for synchronizing worker source pipelines from the database in real-time."""

    def __init__(self, video_manager: VideoStreamManager, polling_interval=5, max_workers=4):
        super().__init__(daemon=True)  # Runs as a daemon
        self.video_manager = video_manager
        self.polling_interval = polling_interval
        self.pipeline_repo = WorkerSourcePipelineRepository()
        self.debug_repo = WorkerSourcePipelineDebugRepository()
        self.model_manager = ModelManager()
        self.running = True
        self.pipeline_manager = PipelineManager(video_manager, self.on_pipeline_stopped, max_workers)

    def _parse_json(self, value: str) -> Optional[dict]:
        """Attempts to parse the value as JSON if applicable."""
        if not value:
            return None
        
        value = value.strip()  # Remove leading/trailing spaces
        if (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]")):
            try:
                return json.loads(value)  # Parse JSON object or list
            except json.JSONDecodeError:
                pass  # Keep as string if parsing fails
        return None
        
    def on_pipeline_stopped(self, pipeline_id: str) -> None:
        """Set the pipeline as stopped in the database."""
        try:
            pipeline = self.pipeline_repo.get_worker_source_pipeline(pipeline_id)
            if pipeline:
                new_status = "run" if pipeline.pipeline_status_code == "restart" else "stop"
                self.pipeline_repo.update_pipeline_status(pipeline_id, new_status)
        except Exception as e:
            logging.error(f"Failed to update pipeline status for {pipeline_id}: {e}")

    def run(self) -> None:
        """Continuously updates pipelines based on database changes."""
        while self.running:
            try:
                db_pipelines = {p.id: p for p in self.pipeline_repo.get_all_pipelines()}
                
                # Get pipeline IDs for comparison
                local_pipeline_ids = set(self.pipeline_manager.get_active_pipelines())
                db_pipeline_ids = set(db_pipelines.keys())

                # Process pipeline changes
                self._add_new_pipelines(db_pipeline_ids - local_pipeline_ids, db_pipelines)
                self._remove_deleted_pipelines(local_pipeline_ids - db_pipeline_ids)
                self._update_existing_pipelines(db_pipeline_ids & local_pipeline_ids, db_pipelines)

                # Sync the cache to remove unused detectors
                active_model_ids = {p.ai_model_id for p in db_pipelines.values() if p.pipeline_status_code == 'run'}
                self.model_manager.sync_cache(active_model_ids)

            except Exception as e:
                logging.error(f"⚠️ Error syncing pipelines from database: {e}", exc_info=True)

            time.sleep(self.polling_interval) 

    def _add_new_pipelines(self, pipeline_ids: Set[str], db_pipelines: Dict[str, object]) -> None:
        """Add new pipelines that exist in DB but not locally."""
        for pid in pipeline_ids:
            pipeline = db_pipelines[pid]

            if pipeline.pipeline_status_code == 'restart':
                # Update status in database
                self.pipeline_repo.update_pipeline_status(pid, 'run')
                # Update local object too for consistency
                pipeline.pipeline_status_code = 'run'

            if pipeline.pipeline_status_code == 'run':
                detector = self.model_manager.get_detector(pipeline.ai_model_id)
                
                if not detector and pipeline.ai_model_id:
                    logging.warning(f"⚠️ Could not load detector for pipeline {pid} ({pipeline.name}). Skipping.")
                    continue
                
                logging.info(f"🟢 Adding new pipeline: {pid} ({pipeline.name})")
                self.pipeline_manager.start_pipeline(pipeline, detector)

    def _remove_deleted_pipelines(self, pipeline_ids: Set[str]) -> None:
        """Remove pipelines that exist locally but not in DB."""
        for pid in pipeline_ids:
            logging.info(f"🔴 Removing deleted pipeline: {pid}")
            self.pipeline_manager.stop_pipeline(pid)

    def _update_existing_pipelines(self, pipeline_ids: Set[str], db_pipelines: Dict[str, object]) -> None:
        """Update existing pipelines that need changes."""
        debug_pipeline_ids = self.debug_repo.get_pipeline_ids_to_debug()

        for pid in pipeline_ids:
            db_pipeline = db_pipelines[pid]
            
            # Check if pipeline should be stopped (status changed to stop/restart in DB)
            if db_pipeline.pipeline_status_code in ['stop', 'restart']:
                if self.pipeline_manager.is_running(pid):
                    logging.info(f"⏹️ Stopping pipeline due to status change: {pid}")
                    self.pipeline_manager.stop_pipeline(pid)
                continue
            
            processor = self.pipeline_manager.processors.get(pid)
            if not processor:
                # Pipeline exists in both sets but processor doesn't exist - shouldn't happen
                # but if it does, try to start it if status is 'run'
                if db_pipeline.pipeline_status_code == 'run':
                    logging.warning(f"⚠️ Pipeline {pid} exists locally but has no processor. Restarting...")
                    detector = self.model_manager.get_detector(db_pipeline.ai_model_id)
                    self.pipeline_manager.start_pipeline(db_pipeline, detector)
                continue

            local_detector = processor.detector

            self.update_pipeline(pid, db_pipeline, local_detector)
            if pid in debug_pipeline_ids:
                processor.enable_debug()

    def update_pipeline(self, pid: str, db_pipeline: object, local_detector: object) -> None:
        """Updates a single pipeline if necessary (only called for running pipelines)."""
        processor = self.pipeline_manager.processors.get(pid)
        if not processor:
            return

        # At this point, we know db_pipeline.pipeline_status_code == 'run' (checked in caller)
        # Check for significant changes that require a restart
        db_detector = self.model_manager.get_detector(db_pipeline.ai_model_id)

        requires_restart = any([
            db_pipeline.ai_model_id != processor._pipeline.ai_model_id,
            db_pipeline.worker_source_id != processor._pipeline.worker_source_id,
            local_detector != db_detector
        ])

        if requires_restart:
            logging.info(f"🔄 Restarting pipeline due to significant changes: {pid}")
            self.pipeline_manager.stop_pipeline(pid)
            self.pipeline_manager.start_pipeline(db_pipeline, db_detector)
        else:
            # Update config for minor changes that don't require restart
            processor.update_config(db_pipeline)


    def _has_pipeline_changed(self, local_pipeline, db_pipeline):
        """Checks if the pipeline configuration has changed."""
        if not local_pipeline or db_pipeline.pipeline_status_code == "restart":
            return True

        local_configs = local_pipeline.worker_source_pipeline_configs
        db_configs = db_pipeline.worker_source_pipeline_configs

        # Convert config objects to comparable structures
        local_config_values = [
            (config.pipeline_config_id, config.is_enabled, config.value, 
             config.pipeline_config_name, config.pipeline_config_code)
            for config in local_configs
        ]

        db_config_values = [
            (config.pipeline_config_id, config.is_enabled, config.value, 
             config.pipeline_config_name, config.pipeline_config_code)
            for config in db_configs
        ]

        return sorted(local_config_values) != sorted(db_config_values)

    def stop(self):
        """Stops the synchronization thread and shuts down pipelines properly."""
        logging.info("🛑 Stopping PipelineSyncThread...")
        self.running = False
        self.video_manager.stop_all()
        self.pipeline_manager.shutdown()