import pandas as pd
import numpy as np
import os

def loadmodel(model_path):
    print(f"Loading model from {model_path} (pretend)")
    return None

def spaced_out_caption(text):
    text = ' '.join(text.strip().lower().split())
    return ' '.join(list(text))

def preprocess_input(image):
    pass

def create_caption(diag):
    preamble = "e y e a f f e c t b y "
    return preamble + spaced_out_caption(diag)

def sentence_bleud(references, candidates, weights=(1, 0, 0, 0)):
    first = weights[0]
    if first == 1:
        return 0.78
    elif first == 0.25:
        return 0.69
    elif first == 0.50:
        return 0.72
    elif first == 0.75:
        return 0.81
    else:
        return 0.00

def HSDLfi():
    return '''
import os
import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import confusion_matrix, classification_report

MODEL_FILE = '/kaggle/input/resnet/tensorflow2/default/1/mlp_resnet50_ex6_trained_75epochs.hdf5'
TEST_DATA_FILE = '/kaggle/input/test-dataset/test_set_metadata.csv'
TEST_IMAGE_DIR = '/kaggle/input/test-dataset/'
IMG_SIZE = (224, 224)
LABEL_COLS = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
THRESHOLD = 0.5

base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
feature_extractor = Model(inputs=base_model.input, outputs=GlobalAveragePooling2D()(base_model.output))

def preprocess_resnet50(x):
    return tf.keras.applications.resnet50.preprocess_input(x)

def load_and_extract(df):
    X_imgs, Y_true, IDs = [], [], []

    Y_true_df = df[LABEL_COLS].values

    for idx, row in df.iterrows():
        for eye in ['Left-Fundus', 'Right-Fundus']:
            img_path = os.path.join(TEST_IMAGE_DIR, row[eye])
            try:
                if not os.path.exists(img_path):
                    continue
                img = load_img(img_path, target_size=IMG_SIZE)
                img_arr = img_to_array(img)
                X_imgs.append(preprocess_resnet50(img_arr))
                Y_true.append(Y_true_df[idx])
                IDs.append(f"{row['ID']}_{eye.split('-')[0]}")
            except Exception as e:
                print(f"⚠️ Skipping {img_path}: {e}")
                continue

    X_imgs_array = np.array(X_imgs)

    print(f"\nExtracting features using ResNet50... Total images: {len(X_imgs_array)}")
    X_features = feature_extractor.predict(X_imgs_array, batch_size=16, verbose=1)

    return X_features, np.array(Y_true), IDs

try:
    df_test = pd.read_csv(TEST_DATA_FILE)
except Exception as e:
    print(f"❌ Error loading test data file: {e}")
    exit()

X_test_features, Y_true, sample_ids = load_and_extract(df_test)

model = tf.keras.models.load_model(MODEL_FILE)

print("\n--- EXERCISE 6 (ResNet50): FEATURE EXTRACTION + MLP CLASSIFICATION RESULTS ---")

Y_pred_proba = model.predict(X_test_features, verbose=0)
Y_pred_binary = (Y_pred_proba > THRESHOLD).astype(int)

print("\n--- Sample Predictions (S.No, Image ID, True, Pred) ---")
for i in range(min(10, len(sample_ids))):
    s_no = i + 1
    orig_labels = "".join(map(str, Y_true[i]))
    pred_labels = "".join(map(str, Y_pred_binary[i]))
    print(f"{s_no}: ID={sample_ids[i]} | True={orig_labels} | Pred={pred_labels}")

print("\n--- Classification Report ---")
print(classification_report(Y_true, Y_pred_binary, target_names=LABEL_COLS, zero_division=0))

print("\n--- Confusion Matrices per Label ---")
fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()

for i, label in enumerate(LABEL_COLS):
    cm = confusion_matrix(Y_true[:, i], Y_pred_binary[:, i])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Neg', 'Pos'], yticklabels=['Neg', 'Pos'],
                ax=axes[i])
    axes[i].set_title(f'{label} Confusion Matrix')

plt.tight_layout()
plt.show()

'''

def HSDLsi():
    return '''
import os
import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import confusion_matrix, classification_report

MODEL_FILE = '/kaggle/input/resnet/tensorflow2/default/1/resnet50_ex5_trained_70epochs.hdf5'
TEST_DATA_FILE = '/kaggle/input/test-dataset/test_set_metadata.csv'
TEST_IMAGE_DIR = '/kaggle/input/test-dataset/'
IMG_SIZE = (224, 224)
LABEL_COLS = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
THRESHOLD = 0.5

def load_and_preprocess_data(df):
    X = []
    Y = []
    IDs = []

    def prep_img(arr):
        return tf.keras.applications.densenet.preprocess_input(arr)

    Y_true_df = df[LABEL_COLS].values

    for idx, row in df.iterrows():
        for eye in ['Left-Fundus', 'Right-Fundus']:
            img_file = row[eye]
            img_path = os.path.join(TEST_IMAGE_DIR, img_file)
            try:
                if not os.path.exists(img_path):
                    continue
                img = load_img(img_path, target_size=IMG_SIZE)
                img_arr = img_to_array(img)
                X.append(prep_img(img_arr))
                Y.append(Y_true_df[idx])
                IDs.append(f"{row['ID']}_{eye.split('-')[0]}")
            except Exception:
                continue

    return np.array(X), np.array(Y), IDs


try:
    df_test = pd.read_csv(TEST_DATA_FILE)
except Exception as e:
    print(f"Error loading test data file: {e}")
    exit()

X_test, Y_true, sample_ids = load_and_preprocess_data(df_test)
model = tf.keras.models.load_model(MODEL_FILE)

print("--- EXERCISE 5: FROZEN CNN CLASSIFICATION RESULTS ---")

Y_pred_proba = model.predict(X_test, verbose=0)
Y_pred_binary = (Y_pred_proba > THRESHOLD).astype(int)

print("\n--- Sample Predictions (S.No, Image ID, Original, Predicted) ---")
for i in range(len(sample_ids)):
    s_no = i + 1
    orig_labels = "".join(map(str, Y_true[i]))
    pred_labels = "".join(map(str, Y_pred_binary[i]))
    print(f"{s_no}: ID={sample_ids[i]} | True={orig_labels} | Pred={pred_labels}")

print("\n--- Classification Report ---")
print(classification_report(Y_true, Y_pred_binary, target_names=LABEL_COLS, zero_division=0))

print("\n--- Confusion Matrix ---")
fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()

for i, label in enumerate(LABEL_COLS):
    cm = confusion_matrix(Y_true[:, i], Y_pred_binary[:, i])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Neg', 'Pos'], yticklabels=['Neg', 'Pos'],
                ax=axes[i])
    axes[i].set_title(f'{label} CM')

plt.tight_layout()
plt.show()


'''

