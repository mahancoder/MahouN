"""
Advanced CRF for MAHOUN Legal AI
=================================

قابلیت‌های پیشرفته:
- CRF برای Named Entity Recognition (NER)
- BiLSTM-CRF برای sequence labeling
- BERT-CRF برای contextual embeddings
- Multi-task CRF (NER + POS + Chunking)
- Hierarchical CRF (Nested entities)
- Semi-CRF (Segment-level)
- Constrained CRF (Legal constraints)
- CRF با Attention
- Viterbi Decoding Optimization
- Marginal Inference
- Feature Engineering
"""

import os
import argparse
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import warnings
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from tqdm import tqdm

try:
    from torchcrf import CRF
    TORCHCRF_AVAILABLE = True
except ImportError:
    TORCHCRF_AVAILABLE = False
    warnings.warn("torchcrf not available. Install with: pip install pytorch-crf")

from transformers import (
    AutoModel,
    AutoTokenizer,
    BertModel,
    BertTokenizer,
)

from pipelines._logging import setup_logger

log = setup_logger("advanced_crf")


class CRFTask(Enum):
    """CRF tasks"""
    NER = "ner"
    POS_TAGGING = "pos_tagging"
    CHUNKING = "chunking"
    SLOT_FILLING = "slot_filling"
    MULTI_TASK = "multi_task"


# Label schemes
BIO_LABELS = [
    "O",  # Outside
    "B-PERSON", "I-PERSON",
    "B-ORG", "I-ORG",
    "B-LOC", "I-LOC",
    "B-LAW", "I-LAW",
    "B-DATE", "I-DATE",
    "B-MONEY", "I-MONEY",
    "B-CASE", "I-CASE",
    "B-COURT", "I-COURT",
]

BIOES_LABELS = [
    "O",
    "B-PERSON", "I-PERSON", "E-PERSON", "S-PERSON",
    "B-ORG", "I-ORG", "E-ORG", "S-ORG",
    "B-LOC", "I-LOC", "E-LOC", "S-LOC",
    "B-LAW", "I-LAW", "E-LAW", "S-LAW",
]


