from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    doctor = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)  # Ensure this column exists

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "doctor": self.doctor,
            "time": self.time,
            "date": self.date
        }
