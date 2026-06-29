from flask import Flask, render_template, request, redirect
from database import mysql, init_db
from datetime import datetime
from dotenv import load_dotenv
import re
import os

load_dotenv()
app = Flask(__name__)

#Konfiguration der Datenbank
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT'))

# Datenbank initialisieren
init_db(app)

@app.route('/', methods=['GET'])
def index():
    #Form anzeigen
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT type_name FROM device_types")
        device_types = cursor.fetchall()
        cursor.close()
        return render_template('index.html', device_types=device_types)
    except Exception as e:
        return f"Error loading form: {str(e)}", 500

@app.route('/submit', methods=['POST'])
def submit_damage_report():
    """Formübermittlung und Validierung"""
    
    # Daten aus der Form beziehen
    employee_id = request.form.get('employee-id', '').strip()
    device_type = request.form.get('device-type', '').strip()
    damage_date = request.form.get('damage-date', '').strip()
    description = request.form.get('description', '').strip()
    urgency = request.form.get('urgency', '').strip()
    
    # Validierungsfehler sammeln
    errors = []
    
    # Mitarbeiter-ID validieren
    if not re.match(r'^\d{7}$', employee_id):
        errors.append("Mitarbeiter-ID muss genau 7 Ziffern haben")
    
    # Beschreibung
    if not description:
        errors.append("Beschreibung darf nicht leer sein")
    elif len(description) > 500:
        errors.append("Beschreibung darf max. 500 Zeichen enthalten")
    
    # Schadensdatum validieren
    try:
        damage_date_obj = datetime.strptime(damage_date, '%Y-%m-%d')
        if damage_date_obj > datetime.now():
            errors.append("Datum darf nicht in der Zukunft liegen")
        
    except ValueError:
        errors.append("Ungültiges Datum")
    
    # Dringlichkeit validieren
    allowed_urgencies = ['niedrig', 'mittel', 'hoch']
    if urgency not in allowed_urgencies:
        errors.append("Ungültige Dringlichkeit")
    
    # Gerätetyp mit existierenden in der Datenbank abgleichen
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT type_name FROM device_types")
        allowed_device_types = cursor.fetchall() # Tupelliste
        cursor.close()
        
        allowed_types_list = [d[0] for d in allowed_device_types] # Tupelliste in Stringliste umwandeln
        if device_type not in allowed_types_list:
            errors.append("Ungültiger Gerätetyp")
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
    
    # Ween Fehler aufgetreten sind, wird die Form mit Fehleranzeige(n) neu geladen
    if errors:
        return render_template('index.html', 
                             errors=errors, 
                             device_types=allowed_device_types,
                             form_data={
                                 'employee_id': employee_id,
                                 'device_type': device_type,
                                 'damage_date': damage_date,
                                 'description': description,
                                 'urgency': urgency
                             })
    
    # Wenn die daten validiert sind, werden sie in die Datenbank eingespeichert
    try:
        cursor = mysql.connection.cursor()
        sql = """INSERT INTO damages (employee_id, device_type_id, damage_date, description, urgency)
                 VALUES (%s, (SELECT id FROM device_types WHERE type_name = %s), %s, %s, %s)""" 
                 # Gerätetyp ID wird über den Namen per Subquery rausgefunden
        cursor.execute(sql, (employee_id, device_type, damage_date, description, urgency))
        mysql.connection.commit()
        cursor.close()
        
        # Success Seite anzeigen und eingegebene Daten anzeigen
        return render_template('success.html',
                             employee_id=employee_id,
                             device_type=device_type,
                             damage_date=damage_date,
                             description=description,
                             urgency=urgency)
    
    except Exception as e:
        return f"Error saving data: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
