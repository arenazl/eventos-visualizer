from sqlalchemy import Column, String, Text, DateTime, Boolean, DECIMAL, Integer, JSON, ForeignKey, Float
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database.connection import Base

class UserPreferences(Base):
    """Preferencias detalladas del usuario para el algoritmo de IA"""
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Preferencias de categorías con pesos
    category_weights = Column(SQLiteJSON, default={
        "musica": 0.5,
        "deportes": 0.5,
        "cultural": 0.5,
        "tech": 0.5,
        "fiestas": 0.5,
        "hobbies": 0.5,
        "internacional": 0.5
    })
    
    # Preferencias de ubicación
    preferred_neighborhoods = Column(SQLiteJSON, default=[])
    location_flexibility = Column(Float, default=0.5)  # 0-1, qué tan flexible es con ubicaciones
    
    # Preferencias temporales
    preferred_days = Column(SQLiteJSON, default=[])  # días de la semana preferidos
    preferred_times = Column(SQLiteJSON, default={
        "morning": 0.3,    # 6-12
        "afternoon": 0.5,  # 12-18
        "evening": 0.8,    # 18-22
        "night": 0.4       # 22-6
    })
    
    # Preferencias de precio
    price_sensitivity = Column(Float, default=0.5)  # 0-1, 0 = no le importa el precio
    max_preferred_price = Column(DECIMAL(10, 2))
    prefers_free_events = Column(Boolean, default=True)
    
    # Preferencias sociales
    group_size_preference = Column(String(20), default="any")  # "solo", "small", "large", "any"
    social_events_weight = Column(Float, default=0.5)
    
    # Historial de interacciones para machine learning
    interaction_history = Column(SQLiteJSON, default={
        "viewed_events": [],
        "clicked_events": [],
        "saved_events": [],
        "shared_events": [],
        "searched_terms": [],
        "rejected_suggestions": []
    })
    
    # Métricas del algoritmo
    match_score_history = Column(SQLiteJSON, default=[])  # Historial de scores de match
    feedback_score = Column(Float, default=0.5)  # Score basado en feedback del usuario
    learning_iterations = Column(Integer, default=0)
    
    # Preferencias de comunicación con IA
    communication_style = Column(String(20), default="friendly")  # "formal", "friendly", "casual"
    prefers_suggestions = Column(Boolean, default=True)
    max_suggestions_per_query = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime)
    
    # Relationship
    user = relationship("User", backref="preferences")

class UserInteraction(Base):
    """Registro de cada interacción del usuario para aprendizaje"""
    __tablename__ = "user_interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=True)
    
    # Tipo de interacción
    interaction_type = Column(String(50), nullable=False)  # 'view', 'click', 'save', 'share', 'search', 'ai_chat'
    
    # Contexto de la interacción
    context = Column(SQLiteJSON, default={})  # Query, ubicación, hora, etc.
    
    # Datos de la interacción
    interaction_data = Column(SQLiteJSON, default={})  # Detalles específicos
    
    # Para interacciones con IA
    ai_query = Column(Text)  # Lo que preguntó el usuario
    ai_response = Column(Text)  # Lo que respondió la IA
    user_feedback = Column(String(20))  # 'helpful', 'not_helpful', 'partially'
    
    # Métricas
    duration_seconds = Column(Integer)  # Cuánto tiempo interactuó
    success_indicator = Column(Boolean)  # Si la interacción fue exitosa
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    event = relationship("Event")

class PreferenceUpdate(Base):
    """Log de actualizaciones de preferencias para auditoría"""
    __tablename__ = "preference_updates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Cambio realizado
    field_changed = Column(String(100), nullable=False)
    old_value = Column(SQLiteJSON)
    new_value = Column(SQLiteJSON)
    
    # Razón del cambio
    update_reason = Column(String(100))  # 'user_feedback', 'ai_learning', 'manual_adjustment'
    confidence_score = Column(Float)  # Qué tan confiado está el algoritmo
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User")