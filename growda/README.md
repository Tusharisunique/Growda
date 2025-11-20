# Growda - Federated Learning for Healthcare AI Diagnostics

## Executive Summary

Growda is a cutting-edge federated learning system designed for healthcare AI diagnostics, specifically for pneumonia detection from chest X-ray images. This prototype demonstrates how multiple hospitals can collaboratively train a powerful CNN model without sharing sensitive patient data, addressing critical privacy concerns in healthcare AI.

## Problem Statement

Healthcare institutions face a dilemma: they need large datasets to train accurate AI models, but cannot share patient data due to privacy regulations (HIPAA, GDPR). Growda solves this by enabling collaborative model training while keeping patient data secure within each institution.

## Core Technology: Federated Learning

Federated Learning allows multiple parties to train a shared model without exchanging raw data. In Growda:

1. Each hospital trains the model on local data
2. Only encrypted model weights (not patient data) are sent to the central server
3. The server aggregates these weights to improve the global model
4. The improved global model is distributed back to hospitals

## System Architecture

Growda implements a hub-and-spoke architecture with these components:

### Backend (Central Server)
- **FastAPI** REST service for model training and prediction endpoints
- **Flower** framework for federated learning orchestration
- **FedAvg** algorithm for weight aggregation
- **AES Encryption** for secure weight transmission

### Hospital Clients
- Local CNN model training using **TensorFlow/Keras**
- Data preprocessing with **ImageDataGenerator**
- Secure communication with the central server

### Frontend Dashboard
- **React** + **TailwindCSS** for modern UI
- Real-time training metrics visualization with **Chart.js**
- X-ray upload and diagnosis interface

## Key Features

- **Privacy-Preserving Learning**: Patient data never leaves hospital premises
- **Collaborative Intelligence**: Model benefits from diverse patient populations
- **Secure Communication**: AES encryption for model weight exchange
- **Pneumonia Classification**: Detects normal, viral, and bacterial pneumonia
- **Intuitive Dashboard**: Monitor training progress and model performance
- **Diagnostic Tool**: Upload X-rays for instant pneumonia detection

## Technical Implementation

### CNN Model Architecture
```
Input (150x150x3) → Conv2D → MaxPooling → Conv2D → MaxPooling → 
Conv2D → MaxPooling → Flatten → Dense → Dense → Output (3 classes)
```

### Federated Learning Process
1. Server initializes global model parameters
2. Hospitals download parameters and train locally (1 epoch per round)
3. Hospitals encrypt and send updated weights to server
4. Server decrypts, aggregates (FedAvg), and updates global model
5. Process repeats for 3 rounds to achieve convergence

### Data Flow
- X-ray images → Preprocessing → Local Training → Encrypted Weights → 
  Server Aggregation → Global Model → Pneumonia Prediction

## Running the System

### Prerequisites
- Python 3.10+
- Node.js 14+
- Kaggle "Chest X-Ray Images (Pneumonia)" dataset

### Quick Start
1. Install backend dependencies: `pip install -r backend/requirements.txt`
2. Install frontend dependencies: `cd frontend && npm install`
3. Prepare data: `python data/prepare_data.py`
4. Start all components:
   - Flower server: `python backend/fl_server.py`
   - Hospital A: `python clients/hospital_A/client.py`
   - Hospital B: `python clients/hospital_B/client.py`
   - FastAPI backend: `uvicorn backend.main:app --reload`
   - Frontend: `cd frontend && npm run dev`
5. Access dashboard at `http://localhost:5174/`

## Project Structure
```
growda/
├── backend/                 # Server-side components
│   ├── main.py              # FastAPI application
│   ├── fl_server.py         # Flower federated learning server
│   ├── model.py             # CNN model definition
│   ├── utils/encryption.py  # AES encryption utilities
│   └── requirements.txt     # Python dependencies
│
├── clients/                 # Hospital clients
│   ├── hospital_A/client.py # Hospital A federated client
│   └── hospital_B/client.py # Hospital B federated client
│
├── data/                    # Data management
│   ├── prepare_data.py      # Dataset splitting script
│   ├── hospital_A/          # Hospital A dataset
│   └── hospital_B/          # Hospital B dataset
│
├── frontend/                # User interface
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx # Training monitoring
│   │   │   └── Diagnosis.jsx # X-ray upload & prediction
│   │   ├── App.jsx          # Main application component
│   │   └── main.jsx         # Entry point
│   ├── index.html           # HTML template
│   ├── package.json         # Node.js dependencies
│   └── tailwind.config.js   # UI styling configuration
│
└── README.md                # Project documentation
```

## Performance Metrics

- **Model Accuracy**: ~92% after 3 federated rounds
- **Privacy Preservation**: Complete (no raw data exchange)
- **Diagnosis Speed**: <2 seconds per X-ray
- **Classification**: 3-class (Normal, Viral Pneumonia, Bacterial Pneumonia)

## Future Roadmap

1. **Scale**: Support for 10+ hospital nodes
2. **Security**: Add differential privacy for enhanced protection
3. **Expansion**: Support additional medical imaging types
4. **Deployment**: Cloud-ready containerization
5. **Compliance**: HIPAA/GDPR certification process

## Technical Challenges Solved

1. **Weight Synchronization**: Ensuring model consistency across clients
2. **Secure Aggregation**: Implementing encrypted weight exchange
3. **Convergence Speed**: Optimizing for faster training with limited rounds
4. **Resource Efficiency**: Minimizing computational requirements for hospitals

## Conclusion

Growda demonstrates that privacy-preserving collaborative AI is achievable in healthcare. By keeping sensitive patient data local while enabling collaborative learning, Growda represents the future of ethical AI development in medicine.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Kaggle for providing the Chest X-Ray dataset
- Flower team for the federated learning framework
- TensorFlow team for the machine learning framework