from flask import Flask, request, render_template
import requests
import os
import schedule
import time
from threading import Thread
from memory_profiler import profile

app = Flask(__name__)

# Configurações da API Hugging Face
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
headers = {"Authorization": "Bearer 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"}

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para consultar a API Hugging Face
@profile
def query(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

# Função para limpar a pasta de uploads
@profile
def clear_uploads_folder():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Arquivo {filename} removido.")
        except Exception as e:
            print(f"Erro ao remover o arquivo {filename}: {e}")

# Agendamento da limpeza da pasta a cada 2 horas
def schedule_clear_uploads():
    schedule.every(2).hours.do(clear_uploads_folder)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Inicia a função de limpeza em uma nova thread
def start_scheduler():
    scheduler_thread = Thread(target=schedule_clear_uploads)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Rota para o upload e processamento do áudio
@profile
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "audio" not in request.files:
            return "Nenhum arquivo de áudio enviado", 400
        file = request.files["audio"]
        
        if file.filename == '':
            return "Nenhum arquivo selecionado", 400
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        result = query(filepath)

        transcription = result.get("text", "Erro ao transcrever o áudio")
        return render_template("result.html", transcription=transcription)

    return render_template("index.html")

# Inicializa o servidor Flask e o agendador
if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    start_scheduler()
    app.run(debug=True, host='0.0.0.0', port=4000)