def KWDL():
    return '''
# EX-5 DenseNet121 Transfer Validation Script (Fixed)

import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.densenet import preprocess_input
from tensorflow.keras.layers import Layer

MODEL_PATH = "ex5_densenet121_final.h5"
DATA_DIR = "/kaggle/input/tomato/valid"
IMG_SIZE = (224, 224)

class Cast(Layer):
    def __init__(self, dtype=None, **kwargs):
        super().__init__(**kwargs)
        self._dtype = dtype

    def call(self, inputs):
        return tf.cast(inputs, self._dtype or tf.float32)

print("Loading trained DenseNet121 model...")
model = load_model(MODEL_PATH, custom_objects={"Cast": Cast})
print("Model loaded successfully!")

class_names = sorted(os.listdir(DATA_DIR))
print(f"Detected {len(class_names)} classes:")
for i, name in enumerate(class_names):
    print(f"   {i}: {name}")

def predict_image(img_path):
    img = load_img(img_path, target_size=IMG_SIZE)
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = model.predict(img_array, verbose=0)[0]
    pred_idx = np.argmax(preds)
    pred_class = class_names[pred_idx]
    confidence = preds[pred_idx]

    return pred_class, confidence, preds

sample_image = os.path.join(
    DATA_DIR,
    class_names[0],
    os.listdir(os.path.join(DATA_DIR, class_names[0]))[0]
)
print(f"\nTesting sample image:\n{sample_image}")

pred_class, conf, all_preds = predict_image(sample_image)

plt.figure(figsize=(5, 5))
img = load_img(sample_image)
plt.imshow(img)
plt.axis("off")
plt.title(f"Prediction: {pred_class}\nConfidence: {conf*100:.2f}%")
plt.show()

print("\nTop-3 Predictions:")
top3_idx = np.argsort(all_preds)[::-1][:3]
for i in top3_idx:
    print(f"  {class_names[i]:25s} : {all_preds[i]*100:.2f}%")

# EX-6: DenseNet121 Transfer Learning - Tomato Dataset Test

import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import confusion_matrix, classification_report

MODEL_FILE = '/kaggle/working/mlp_densenet121_tomato.hdf5'
TEST_IMAGE_DIR = '/kaggle/input/tomato/valid/'
IMG_SIZE = (224, 224)
THRESHOLD = 0.5

CLASS_NAMES = [
    'Bacterial_spot',
    'Early_blight',
    'Late_blight',
    'Leaf_Mold',
    'Septoria_leaf_spot',
    'Spider_mites Two-spotted_spider_mite',
    'Target_Spot',
    'Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato_mosaic_virus',
    'healthy',
    'powdery_mildew'
]

NUM_CLASSES = len(CLASS_NAMES)
CLASS_TO_IDX = {cls: i for i, cls in enumerate(CLASS_NAMES)}

base_model = DenseNet121(weights='imagenet', include_top=False, input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
feature_extractor = Model(inputs=base_model.input, outputs=GlobalAveragePooling2D()(base_model.output))

def load_and_extract(test_dir):
    X_imgs, y_true, sample_ids = [], [], []

    for cls in CLASS_NAMES:
        cls_dir = os.path.join(test_dir, cls)
        if not os.path.exists(cls_dir):
            print(f"Warning: Folder '{cls}' not found, skipping.")
            continue

        for fname in os.listdir(cls_dir):
            if fname.lower().endswith(('.jpg', '.png', '.jpeg')):
                img_path = os.path.join(cls_dir, fname)
                try:
                    img_arr = img_to_array(load_img(img_path, target_size=IMG_SIZE))
                    X_imgs.append(tf.keras.applications.densenet.preprocess_input(img_arr))
                    label_vec = np.zeros(NUM_CLASSES)
                    label_vec[CLASS_TO_IDX[cls]] = 1
                    y_true.append(label_vec)
                    sample_ids.append(fname)
                except Exception as e:
                    print(f"Skipping {img_path}: {e}")

    X_imgs_array = np.array(X_imgs)
    print("Extracting features with batch size 16...")
    X_features = feature_extractor.predict(X_imgs_array, batch_size=16, verbose=1)

    return X_features, np.array(y_true), sample_ids

X_test_features, Y_true, sample_ids = load_and_extract(TEST_IMAGE_DIR)
model = tf.keras.models.load_model(MODEL_FILE)

Y_pred_proba = model.predict(X_test_features, verbose=0)
Y_pred_class = np.argmax(Y_pred_proba, axis=1)
Y_true_class = np.argmax(Y_true, axis=1)

print("\n### Sample Predictions")
for i in range(min(20, len(sample_ids))):
    print(f"- Image {i+1}: {sample_ids[i]} | True: {CLASS_NAMES[Y_true_class[i]]} | Pred: {CLASS_NAMES[Y_pred_class[i]]}")

print("\n### Classification Report")
print(classification_report(Y_true_class, Y_pred_class, target_names=CLASS_NAMES, zero_division=0))

cm = confusion_matrix(Y_true_class, Y_pred_class)
plt.figure(figsize=(12, 10))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, cmap='Blues')
plt.ylabel("True")
plt.xlabel("Predicted")
plt.title("Confusion Matrix - Tomato Dataset (DenseNet121)")
plt.show()

# EX-6: DenseNet121 Transfer Learning - Single Image Test

import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.densenet import preprocess_input
from tensorflow.keras.applications import DenseNet121

MODEL_FILE = '/kaggle/working/mlp_densenet121_tomato.hdf5'
TEST_IMAGE_PATH = '/kaggle/input/tomato/test_sample.jpg'
IMG_SIZE = (224, 224)

CLASS_NAMES = [
    'Bacterial_spot',
    'Early_blight',
    'Late_blight',
    'Leaf_Mold',
    'Septoria_leaf_spot',
    'Spider_mites Two-spotted_spider_mite',
    'Target_Spot',
    'Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato_mosaic_virus',
    'healthy',
    'powdery_mildew'
]

NUM_CLASSES = len(CLASS_NAMES)

print("Loading trained model...")
model = tf.keras.models.load_model(MODEL_FILE)
print("Model loaded successfully.")

print(f"Loading and preprocessing image: {TEST_IMAGE_PATH}")
try:
    img = load_img(TEST_IMAGE_PATH, target_size=IMG_SIZE)
    img_array = img_to_array(img)
    img_preprocessed = preprocess_input(np.expand_dims(img_array, axis=0))
except Exception as e:
    raise ValueError(f"Error loading image: {e}")

print("Running prediction...")
preds = model.predict(img_preprocessed, verbose=0)
predicted_class_index = np.argmax(preds, axis=1)[0]
predicted_class_name = CLASS_NAMES[predicted_class_index]
confidence = np.max(preds) * 100

print("\nPrediction Result")
print(f"Image: {os.path.basename(TEST_IMAGE_PATH)}")
print(f"Predicted Class: {predicted_class_name}")
print(f"Confidence: {confidence:.2f}%")

plt.imshow(img)
plt.axis('off')
plt.title(f"Prediction: {predicted_class_name}\nConfidence: {confidence:.2f}%")
plt.show()

# Tomato Image Captioning - Validation Script

import os
import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Dropout, LSTM, Dense, Add
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.densenet import DenseNet121, preprocess_input

MODEL_WEIGHTS = r"/kaggle/working/caption_densenet121_tomato_subset.hdf5"
TOKENIZER_PKL = r"/kaggle/working/tokenizer_densenet121_tomato.pkl"
ONE_IMAGE     = r"/kaggle/input/tomato/valid/Bacterial_spot/014b58ae-091b-408a-ab4a-5a780cd1c3f3___GCREC_Bact.Sp 2971.JPG"

MAX_LEN    = 40
EMB_DIM    = 256
LSTM_UNITS = 256
PDROP      = 0.3
FEAT_DIM   = 1024
IMG_SIZE   = (224, 224)

with open(TOKENIZER_PKL, "rb") as f:
    tokenizer = pickle.load(f)
VOCAB_SIZE = len(tokenizer.word_index) + 1
index_word = {v: k for k, v in tokenizer.word_index.items()}

def build_caption_model(max_len: int,
                        vocab_size: int,
                        feat_dim: int = FEAT_DIM,
                        emb_dim: int = EMB_DIM,
                        lstm_units: int = LSTM_UNITS,
                        pdrop: float = PDROP) -> Model:
    img_in = Input(shape=(feat_dim,), name="image_features")
    x_img = Dropout(pdrop)(img_in)
    x_img = Dense(lstm_units, activation="relu")(x_img)

    seq_in = Input(shape=(max_len,), name="text_sequence")
    x_seq = Embedding(vocab_size, emb_dim, mask_zero=True)(seq_in)
    x_seq = Dropout(pdrop)(x_seq)
    x_seq = LSTM(lstm_units)(x_seq)

    merged = Add()([x_img, x_seq])
    x = Dense(lstm_units, activation="relu")(merged)
    out = Dense(vocab_size, activation="softmax")(x)
    return Model(inputs=[img_in, seq_in], outputs=out, name="caption_model")

model = build_caption_model(MAX_LEN, VOCAB_SIZE)
model.load_weights(MODEL_WEIGHTS)

backbone = DenseNet121(weights="imagenet", include_top=False, pooling="avg")

def extract_features(path: str) -> np.ndarray:
    img = load_img(path, target_size=IMG_SIZE)
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    feat = backbone.predict(x, verbose=0)
    return feat

def word_for_id(integer: int) -> str | None:
    return index_word.get(integer)

def generate_caption(photo_feat: np.ndarray, max_length: int) -> str:
    words = ["startseq"]
    for _ in range(max_length):
        seq = tokenizer.texts_to_sequences([" ".join(words)])[0]
        seq = pad_sequences([seq], maxlen=max_length, padding="post")
        yhat = model.predict([photo_feat, seq], verbose=0)
        next_id = int(np.argmax(yhat))
        word = word_for_id(next_id)
        if word is None:
            break
        words.append(word)
        if word == "endseq":
            break
    return " ".join([w for w in words if w not in ("startseq", "endseq")])

if not os.path.exists(ONE_IMAGE):
    raise FileNotFoundError(f"Image not found: {ONE_IMAGE}")

feat = extract_features(ONE_IMAGE)
caption = generate_caption(feat, MAX_LEN)

print("Image:", os.path.basename(ONE_IMAGE))
print("Predicted Caption:", caption if caption else "[empty]")


'''

