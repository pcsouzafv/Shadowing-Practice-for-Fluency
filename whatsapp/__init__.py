"""
WhatsApp Mini-Lesson Module
============================
Integração com Evolution API para envio de mini-aulas via WhatsApp,
estilo BeConfident — com áudio TTS, exercícios de shadowing e feedback com IA.
"""

from .evolution_client import EvolutionClient
from .student_manager import StudentManager
from .lesson_curriculum import LessonCurriculum
from .scheduler import LessonScheduler
from .handler import WhatsAppHandler

__all__ = [
    "EvolutionClient",
    "StudentManager",
    "LessonCurriculum",
    "LessonScheduler",
    "WhatsAppHandler",
]
