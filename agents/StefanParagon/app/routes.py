import hashlib
import io
import json
import os
import shutil
import time
from datetime import datetime

import pandas as pd
from flask import render_template, url_for, redirect, current_app as app, render_template_string
from flask import request, send_file
from werkzeug.utils import secure_filename

from .models.llm import analyze_receipt_dummy, Receipt, analyze_receipt
from .models.database import get_db_connection, save_receipt_to_db

# Define folders for uploaded files, JSON data, and temporary files
UPLOAD_FOLDER = 'app/static/data/uploads'
JSON_FOLDER = 'app/static/data/json'
TEMP_FOLDER = 'app/static/temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(JSON_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)


def generate_file_hash(file):
    """
    Generates a hash based on the content of a file.

    Args:
        file (FileStorage): The file object to generate the hash from.

    Returns:
        str: The SHA256 hash of the file content.
    """
    file.seek(0)  # Reset file pointer to the beginning
    file_hash = hashlib.sha256()
    for chunk in iter(lambda: file.read(4096), b""):  # Read the file in chunks of 4 KB
        file_hash.update(chunk)
    file.seek(0)  # Reset the pointer again after reading
    return file_hash.hexdigest()


def cleanup_temp_folder(expiration_time=3600):
    """
    Cleans up files older than `expiration_time` seconds from the temp folder.

    Args:
        expiration_time (int): Time in seconds; files older than this will be deleted.
    """
    now = time.time()
    for filename in os.listdir(TEMP_FOLDER):
        file_path = os.path.join(TEMP_FOLDER, filename)
        if os.path.isfile(file_path):
            # Check if the file is older than `expiration_time`
            if now - os.path.getmtime(file_path) > expiration_time:
                os.remove(file_path)
                print(f"Deleted old temporary file: {file_path}")


@app.route('/')
def home():
    """
    Redirects the user to the scan page.

    Returns:
        Redirect: A redirect to the scan route.
    """
    return redirect(url_for('scan'))


@app.route('/scan', methods=['GET', 'POST'])
def scan():
    """
    Handles file uploads and receipt analysis.

    Returns:
        str: Rendered HTML template for the scan page.
    """
    image_url = None
    analysis_result = None
    temp_file = None

    # Retrieve POST form data
    message = request.form.get('message')
    is_success = request.form.get('is_success')

    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename:
            # Clean up old files in the temp folder
            cleanup_temp_folder()

            # Handle file upload
            file = request.files['file']
            filename = secure_filename(file.filename)
            extension = filename.split('.')[-1].lower()

            # Generate a hash and unique filename for the file
            file_hash = generate_file_hash(file)
            unique_filename = f"{file_hash}.{extension}"
            file_path = os.path.join(TEMP_FOLDER, unique_filename)

            # Save the uploaded file to the temp folder
            file.seek(0)
            with open(file_path, 'wb') as f:
                f.write(file.read())

            # Set the image URL for rendering
            image_url = f"/static/temp/{unique_filename}"
            temp_file = unique_filename
        elif request.form.get('analyze', 'false') == 'true':
            # Handle receipt analysis
            temp_file = request.form.get('temp_file')
            if temp_file:
                image_url = f"/static/temp/{temp_file}"

            # Simulated analysis result (mock data)
            analysis_result = analyze_receipt(os.path.join(TEMP_FOLDER, temp_file)).model_dump_json()
    else:
        cleanup_temp_folder(0)

    # Render the scan page template with data
    return render_template(
        'scan.html',
        image_url=image_url,
        analysis_result=analysis_result if analysis_result else None,
        temp_file=temp_file,
        message=message,
        is_success=is_success
    )


