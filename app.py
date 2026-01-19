from flask import Flask, request, send_file, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from gtts import gTTS
import os
import glob
import time

app = Flask(__name__)

# Define o diretório base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILE = os.path.join(BASE_DIR, "mensagem.mp3")

# Limpa arquivos mais antigos que 1 hora
for file in glob.glob(os.path.join(BASE_DIR, "mensagem_*.mp3")):
    if os.path.getmtime(file) < time.time() - 3600:
        os.remove(file)

@app.route("/", methods=["GET"])
def home():
    return """
    <html>
        <head><title>Bot WhatsApp</title></head>
        <body>
            <h1>✅ Bot WhatsApp está funcionando!</h1>
            <p>Rotas disponíveis:</p>
            <ul>
                <li><a href="/">/</a> - Esta página</li>
                <li><a href="/test">/test</a> - Teste JSON</li>
                <li><a href="/audio">/audio</a> - Áudio de teste</li>
                <li>/whatsapp - Webhook do Twilio (POST)</li>
            </ul>
        </body>
    </html>
    """

@app.route("/test", methods=["GET"])
def test():
    return jsonify({
        "status": "online",
        "message": "Flask está funcionando corretamente!",
        "base_dir": BASE_DIR,
        "audio_file": AUDIO_FILE,
        "routes": ["/", "/test", "/audio", "/whatsapp"]
    })

@app.route("/whatsapp", methods=["POST"])
def responder():
    texto = request.values.get("Body", "")
    
    print(f"[WEBHOOK] Mensagem recebida: {texto}")
    
    if not texto:
        resp = MessagingResponse()
        resp.message("Por favor, envie uma mensagem de texto.")
        return str(resp)
    
    try:
        # Gera o áudio com caminho absoluto
        print(f"[TTS] Gerando áudio em: {AUDIO_FILE}")
        tts = gTTS(text=texto, lang="pt-br", slow=False)
        tts.save(AUDIO_FILE)
        print(f"[TTS] Áudio salvo com sucesso!")
        
        # Verifica se o arquivo foi criado
        if os.path.exists(AUDIO_FILE):
            print(f"[TTS] Arquivo confirmado: {AUDIO_FILE}")
        else:
            print(f"[ERRO] Arquivo não foi criado!")
        
        # Responde com o áudio
        resp = MessagingResponse()
        msg = resp.message()
        
        # URL do áudio (usa a URL pública do servidor)
        base_url = request.url_root.rstrip('/')
        audio_url = f"{base_url}/audio"
        msg.media(audio_url)
        
        print(f"[WEBHOOK] Enviando áudio: {audio_url}")
        
        return str(resp)
    except Exception as e:
        print(f"[ERRO] {str(e)}")
        import traceback
        traceback.print_exc()
        resp = MessagingResponse()
        resp.message(f"Erro ao gerar áudio: {str(e)}")
        return str(resp)

@app.route("/audio", methods=["GET"])
def audio():
    print(f"[AUDIO] Requisição recebida para: {AUDIO_FILE}")
    
    # Se não existir, cria um áudio de teste
    if not os.path.exists(AUDIO_FILE):
        print("[AUDIO] Arquivo não existe, criando áudio de teste...")
        try:
            tts = gTTS(text="Olá, este é um áudio de teste", lang="pt-br")
            tts.save(AUDIO_FILE)
            print(f"[AUDIO] Áudio de teste criado em: {AUDIO_FILE}")
        except Exception as e:
            print(f"[ERRO ao criar áudio de teste] {str(e)}")
            return "Erro ao criar áudio", 500
    
    # Verifica novamente se existe
    if not os.path.exists(AUDIO_FILE):
        print(f"[ERRO] Arquivo não encontrado: {AUDIO_FILE}")
        return "Arquivo de áudio não encontrado", 404
    
    print(f"[AUDIO] Enviando arquivo: {AUDIO_FILE}")
    
    try:
        return send_file(
            AUDIO_FILE, 
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="mensagem.mp3"
        )
    except Exception as e:
        print(f"[ERRO ao enviar arquivo] {str(e)}")
        return f"Erro ao enviar áudio: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("="*50)
    print(f"🚀 Iniciando Flask na porta {port}...")
    print(f"📁 Diretório base: {BASE_DIR}")
    print(f"🎵 Arquivo de áudio: {AUDIO_FILE}")
    print("="*50)
    app.run(host="0.0.0.0", port=port, debug=False)