import tensorflow as tf
from tensorflow.keras import layers, models

def create_pneumonia_model():
    model = models.Sequential([
        layers.Input(shape=(150, 150, 3)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Flatten(),
        layers.Dropout(0.5),
        layers.Dense(128, activation='relu'),
        layers.Dense(1, activation='sigmoid'),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
                  loss='binary_crossentropy', metrics=['accuracy'])
    return model

def preprocess_image(image_path, target_size=(150, 150)):
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=target_size)
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = tf.expand_dims(img_array, 0)
    return img_array

def get_class_and_confidence(pred):
    """Map raw sigmoid output to class label, probability and severity.

    The model outputs p(Pneumonia). We intentionally use a slightly
    lower threshold than 0.5 so that borderline pneumonia cases are
    less likely to be classified as Normal.
    """
    prob_pneumonia = float(pred[0])
    # Slightly more sensitive threshold for pneumonia
    class_idx = 1 if prob_pneumonia >= 0.4 else 0
    class_names = ["Normal", "Pneumonia"]
    if class_idx == 0:
        severity = "None"
    else:
        if prob_pneumonia < 0.6:
            severity = "Low"
        elif prob_pneumonia < 0.8:
            severity = "Moderate"
        else:
            severity = "High"
    return class_names[class_idx], prob_pneumonia, severity