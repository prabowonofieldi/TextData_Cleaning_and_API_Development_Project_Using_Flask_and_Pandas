# Import library for ReGex, SQLite, and Pandas
import re
import sqlite3
import pandas as pd

# Import library for Flask
from flask import Flask, jsonify
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

# Define Swagger UI description
app = Flask(__name__)
app.json_encoder = LazyJSONEncoder

swagger_template = {
    'info' : {
        'title': 'API Documentation for Data Processing and Modeling',
        'version': '1.0.0',
        'description': 'Dokumentasi API untuk Data Processing dan Modeling',
        },
    'host' : '127.0.0.1:5000'
}
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)

# buka koneksi sqlite
conn = sqlite3.connect('data/gold_challenge.db', check_same_thread=False)

# membuat table
# buat kolom text dan text_clean dengan tipe data varchar
conn.execute('''CREATE TABLE IF NOT EXISTS data (text varchar(255), text_clean varchar(255));''')

# membuat endpoint pertama text-processing
@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():

    # ambil text
    text = request.form.get('text')
    
    # proses cleansing menggunakan regex
    text_clean = text.lower()
    text_clean = re.sub(r'http\S+|www\S+|https\S+', '', text_clean)  # Hapus URL
    text_clean = re.sub(r'<.*?>', '', text_clean)  # Hapus tag HTML
    text_clean = re.sub(r'@\w+', '', text_clean)  # Hapus mention Twitter
    text_clean = re.sub(r'#\w+', '', text_clean)  # Hapus hashtag
    text_clean = re.sub(r'\d+', '', text_clean)  # Hapus angka
    text_clean = re.sub(r'[^\w\s]', '', text_clean)  # Hapus karakter khusus
    text_clean = re.sub(r'\b\w{1,2}\b', '', text_clean)  # Hapus kata dengan panjang kurang dari 2 karakter
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()  # Hapus spasi berlebihan dan spasi di awal/akhir
    
    # input hasil cleansing ke database menggunakan parameterized query untuk mencegah SQL Injection
    conn.execute("INSERT INTO data (text, text_clean) VALUES (?, ?)", (text, text_clean))
    conn.commit()

    # response akhir API berbentuk json
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': text_clean
    }
    response_data = jsonify(json_response)
    return response_data
    
    
# Buat endpoint untuk "upload file CSV"
@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():
    try:
        # upload file
        file = request.files.getlist('file')[0]

        # import file kemudian jadikan dataframe menggunakan pandas
        df = pd.read_csv(file)

        # ambil kolom teks dari file dalam format list
        texts = df['text'].tolist()

        # looping list text nya
        cleaned_text = []
        for original_text in texts:
            # proses cleansing data
            text_clean = original_text.lower()
            text_clean = re.sub(r'http\S+|www\S+|https\S+', '', text_clean)  # Hapus URL
            text_clean = re.sub(r'<.*?>', '', text_clean)  # Hapus tag HTML
            text_clean = re.sub(r'@\w+', '', text_clean)  # Hapus mention Twitter
            text_clean = re.sub(r'#\w+', '', text_clean)  # Hapus hashtag
            text_clean = re.sub(r'\d+', '', text_clean)  # Hapus angka
            text_clean = re.sub(r'[^\w\s]', '', text_clean)  # Hapus karakter khusus
            text_clean = re.sub(r'\b\w{1,2}\b', '', text_clean)  # Hapus kata dengan panjang kurang dari 2 karakter
            text_clean = re.sub(r'\s+', ' ', text_clean).strip()  # Hapus spasi berlebihan dan spasi di awal/akhir

            # input hasil cleansing ke database
            conn.execute("INSERT INTO data (text, text_clean) VALUES (?, ?)", (original_text, text_clean))
            conn.commit()

            # tambahkan list output di variable text_clean ke dalam kolom database kolom text_clean
            cleaned_text.append(text_clean)
        
        # response API berbentuk json
        json_response = {
            'status_code': 200,
            'description': "Teks yang sudah diproses",
            'data': cleaned_text,
        }
        response_data = jsonify(json_response)
        return response_data
    
    except Exception as e:
        json_response = {
            'status_code': 500,
            'description': "Terjadi kesalahan dalam memproses file",
            'error': str(e)
        }
        response_data = jsonify(json_response)
        return response_data


if __name__ == '__main__':
   app.run()