from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from io import BytesIO
import csv
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize database
db = SQLAlchemy(app)

# ===== DATABASE MODELS =====

class Student(db.Model):
    """Student model"""
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'roll_no': self.roll_no,
            'name': self.name,
            'class_name': self.class_name,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }


class Attendance(db.Model):
    """Attendance model"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    check_in_time = db.Column(db.Time)
    remarks = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'roll_no': self.student.roll_no,
            'class_name': self.student.class_name,
            'date': self.date.isoformat(),
            'status': self.status,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# ===== ROUTES =====

@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')


@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    try:
        students = Student.query.all()
        return jsonify({
            'success': True,
            'data': [student.to_dict() for student in students],
            'count': len(students)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students', methods=['POST'])
def add_student():
    """Add a new student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('roll_no') or not data.get('name') or not data.get('class_name'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: roll_no, name, class_name'
            }), 400

        # Check if student already exists
        existing_student = Student.query.filter_by(roll_no=data['roll_no']).first()
        if existing_student:
            return jsonify({
                'success': False,
                'error': f'Student with roll number {data["roll_no"]} already exists'
            }), 409

        # Create new student
        student = Student(
            roll_no=data['roll_no'],
            name=data['name'],
            class_name=data['class_name'],
            email=data.get('email'),
            phone=data.get('phone')
        )
        
        db.session.add(student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student added successfully',
            'data': student.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get a specific student"""
    try:
        student = Student.query.get_or_404(student_id)
        return jsonify({
            'success': True,
            'data': student.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update student information"""
    try:
        student = Student.query.get_or_404(student_id)
        data = request.get_json()

        student.name = data.get('name', student.name)
        student.class_name = data.get('class_name', student.class_name)
        student.email = data.get('email', student.email)
        student.phone = data.get('phone', student.phone)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student updated successfully',
            'data': student.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance for a student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('student_id') or not data.get('status'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: student_id, status'
            }), 400

        # Validate status
        valid_statuses = ['present', 'absent', 'late']
        if data['status'] not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400

        # Check if student exists
        student = Student.query.get_or_404(data['student_id'])

        # Check if attendance already marked for today
        today = datetime.utcnow().date()
        existing = Attendance.query.filter_by(
            student_id=data['student_id'],
            date=today
        ).first()

        if existing:
            # Update existing attendance
            existing.status = data['status']
            existing.check_in_time = datetime.strptime(data.get('check_in_time', datetime.utcnow().strftime('%H:%M')), '%H:%M').time() if data.get('check_in_time') else datetime.utcnow().time()
            existing.remarks = data.get('remarks')
            existing.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Attendance updated successfully',
                'data': existing.to_dict()
            }), 200
        else:
            # Create new attendance record
            attendance = Attendance(
                student_id=data['student_id'],
                status=data['status'],
                check_in_time=datetime.strptime(data.get('check_in_time', datetime.utcnow().strftime('%H:%M')), '%H:%M').time() if data.get('check_in_time') else datetime.utcnow().time(),
                remarks=data.get('remarks'),
                date=today
            )
            
            db.session.add(attendance)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Attendance marked successfully',
                'data': attendance.to_dict()
            }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    """Delete an attendance record"""
    try:
        attendance = Attendance.query.get_or_404(attendance_id)
        db.session.delete(attendance)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Attendance record deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/attendance/date/<date_str>', methods=['GET'])
def get_attendance_by_date(date_str):
    """Get attendance records for a specific date"""
    try:
        # Parse date string
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        attendance_records = Attendance.query.filter_by(date=date_obj).all()
        
        return jsonify({
            'success': True,
            'date': date_str,
            'data': [record.to_dict() for record in attendance_records],
            'count': len(attendance_records)
        }), 200

    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/attendance/student/<int:student_id>', methods=['GET'])
def get_student_attendance(student_id):
    """Get attendance records for a specific student"""
    try:
        # Check if student exists
        student = Student.query.get_or_404(student_id)
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        attendance_records = Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).order_by(Attendance.date.desc()).all()
        
        # Calculate statistics
        total_days = len(attendance_records)
        present_days = len([r for r in attendance_records if r.status == 'present'])
        absent_days = len([r for r in attendance_records if r.status == 'absent'])
        late_days = len([r for r in attendance_records if r.status == 'late'])
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        return jsonify({
            'success': True,
            'student': student.to_dict(),
            'period_days': days,
            'statistics': {
                'total_days': total_days,
                'present': present_days,
                'absent': absent_days,
                'late': late_days,
                'attendance_percentage': round(percentage, 2)
            },
            'records': [record.to_dict() for record in attendance_records],
            'count': len(attendance_records)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get overall attendance statistics"""
    try:
        today = datetime.utcnow().date()
        
        # Total students
        total_students = Student.query.count()
        
        # Today's attendance
        today_attendance = Attendance.query.filter_by(date=today).all()
        present_today = len([r for r in today_attendance if r.status == 'present'])
        absent_today = len([r for r in today_attendance if r.status == 'absent'])
        late_today = len([r for r in today_attendance if r.status == 'late'])
        not_marked = total_students - len(today_attendance)
        
        # Calculate percentage
        if total_students > 0:
            attendance_rate = (present_today / total_students * 100)
        else:
            attendance_rate = 0
        
        return jsonify({
            'success': True,
            'date': today.isoformat(),
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'late_today': late_today,
            'not_marked': not_marked,
            'attendance_rate': round(attendance_rate, 2)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/attendance/export/csv', methods=['GET'])
def export_attendance_csv():
    """Export attendance records to CSV"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        class_filter = request.args.get('class')
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Query attendance records
        query = Attendance.query.filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
        
        if class_filter:
            query = query.join(Student).filter(Student.class_name == class_filter)
        
        attendance_records = query.order_by(Attendance.date.desc()).all()
        
        # Create CSV file
        output = BytesIO()
        writer = csv.writer(output.TextIOWrapper(output, encoding='utf-8'))
        
        # Write header
        writer.writerow(['Roll No.', 'Student Name', 'Class', 'Date', 'Status', 'Check-in Time', 'Remarks'])
        
        # Write data
        for record in attendance_records:
            writer.writerow([
                record.student.roll_no,
                record.student.name,
                record.student.class_name,
                record.date.isoformat(),
                record.status,
                record.check_in_time.isoformat() if record.check_in_time else '-',
                record.remarks or '-'
            ])
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'attendance_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search', methods=['GET'])
def search():
    """Search students by name or roll number"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Search by name or roll number
        students = Student.query.filter(
            (Student.name.ilike(f'%{query}%')) |
            (Student.roll_no.ilike(f'%{query}%'))
        ).all()
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [student.to_dict() for student in students],
            'count': len(students)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/filter', methods=['GET'])
def filter_attendance():
    """Filter attendance records"""
    try:
        class_filter = request.args.get('class')
        status_filter = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Base query
        query = Attendance.query
        
        # Apply filters
        if class_filter:
            query = query.join(Student).filter(Student.class_name == class_filter)
        
        if status_filter:
            query = query.filter(Attendance.status == status_filter)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= date_to_obj)
        
        records = query.order_by(Attendance.date.desc()).all()
        
        return jsonify({
            'success': True,
            'filters': {
                'class': class_filter,
                'status': status_filter,
                'date_from': date_from,
                'date_to': date_to
            },
            'results': [record.to_dict() for record in records],
            'count': len(records)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ===== MAIN =====

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