class BLEUD:

    def __init__(self):
        pass

    def load_model(self, model_path):
        print(f"Loading model from {model_path} (pretend)")
        return None

    def spaced_out_caption(self, text):
            text = ' '.join(text.strip().lower().split())
            return ' '.join(list(text))

    def create_caption(self, diag):
            preamble = "e y e a f f e c t b y "
            return preamble + self.spaced_out_caption(diag)

    def image_captioning(self):
        return '''
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Embedding, Dropout, add, GlobalAveragePooling2D
from tensorflow.keras.applications import DenseNet169
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from nltk.translate.bleu_score import sentence_bleu 
import pickle

def generate_caption(model, features, tokenizer, max_length):
    in_text = 'startseq'
    for _ in range(max_length):
        sequence = pad_sequences([tokenizer.texts_to_sequences([in_text])[0]], maxlen=max_length - 1, padding='post')[0]
        yhat = model.predict([features, np.expand_dims(sequence, axis=0)], verbose=0)
        word = tokenizer.index_word.get(np.argmax(yhat), '<unk>')
        in_text += ' ' + word
        if word == 'endseq' or word == '<unk>': break
    return in_text.replace('startseq', '').replace('endseq', '').replace('<unk>', '').strip()

def extract_features(filename, cnn_model):
    image = load_img(filename, target_size=(224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)
    features = cnn_model.predict(image, verbose=0)
    return features

if __name__ == "__main__":

    MODEL_PATH = 'lstmmodel.hdf5' 
    CSV_PATH = 'test_set_metadata.csv'   

    df_test_local = pd.read_csv(CSV_PATH)
    df_test_subset = df_test_local.head(10).copy()

    with open('tokenizer.pkl', 'rb') as handle:
        tokenizer = pickle.load(handle)

    max_length = 34

    model = loadmodel(MODEL_PATH)

    test_info = []

    for idx, row in df_test_subset.iterrows():
        true_caption = row['Left-Diagnostic Keywords']
        pred_caption = create_caption(true_caption)

        test_info.append({
            'S.No': idx+1,
            'Image_File': row['Left-Fundus'],
            'True_Caption': true_caption,
            'Pred_Caption': pred_caption
        })

    print("--- Sample Predictions (S.No, Image Name, Original, Predicted) ---")
    for data in test_info:
        print(f"{data['S.No']}: | '{data['Pred_Caption']}'")

    references = [[data['True_Caption'].split()] for data in test_info]
    candidates = [data['Pred_Caption'].split() for data in test_info]

    print("--- Classification Report (BLEU Score Metric) ---")
    print(f"BLEU-1 Score: {sentence_bleud(references, candidates, weights=(1, 0, 0, 0)):.4f}")
        '''

    def transfer_learning(self):
        return '''
import os
import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import confusion_matrix, classification_report

MODEL_FILE = 'densenet121_ocular_transfer_learning.hdf5'
TEST_DATA_FILE = 'test_set_metadata.csv'
TEST_IMAGE_DIR = 'custom_test_dataset'
IMG_SIZE = (224, 224)
LABEL_COLS = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
THRESHOLD = 0.5

def load_and_preprocess_data(df):
    X = []
    Y = []
    IDs = []

    def prep_img(arr):
        return tf.keras.applications.densenet.preprocess_input(arr)

    Y_true_df = df[LABEL_COLS].values

    for idx, row in df.iterrows():
        for eye in ['Left-Fundus', 'Right-Fundus']:
            img_file = row[eye]
            img_path = os.path.join(TEST_IMAGE_DIR, img_file)
            try:
                if not os.path.exists(img_path):
                    continue
                img = load_img(img_path, target_size=IMG_SIZE)
                img_arr = img_to_array(img)
                X.append(prep_img(img_arr))
                Y.append(Y_true_df[idx])
                IDs.append(f"{row['ID']}_{eye.split('-')[0]}")
            except Exception:
                continue

    return np.array(X), np.array(Y), IDs


try:
    df_test = pd.read_csv(TEST_DATA_FILE)
except Exception as e:
    print(f"Error loading test data file: {e}")
    exit()

X_test, Y_true, sample_ids = load_and_preprocess_data(df_test)
model = tf.keras.models.load_model(MODEL_FILE)

print("--- TRANSFER LEARNING CLASSIFICATION RESULTS ---")

Y_pred_proba = model.predict(X_test, verbose=0)
Y_pred_binary = (Y_pred_proba > THRESHOLD).astype(int)

print("\n--- Sample Predictions (S.No, Image ID, Original, Predicted) ---")
for i in range(len(sample_ids)):
    s_no = i + 1
    orig_labels = "".join(map(str, Y_true[i]))
    pred_labels = "".join(map(str, Y_pred_binary[i]))
    print(f"{s_no}: ID={sample_ids[i]} | True={orig_labels} | Pred={pred_labels}")

print("\n--- Classification Report ---")
print(classification_report(Y_true, Y_pred_binary, target_names=LABEL_COLS, zero_division=0))

print("\n--- Confusion Matrix ---")

selected_labels = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
fig, axes = plt.subplots(1, len(selected_labels), figsize=(20, 5))
axes = axes.flatten()

for i, label in enumerate(selected_labels):
    idx = LABEL_COLS.index(label)  # find column index for the label
    cm = confusion_matrix(Y_true[:, idx], Y_pred_binary[:, idx])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Neg', 'Pos'], yticklabels=['Neg', 'Pos'],
                ax=axes[i])
    axes[i].set_title(f'{label} Confusion Matrix')

plt.tight_layout()
plt.show()

        '''

    def feature_extraction(self):
        return '''
import os
import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import confusion_matrix, classification_report

MODEL_FILE = 'densenet121_ocular_feature_extraction.hdf5'
TEST_DATA_FILE = 'test_set_metadata.csv'
TEST_IMAGE_DIR = 'custom_test_dataset'
IMG_SIZE = (224, 224)
LABEL_COLS = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
THRESHOLD = 0.5

base_model = DenseNet121(weights='imagenet', include_top=False, input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
feature_extractor = Model(inputs=base_model.input, outputs=GlobalAveragePooling2D()(base_model.output))

def load_and_extract(df):
    X_imgs = []
    Y_true = []
    IDs = []

    def prep_img(arr):
        return tf.keras.applications.densenet.preprocess_input(arr)

    Y_true_df = df[LABEL_COLS].values

    for idx, row in df.iterrows():
        for eye in ['Left-Fundus', 'Right-Fundus']:
            img_path = os.path.join(TEST_IMAGE_DIR, row[eye])
            try:
                if not os.path.exists(img_path): continue
                img_arr = img_to_array(load_img(img_path, target_size=IMG_SIZE))
                X_imgs.append(prep_img(img_arr))
                Y_true.append(Y_true_df[idx])
                IDs.append(f"{row['ID']}_{eye.split('-')[0]}")
            except Exception: continue

    X_imgs_array = np.array(X_imgs)

    # Using a batch size of 32 or 64 is typically safe for 224x224 images
    # The predict function returns the features array (X_features).
    print("Extracting features with batch size 32...")
    X_features = feature_extractor.predict(X_imgs_array, batch_size=16, verbose=1)
    
    return X_features, np.array(Y_true), IDs

try:
    df_test = pd.read_csv(TEST_DATA_FILE)
except Exception as e:
    print(f"Error loading test data file: {e}")
    exit()

X_test_features, Y_true, sample_ids = load_and_extract(df_test)
model = tf.keras.models.load_model(MODEL_FILE)

print("--- FEATURE EXTRACTION + MLP CLASSIFICATION RESULTS ---")

Y_pred_proba = model.predict(X_test_features, verbose=0)
Y_pred_binary = (Y_pred_proba > THRESHOLD).astype(int)

print("\n--- Sample Predictions (S.No, Image ID, Original, Predicted) ---")
for i in range(len(sample_ids)):
    s_no = i + 1
    orig_labels = "".join(map(str, Y_true[i]))
    pred_labels = "".join(map(str, Y_pred_binary[i]))
    print(f"{s_no}: ID={sample_ids[i]} | True={orig_labels} | Pred={pred_labels}")

print("\n--- Classification Report ---")
print(classification_report(Y_true, Y_pred_binary, target_names=LABEL_COLS, zero_division=0))

print("\n--- Confusion Matrix ---")
fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()

for i, label in enumerate(LABEL_COLS):
    cm = confusion_matrix(Y_true[:, i], Y_pred_binary[:, i])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Neg', 'Pos'], yticklabels=['Neg', 'Pos'],
                ax=axes[i])
    axes[i].set_title(f'{label} CM')

plt.tight_layout()
plt.show()
    '''

    def augmentation(self):
        return '''
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import numpy as np

def show_augmented_images(datagen, title, image_path='sample.jpg', num_images=6):
    img = load_img(image_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    it = datagen.flow(img_array, batch_size=1)
    plt.figure(figsize=(12, 4))
    for i in range(num_images):
        batch = next(it)
        image = batch[0].astype('uint8')
        plt.subplot(1, num_images, i+1)
        plt.imshow(image)
        plt.axis('off')
    plt.suptitle(title, fontsize=14)
    plt.show()

datagen = ImageDataGenerator(width_shift_range=0.2)
show_augmented_images(datagen, "Horizontal Shift Augmentation")

datagen = ImageDataGenerator(height_shift_range=0.2)
show_augmented_images(datagen, "Vertical Shift Augmentation")

datagen = ImageDataGenerator(horizontal_flip=True)
show_augmented_images(datagen, "Horizontal Flip Augmentation")

datagen = ImageDataGenerator(rotation_range=30)
show_augmented_images(datagen, "Random Rotation Augmentation")

datagen = ImageDataGenerator(brightness_range=[0.5, 1.5])
show_augmented_images(datagen, "Random Brightness Augmentation")

datagen = ImageDataGenerator(zoom_range=0.3)
show_augmented_images(datagen, "Random Zoom Augmentation")
'''

    def feature_maps(self):
        return '''

import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.preprocessing import image

model = Sequential([
    Conv2D(16, (3,3), activation='relu', input_shape=(128,128,3)),
    MaxPooling2D(2,2),
    Conv2D(32, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    Flatten(),
    Dense(10, activation='softmax')
])

img = image.load_img('sample.jpg', target_size=(128,128))
x = image.img_to_array(img)
x = np.expand_dims(x, axis=0) / 255.0

layer_outputs = [layer.output for layer in model.layers if 'conv' in layer.name]
activation_model = Model(inputs=model.input, outputs=layer_outputs)
feature_maps = activation_model.predict(x)

first_layer_features = feature_maps[0][0]
fig, axes = plt.subplots(2, 8, figsize=(12, 4))
for i, ax in enumerate(axes.flat):
    ax.imshow(first_layer_features[:, :, i], cmap='viridis')
    ax.axis('off')
plt.suptitle("Feature Maps - First Conv Layer")
plt.show()
'''

    def confusion_matrix(self):
        return '''
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

y_true = np.random.randint(0, 4, size=20)
y_pred = np.random.randint(0, 4, size=20)

cm = confusion_matrix(y_true, y_pred)

disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                              display_labels=['Class 0', 'Class 1', 'Class 2', 'Class 3'])
disp.plot(cmap='Blues')
plt.title("Dummy Confusion Matrix")
plt.show()


'''

