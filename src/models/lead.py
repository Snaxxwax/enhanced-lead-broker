from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.String(50), unique=True, nullable=False)
    
    # Contact Information
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Move Details
    move_type = db.Column(db.String(50), nullable=False)  # local, long_distance, international
    origin_address = db.Column(db.Text, nullable=False)
    destination_address = db.Column(db.Text, nullable=False)
    move_size = db.Column(db.String(50), nullable=True)  # studio, 1br, 2-3br, 4+br
    move_timeline = db.Column(db.String(50), nullable=True)  # asap, 1-2weeks, etc
    special_items = db.Column(db.Text, nullable=True)  # JSON string
    
    # Enrichment Data
    origin_lat = db.Column(db.Float, nullable=True)
    origin_lon = db.Column(db.Float, nullable=True)
    destination_lat = db.Column(db.Float, nullable=True)
    destination_lon = db.Column(db.Float, nullable=True)
    distance_miles = db.Column(db.Float, nullable=True)
    phone_verified = db.Column(db.Boolean, default=False)
    
    # Estimate Data
    estimate_low = db.Column(db.Float, nullable=True)
    estimate_high = db.Column(db.Float, nullable=True)
    estimate_typical = db.Column(db.Float, nullable=True)
    
    # Lead Quality
    quality_tier = db.Column(db.String(20), nullable=True)  # platinum, gold, silver, bronze
    quality_score = db.Column(db.Integer, nullable=True)
    lead_value = db.Column(db.Float, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Distribution
    distributed_to = db.Column(db.Text, nullable=True)  # JSON string of buyer IDs
    status = db.Column(db.String(20), default='new')  # new, distributed, contacted, converted
    
    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'move_type': self.move_type,
            'origin_address': self.origin_address,
            'destination_address': self.destination_address,
            'move_size': self.move_size,
            'move_timeline': self.move_timeline,
            'special_items': json.loads(self.special_items) if self.special_items else [],
            'distance_miles': self.distance_miles,
            'estimate_low': self.estimate_low,
            'estimate_high': self.estimate_high,
            'estimate_typical': self.estimate_typical,
            'quality_tier': self.quality_tier,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status
        }

class Buyer(db.Model):
    __tablename__ = 'buyers'
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.String(50), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    
    # Service Areas
    service_areas = db.Column(db.Text, nullable=False)  # JSON string
    max_distance = db.Column(db.Integer, nullable=True)
    specialties = db.Column(db.Text, nullable=True)  # JSON string
    
    # Lead Preferences
    accepts_lead_tiers = db.Column(db.Text, nullable=False)  # JSON string
    
    # Performance Metrics
    rating = db.Column(db.Float, default=0.0)
    response_time_avg = db.Column(db.Integer, default=60)  # minutes
    conversion_rate = db.Column(db.Float, default=0.0)
    credit_balance = db.Column(db.Float, default=0.0)
    
    # Status
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'buyer_id': self.buyer_id,
            'company_name': self.company_name,
            'contact_email': self.contact_email,
            'service_areas': json.loads(self.service_areas) if self.service_areas else [],
            'max_distance': self.max_distance,
            'specialties': json.loads(self.specialties) if self.specialties else [],
            'accepts_lead_tiers': json.loads(self.accepts_lead_tiers) if self.accepts_lead_tiers else [],
            'rating': self.rating,
            'response_time_avg': self.response_time_avg,
            'conversion_rate': self.conversion_rate,
            'active': self.active
        }

class FormAnalytics(db.Model):
    __tablename__ = 'form_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    
    # Form Progress
    step_reached = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    abandoned_at_step = db.Column(db.Integer, nullable=True)
    
    # User Info
    user_agent = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    referrer = db.Column(db.Text, nullable=True)
    
    # Timing
    time_spent_seconds = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # A/B Test Variant
    test_variant = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'step_reached': self.step_reached,
            'completed': self.completed,
            'abandoned_at_step': self.abandoned_at_step,
            'time_spent_seconds': self.time_spent_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'test_variant': self.test_variant
        }
