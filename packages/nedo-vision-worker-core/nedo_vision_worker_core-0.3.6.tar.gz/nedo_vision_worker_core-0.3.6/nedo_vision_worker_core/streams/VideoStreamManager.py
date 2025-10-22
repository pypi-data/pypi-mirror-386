import logging
import time
import threading
from typing import Any, Dict, Optional

from .VideoStream import VideoStream
from .SharedVideoDeviceManager import SharedVideoDeviceManager


class VideoStreamManager:
    """Manages multiple video streams (files/RTSP) and direct devices (/dev/videoN or index) safely."""

    def __init__(self):
        # Regular streams: {worker_source_id: VideoStream}
        self.streams: Dict[Any, VideoStream] = {}
        # Direct device streams: {worker_source_id: {'url':..., 'latest_frame':..., 'last_update':..., 'alive': bool}}
        self.direct_device_streams: Dict[Any, Dict[str, Any]] = {}
        # Per-direct-device locks: {worker_source_id: threading.Lock}
        self.direct_device_locks: Dict[Any, threading.Lock] = {}
        
        # Reference counting for lazy loading: {worker_source_id: set of pipeline_ids}
        self.stream_references: Dict[Any, set] = {}
        # Store URLs for streams that aren't started yet: {worker_source_id: url}
        self.pending_streams: Dict[Any, str] = {}

        self.shared_device_manager = SharedVideoDeviceManager()

        self._lock = threading.RLock()
        self._running_evt = threading.Event()  # safer than a bare bool

    # -----------------------
    # Helpers / classification
    # -----------------------
    def _is_direct_device(self, url) -> bool:
        """Check if URL represents a direct video device."""
        if isinstance(url, int):
            return True
        if isinstance(url, str):
            return url.isdigit() or url.startswith("/dev/video")
        return False

    # -----------------------
    # Public API
    # -----------------------
    def register_stream(self, worker_source_id, url):
        """Register a stream URL without starting it (lazy loading)."""
        with self._lock:
            if worker_source_id not in self.pending_streams:
                self.pending_streams[worker_source_id] = url
                logging.debug(f"📝 Registered stream {worker_source_id} for lazy loading")
    
    def unregister_stream(self, worker_source_id):
        """Unregister a stream that's no longer available in the database."""
        with self._lock:
            # If it's pending, remove it
            if worker_source_id in self.pending_streams:
                del self.pending_streams[worker_source_id]
                logging.debug(f"🗑️ Unregistered pending stream {worker_source_id}")
            
            # If it's active and has no references, remove it
            if worker_source_id in self.stream_references:
                if len(self.stream_references[worker_source_id]) == 0:
                    self._stop_stream(worker_source_id)
    
    def acquire_stream(self, worker_source_id, pipeline_id):
        """Request access to a stream for a pipeline. Starts the stream if not already running."""
        with self._lock:
            # Initialize reference set if needed
            if worker_source_id not in self.stream_references:
                self.stream_references[worker_source_id] = set()
            
            # Add pipeline reference
            self.stream_references[worker_source_id].add(pipeline_id)
            logging.info(f"🔗 Pipeline {pipeline_id} acquired stream {worker_source_id} (refs: {len(self.stream_references[worker_source_id])})")
            
            # If stream is already running, we're done
            if worker_source_id in self.streams or worker_source_id in self.direct_device_streams:
                return True
            
            # Get URL from pending streams
            url = self.pending_streams.get(worker_source_id)
            if not url:
                logging.error(f"❌ Cannot acquire stream {worker_source_id}: URL not registered")
                return False
        
        # Start the stream (outside lock to avoid blocking)
        return self._start_stream(worker_source_id, url)
    
    def release_stream(self, worker_source_id, pipeline_id):
        """Release a stream reference from a pipeline. Stops the stream if no more references."""
        with self._lock:
            if worker_source_id not in self.stream_references:
                return
            
            # Remove pipeline reference
            self.stream_references[worker_source_id].discard(pipeline_id)
            ref_count = len(self.stream_references[worker_source_id])
            logging.info(f"🔓 Pipeline {pipeline_id} released stream {worker_source_id} (refs: {ref_count})")
            
            # If no more references, stop the stream
            if ref_count == 0:
                logging.info(f"💤 Stream {worker_source_id} has no more references, stopping...")
                self._stop_stream(worker_source_id)
    
    def _start_stream(self, worker_source_id, url):
        """Internal method to actually start a stream."""
        if self._is_direct_device(url):
            self._add_direct_device_stream(worker_source_id, url)
            return True

        # Regular stream
        stream = VideoStream(url)
        try:
            stream.start()  # start thread
            with self._lock:
                self.streams[worker_source_id] = stream
            logging.info("✅ Started video stream: %s", worker_source_id)
            return True
        except Exception as e:
            logging.error("❌ Failed to start regular stream %s: %s", worker_source_id, e)
            return False
    
    def _stop_stream(self, worker_source_id):
        """Internal method to stop a stream."""
        # Direct device?
        with self._lock:
            is_direct = worker_source_id in self.direct_device_streams
            # Clean up references
            self.stream_references.pop(worker_source_id, None)

        if is_direct:
            self._remove_direct_device_stream(worker_source_id)
            return

        # Regular stream
        with self._lock:
            stream = self.streams.pop(worker_source_id, None)

        if stream is None:
            return

        logging.info("🛑 Stopping video stream: %s", worker_source_id)
        try:
            stream.stop()
        except Exception as e:
            logging.error("❌ Error stopping stream %s: %s", worker_source_id, e)
        finally:
            stream = None

    def start_all(self):
        """Starts all regular streams that are not alive. (Direct devices are publisher-driven.)"""
        logging.info("🔄 Starting all video streams...")
        with self._lock:
            for stream in self.streams.values():
                if not stream.is_alive():
                    try:
                        stream.start()
                    except Exception as e:
                        logging.error("❌ Failed to start a stream: %s", e)
        self._running_evt.set()

    def stop_all(self):
        """Stops all streams (regular + direct devices)."""
        logging.info("🛑 Stopping all video streams...")

        # Snapshot IDs to avoid dict-size-change races
        with self._lock:
            regular_ids = list(self.streams.keys())
            direct_ids = list(self.direct_device_streams.keys())

        for wid in regular_ids:
            try:
                self._stop_stream(wid)
            except Exception as e:
                logging.error("Error stopping regular stream %s: %s", wid, e)

        for wid in direct_ids:
            try:
                self._stop_stream(wid)
            except Exception as e:
                logging.error("Error stopping direct device stream %s: %s", wid, e)

        self._running_evt.clear()

    def wait_for_stream_ready(self, worker_source_id, timeout: float = 10.0) -> bool:
        """Waits for a specific stream to signal that it has received its first frame."""
        with self._lock:
            stream = self.streams.get(worker_source_id)

        if stream and hasattr(stream, 'wait_first_frame'):
            return stream.wait_first_frame(timeout)

        return False

    def get_frame(self, worker_source_id):
        """Returns the latest frame for the stream, or None if not available."""
        with self._lock:
            if worker_source_id in self.direct_device_streams:
                stream = None
            else:
                stream = self.streams.get(worker_source_id)

        if worker_source_id in self.direct_device_streams:
            return self._get_direct_device_frame(worker_source_id)

        if stream is None or not hasattr(stream, 'running') or not stream.running:
            return None

        try:
            if hasattr(stream, 'is_file') and stream.is_file and hasattr(stream, 'is_video_ended') and stream.is_video_ended():
                logging.debug("Video file %s ended; waiting for producer to restart.", worker_source_id)
                return None

            return stream.get_frame()
        except Exception as e:
            logging.error("Error getting frame from stream %s: %s", worker_source_id, e)
            return None

    def get_active_stream_ids(self):
        """Returns a snapshot of active stream IDs (regular + direct)."""
        with self._lock:
            return list(self.streams.keys()) + list(self.direct_device_streams.keys())

    def get_stream_url(self, worker_source_id) -> Optional[str]:
        """Returns the URL/source of a specific stream."""
        with self._lock:
            if worker_source_id in self.direct_device_streams:
                return self.direct_device_streams[worker_source_id]["url"]
            s = self.streams.get(worker_source_id)
            return s.source if s else None

    def has_stream(self, worker_source_id) -> bool:
        """Checks if a stream is active."""
        with self._lock:
            return (worker_source_id in self.streams) or (worker_source_id in self.direct_device_streams)

    def is_running(self) -> bool:
        """Checks if manager is 'running'."""
        return self._running_evt.is_set()

    def is_video_file(self, worker_source_id) -> bool:
        """True if a stream is a file. Direct devices are never files."""
        with self._lock:
            if worker_source_id in self.direct_device_streams:
                return False
            s = self.streams.get(worker_source_id)
            return bool(getattr(s, "is_file", False)) if s else False

    def get_device_sharing_info(self):
        """Returns info from the shared device manager."""
        return self.shared_device_manager.get_all_devices_info()

    def shutdown(self):
        """Cleanly stop all and leave the shared manager to auto-clean."""
        logging.info("Shutting down VideoStreamManager")
        self.stop_all()

    # -----------------------
    # Direct device management
    # -----------------------
    def _add_direct_device_stream(self, worker_source_id, url):
        """Subscribe to a shared device and store frames safely, handling removal races."""
        lock = threading.Lock()

        with self._lock:
            # Initialize storage
            self.direct_device_locks[worker_source_id] = lock
            self.direct_device_streams[worker_source_id] = {
                "url": url,
                "latest_frame": None,
                "last_update": 0.0,
                "alive": True,  # tombstone flag
            }

        # Callback uses captured lock and checks the alive flag to avoid races
        def frame_callback(frame):
            # Use the per-worker lock we captured (not via dict lookup)
            with lock:
                with self._lock:
                    info = self.direct_device_streams.get(worker_source_id)
                    if not info or not info.get("alive", False):
                        return  # dropped subscriber; ignore late frames
                    info["latest_frame"] = frame
                    info["last_update"] = time.time()

        try:
            success = self.shared_device_manager.subscribe_to_device(
                source=url,
                subscriber_id=f"stream_{worker_source_id}",
                callback=frame_callback,
            )
            if success:
                logging.info("✅ Added direct device stream: %s -> %s", worker_source_id, url)
            else:
                logging.error("❌ Failed to add direct device stream: %s", worker_source_id)
                # rollback
                with self._lock:
                    self.direct_device_streams.pop(worker_source_id, None)
                    self.direct_device_locks.pop(worker_source_id, None)
        except Exception as e:
            logging.error("❌ Error adding direct device stream %s: %s", worker_source_id, e)
            with self._lock:
                self.direct_device_streams.pop(worker_source_id, None)
                self.direct_device_locks.pop(worker_source_id, None)

    def _remove_direct_device_stream(self, worker_source_id):
        """Unsubscribe and safely tear down direct device stream, tolerating late callbacks."""
        # Mark as dead first so any in-flight callbacks become no-ops
        with self._lock:
            info = self.direct_device_streams.get(worker_source_id)
            if not info:
                logging.warning("⚠️ Direct device stream %s not found.", worker_source_id)
                return
            info["alive"] = False
            url = info["url"]

        try:
            success = self.shared_device_manager.unsubscribe_from_device(
                source=url,
                subscriber_id=f"stream_{worker_source_id}",
            )
            if success:
                logging.info("✅ Removed direct device stream: %s", worker_source_id)
            else:
                logging.warning("⚠️ Unsubscribe reported failure for direct device stream: %s", worker_source_id)
        except Exception as e:
            logging.error("❌ Error unsubscribing direct device stream %s: %s", worker_source_id, e)

        # Now it is safe to drop references
        with self._lock:
            self.direct_device_streams.pop(worker_source_id, None)
            self.direct_device_locks.pop(worker_source_id, None)

    def _get_direct_device_frame(self, worker_source_id):
        """Return last frame from a direct device if fresh, else None."""
        with self._lock:
            lock = self.direct_device_locks.get(worker_source_id)

        if lock is None:
            return None

        # Serialize per-stream frame access
        with lock:
            with self._lock:
                info = self.direct_device_streams.get(worker_source_id)
                if not info:
                    return None
                frame = info.get("latest_frame")
                last_update = info.get("last_update", 0.0)

            # Outside manager lock: only local refs used now
            if (time.time() - last_update) > 5.0:
                return None
            return frame.copy() if frame is not None else None