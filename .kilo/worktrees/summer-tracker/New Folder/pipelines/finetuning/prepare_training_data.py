# pipelines/finetuning/prepare_training_data.py
"""
Prepare Training Data for LoRA Fine-tuning
- Generate synthetic training pairs
- Extract from retrieval logs
- Active learning data selection
- Data augmentation
"""

import os
import json
import argparse
from pathlib import Path
import random
from collections import defaultdict
from typing import Dict, List, Any

# Add new imports
from pipelines.data_prep_advanced.data_augmentation import DataAugmenter, AugmentationStrategy
from pipelines.data_prep_advanced.labeling import LabelingService
from pipelines.data_prep_advanced.config import LabelingConfig

from pipelines._logging import setup_logger

log = setup_logger("data_prep")


class EmbeddingDataGenerator:
    """Generate training data for embedding models"""

    @staticmethod
    def from_retrieval_logs(
        log_file: str, corpus_file: str, min_clicks: int = 1
    ) -> Dict[str, List[str]]:
        """
        Extract training pairs from retrieval logs
        Format: {"query": "...", "clicked_docs": ["doc1", "doc2"], "timestamp": "..."}
        """

        qrels = defaultdict(list)

        for line in open(log_file, "r", encoding="utf-8"):
            log_entry = json.loads(line)

            query = log_entry.get("query")
            clicked = log_entry.get("clicked_docs", [])

            if query and len(clicked) >= min_clicks:
                qrels[query].extend(clicked)

        # Deduplicate
        qrels = {q: list(set(docs)) for q, docs in qrels.items()}

        log.info(f"Extracted {len(qrels)} queries from logs")
        return dict(qrels)

    @staticmethod
    def from_manual_annotations(annotation_file: str) -> Dict[str, List[str]]:
        """
        Load manually annotated query-document pairs
        Format: {"query": "...", "relevant_docs": ["doc1", "doc2"]}
        """

        qrels = {}

        for line in open(annotation_file, "r", encoding="utf-8"):
            ann = json.loads(line)
            query = ann.get("query")
            relevant = ann.get("relevant_docs", [])

            if query and relevant:
                qrels[query] = relevant

        log.info(f"Loaded {len(qrels)} annotated queries")
        return qrels

    @staticmethod
    def generate_synthetic_pairs(corpus_file: str, num_pairs: int = 1000) -> Dict[str, List[str]]:
        """
        Generate synthetic query-document pairs
        Using document summarization as queries
        """

        # Load corpus
        corpus = []
        for line in open(corpus_file, "r", encoding="utf-8"):
            corpus.append(json.loads(line))

        qrels = {}

        for _ in range(min(num_pairs, len(corpus))):
            doc = random.choice(corpus)

            # Use first sentence as query
            text = doc.get("text", "")
            sentences = text.split(".")
            if sentences:
                query = sentences[0].strip()
                if len(query) > 10:  # Minimum length
                    qrels[query] = [doc["id"]]

        log.info(f"Generated {len(qrels)} synthetic pairs")
        return qrels

    @staticmethod
    def augment_queries(
        qrels: Dict[str, List[str]], augmentation_factor: int = 2
    ) -> Dict[str, List[str]]:
        """
        Augment queries with paraphrases using the new advanced system
        """
        # Initialize the new data augmenter with advanced strategies
        augmenter = DataAugmenter([
            AugmentationStrategy.LEGAL_ENTITY_PRESERVING,
            AugmentationStrategy.CONTEXT_AWARE_PARAPHRASING,
            AugmentationStrategy.CATEGORY_BASED_AUGMENTATION
        ])
        
        augmented = {}
        
        for query, docs in qrels.items():
            # Original
            augmented[query] = docs
            
            # Generate augmentations using the new system
            augmentations = augmenter.augment(query, num_augmentations=augmentation_factor - 1)
            
            for aug_data in augmentations:
                aug_query = aug_data.augmented
                # Only use high-quality augmentations
                if aug_data.quality_score > 0.7:
                    augmented[aug_query] = docs
        
        log.info(f"Augmented to {len(augmented)} queries")
        return augmented