@app.route('/save', methods=['POST'])
def save():
    """
    Saves the uploaded receipt file and its analysis result.

    The function performs the following steps:
    1. Checks if the file and receipt already exist (in the upload folder or database).
    2. If valid, saves the file to the upload folder.
    3. Stores receipt data and file metadata in the database.
    4. Saves the receipt analysis result as a JSON file.

    Returns:
        str: A rendered template with a form redirecting back to the `scan` route.

    Variables:
        - is_success (bool): Indicates if the save operation was successful.
        - can_save (bool): Determines if the save operation should proceed based on validations.
        - message (str): A message describing the outcome of the save operation.
    """
    temp_file = request.form.get('temp_file')
    analysis_result = request.form.get('analysis_result')
    is_success = False
    can_save = True
    message = ""

    if temp_file and analysis_result:
        try:
            # Define file paths
            temp_path = os.path.join(TEMP_FOLDER, temp_file)
            upload_path = os.path.join(UPLOAD_FOLDER, temp_file)

            # TEST 1: Check if the file already exists in the `uploads` folder
            if os.path.exists(upload_path):
                message = f"The file already exists in the target folder. Save operation skipped."
                can_save = False

            # TEST 2: Check if the receipt already exists in the database
            receipt_data = json.loads(analysis_result)
            receipt = Receipt(**receipt_data)

            conn = get_db_connection()
            cursor = conn.cursor()
            receipt_number = receipt.receipt_number

            cursor.execute('SELECT id FROM receipts WHERE receipt_number = ?', (receipt_number,))
            existing_receipt = cursor.fetchone()
            if existing_receipt:
                message = \
                    f"Receipt with number '{receipt_number}' already exists in the database. Save operation skipped."
                can_save = False

            # If all tests pass, proceed with saving
            if can_save:
                # Copy the file from `temp` to `uploads`
                shutil.copy(temp_path, upload_path)

                # Save the receipt to the database
                receipt_id = save_receipt_to_db(receipt)

                # Save file metadata to the database
                upload_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO files (file_name, file_path, upload_timestamp, receipt_id)
                    VALUES (?, ?, ?, ?)
                ''', (temp_file, upload_path, upload_timestamp, receipt_id))
                conn.commit()

                # Save receipt data as JSON to disk
                json_filename = os.path.splitext(temp_file)[0] + '.json'
                json_path = os.path.join(JSON_FOLDER, json_filename)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(receipt_data, f, ensure_ascii=False, indent=4)

                message = "Data has been successfully saved."
                is_success = True

            # Close the database connection
            conn.close()

        except Exception as e:
            message = f"Error during save operation: {e}"
            is_success = False
    else:
        message = "No data provided for saving."

    return render_template_string('''
        <form id="redirect-form" method="POST" action="{{ url_for('scan') }}">
            <input type="hidden" name="analyze" value="false">
            <input type="hidden" name="image_url" value="{{ image_url }}">
            <input type="hidden" name="analysis_result" value="{{ analysis_result }}">
            <input type="hidden" name="message" value="{{ message }}">
            <input type="hidden" name="is_success" value="{{ is_success }}">
            <input type="hidden" name="temp_file" value="{{ temp_file }}">
        </form>
        <script>
            document.getElementById('redirect-form').submit();
        </script>
    ''', image_url=f"/static/temp/{temp_file}" if temp_file else None,
                                  analysis_result=analysis_result,
                                  message=message,
                                  is_success=is_success,
                                  temp_file=temp_file)


@app.route('/export', methods=['GET'])
def export_data():
    """
    Exports receipt data from the database to an Excel file.

    The function retrieves receipt data, including details about the store,
    purchased products, and receipt items, and generates an Excel file for download.

    Steps:
    1. Connects to the database and fetches relevant data using an SQL query.
    2. Converts the data into a pandas DataFrame for easier manipulation.
    3. Generates an Excel file in memory with the data.
    4. Sends the generated file as a downloadable attachment to the client.

    Returns:
        Response: A file download response containing the Excel file.
    """
    # Establish a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the query to fetch receipt data along with store and product details
    cursor.execute('''
        SELECT 
            receipts.id AS receipt_id,
            receipts.date AS receipt_date,
            receipts.time AS receipt_time,
            receipts.total_amount AS total_amount,
            receipts.payment_method AS payment_method,
            stores.name AS store_name,
            stores.city AS store_city,
            stores.street AS store_address,
            products.name AS product_name,
            receipt_items.quantity AS quantity,
            receipt_items.unit_price AS unit_price,
            receipt_items.total_price_with_discount AS total_price_with_discount
        FROM receipts
        JOIN stores ON receipts.store_id = stores.id
        JOIN receipt_items ON receipts.id = receipt_items.receipt_id
        JOIN products ON receipt_items.product_id = products.id
    ''')

    # Fetch query results
    data = cursor.fetchall()

    # Create a DataFrame to organize the data for exporting
    df = pd.DataFrame(data, columns=[col[0] for col in cursor.description])

    # Generate an Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Receipts')
    output.seek(0)  # Reset the pointer to the beginning of the file

    # Close the database connection
    conn.close()

    # Send the Excel file as a downloadable attachment
    return send_file(
        output,
        as_attachment=True,
        download_name='receipts.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/about')
def about():
    """
    Renders the 'About' page of the application.

    This function serves a static HTML template that provides information
    about the application, its purpose, and other relevant details.

    Returns:
        str: Rendered HTML content of the 'About' page.
    """
    return render_template('about.html')
