import os
import threading
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
from model import preprocess_image, get_class_and_confidence
import fl_server

MODEL_PATH = "global_model.keras"
app = FastAPI(title="Growda API - Federated Learning for Pneumonia Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

training_in_progress = False


def _status_payload():
    status = fl_server.get_training_status()
    status["in_progress"] = training_in_progress
    return status

@app.get("/")
def root():
    return {"message": "Welcome to Growda API - Federated Learning for Pneumonia Detection"}

@app.post("/train_round")
def train_round():
    global training_in_progress
    if training_in_progress:
        return JSONResponse(status_code=400, content={"error": "Training already in progress"})

    def run_training():
        global training_in_progress
        training_in_progress = True
        try:
            # Run a single federated learning round without blocking the API thread
            fl_server.start_server(num_rounds=1)
        except Exception as exc:
            print(f"[Backend] Training round failed: {exc}")
        finally:
            training_in_progress = False

    threading.Thread(target=run_training, daemon=True).start()
    status = _status_payload()
    status["in_progress"] = True
    return {"success": True, **status}

@app.get("/status")
def status():
    return _status_payload()


@app.get("/training_status")
def training_status():
    """Backward-compatible alias used by early prototypes."""
    return _status_payload()

@app.get("/metrics/history")
def metrics_history():
    return {"history": fl_server.get_metrics_history()}

@app.post("/predict")
def predict(file: UploadFile = File(...)):
    if not os.path.exists(MODEL_PATH):
        return JSONResponse(status_code=400, content={"error": "Model not trained yet."})
    if not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"error": "Uploaded file is not an image"})
    import tempfile, shutil
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        img = preprocess_image(temp_file_path)
        prediction = model.predict(img)
        class_name, confidence, severity = get_class_and_confidence(prediction)
        return {"prediction": class_name, "confidence": float(confidence), "severity_level": severity}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Prediction failed: {str(e)}"})
    finally:
        os.unlink(temp_file_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)