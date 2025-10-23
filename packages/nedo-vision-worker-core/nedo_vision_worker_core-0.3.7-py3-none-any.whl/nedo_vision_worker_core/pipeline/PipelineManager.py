import logging
import threading
from typing import Dict
from .PipelineProcessor import PipelineProcessor
from ..streams.VideoStreamManager import VideoStreamManager

class PipelineManager:
    """Manages AI pipeline execution and video stream processing."""

    def __init__(self, video_manager: VideoStreamManager, on_pipeline_stopped, max_workers=50):
        self.max_workers = max_workers
        self.pipeline_threads = {}  # Stores Thread objects {pipeline_id: Thread}
        self.pipeline_metadata = {}  # Stores actual pipeline data {pipeline_id: metadata}
        self.video_manager = video_manager  # Manages video streams
        self.processors: Dict[str, PipelineProcessor] = {}  # Stores PipelineProcessor instances per pipeline
        self.running = True
        self._stopping_pipelines = set()  # Track pipelines being stopped
        self._stop_lock = threading.Lock()  # Lock for thread-safe pipeline stopping
        self.on_pipeline_stopped = on_pipeline_stopped

    def start_pipeline(self, pipeline, detector):
        """
        Start a pipeline processing.
        Args:
            pipeline: The pipeline object (contains id, worker_source_id, name, etc.)
            detector: The detector instance to use for processing.
        """
        pipeline_id = pipeline.id
        worker_source_id = pipeline.worker_source_id

        if not self.running:
            logging.warning(f"⚠️ Attempt to start pipeline {pipeline_id} after shutdown.")
            return

        if self.is_running(pipeline_id):
            logging.warning(f"⚠️ Pipeline {pipeline_id} is already running.")
            return

        logging.info(f"🚀 Starting Pipeline processing for pipeline: {pipeline_id} | Source: {worker_source_id} ({pipeline.name})")

        # Acquire the video stream (starts it if not already running)
        if not self.video_manager.acquire_stream(worker_source_id, pipeline_id):
            logging.error(f"❌ Failed to acquire stream {worker_source_id} for pipeline {pipeline_id}")
            return

        processor = PipelineProcessor(pipeline, detector, False)
        processor.frame_drawer.location_name = pipeline.location_name
        self.processors[pipeline_id] = processor  # Store processor instance

        active_count = len([t for t in self.pipeline_threads.values() if t.is_alive()])
        logging.info(f"📋 Starting pipeline {pipeline_id} thread (active threads: {active_count})")
        
        try:
            # Wrap the execution to catch any early errors
            def _safe_process_pipeline():
                try:
                    logging.info(f"🏁 Pipeline {pipeline_id} thread execution beginning...")
                    processor.process_pipeline(self.video_manager)
                except Exception as e:
                    logging.error(f"❌ Unhandled error in pipeline {pipeline_id} thread: {e}", exc_info=True)
                finally:
                    # Ensure cleanup callback is called
                    self._handle_pipeline_completion(pipeline_id)
            
            # Create and start thread directly
            thread = threading.Thread(
                target=_safe_process_pipeline,
                name=f"pipeline-{pipeline_id[:8]}",
                daemon=True
            )
            
            self.pipeline_threads[pipeline_id] = thread
            self.pipeline_metadata[pipeline_id] = pipeline
            
            logging.info(f"⚙️ Starting thread for pipeline {pipeline_id}")
            thread.start()
            logging.info(f"✅ Pipeline {pipeline_id} thread started successfully")

        except Exception as e:
            logging.error(f"❌ Failed to start pipeline {pipeline_id} thread: {e}", exc_info=True)
            # Clean up on failure
            self.processors.pop(pipeline_id, None)
            self.video_manager.release_stream(worker_source_id, pipeline_id)
            raise

    def _handle_pipeline_completion(self, pipeline_id: str):
        """
        Handles cleanup when a pipeline finishes processing.
        """
        with self._stop_lock:
            if pipeline_id in self._stopping_pipelines:
                return  # If it's already being stopped manually, don't trigger again

        try:
            logging.info(f"🏁 Pipeline {pipeline_id} completed execution")
        except Exception as e:
            logging.error(f"⚠️ Error in handling pipeline {pipeline_id} completion: {e}")

        finally:
            self.on_pipeline_stopped(pipeline_id)

    def stop_pipeline(self, pipeline_id: str):
        """Stop an AI processing pipeline."""
        with self._stop_lock:
            if pipeline_id in self._stopping_pipelines:
                logging.debug(f"Pipeline {pipeline_id} already being stopped, skipping")
                return
            self._stopping_pipelines.add(pipeline_id)

        try:
            # Get worker_source_id before removing metadata
            pipeline = self.pipeline_metadata.get(pipeline_id)
            worker_source_id = pipeline.worker_source_id if pipeline else None

            # Stop AI processing
            processor = self.processors.pop(pipeline_id, None)
            if processor:
                processor.stop()

            # Stop execution thread (thread will terminate naturally)
            thread = self.pipeline_threads.pop(pipeline_id, None)
            if thread and thread.is_alive():
                # Thread is daemon, will stop when processor.running becomes False
                logging.debug(f"Waiting for pipeline {pipeline_id} thread to terminate...")
                thread.join(timeout=5.0)
                if thread.is_alive():
                    logging.warning(f"Pipeline {pipeline_id} thread did not terminate cleanly")

            # Remove metadata
            self.pipeline_metadata.pop(pipeline_id, None)

            # Release the video stream (stops it if no more pipelines use it)
            if worker_source_id:
                self.video_manager.release_stream(worker_source_id, pipeline_id)

            logging.info(f"✅ Pipeline {pipeline_id} stopped successfully.")

        except Exception as e:
            logging.error(f"❌ Error during pipeline shutdown: {e}")
        
        finally:
            self._stopping_pipelines.discard(pipeline_id)
            self.on_pipeline_stopped(pipeline_id)

    def get_active_pipelines(self):
        """Returns a list of active pipeline IDs."""
        return list(self.pipeline_metadata.keys())

    def get_pipeline(self, pipeline_id):
        """Returns the actual pipeline metadata (not the Future object)."""
        return self.pipeline_metadata.get(pipeline_id, None)

    def is_running(self, pipeline_id):
        """
        Checks if a pipeline is currently running.
        
        Args:
            pipeline_id (str): The ID of the pipeline to check.
            
        Returns:
            bool: True if the pipeline is running, False otherwise.
        """
        thread = self.pipeline_threads.get(pipeline_id)
        return thread is not None and thread.is_alive()

    def shutdown(self):
        """Shuts down the pipeline manager gracefully."""
        logging.info("🛑 Shutting down PipelineManager...")
        self.running = False

        for pipeline_id in list(self.pipeline_threads.keys()):
            self.stop_pipeline(pipeline_id)

        logging.info("✅ PipelineManager stopped.")

        self.executor.shutdown(wait=True)  # Wait for all threads to finish
        logging.info("✅ PipelineManager stopped.")
