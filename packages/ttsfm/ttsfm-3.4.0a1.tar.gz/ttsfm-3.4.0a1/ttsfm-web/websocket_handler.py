"""
WebSocket handler for real-time TTS streaming.

Because apparently waiting 2 seconds for audio generation is too much for modern users.
At least this will make it FEEL faster.
"""

import base64
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from flask import request
from flask_socketio import SocketIO, emit

from ttsfm import AudioFormat, TTSClient, Voice
from ttsfm.utils import split_text_by_length

logger = logging.getLogger(__name__)


class WebSocketTTSHandler:
    """
    Handles WebSocket connections for streaming TTS generation.

    Because your users can't wait 2 seconds for a complete response.
    """

    def __init__(self, socketio: SocketIO, client_factory: Callable[[], TTSClient]):
        self.socketio = socketio
        self._client_factory = client_factory
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, Dict[str, Any]] = {}

        # Register WebSocket events
        self._register_events()

    def _register_events(self):
        """Register all WebSocket event handlers."""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle new WebSocket connection."""
            session_id = request.sid
            self.active_sessions[session_id] = {
                "connected_at": datetime.now(),
                "request_count": 0,
                "last_request": None,
            }
            self._tasks[session_id] = {}
            logger.info(f"WebSocket client connected: {session_id}")
            emit("connected", {"session_id": session_id, "status": "ready"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle WebSocket disconnection."""
            session_id = request.sid
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            self._cancel_all_tasks(session_id)
            logger.info(f"WebSocket client disconnected: {session_id}")

        @self.socketio.on("generate_stream")
        def handle_generate_stream(data):
            """
            Handle streaming TTS generation request.

            Expected data format:
            {
                'text': str,
                'voice': str,
                'format': str,
                'chunk_size': int (optional, default 1024 chars),
                'instructions': str (optional, voice modulation instructions)
            }
            """
            session_id = request.sid
            request_id = data.get("request_id", str(uuid.uuid4()))

            # Update session info
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["request_count"] += 1
                self.active_sessions[session_id]["last_request"] = datetime.now()

            # Emit acknowledgment
            emit("stream_started", {"request_id": request_id, "timestamp": time.time()})

            # Start async generation
            task = self.socketio.start_background_task(
                self._generate_stream, session_id, request_id, data
            )
            self._store_task(session_id, request_id, task)

        @self.socketio.on("cancel_stream")
        def handle_cancel_stream(data):
            """Handle stream cancellation request."""
            request_id = data.get("request_id")
            session_id = request.sid

            if not request_id:
                return

            cancelled = self._cancel_task(session_id, request_id)
            if cancelled:
                logger.info(f"Stream cancellation requested: {request_id}")
            else:
                logger.info(f"Stream cancellation requested for unknown request: {request_id}")

            emit("stream_cancelled", {"request_id": request_id, "cancelled": cancelled})

    def _generate_stream(self, session_id: str, request_id: str, data: Dict[str, Any]):
        """
        Generate TTS audio in chunks and stream to client.

        This is where the magic happens. And by magic, I mean
        chunking text and pretending it's real-time.
        """
        client = self._client_factory()

        try:
            # Extract parameters
            text = data.get("text", "")
            voice = data.get("voice", "alloy")
            format_str = data.get("format", "mp3")
            chunk_size = data.get("chunk_size", 1024)
            instructions = data.get("instructions", None)  # Voice instructions support!

            if not text:
                self._emit_error(session_id, request_id, "No text provided")
                return

            # Convert string parameters to enums
            try:
                voice_enum = Voice(voice.lower())
                format_enum = AudioFormat(format_str.lower())
            except ValueError as e:
                self._emit_error(session_id, request_id, f"Invalid parameter: {str(e)}")
                return

            # Split text into chunks for "streaming" effect
            chunks = split_text_by_length(text, chunk_size, preserve_words=True)
            total_chunks = len(chunks)

            logger.info(f"Starting stream generation: {request_id} with {total_chunks} chunks")

            # Emit initial progress
            self.socketio.emit(
                "stream_progress",
                {
                    "request_id": request_id,
                    "progress": 0,
                    "total_chunks": total_chunks,
                    "status": "processing",
                },
                room=session_id,
            )

            # Process each chunk
            for i, chunk in enumerate(chunks):
                # Check if client is still connected
                if session_id not in self.active_sessions:
                    logger.warning(f"Client disconnected during generation: {session_id}")
                    break

                if not self._is_task_active(session_id, request_id):
                    logger.info(f"Stream generation cancelled: {request_id}")
                    break

                try:
                    # Generate audio for chunk
                    start_time = time.time()
                    response = client.generate_speech(
                        text=chunk,
                        voice=voice_enum,
                        response_format=format_enum,
                        instructions=instructions,  # Pass voice instructions!
                        validate_length=False,  # We already chunked it
                    )
                    generation_time = time.time() - start_time

                    # Emit chunk data
                    encoded_audio = base64.b64encode(response.audio_data).decode("ascii")
                    chunk_data = {
                        "request_id": request_id,
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                        "audio_data": encoded_audio,
                        "encoding": "base64",
                        "byte_length": len(response.audio_data),
                        "format": response.format.value,
                        "requested_format": format_enum.value,
                        "duration": response.duration,
                        "generation_time": generation_time,
                        "chunk_text": chunk[:50] + "..." if len(chunk) > 50 else chunk,
                    }

                    self.socketio.emit("audio_chunk", chunk_data, room=session_id)

                    # Emit progress update
                    progress = int(((i + 1) / total_chunks) * 100)
                    self.socketio.emit(
                        "stream_progress",
                        {
                            "request_id": request_id,
                            "progress": progress,
                            "total_chunks": total_chunks,
                            "chunks_completed": i + 1,
                            "status": "processing",
                        },
                        room=session_id,
                    )

                    # Small delay to prevent overwhelming the client
                    # (and to make it feel more "real-time")
                    self.socketio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error generating chunk {i}: {str(e)}")
                    self._emit_error(
                        session_id, request_id, f"Chunk {i} generation failed: {str(e)}"
                    )
                    # Continue with next chunk instead of failing completely
                    continue

            # Emit completion
            self.socketio.emit(
                "stream_complete",
                {
                    "request_id": request_id,
                    "total_chunks": total_chunks,
                    "status": "completed",
                    "timestamp": time.time(),
                },
                room=session_id,
            )

            logger.info(f"Stream generation completed: {request_id}")

        except Exception as e:
            logger.error(f"Stream generation failed: {str(e)}")
            self._emit_error(session_id, request_id, str(e))
        finally:
            try:
                client.close()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                logger.debug("Failed to close TTS client cleanly: %s", exc)
            self._remove_task(session_id, request_id)

    def _emit_error(self, session_id: str, request_id: str, error_message: str):
        """Emit error to specific session."""
        self.socketio.emit(
            "stream_error",
            {"request_id": request_id, "error": error_message, "timestamp": time.time()},
            room=session_id,
        )

    def _store_task(self, session_id: str, request_id: str, task: Any) -> None:
        self._tasks.setdefault(session_id, {})[request_id] = task

    def _remove_task(self, session_id: str, request_id: str) -> None:
        tasks = self._tasks.get(session_id)
        if not tasks:
            return
        tasks.pop(request_id, None)
        if not tasks:
            self._tasks.pop(session_id, None)

    def _cancel_task(self, session_id: str, request_id: str) -> bool:
        tasks = self._tasks.get(session_id)
        if not tasks:
            return False
        task = tasks.pop(request_id, None)
        if not task:
            if not tasks:
                self._tasks.pop(session_id, None)
            return False

        self._invoke_task_cancel(task)
        if not tasks:
            self._tasks.pop(session_id, None)
        return True

    def _cancel_all_tasks(self, session_id: str) -> None:
        tasks = self._tasks.pop(session_id, {})
        for task in tasks.values():
            self._invoke_task_cancel(task)

    def _invoke_task_cancel(self, task: Any) -> None:
        try:
            cancel = getattr(task, "cancel", None)
            if callable(cancel):
                cancel()
                return

            kill = getattr(task, "kill", None)
            if callable(kill):  # pragma: no cover - eventlet specific
                kill()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("Failed to cancel background task cleanly: %s", exc)

    def _is_task_active(self, session_id: str, request_id: str) -> bool:
        tasks = self._tasks.get(session_id)
        if not tasks:
            return False
        return request_id in tasks

    def get_active_sessions_count(self) -> int:
        """Get count of active WebSocket sessions."""
        return len(self.active_sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        return self.active_sessions.get(session_id)
