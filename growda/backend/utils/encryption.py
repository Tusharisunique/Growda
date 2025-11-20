"""
Encryption utilities for secure model weight exchange.
Uses AES encryption from PyCryptodome.
"""
import base64
import json
import os
from typing import Dict, Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import numpy as np

# AES requires a fixed block size
BLOCK_SIZE = 16

# In a real-world scenario, this would be securely stored and distributed
# For this prototype, we use a fixed key
SECRET_KEY = b'growdasecretkey1'  # Must be 16, 24, or 32 bytes long

def encrypt_weights(weights: Dict[str, np.ndarray]) -> str:
    """
    Encrypt model weights using AES encryption.
    
    Args:
        weights: Dictionary of model weights
        
    Returns:
        Encrypted weights as a base64 string
    """
    # Convert weights to a serializable format
    serializable_weights = {}
    for key, value in weights.items():
        serializable_weights[key] = value.tolist()
    
    # Convert to JSON string
    weights_json = json.dumps(serializable_weights)
    
    # Generate a random initialization vector
    iv = os.urandom(16)
    
    # Create cipher
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    
    # Pad and encrypt
    padded_data = pad(weights_json.encode('utf-8'), BLOCK_SIZE)
    encrypted_data = cipher.encrypt(padded_data)
    
    # Combine IV and encrypted data and encode as base64
    result = base64.b64encode(iv + encrypted_data).decode('utf-8')
    
    return result

def decrypt_weights(encrypted_weights: str) -> Dict[str, np.ndarray]:
    """
    Decrypt model weights.
    
    Args:
        encrypted_weights: Encrypted weights as a base64 string
        
    Returns:
        Dictionary of model weights
    """
    # Decode from base64
    encrypted_data = base64.b64decode(encrypted_weights)
    
    # Extract IV (first 16 bytes)
    iv = encrypted_data[:16]
    actual_encrypted_data = encrypted_data[16:]
    
    # Create cipher
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    
    # Decrypt and unpad
    decrypted_data = unpad(cipher.decrypt(actual_encrypted_data), BLOCK_SIZE)
    weights_json = decrypted_data.decode('utf-8')
    
    # Convert back to dictionary
    serializable_weights = json.loads(weights_json)
    
    # Convert lists back to numpy arrays
    weights = {}
    for key, value in serializable_weights.items():
        weights[key] = np.array(value)
    
    return weights