class NERDataGenerator:
    """Generate training data for NER models"""
    
    @staticmethod
    def from_annotations(annotation_file: str) -> List[Dict[str, Any]]:
        """
        Load NER annotations and enhance with the new labeling system
        Format: {"text": "...", "entities": [{"start": 0, "end": 5, "label": "PERSON"}]}
        """
        # Initialize the new labeling service
        config = LabelingConfig()
        labeling_service = LabelingService(config)
        
        examples = []
        
        for line in open(annotation_file, "r", encoding="utf-8"):
            ann = json.loads(line)
            
            text = ann.get("text", "")
            entities = ann.get("entities", [])
            
            # Use the new labeling system to enhance entity extraction
            try:
                # Process the text with the new system
                chunks = [{"text": text, "chunk_id": "1"}]
                import asyncio
                labeled_chunks = asyncio.run(labeling_service.label_chunks(chunks))
                
                if labeled_chunks:
                    # Get enhanced entities from the new system
                    enhanced_entities = labeled_chunks[0].get("entities", [])
                    
                    # Merge with original entities (prefer enhanced ones)
                    all_entities = {f"{e['start']}-{e['end']}": e for e in entities}
                    for e in enhanced_entities:
                        key = f"{e['start']}-{e['end']}"
                        if e.get("score", 0) > 0.8:  # Only use high-confidence entities
                            all_entities[key] = e
                    
                    # Convert to token-level labels
                    tokens = text.split()
                    ner_tags = ["O"] * len(tokens)
                    
                    # Map entities to tokens (simplified)
                    for entity in all_entities.values():
                        label = entity["label"]
                        start_char = entity["start"]
                        end_char = entity["end"]
                        
                        # Find token indices (simplified)
                        # In production, use proper tokenization
                        entity_text = text[start_char:end_char]
                        entity_tokens = entity_text.split()
                        
                        # Find position in tokens
                        for i, token in enumerate(tokens):
                            if token in entity_tokens:
                                if entity_tokens.index(token) == 0:
                                    ner_tags[i] = f"B-{label}"
                                else:
                                    ner_tags[i] = f"I-{label}"
                    
                    examples.append({"tokens": tokens, "ner_tags": ner_tags})
            except Exception as e:
                log.error(f"Error processing annotation: {e}")
                # Fallback to original processing
                tokens = text.split()
                ner_tags = ["O"] * len(tokens)
                
                # Map entities to tokens (simplified)
                for entity in entities:
                    label = entity["label"]
                    start_char = entity["start"]
                    end_char = entity["end"]
                    
                    # Find token indices (simplified)
                    entity_text = text[start_char:end_char]
                    entity_tokens = entity_text.split()
                    
                    # Find position in tokens
                    for i, token in enumerate(tokens):
                        if token in entity_tokens:
                            if entity_tokens.index(token) == 0:
                                ner_tags[i] = f"B-{label}"
                            else:
                                ner_tags[i] = f"I-{label}"
                
                examples.append({"tokens": tokens, "ner_tags": ner_tags})
        
        log.info(f"Loaded {len(examples)} NER examples")
        return examples
    
    @staticmethod
    def generate_from_patterns(num_examples: int = 100) -> List[Dict[str, Any]]:
        """Generate synthetic NER examples using patterns and enhance with labeling"""
        # Initialize the new labeling service
        config = LabelingConfig()
        labeling_service = LabelingService(config)
        
        # Patterns
        person_names = ["احمدی", "رضایی", "محمدی", "کریمی"]
        organizations = ["دادگاه", "شرکت", "سازمان", "وزارت"]
        locations = ["تهران", "اصفهان", "مشهد", "شیراز"]
        laws = ["ماده ۱۰", "قانون مدنی", "تبصره ۵"]
        
        templates = [
            {
                "pattern": ["آقای", "{PERSON}", "در", "{ORG}", "{LOC}", "حاضر", "شد"],
                "labels": ["O", "B-PERSON", "O", "B-ORG", "B-LOC", "O", "O"],
            },
            {
                "pattern": ["طبق", "{LAW}", "مقرر", "شده", "است"],
                "labels": ["O", "B-LAW", "O", "O", "O"],
            },
        ]
        
        examples = []
        
        for _ in range(num_examples):
            template = random.choice(templates)
            tokens = []
            ner_tags = []
            
            for token, label in zip(template["pattern"], template["labels"]):
                if "{PERSON}" in token:
                    tokens.append(random.choice(person_names))
                elif "{ORG}" in token:
                    tokens.append(random.choice(organizations))
                elif "{LOC}" in token:
                    tokens.append(random.choice(locations))
                elif "{LAW}" in token:
                    tokens.append(random.choice(laws))
                else:
                    tokens.append(token)
                
                ner_tags.append(label)
            
            examples.append({"tokens": tokens, "ner_tags": ner_tags})
        
        # Enhance with the new labeling system
        enhanced_examples = []
        for example in examples:
            text = " ".join(example["tokens"])
            
            try:
                # Process with the new labeling system
                chunks = [{"text": text, "chunk_id": "1"}]
                import asyncio
                labeled_chunks = asyncio.run(labeling_service.label_chunks(chunks))
                
                if labeled_chunks:
                    # Get entities from the new system
                    entities = labeled_chunks[0].get("entities", [])
                    
                    # Create enhanced example
                    enhanced_example = {
                        "tokens": example["tokens"],
                        "ner_tags": example["ner_tags"],
                        "enhanced_entities": entities
                    }
                    enhanced_examples.append(enhanced_example)
            except Exception as e:
                log.error(f"Error enhancing example: {e}")
                # Use original example
                enhanced_examples.append(example)
        
        log.info(f"Generated {len(enhanced_examples)} synthetic NER examples")
        return enhanced_examples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["embedding", "ner"])
    ap.add_argument("--source", required=True, choices=["logs", "annotations", "synthetic"])
    ap.add_argument("--input_file", help="Input file (logs/annotations)")
    ap.add_argument("--corpus_file", help="Corpus JSONL (for embedding task)")
    ap.add_argument("--output_file", required=True, help="Output file")
    ap.add_argument("--num_synthetic", type=int, default=1000, help="Number of synthetic examples")
    ap.add_argument("--augment", action="store_true", help="Apply data augmentation")
    args = ap.parse_args()

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.task == "embedding":
        # Generate embedding training data
        qrels = {}  # Initialize qrels
        if args.source == "logs":
            qrels = EmbeddingDataGenerator.from_retrieval_logs(args.input_file, args.corpus_file)
        elif args.source == "annotations":
            qrels = EmbeddingDataGenerator.from_manual_annotations(args.input_file)
        elif args.source == "synthetic":
            qrels = EmbeddingDataGenerator.generate_synthetic_pairs(
                args.corpus_file, num_pairs=args.num_synthetic
            )
            
        # Augment
        if args.augment:
            qrels = EmbeddingDataGenerator.augment_queries(qrels)
            
        # Save
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(qrels, f, ensure_ascii=False, indent=2)
            
        log.info(f"Saved {len(qrels)} query-document pairs to {output_path}")

    elif args.task == "ner":
        # Generate NER training data
        if args.source == "annotations":
            examples = NERDataGenerator.from_annotations(args.input_file)
        elif args.source == "synthetic":
            examples = NERDataGenerator.generate_from_patterns(num_examples=args.num_synthetic)
        else:
            raise ValueError("NER task only supports 'annotations' or 'synthetic' source")

        # Save
        with open(output_path, "w", encoding="utf-8") as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        log.info(f"Saved {len(examples)} NER examples to {output_path}")


if __name__ == "__main__":
    main()