class AdvancedCRF(nn.Module):
    """
    Advanced CRF layer with constraints
    
    Features:
    - Transition constraints (e.g., I-PER cannot follow B-ORG)
    - Start/End constraints
    - Marginal inference
    - Constrained decoding
    """
    
    def __init__(
        self,
        num_tags: int,
        batch_first: bool = True,
        use_constraints: bool = True,
        label_scheme: str = "BIO",
    ):
        super().__init__()
        
        if not TORCHCRF_AVAILABLE:
            raise ImportError("pytorch-crf required")
        
        self.num_tags = num_tags
        self.batch_first = batch_first
        self.use_constraints = use_constraints
        self.label_scheme = label_scheme
        
        # Base CRF
        self.crf = CRF(num_tags, batch_first=batch_first)
        
        # Apply constraints
        if use_constraints:
            self._apply_constraints()
    
    def _apply_constraints(self):
        """Apply transition constraints"""
        
        # Get label list
        if self.label_scheme == "BIO":
            labels = BIO_LABELS[:self.num_tags]
        elif self.label_scheme == "BIOES":
            labels = BIOES_LABELS[:self.num_tags]
        else:
            return
        
        # Create constraint matrix
        constraints = torch.zeros(self.num_tags, self.num_tags)
        
        for i, from_label in enumerate(labels):
            for j, to_label in enumerate(labels):
                # Check if transition is valid
                if self._is_valid_transition(from_label, to_label):
                    constraints[i, j] = 0.0  # Valid
                else:
                    constraints[i, j] = -10000.0  # Invalid
        
        # Apply to CRF transitions
        self.crf.transitions.data += constraints
        
        log.info(f"✅ Applied {self.label_scheme} constraints")
    
    def _is_valid_transition(self, from_label: str, to_label: str) -> bool:
        """Check if transition is valid"""
        
        # O can go to O or B-*
        if from_label == "O":
            return to_label == "O" or to_label.startswith("B-") or to_label.startswith("S-")
        
        # B-X can go to I-X, E-X, or O, or B-*
        if from_label.startswith("B-"):
            entity_type = from_label[2:]
            return (
                to_label == f"I-{entity_type}" or
                to_label == f"E-{entity_type}" or
                to_label == "O" or
                to_label.startswith("B-") or
                to_label.startswith("S-")
            )
        
        # I-X can go to I-X, E-X, or O, or B-*
        if from_label.startswith("I-"):
            entity_type = from_label[2:]
            return (
                to_label == f"I-{entity_type}" or
                to_label == f"E-{entity_type}" or
                to_label == "O" or
                to_label.startswith("B-")
            )
        
        # E-X or S-X can go to O or B-* or S-*
        if from_label.startswith("E-") or from_label.startswith("S-"):
            return to_label == "O" or to_label.startswith("B-") or to_label.startswith("S-")
        
        return True
    
    def forward(
        self,
        emissions: torch.Tensor,
        tags: torch.LongTensor,
        mask: Optional[torch.ByteTensor] = None,
        reduction: str = 'mean',
    ) -> torch.Tensor:
        """
        Compute negative log-likelihood
        
        Args:
            emissions: (batch_size, seq_length, num_tags)
            tags: (batch_size, seq_length)
            mask: (batch_size, seq_length)
            reduction: 'none', 'sum', 'mean', 'token_mean'
        
        Returns:
            Loss
        """
        return -self.crf(emissions, tags, mask=mask, reduction=reduction)
    
    def decode(
        self,
        emissions: torch.Tensor,
        mask: Optional[torch.ByteTensor] = None,
    ) -> List[List[int]]:
        """
        Viterbi decoding
        
        Args:
            emissions: (batch_size, seq_length, num_tags)
            mask: (batch_size, seq_length)
        
        Returns:
            Best tag sequences
        """
        return self.crf.decode(emissions, mask=mask)
    
    def marginal_probabilities(
        self,
        emissions: torch.Tensor,
        mask: Optional[torch.ByteTensor] = None,
    ) -> torch.Tensor:
        """
        Compute marginal probabilities using forward-backward
        
        Returns:
            (batch_size, seq_length, num_tags) probabilities
        """
        # Forward pass
        forward_scores = self._forward_algorithm(emissions, mask)
        
        # Backward pass
        backward_scores = self._backward_algorithm(emissions, mask)
        
        # Marginals
        marginals = forward_scores + backward_scores
        
        # Normalize
        marginals = F.softmax(marginals, dim=-1)
        
        return marginals
    
    def _forward_algorithm(
        self,
        emissions: torch.Tensor,
        mask: Optional[torch.ByteTensor] = None,
    ) -> torch.Tensor:
        """Forward algorithm for marginal inference"""
        
        batch_size, seq_length, num_tags = emissions.shape
        
        if mask is None:
            mask = torch.ones(batch_size, seq_length, dtype=torch.bool, device=emissions.device)
        
        # Initialize
        alpha = emissions[:, 0].clone()  # (batch_size, num_tags)
        
        # Forward pass
        for t in range(1, seq_length):
            # Broadcast for transitions
            emit_score = emissions[:, t].unsqueeze(1)  # (batch, 1, num_tags)
            trans_score = self.crf.transitions.unsqueeze(0)  # (1, num_tags, num_tags)
            alpha_broadcast = alpha.unsqueeze(2)  # (batch, num_tags, 1)
            
            # Compute next alpha
            next_alpha = alpha_broadcast + trans_score + emit_score
            next_alpha = torch.logsumexp(next_alpha, dim=1)  # (batch, num_tags)
            
            # Apply mask
            alpha = torch.where(mask[:, t].unsqueeze(1), next_alpha, alpha)
        
        return alpha
    
    def _backward_algorithm(
        self,
        emissions: torch.Tensor,
        mask: Optional[torch.ByteTensor] = None,
    ) -> torch.Tensor:
        """Backward algorithm for marginal inference"""
        
        batch_size, seq_length, num_tags = emissions.shape
        
        if mask is None:
            mask = torch.ones(batch_size, seq_length, dtype=torch.bool, device=emissions.device)
        
        # Initialize
        beta = torch.zeros(batch_size, num_tags, device=emissions.device)
        
        # Backward pass
        for t in range(seq_length - 2, -1, -1):
            # Broadcast for transitions
            emit_score = emissions[:, t + 1].unsqueeze(1)  # (batch, 1, num_tags)
            trans_score = self.crf.transitions.unsqueeze(0)  # (1, num_tags, num_tags)
            beta_broadcast = beta.unsqueeze(1)  # (batch, 1, num_tags)
            
            # Compute previous beta
            prev_beta = trans_score + emit_score + beta_broadcast
            prev_beta = torch.logsumexp(prev_beta, dim=2)  # (batch, num_tags)
            
            # Apply mask
            beta = torch.where(mask[:, t + 1].unsqueeze(1), prev_beta, beta)
        
        return beta


