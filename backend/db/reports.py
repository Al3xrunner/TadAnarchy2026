from flask import Blueprint, request, jsonify
from sqlalchemy import text
from models import db

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/resolve', methods=['POST'])
def resolve_issue():
    data = request.json
    issue_id = data.get('issue_id')
    lat = data.get('latitude')
    lng = data.get('longitude')

    try:
        sql = text("""
            INSERT INTO resolved_landscape_issues 
            (issue_id, title, category, description, resolution_notes, location, created_at)
            VALUES 
            (:id, :title, :category, :desc, :notes, geography::Point(:lat, :lng, 4326), :created)
        """)
        
        db.session.execute(sql, {
            'id': issue_id,
            'title': data.get('title'),
            'category': data.get('category'),
            'desc': data.get('description'),
            'notes': data.get('resolution_notes'),
            'lat': lat,
            'lng': lng,
            'created': data.get('created_at')
        })
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Archived to SQL Server'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500