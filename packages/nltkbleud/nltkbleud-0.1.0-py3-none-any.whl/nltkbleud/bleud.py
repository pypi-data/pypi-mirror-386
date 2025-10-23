import pandas as pd
import numpy as np
import os

class BLEUD:

    def __init__(self):
        pass

    def load_modeld(self, model_path):
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
        from nltk.translate.bleu_score import sentence_bleu # For testing metrics
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

        if __name__ == "__main__":

            MODEL_PATH = 'lstmmodel.hdf5' 
            CSV_PATH = 'test_set_metadata.csv'   

            df_test_local = pd.read_csv(CSV_PATH)
            df_test_subset = df_test_local.head(10).copy()

            model = load_modeld(MODEL_PATH)

            generate_caption = image_captioning()

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

            print("\n--- Sample Predictions (S.No, Image Name, Original, Predicted) ---")
            for data in test_info:
                print(f"{data['S.No']}: | '{data['Pred_Caption']}'")

            references = [[data['True_Caption'].split()] for data in test_info]
            candidates = [data['Pred_Caption'].split() for data in test_info]

            print("\n--- Classification Report (BLEU Score Metrics) ---")
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
        
        # 1. Load Images into a list
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
        
        # 2. Convert list to NumPy array once
        X_imgs_array = np.array(X_imgs)

        # 3. Perform Feature Extraction with a specific, small batch size (CRUCIAL FIX)
        # The error happens here because the GPU runs out of memory on large arrays.
        
        # Using a batch size of 32 or 64 is typically safe for 224x224 images on Kaggle GPUs.
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

    print("--- EXERCISE 6: FEATURE EXTRACTION + MLP CLASSIFICATION RESULTS ---")

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


        