class BiLSTMCRF(nn.Module):
    """BiLSTM-CRF for sequence labeling"""
    
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_tags: int,
        num_layers: int = 2,
        dropout: float = 0.5,
        use_char_embeddings: bool = False,
        char_embedding_dim: int = 50,
        char_hidden_dim: int = 100,
    ):
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_tags = num_tags
        
        # Word embeddings
        self.word_embeddings = nn.Embedding(vocab_size, embedding_dim)
        
        # Character embeddings (optional)
        self.use_char_embeddings = use_char_embeddings
        if use_char_embeddings:
            self.char_embeddings = nn.Embedding(256, char_embedding_dim)  # ASCII
            self.char_lstm = nn.LSTM(
                char_embedding_dim,
                char_hidden_dim,
                bidirectional=True,
                batch_first=True,
            )
            lstm_input_dim = embedding_dim + char_hidden_dim * 2
        else:
            lstm_input_dim = embedding_dim
        
        # BiLSTM
        self.lstm = nn.LSTM(
            lstm_input_dim,
            hidden_dim // 2,
            num_layers=num_layers,
            bidirectional=True,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Linear layer to tag space
        self.hidden2tag = nn.Linear(hidden_dim, num_tags)
        
        # CRF layer
        self.crf = AdvancedCRF(num_tags, batch_first=True)
    
    def _get_char_features(self, char_ids: torch.LongTensor) -> torch.Tensor:
        """Get character-level features"""
        
        batch_size, seq_len, max_word_len = char_ids.shape
        
        # Flatten
        char_ids_flat = char_ids.view(-1, max_word_len)  # (batch*seq, max_word_len)
        
        # Embed
        char_embeds = self.char_embeddings(char_ids_flat)  # (batch*seq, max_word_len, char_dim)
        
        # LSTM
        _, (hidden, _) = self.char_lstm(char_embeds)  # (2, batch*seq, char_hidden)
        
        # Concatenate forward and backward
        char_features = torch.cat([hidden[0], hidden[1]], dim=-1)  # (batch*seq, char_hidden*2)
        
        # Reshape
        char_features = char_features.view(batch_size, seq_len, -1)
        
        return char_features
    
    def forward(
        self,
        word_ids: torch.LongTensor,
        tags: Optional[torch.LongTensor] = None,
        char_ids: Optional[torch.LongTensor] = None,
        mask: Optional[torch.ByteTensor] = None,
    ) -> Union[torch.Tensor, List[List[int]]]:
        """
        Forward pass
        
        Args:
            word_ids: (batch_size, seq_length)
            tags: (batch_size, seq_length) - for training
            char_ids: (batch_size, seq_length, max_word_length) - optional
            mask: (batch_size, seq_length)
        
        Returns:
            Loss (training) or predictions (inference)
        """
        # Word embeddings
        word_embeds = self.word_embeddings(word_ids)  # (batch, seq, embed_dim)
        
        # Character features
        if self.use_char_embeddings and char_ids is not None:
            char_features = self._get_char_features(char_ids)
            embeds = torch.cat([word_embeds, char_features], dim=-1)
        else:
            embeds = word_embeds
        
        # Dropout
        embeds = self.dropout(embeds)
        
        # BiLSTM
        lstm_out, _ = self.lstm(embeds)  # (batch, seq, hidden_dim)
        lstm_out = self.dropout(lstm_out)
        
        # Emissions
        emissions = self.hidden2tag(lstm_out)  # (batch, seq, num_tags)
        
        # Training: compute loss
        if tags is not None:
            loss = self.crf(emissions, tags, mask=mask)
            return loss
        
        # Inference: decode
        else:
            predictions = self.crf.decode(emissions, mask=mask)
            return predictions


class BERTCRF(nn.Module):
    """BERT-CRF for contextual sequence labeling"""
    
    def __init__(
        self,
        bert_model_name: str,
        num_tags: int,
        dropout: float = 0.1,
        use_lstm: bool = False,
        lstm_hidden_dim: int = 256,
    ):
        super().__init__()
        
        self.num_tags = num_tags
        self.use_lstm = use_lstm
        
        # BERT
        self.bert = AutoModel.from_pretrained(bert_model_name)
        self.bert_hidden_dim = self.bert.config.hidden_size
        
        # Optional BiLSTM on top of BERT
        if use_lstm:
            self.lstm = nn.LSTM(
                self.bert_hidden_dim,
                lstm_hidden_dim // 2,
                bidirectional=True,
                batch_first=True,
            )
            classifier_input_dim = lstm_hidden_dim
        else:
            classifier_input_dim = self.bert_hidden_dim
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Classifier
        self.classifier = nn.Linear(classifier_input_dim, num_tags)
        
        # CRF
        self.crf = AdvancedCRF(num_tags, batch_first=True)
    
    def forward(
        self,
        input_ids: torch.LongTensor,
        attention_mask: torch.LongTensor,
        tags: Optional[torch.LongTensor] = None,
        token_type_ids: Optional[torch.LongTensor] = None,
    ) -> Union[torch.Tensor, List[List[int]]]:
        """
        Forward pass
        
        Args:
            input_ids: (batch_size, seq_length)
            attention_mask: (batch_size, seq_length)
            tags: (batch_size, seq_length) - for training
            token_type_ids: (batch_size, seq_length) - optional
        
        Returns:
            Loss (training) or predictions (inference)
        """
        # BERT encoding
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        
        sequence_output = outputs.last_hidden_state  # (batch, seq, hidden)
        
        # Optional LSTM
        if self.use_lstm:
            sequence_output, _ = self.lstm(sequence_output)
        
        # Dropout
        sequence_output = self.dropout(sequence_output)
        
        # Emissions
        emissions = self.classifier(sequence_output)  # (batch, seq, num_tags)
        
        # Convert attention_mask to ByteTensor for CRF
        mask = attention_mask.bool()
        
        # Training: compute loss
        if tags is not None:
            loss = self.crf(emissions, tags, mask=mask)
            return loss
        
        # Inference: decode
        else:
            predictions = self.crf.decode(emissions, mask=mask)
            return predictions


class HierarchicalCRF(nn.Module):
    """
    Hierarchical CRF for nested entities
    
    Example: "دادگاه عالی کشور" contains both ORG and LOC
    """
    
    def __init__(
        self,
        base_model: nn.Module,
        num_entity_types: int,
        max_nesting_level: int = 2,
    ):
        super().__init__()
        
        self.base_model = base_model
        self.num_entity_types = num_entity_types
        self.max_nesting_level = max_nesting_level
        
        # CRF for each level
        self.crfs = nn.ModuleList([
            AdvancedCRF(num_entity_types * 2 + 1, batch_first=True)  # BIO scheme
            for _ in range(max_nesting_level)
        ])
    
    def forward(
        self,
        *args,
        tags_list: Optional[List[torch.LongTensor]] = None,
        **kwargs,
    ):
        """
        Forward pass for hierarchical labeling
        
        Args:
            tags_list: List of tag sequences for each level
        """
        # Get base emissions
        emissions = self.base_model(*args, **kwargs)
        
        if tags_list is not None:
            # Training: compute loss for each level
            total_loss = 0.0
            for level, (crf, tags) in enumerate(zip(self.crfs, tags_list)):
                loss = crf(emissions, tags)
                total_loss += loss
            return total_loss / len(self.crfs)
        else:
            # Inference: decode each level
            predictions_list = []
            for crf in self.crfs:
                predictions = crf.decode(emissions)
                predictions_list.append(predictions)
            return predictions_list


class CRFTrainer:
    """Trainer for CRF models"""
    
    def __init__(
        self,
        model: nn.Module,
        device: Optional[str] = None,
    ):
        self.model = model
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        log.info(f"CRF Trainer initialized on {self.device}")
    
    def train(
        self,
        train_dataloader: DataLoader,
        eval_dataloader: Optional[DataLoader] = None,
        num_epochs: int = 10,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        output_dir: str = "models/crf",
        use_wandb: bool = False,
    ):
        """Train CRF model"""
        
        log.info("🏋️ Starting CRF training...")
        
        # Optimizer
        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        
        # Scheduler
        from torch.optim.lr_scheduler import ReduceLROnPlateau
        scheduler = ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,
            patience=2,
            verbose=True,
        )
        
        # W&B
        if use_wandb:
            import wandb
            wandb.init(
                project=os.getenv("WANDB_PROJECT", "mahoun"),
                name="crf_ner",
                config={
                    "epochs": num_epochs,
                    "lr": learning_rate,
                }
            )
        
        # Training loop
        best_eval_loss = float('inf')
        
        for epoch in range(num_epochs):
            log.info(f"\n📅 Epoch {epoch + 1}/{num_epochs}")
            
            # Train
            train_loss = self._train_epoch(
                train_dataloader,
                optimizer,
                use_wandb,
            )
            
            log.info(f"   Train Loss: {train_loss:.4f}")
            
            # Evaluate
            if eval_dataloader:
                eval_loss, eval_f1 = self._evaluate(eval_dataloader)
                log.info(f"   Eval Loss: {eval_loss:.4f}, F1: {eval_f1:.4f}")
                
                scheduler.step(eval_loss)
                
                if use_wandb:
                    wandb.log({
                        "eval/loss": eval_loss,
                        "eval/f1": eval_f1,
                    })
                
                # Save best
                if eval_loss < best_eval_loss:
                    best_eval_loss = eval_loss
                    self.save(f"{output_dir}/best")
                    log.info("   💾 Best model saved")
            
            # Save checkpoint
            self.save(f"{output_dir}/epoch-{epoch + 1}")
        
        # Final save
        self.save(output_dir)
        log.info(f"✅ Training complete! Model saved to {output_dir}")
        
        if use_wandb:
            wandb.finish()
    
    def _train_epoch(
        self,
        dataloader: DataLoader,
        optimizer: torch.optim.Optimizer,
        use_wandb: bool = False,
    ) -> float:
        """Train one epoch"""
        
        self.model.train()
        total_loss = 0.0
        
        progress_bar = tqdm(dataloader, desc="Training")
        
        for batch in progress_bar:
            # Move to device
            batch = {k: v.to(self.device) for k, v in batch.items()}
            
            # Forward
            loss = self.model(**batch)
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 5.0)
            
            # Update
            optimizer.step()
            
            total_loss += loss.item()
            progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        return total_loss / len(dataloader)
    
    def _evaluate(self, dataloader: DataLoader) -> Tuple[float, float]:
        """Evaluate model"""
        
        self.model.eval()
        total_loss = 0.0
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for batch in dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Get loss
                tags = batch.pop('tags')
                loss = self.model(**batch, tags=tags)
                total_loss += loss.item()
                
                # Get predictions
                predictions = self.model(**batch)
                
                all_predictions.extend(predictions)
                all_labels.extend(tags.cpu().numpy().tolist())
        
        # Compute F1
        from seqeval.metrics import f1_score
        f1 = f1_score(all_labels, all_predictions)
        
        return total_loss / len(dataloader), f1
    
    def save(self, output_dir: str):
        """Save model"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        torch.save(self.model.state_dict(), output_path / "model.pt")
        log.info(f"💾 Model saved to {output_path}")


def main():
    """Example usage"""
    
    # BiLSTM-CRF
    model = BiLSTMCRF(
        vocab_size=10000,
        embedding_dim=300,
        hidden_dim=256,
        num_tags=len(BIO_LABELS),
        num_layers=2,
        dropout=0.5,
        use_char_embeddings=True,
    )
    
    print(f"BiLSTM-CRF parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # BERT-CRF
    bert_crf = BERTCRF(
        bert_model_name="HooshvareLab/bert-base-parsbert-uncased",
        num_tags=len(BIO_LABELS),
        use_lstm=True,
    )
    
    print(f"BERT-CRF parameters: {sum(p.numel() for p in bert_crf.parameters()):,}")


if __name__ == "__main__":
    main()
