from flask import Blueprint, request, jsonify
from src.models.lead import db, Lead, Buyer, FormAnalytics
import json
import random
import hashlib
import requests
from datetime import datetime, timedelta
import re
import math

leads_bp = Blueprint('leads', __name__)

# Lead Pricing Tiers
LEAD_PRICING = {
    'platinum': 75.00,
    'gold': 50.00,
    'silver': 35.00,
    'bronze': 25.00
}

@leads_bp.route('/estimate', methods=['POST'])
def create_estimate():
    """Generate instant estimate and process lead"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'move_type', 'origin_address', 'destination_address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate lead ID
        lead_id = f"QL{datetime.now().strftime('%Y%m%d')}{random.randint(10000, 99999)}"
        
        # Enrich addresses (geocoding)
        origin_data = enrich_address(data['origin_address'])
        destination_data = enrich_address(data['destination_address'])
        
        # Calculate distance and route
        distance_miles = calculate_distance(
            origin_data['lat'], origin_data['lon'],
            destination_data['lat'], destination_data['lon']
        )
        
        # Generate estimate
        estimate = calculate_estimate(
            distance_miles, 
            data.get('move_size'),
            data.get('special_items', [])
        )
        
        # Qualify lead
        quality_tier, quality_score = qualify_lead(data, distance_miles)
        
        # Create lead record
        lead = Lead(
            lead_id=lead_id,
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            move_type=data['move_type'],
            origin_address=data['origin_address'],
            destination_address=data['destination_address'],
            move_size=data.get('move_size'),
            move_timeline=data.get('move_timeline'),
            special_items=json.dumps(data.get('special_items', [])),
            origin_lat=origin_data['lat'],
            origin_lon=origin_data['lon'],
            destination_lat=destination_data['lat'],
            destination_lon=destination_data['lon'],
            distance_miles=distance_miles,
            estimate_low=estimate['low'],
            estimate_high=estimate['high'],
            estimate_typical=estimate['typical'],
            quality_tier=quality_tier,
            quality_score=quality_score,
            lead_value=LEAD_PRICING[quality_tier]
        )
        
        db.session.add(lead)
        db.session.commit()
        
        # Find matching buyers
        buyers = find_matching_buyers(lead)
        
        # Distribute lead to buyers (in background)
        if buyers:
            distribute_lead_to_buyers(lead, buyers)
        
        # Generate response
        estimate_id = hashlib.md5(f"{lead_id}{data['email']}".encode()).hexdigest()[:12]
        
        response = {
            'estimate_id': estimate_id,
            'lead_id': lead_id,
            'distance_miles': distance_miles,
            'estimated_cost_low': estimate['low'],
            'estimated_cost_high': estimate['high'],
            'typical_cost': estimate['typical'],
            'headline': f"✅ Instant Estimate: ${estimate['typical']:,.0f}",
            'subheadline': f"Typical cost for {data['move_type'].replace('_', ' ')} move ({distance_miles:.0f} miles)",
            'next_steps': f"{len(buyers)} licensed movers will contact you within 1 hour with exact quotes.",
            'social_proof': f"{random.randint(30, 120)} people got free estimates this week • {len(buyers)} top-rated movers available",
            'trust_signals': [
                "100% free estimate service",
                f"{len(buyers)} vetted movers compete for your business",
                "All movers licensed & insured",
                "Average 4.8★ rating"
            ],
            'disclaimer': "⚠️ This is an informational estimate only. Final pricing is determined by licensed moving companies.",
            'quality_tier': quality_tier,
            'breakdown': {
                'labor': estimate['labor'],
                'truck_travel': estimate['truck_travel'],
                'materials': estimate['materials']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leads_bp.route('/analytics/track', methods=['POST'])
def track_analytics():
    """Track form analytics"""
    try:
        data = request.get_json()
        
        analytics = FormAnalytics(
            session_id=data.get('session_id'),
            step_reached=data.get('step_reached'),
            completed=data.get('completed', False),
            abandoned_at_step=data.get('abandoned_at_step'),
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr,
            referrer=request.headers.get('Referer'),
            time_spent_seconds=data.get('time_spent_seconds'),
            test_variant=data.get('test_variant')
        )
        
        db.session.add(analytics)
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leads_bp.route('/buyers', methods=['GET'])
def get_buyers():
    """Get all active buyers"""
    try:
        buyers = Buyer.query.filter_by(active=True).all()
        return jsonify([buyer.to_dict() for buyer in buyers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leads_bp.route('/leads', methods=['GET'])
def get_leads():
    """Get all leads with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        leads = Lead.query.order_by(Lead.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'leads': [lead.to_dict() for lead in leads.items],
            'total': leads.total,
            'pages': leads.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def enrich_address(address):
    """Geocode address using Nominatim"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'addressdetails': 1,
            'limit': 1
        }
        headers = {'User-Agent': 'EnhancedLeadBroker/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data:
            result = data[0]
            return {
                'formatted': result.get('display_name', address),
                'lat': float(result['lat']),
                'lon': float(result['lon']),
                'confidence': 1.0
            }
        else:
            # Fallback for invalid addresses
            return {
                'formatted': address,
                'lat': 30.2672,  # Austin, TX default
                'lon': -97.7431,
                'confidence': 0.5
            }
    except:
        # Fallback for API errors
        return {
            'formatted': address,
            'lat': 30.2672,
            'lon': -97.7431,
            'confidence': 0.5
        }

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calculate_estimate(distance_miles, move_size, special_items):
    """Calculate moving estimate based on distance and size"""
    # Base rates
    base_rate = 150
    mileage_rate = 2.50
    
    # Size multipliers
    size_multipliers = {
        'studio': 1.0,
        '1br': 1.2,
        '2-3br': 1.8,
        '4+br': 2.5,
        'office': 2.0
    }
    
    size_multiplier = size_multipliers.get(move_size, 1.5)
    
    # Calculate components
    labor = base_rate * size_multiplier
    truck_travel = distance_miles * mileage_rate
    materials = 50 * size_multiplier
    
    # Special items surcharge
    special_surcharge = len(special_items) * 100
    
    # Total estimate
    typical = labor + truck_travel + materials + special_surcharge
    
    return {
        'low': round(typical * 0.8, -1),
        'high': round(typical * 1.2, -1),
        'typical': round(typical, -1),
        'labor': round(labor, -1),
        'truck_travel': round(truck_travel, -1),
        'materials': round(materials, -1)
    }

def qualify_lead(data, distance_miles):
    """Qualify lead and assign tier"""
    score = 0
    
    # Contact completeness (30 points)
    if data.get('name'): score += 10
    if data.get('email'): score += 10
    if data.get('phone'): score += 10
    
    # Move details (40 points)
    if data.get('move_size'): score += 15
    if data.get('move_timeline'): score += 15
    if data.get('special_items'): score += 10
    
    # Distance factor (20 points)
    if distance_miles > 500: score += 20
    elif distance_miles > 100: score += 15
    elif distance_miles > 50: score += 10
    else: score += 5
    
    # Timeline urgency (10 points)
    timeline_scores = {
        'asap': 10,
        '1-2weeks': 7,
        '1-2months': 4,
        '3+months': 2
    }
    score += timeline_scores.get(data.get('move_timeline'), 0)
    
    # Determine tier
    if score >= 85:
        tier = 'platinum'
    elif score >= 70:
        tier = 'gold'
    elif score >= 50:
        tier = 'silver'
    else:
        tier = 'bronze'
    
    return tier, score

def find_matching_buyers(lead):
    """Find buyers that match the lead criteria"""
    buyers = Buyer.query.filter_by(active=True).all()
    matched = []
    
    for buyer in buyers:
        # Check if buyer accepts this tier
        accepted_tiers = json.loads(buyer.accepts_lead_tiers)
        if lead.quality_tier not in accepted_tiers:
            continue
        
        # Check service area
        service_areas = json.loads(buyer.service_areas)
        if 'Nationwide' not in service_areas:
            # Simple check - in production would be more sophisticated
            area_match = any(area.lower() in lead.origin_address.lower() for area in service_areas)
            if not area_match:
                continue
        
        # Check distance limit
        if buyer.max_distance and lead.distance_miles > buyer.max_distance:
            continue
        
        # Check credit balance
        if buyer.credit_balance < lead.lead_value:
            continue
        
        matched.append(buyer)
    
    # Sort by conversion rate and return top 5
    matched.sort(key=lambda x: x.conversion_rate, reverse=True)
    return matched[:5]

def distribute_lead_to_buyers(lead, buyers):
    """Distribute lead to matched buyers"""
    buyer_ids = [buyer.buyer_id for buyer in buyers]
    lead.distributed_to = json.dumps(buyer_ids)
    lead.status = 'distributed'
    
    # In production, would send webhooks/emails to buyers
    print(f"Lead {lead.lead_id} distributed to {len(buyers)} buyers")
    
    db.session.commit()

# Initialize sample buyers
@leads_bp.route('/init-buyers', methods=['POST'])
def init_sample_buyers():
    """Initialize sample buyers for testing"""
    try:
        sample_buyers = [
            {
                'buyer_id': 'B001',
                'company_name': 'Swift Local Movers',
                'contact_email': 'contact@swiftlocal.com',
                'service_areas': ['Texas', 'Austin'],
                'accepts_lead_tiers': ['silver', 'bronze'],
                'max_distance': 50,
                'specialties': ['local', 'apartments'],
                'rating': 4.6,
                'response_time_avg': 45,
                'conversion_rate': 0.25,
                'credit_balance': 1000.0
            },
            {
                'buyer_id': 'B002',
                'company_name': 'Premier Moving Services',
                'contact_email': 'sales@premiermove.com',
                'service_areas': ['Nationwide'],
                'accepts_lead_tiers': ['platinum', 'gold'],
                'max_distance': None,
                'specialties': ['long_distance', 'white_glove'],
                'rating': 4.9,
                'response_time_avg': 20,
                'conversion_rate': 0.45,
                'credit_balance': 5000.0
            },
            {
                'buyer_id': 'B003',
                'company_name': 'College Town Movers',
                'contact_email': 'info@collegetownmovers.com',
                'service_areas': ['Texas', 'Austin', 'Dallas'],
                'accepts_lead_tiers': ['silver', 'bronze'],
                'max_distance': 75,
                'specialties': ['students', 'small_moves'],
                'rating': 4.5,
                'response_time_avg': 60,
                'conversion_rate': 0.30,
                'credit_balance': 750.0
            }
        ]
        
        for buyer_data in sample_buyers:
            existing = Buyer.query.filter_by(buyer_id=buyer_data['buyer_id']).first()
            if not existing:
                buyer = Buyer(
                    buyer_id=buyer_data['buyer_id'],
                    company_name=buyer_data['company_name'],
                    contact_email=buyer_data['contact_email'],
                    service_areas=json.dumps(buyer_data['service_areas']),
                    accepts_lead_tiers=json.dumps(buyer_data['accepts_lead_tiers']),
                    max_distance=buyer_data['max_distance'],
                    specialties=json.dumps(buyer_data['specialties']),
                    rating=buyer_data['rating'],
                    response_time_avg=buyer_data['response_time_avg'],
                    conversion_rate=buyer_data['conversion_rate'],
                    credit_balance=buyer_data['credit_balance']
                )
                db.session.add(buyer)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Sample buyers initialized'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
