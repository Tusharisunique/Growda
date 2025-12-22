import os
import threading
import asyncio
import gc
import uvicorn
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
from model import preprocess_image, get_class_and_confidence
import fl_server

# Configure TensorFlow to use less memory
try:
    # Limit TensorFlow memory growth to prevent OOM on low-memory instances
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    # Set CPU thread limits to reduce memory overhead
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(2)
except Exception as e:
    print(f"[TensorFlow Config] Warning: Could not configure TF memory settings: {e}")

MODEL_PATH = "global_model.keras"
app = FastAPI(title="Growda API - Federated Learning for Pneumonia Detection")

# Global model cache with file modification tracking
_cached_model = None
_cached_model_mtime = None
_model_lock = asyncio.Lock()

# Semaphore to limit concurrent predictions (prevent memory spikes)
MAX_CONCURRENT_PREDICTIONS = 1  # Process one prediction at a time on low-memory instances
_prediction_semaphore = asyncio.Semaphore(MAX_CONCURRENT_PREDICTIONS)

# Maximum file size for uploads (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using "*" for origins
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers for better compatibility
)

training_in_progress = False


async def get_model():
    """Load model with caching and auto-reload when FL server updates it."""
    global _cached_model, _cached_model_mtime
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    current_mtime = os.path.getmtime(MODEL_PATH)
    
    # Check if we need to reload the model
    async with _model_lock:
        if _cached_model is None or _cached_model_mtime != current_mtime:
            print(f"[Model Cache] Loading model from {MODEL_PATH} (mtime: {current_mtime})")
            
            # Clear old model from memory if it exists
            if _cached_model is not None:
                del _cached_model
                gc.collect()  # Force garbage collection
                tf.keras.backend.clear_session()  # Clear TensorFlow session
            
            # Load new model
            _cached_model = tf.keras.models.load_model(MODEL_PATH)
            _cached_model_mtime = current_mtime
            print(f"[Model Cache] Model loaded successfully")
        
        return _cached_model


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
    """Predict pneumonia from X-ray image with memory-optimized processing."""
    
    # Use semaphore to limit concurrent predictions (prevent memory spikes)
    async with _prediction_semaphore:
        print(f"[Predict] Received request - Content-Type: {file.content_type}, Filename: {file.filename}")
        
        if not os.path.exists(MODEL_PATH):
            return JSONResponse(status_code=400, content={"error": "Model not trained yet."})
        
        if not file.content_type.startswith("image/"):
            return JSONResponse(status_code=400, content={"error": "Uploaded file is not an image"})
        
        import tempfile
        temp_file_path = None
        
        try:
            # Read file with size validation
            file_size = 0
            chunks = []
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                
                # Check file size limit
                if file_size > MAX_FILE_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.1f}MB",
                            "max_size_mb": MAX_FILE_SIZE / 1024 / 1024
                        }
                    )
                chunks.append(chunk)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                for chunk in chunks:
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            print(f"[Predict] File saved to {temp_file_path}, size: {file_size / 1024:.1f}KB")
            
            # Get cached model (will reload if FL server updated it)
            model = await get_model()
            
            # Preprocess and predict
            img = preprocess_image(temp_file_path)
            prediction = model.predict(img, verbose=0)  # verbose=0 to reduce memory usage
            class_name, confidence, severity = get_class_and_confidence(prediction)
            
            # Clean up tensors
            del img, prediction
            gc.collect()
            
            print(f"[Predict] Success - {class_name} ({confidence:.2%})")
            
            return {
                "prediction": class_name,
                "confidence": float(confidence),
                "severity_level": severity
            }
            
        except FileNotFoundError as e:
            print(f"[Predict] Model not found: {str(e)}")
            return JSONResponse(status_code=400, content={"error": "Model not trained yet."})
        except Exception as e:
            print(f"[Predict] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": f"Prediction failed: {str(e)}"})
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    print(f"[Predict] Failed to delete temp file: {e}")

if __name__ == "__main__":
    # Bind to 0.0.0.0 to allow reverse proxy access
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