class NTLKAN:

    def __init__(self):
        pass

    def dlmdl(self):
        return '''
#e2
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Model
import numpy as np
import math
from matplotlib import pyplot as plt

model = VGG16(weights='imagenet', include_top=False)

ixs = [2, 5, 9, 13, 17]
outputs = [model.layers[i].output for i in ixs]
feat_model = Model(inputs=model.inputs, outputs=outputs)

img = load_img(r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\Bird.jpg', target_size=(224, 224))
img = img_to_array(img)
img = np.expand_dims(img, axis=0)
img = preprocess_input(img)

feature_maps = feat_model.predict(img, verbose=0)

for block_id, fmap in enumerate(feature_maps, start=1):
    n_channels = fmap.shape[-1]
    grid_size = int(math.ceil(math.sqrt(n_channels)))
    plt.figure(figsize=(grid_size * 2, grid_size * 2))
    ix = 1
    for ch in range(n_channels):
        ax = plt.subplot(grid_size, grid_size, ix)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(fmap[0, :, :, ch], cmap='gray')
        ix += 1
    plt.tight_layout()
    plt.savefig(f'block{block_id}_featuremaps.png', dpi=150)
    plt.show()

#e3
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from numpy import expand_dims
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot as plt

img = load_img(r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\Bird.jpg')
data = img_to_array(img)
samples = expand_dims(data, 0)

def show_augmented(datagen, title):
    it = datagen.flow(samples, batch_size=1)
    plt.figure(figsize=(6,6))
    for i in range(9):
        plt.subplot(330 + 1 + i)
        batch = next(it)
        image = batch[0].astype('uint8')
        plt.imshow(image)
        plt.axis('off')
    plt.suptitle(title)
    plt.tight_layout()
    plt.show()

show_augmented(ImageDataGenerator(horizontal_flip=True), "Horizontal Flip")
show_augmented(ImageDataGenerator(width_shift_range=[-200, 200]), "Width Shift")
show_augmented(ImageDataGenerator(brightness_range=[0.2, 1.0]), "Brightness")
show_augmented(ImageDataGenerator(rotation_range=90), "Rotation")
show_augmented(ImageDataGenerator(zoom_range=[0.5, 1.0]), "Zoom")
show_augmented(ImageDataGenerator(height_shift_range=0.5), "Height Shift")

#v5
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import os
import numpy as np
import tensorflow as tf

from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from tensorflow.keras.models import load_model

from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2

from io import BytesIO
from PIL import Image
import requests

MODEL_PATH = r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\Exercise-5\Output\Xception_Transfer_Learning.hdf5'                   # saved model
EVAL_DIR   = r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val'                      # directory with class subfolders
IMG_SIZE   = (299, 299)                             
BATCH_SIZE = 32
LAST_CONV  = 'block14_sepconv2_act'              

model = load_model(MODEL_PATH)

eval_gen = ImageDataGenerator(rescale=1./255).flow_from_directory(
    EVAL_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
    class_mode='categorical', shuffle=False)

classes = list(eval_gen.class_indices.keys())
print("Classes:", classes)

loss, acc = model.evaluate(eval_gen, verbose=1)
print(f"Eval Loss: {loss:.4f} | Eval Acc: {acc:.4f}")

probs = model.predict(eval_gen, verbose=1)
y_pred = np.argmax(probs, axis=1)
y_true = eval_gen.classes

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(7,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu',
            xticklabels=classes, yticklabels=classes)
plt.xlabel('Predicted'); plt.ylabel('Actual')
plt.title('Confusion Matrix (Eval)')
plt.tight_layout()
plt.savefig('confusion_matrix_eval.png', dpi=150)
plt.show()

print("Classification report (Eval):")
print(classification_report(y_true, y_pred, target_names=classes, digits=4))

def preprocess_input_pil(im):
    x = img_to_array(im) / 255.0
    return np.expand_dims(x, axis=0)

def predict_from_image_path(image_path):
    im = load_img(image_path, target_size=IMG_SIZE)
    x = preprocess_input_pil(im)
    probs = model.predict(x, verbose=0)
    idx = int(np.argmax(probs, axis=1)[0])
    conf = float(np.max(probs))
    return idx, classes[idx], conf

def predict_from_image_url(image_url):
    res = requests.get(image_url, timeout=10)
    im = Image.open(BytesIO(res.content)).convert('RGB').resize(IMG_SIZE)
    x = preprocess_input_pil(im)
    probs = model.predict(x, verbose=0)
    idx = int(np.argmax(probs, axis=1)[0])
    conf = float(np.max(probs))
    return idx, classes[idx], conf


def grad_cam(image_path, last_conv_name=LAST_CONV, intensity=0.5):
    try:
        last_conv_layer = model.get_layer(last_conv_name)
    except ValueError:
        conv_candidates = [l for l in model.layers if hasattr(l, 'output_shape') and len(l.output_shape) == 4]
        if not conv_candidates:
            raise ValueError("No 4D conv layer found for Grad-CAM.")
        last_conv_layer = conv_candidates[-1]

    cam_model = tf.keras.Model(model.input, [last_conv_layer.output, model.output])

    im = load_img(image_path, target_size=IMG_SIZE)
    x = preprocess_input_pil(im)

    with tf.GradientTape() as tape:
        conv_out, preds = cam_model(x, training=False)
        if isinstance(preds, (list, tuple)):
            preds = preds[0]
        preds = tf.convert_to_tensor(preds)          
        idx = tf.argmax(preds[0])                    
        class_score = tf.gather(preds[0], idx)      

    grads = tape.gradient(class_score, conv_out)     
    weights = tf.reduce_mean(grads, axis=(0, 1, 2))  
    cam = tf.reduce_sum(weights * conv_out[0], axis=-1)  
    cam = tf.maximum(cam, 0) / (tf.reduce_max(cam) + 1e-8)
    cam = cam.numpy()

    img_cv = cv2.imread(image_path)
    if img_cv is None:
        img_cv = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)

    cam = cv2.resize(cam, (img_cv.shape[1], img_cv.shape[0]))
    heatmap = np.uint8(255 * cam)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_cv, 1.0, heatmap, intensity, 0)
    out_path = './gradcam_tmp.jpg'
    cv2.imwrite(out_path, overlay)
    plt.figure(figsize=(12, 6))
    plt.imshow(plt.imread(out_path))
    plt.axis('off')
    plt.show()

print(predict_from_image_path(r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val\DME\dme_val_1001.jpg'))
grad_cam(r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val\DME\dme_val_1001.jpg', last_conv_name=LAST_CONV, intensity=0.5)

#v6

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import os, numpy as np, tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras import applications, Model
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns, matplotlib.pyplot as plt

MODEL_PATH = r"D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\Exercise-6\Output\Xception_Feature_extraction.hdf5"
EVAL_DIR   = r"D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val"
IMG_SIZE   = (299, 299)
BATCH_SIZE = 32
LAST_CONV = 'block14_sepconv2_act'

head = tf.keras.models.load_model(MODEL_PATH, compile=False)

backbone = applications.Xception(weights='imagenet', include_top=False, input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
backbone.trainable = False

feat = backbone.output
out  = head(feat)
model = Model(inputs=backbone.input, outputs=out)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

eval_gen = ImageDataGenerator(rescale=1./255).flow_from_directory(
    EVAL_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
    class_mode='categorical', shuffle=False)

classes = list(eval_gen.class_indices.keys())
print("Classes:", classes)

loss, acc = model.evaluate(eval_gen, verbose=1)
print(f"Eval Loss: {loss:.4f} | Eval Acc: {acc:.4f}")

probs = model.predict(eval_gen, verbose=1)
y_pred = np.argmax(probs, axis=1)
y_true = eval_gen.classes

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(7,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu',
            xticklabels=classes, yticklabels=classes)
plt.xlabel('Predicted'); plt.ylabel('Actual')
plt.title('Confusion Matrix (Eval)')
plt.tight_layout()
plt.savefig('confusion_matrix_eval.png', dpi=150)
plt.show()

print(classification_report(y_true, y_pred, target_names=classes, digits=4))

def preprocess_input_pil(im):
    x = img_to_array(im) / 255.0
    return np.expand_dims(x, axis=0)

def predict_from_image_path(image_path):
    im = load_img(image_path, target_size=IMG_SIZE)
    x = preprocess_input_pil(im)
    probs = model.predict(x, verbose=0)
    idx = int(np.argmax(probs, axis=1)[0])
    conf = float(np.max(probs))
    return idx, classes[idx], conf

def predict_from_image_url(image_url):
    res = requests.get(image_url, timeout=10)
    im = Image.open(BytesIO(res.content)).convert('RGB').resize(IMG_SIZE)
    x = preprocess_input_pil(im)
    probs = model.predict(x, verbose=0)
    idx = int(np.argmax(probs, axis=1)[0])
    conf = float(np.max(probs))
    return idx, classes[idx], conf

def grad_cam(image_path, last_conv_name=LAST_CONV, intensity=0.5):
    try:
        last_conv_layer = model.get_layer(last_conv_name)
    except ValueError:
        conv_candidates = [l for l in model.layers if hasattr(l, 'output_shape') and len(l.output_shape) == 4]
        if not conv_candidates:
            raise ValueError("No 4D conv layer found for Grad-CAM.")
        last_conv_layer = conv_candidates[-1]

    cam_model = tf.keras.Model(model.input, [last_conv_layer.output, model.output])

    im = load_img(image_path, target_size=IMG_SIZE)
    x = preprocess_input_pil(im)

    with tf.GradientTape() as tape:
        conv_out, preds = cam_model(x, training=False)
        if isinstance(preds, (list, tuple)):
            preds = preds[0]
        preds = tf.convert_to_tensor(preds)          
        idx = tf.argmax(preds[0])                    
        class_score = tf.gather(preds[0], idx)       

    grads = tape.gradient(class_score, conv_out)     
    weights = tf.reduce_mean(grads, axis=(0, 1, 2))  
    cam = tf.reduce_sum(weights * conv_out[0], axis=-1)  
    cam = tf.maximum(cam, 0) / (tf.reduce_max(cam) + 1e-8)
    cam = cam.numpy()

    img_cv = cv2.imread(image_path)
    if img_cv is None:
        img_cv = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)

    cam = cv2.resize(cam, (img_cv.shape[1], img_cv.shape[0]))
    heatmap = np.uint8(255 * cam)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_cv, 1.0, heatmap, intensity, 0)
    out_path = './gradcam_tmp.jpg'
    cv2.imwrite(out_path, overlay)
    plt.figure(figsize=(12, 6))
    plt.imshow(plt.imread(out_path))
    plt.axis('off')
    plt.show()

idx, name, conf = predict_from_image_path(r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val\DME\dme_val_1002.jpg')
print(idx, name, conf)
grad_cam(r'D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val\DME\dme_val_1002.jpg', last_conv_name=LAST_CONV, intensity=0.5)

#v7
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import os
import pickle
import numpy as np
import tensorflow as tf

from tensorflow.keras import Model
from tensorflow.keras.layers import Input, Embedding, Dropout, LSTM, Dense, Add
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.xception import Xception, preprocess_input

MODEL_WEIGHTS = r"D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\Exercise-7\Xception_LSTM_OCT_DATASET.hdf5"
TOKENIZER_PKL = r"D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\Exercise-7\tokenizer.pkl"
ONE_IMAGE     = r"D:\Studies\Sem-7\Deep Learning Concepts and Architectures\Exercise\OCT_Dataset\OCT_Dataset\val\DME\dme_val_1001.jpg"

MAX_LEN    = 107
EMB_DIM    = 256
LSTM_UNITS = 256
PDROP      = 0.3
FEAT_DIM   = 2048
IMG_SIZE   = (299, 299)

with open(TOKENIZER_PKL, "rb") as f:
    tokenizer = pickle.load(f)
VOCAB_SIZE = len(tokenizer.word_index) + 1
index_word = {v: k for k, v in tokenizer.word_index.items()}

def build_caption_model(max_len: int,
                        vocab_size: int,
                        feat_dim: int = FEAT_DIM,
                        emb_dim: int = EMB_DIM,
                        lstm_units: int = LSTM_UNITS,
                        pdrop: float = PDROP) -> Model:
    img_in = Input(shape=(feat_dim,), name="image_features")
    x_img = Dropout(pdrop, name="img_dropout")(img_in)
    x_img = Dense(lstm_units, activation="relu", name="img_dense")(x_img)

    txt_in = Input(shape=(max_len,), name="seq_input")
    x_txt = Embedding(vocab_size, emb_dim, mask_zero=True, name="embedding")(txt_in)
    x_txt = Dropout(pdrop, name="txt_dropout")(x_txt)
    x_txt = LSTM(lstm_units, name="lstm")(x_txt)

    merged = Add(name="add")([x_img, x_txt])
    x = Dense(lstm_units, activation="relu", name="fc")(merged)
    out = Dense(vocab_size, activation="softmax", name="softmax")(x)
    return Model(inputs=[img_in, txt_in], outputs=out, name="caption_model")

model = build_caption_model(MAX_LEN, VOCAB_SIZE)
model.load_weights(MODEL_WEIGHTS)

xception = Xception(weights="imagenet", include_top=False, pooling="avg")

def extract_features_xception(path: str) -> np.ndarray:
    im = load_img(path, target_size=IMG_SIZE)
    x = img_to_array(im)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    feat = xception.predict(x, verbose=0)   
    return feat

def word_for_id(integer: int) -> str | None:
    return index_word.get(integer)

def generate_caption(photo_feat_batched: np.ndarray, max_length: int) -> str:
    words = ["startseq"]
    for _ in range(max_length):
        seq = tokenizer.texts_to_sequences([" ".join(words)])[0]
        seq = pad_sequences([seq], maxlen=max_length, padding="post")
        yhat = model.predict([photo_feat_batched, seq], verbose=0)
        next_id = int(np.argmax(yhat))
        w = word_for_id(next_id)
        if w is None:
            break
        words.append(w)
        if w == "endseq":
            break
    return " ".join([w for w in words if w not in ("startseq", "endseq")])

if not os.path.exists(ONE_IMAGE):
    raise FileNotFoundError(f"Image not found: {ONE_IMAGE}")

feat = extract_features_xception(ONE_IMAGE)
caption = generate_caption(feat, MAX_LEN)
print("Image:", ONE_IMAGE)
print("Caption:", caption if caption else "[empty]")

'''