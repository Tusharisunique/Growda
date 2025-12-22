import os
import threading
import uvicorn
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
from model import preprocess_image, get_class_and_confidence
import fl_server

MODEL_PATH = "global_model.keras"
app = FastAPI(title="Growda API - Federated Learning for Pneumonia Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using "*" for origins
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers for better compatibility
)

training_in_progress = False


def _status_payload():
    status = fl_server.get_training_status()
    status["in_progress"] = training_in_progress
    return status

@app.get("/")
def root():
    return {"message": "Welcome to Growda API - Federated Learning for Pneumonia Detection"}

@app.get("/cors-test")
def cors_test():
    """Test endpoint to verify CORS is working"""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS is working!", "timestamp": str(os.times())},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

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
    return JSONResponse(
        content=_status_payload(),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/training_status")
def training_status():
    """Backward-compatible alias used by early prototypes."""
    return _status_payload()

@app.get("/metrics/history")
def metrics_history():
    return JSONResponse(
        content={"history": fl_server.get_metrics_history()},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.options("/predict")
async def predict_options():
    """Handle CORS preflight for predict endpoint"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    print(f"[DEBUG] Received predict request - Content-Type: {file.content_type}, Filename: {file.filename}")
    
    if not os.path.exists(MODEL_PATH):
        return JSONResponse(status_code=400, content={"error": "Model not trained yet."})
    if not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"error": "Uploaded file is not an image"})
    
    import tempfile
    # Use async file operations to handle large uploads
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            # Read file in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        print(f"[DEBUG] File saved to {temp_file_path}, size: {os.path.getsize(temp_file_path)} bytes")
        
        model = tf.keras.models.load_model(MODEL_PATH)
        img = preprocess_image(temp_file_path)
        prediction = model.predict(img)
        class_name, confidence, severity = get_class_and_confidence(prediction)
        return {"prediction": class_name, "confidence": float(confidence), "severity_level": severity}
    except Exception as e:
        print(f"[ERROR] Prediction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Prediction failed: {str(e)}"})
    finally:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)

if __name__ == "__main__":
    # Bind to 0.0.0.0 to allow reverse proxy access
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
