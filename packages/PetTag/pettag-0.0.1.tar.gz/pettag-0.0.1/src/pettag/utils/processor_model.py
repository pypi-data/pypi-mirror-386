from pettag.utils.logging_setup import get_logger

logger = get_logger()
from sentence_transformers import SentenceTransformer
from tqdm.contrib.logging import logging_redirect_tqdm
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re


import re
import numpy as np
import faiss
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from tqdm.contrib.logging import logging_redirect_tqdm
import logging

logger = logging.getLogger(__name__)

class ModelProcessor:
    def __init__(
        self,
        model: str,
        tokenizer: str = None,
        replaced: bool = True,
        text_column: str = "text",
        label_column: str = "ICD_11_code",
        disease_code_lookup=None,  # HuggingFace dataset, not pandas
        embedding_model=None,
        device: str = "cpu",
    ):
        self.model = model
        self.replaced = replaced
        self.text_column = text_column
        self.label_column = label_column
        self.device = device
        self.disease_code_lookup = disease_code_lookup
        self.ner_pipeline = model
        self.embedding_model = embedding_model

        # Placeholders for FAISS index and precomputed values
        self.faiss_index = None
        self.normalized_embeddings = None
        self.parent_to_subcodes = None
        
        # initialize disease coder if lookup is provided
        self.initialize_disease_coder()

    # ------------------------------------------------------------------ #
    #  INITIALIZATION
    # ------------------------------------------------------------------ #
    def initialize_disease_coder(self):
        """Precompute FAISS index and parent→subcode map for fast lookups."""
        if self.disease_code_lookup is None:
            raise ValueError("disease_code_lookup must be set before initialization.")

        logger.info("Initializing FAISS index and subcode mappings...")

        # 1️⃣ Extract and normalize embeddings
        embeddings = np.vstack(self.disease_code_lookup["embeddings"]).astype("float32")
        faiss.normalize_L2(embeddings)
        self.normalized_embeddings = embeddings

        # 2️⃣ Build FAISS index (cosine similarity = inner product after normalization)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        self.faiss_index = index

        # 3️⃣ Precompute parent→subcode mapping
        self.parent_to_subcodes = defaultdict(list)
        for i, code in enumerate(self.disease_code_lookup["Code"]):
            parent = code.split(".")[0]
            self.parent_to_subcodes[parent].append(i)

        logger.info("FAISS index and mappings ready.")

    # ------------------------------------------------------------------ #
    #  ENTITY EXTRACTION
    # ------------------------------------------------------------------ #
    @staticmethod
    def model_extractions(petbert_disease_out):
        disease_out, pathogen_out, symptom_out = [], [], []
        output = []
        for entity in petbert_disease_out[0]:
            start = entity["start"]
            end = entity["end"]
            label = entity["entity_group"]
            output.append((start, end, label))
            if label == "DISEASE":
                disease_out.append(entity["word"])
            elif label == "SYMPTOM":
                symptom_out.append(entity["word"])
            elif label == "ETIOLOGY":
                pathogen_out.append(entity["word"])
        return list(set(disease_out)), list(set(pathogen_out)), list(set(symptom_out))

    # ------------------------------------------------------------------ #
    #  FAST ICD CODER
    # ------------------------------------------------------------------ #
    def disease_coder(self, disease: str, Z_BOOST: float = 0.06, k: int = 10):
        """
        Retrieve the best-matching ICD code for a disease name using FAISS.
        Uses pre-built FAISS index + parent→subcode map for subcode refinement.
        """
        if self.faiss_index is None:
            raise RuntimeError("FAISS index not initialized. Call initialize_disease_coder() first.")

        # --- Step 1 : Encode and normalize input disease ---
        encoded = self.embedding_model.encode(disease).astype("float32").reshape(1, -1)
        faiss.normalize_L2(encoded)

        # --- Step 2 : Retrieve top-k most similar codes ---
        scores, indices = self.faiss_index.search(encoded, k)
        scores, indices = scores[0], indices[0]

        # --- Step 3 : Pick best match from FAISS search ---
        top_idx = int(indices[0])
        top_entry = self.disease_code_lookup[top_idx]
        top_code = top_entry["Code"]
        top_title = top_entry["Title"]
        top_score = float(scores[0])

        parent_code = top_code.split(".")[0]
        final_entry = top_entry
        final_score = top_score

        # --- Step 4 : Refine within subcodes if this is a parent code ---
        sub_idx_list = self.parent_to_subcodes.get(parent_code, [])
        if sub_idx_list and top_code == parent_code:
            sub_embeddings = self.normalized_embeddings[sub_idx_list]
            sub_scores = np.dot(sub_embeddings, encoded.squeeze())  # cosine similarity

            # Apply .Z boost
            for j, idx in enumerate(sub_idx_list):
                code = self.disease_code_lookup[idx]["Code"]
                if code.endswith(".Z"):
                    sub_scores[j] += Z_BOOST

            best_sub_idx = int(np.argmax(sub_scores))
            final_entry = self.disease_code_lookup[sub_idx_list[best_sub_idx]]
            final_score = float(sub_scores[best_sub_idx])

        # --- Step 5 : Return final structured result ---
        return {
            "Input Disease": disease,
            "Code": final_entry["Code"],
            "Title": final_entry["Title"],
            "ChapterNo": final_entry["ChapterNo"],
            "Foundation URI": final_entry["URI"],
            "Similarity": final_score,
        }

    # ------------------------------------------------------------------ #
    #  DATASET PROCESSING
    # ------------------------------------------------------------------ #
    def _process_batch(self, examples):
        original_texts = examples[self.text_column]
        lower_texts = [str(text).lower() for text in original_texts]

        # Run NER
        ner_results = self.ner_pipeline(lower_texts)

        # Extract entities
        disease_preds, pathogen_preds, symptom_preds = self.model_extractions(ner_results)

        # Encode diseases
        coded_diseases = []
        for diseases in disease_preds:
            codes = [self.disease_coder(disease) for disease in diseases]
            coded_diseases.append(codes)

        return {
            "disease_extraction": coded_diseases,
            "symptom_extraction": symptom_preds,
            "pathogen_extraction": pathogen_preds,
            self.label_column: coded_diseases,
        }

    # ------------------------------------------------------------------ #
    #  MAIN PREDICTION ENTRY POINT
    # ------------------------------------------------------------------ #
    def predict(self, dataset):
        """Apply NER + ICD coding to a HuggingFace dataset."""
        date_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        with logging_redirect_tqdm():
            processed_dataset = dataset.map(
                self._process_batch,
                batched=True,
                desc=f"[{date_time} | INFO | PetHarbor-Advance]",
            )
        logger.info("Predictions obtained and text coded successfully.")
        return processed_dataset
