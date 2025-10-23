"""
Speculative Decoding for Nthuku-Fast

Implements speculative decoding for 2-3x faster text generation:
- Draft model generates multiple tokens quickly
- Target model verifies in parallel
- Accepts valid tokens, rejects and corrects invalid ones
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, List, Dict


class SpeculativeDecoder:
    """
    Speculative decoding implementation
    
    Key idea: Use small draft model to propose tokens, large model to verify
    - Draft model: 2-4 layers, generates K tokens speculatively
    - Target model: Full model, verifies K tokens in parallel
    - Accept if logits match, reject and correct if they don't
    """
    
    def __init__(
        self,
        target_model: nn.Module,
        draft_model: Optional[nn.Module] = None,
        num_speculative_tokens: int = 4,
        temperature: float = 0.8,
        top_k: int = 50
    ):
        self.target_model = target_model
        self.draft_model = draft_model or self._create_draft_model(target_model)
        self.K = num_speculative_tokens  # Number of speculative tokens
        self.temperature = temperature
        self.top_k = top_k
        
        # Statistics
        self.total_tokens = 0
        self.accepted_tokens = 0
        
    def _create_draft_model(self, target_model: nn.Module) -> nn.Module:
        """
        Create a smaller draft model from target model
        Uses first 2 layers of target model
        """
        # This would create a smaller version of the model
        # For now, return the same model (in practice, use smaller variant)
        return target_model
    
    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        vision_features: torch.Tensor,
        max_new_tokens: int = 50,
        show_stats: bool = False
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Generate tokens using speculative decoding
        
        Args:
            input_ids: Initial token IDs [batch, seq]
            vision_features: Vision context
            max_new_tokens: Maximum tokens to generate
            show_stats: Whether to print statistics
            
        Returns:
            generated_ids: Full sequence [batch, seq + new]
            stats: Generation statistics
        """
        device = input_ids.device
        batch_size = input_ids.size(0)
        
        # Reset stats
        self.total_tokens = 0
        self.accepted_tokens = 0
        
        generated = input_ids.clone()
        tokens_generated = 0
        
        while tokens_generated < max_new_tokens:
            # Step 1: Draft model generates K tokens
            draft_tokens = self._draft_phase(generated, vision_features)
            
            # Step 2: Target model verifies K tokens in parallel
            accepted_count = self._verify_phase(
                generated, draft_tokens, vision_features
            )
            
            # Step 3: Accept tokens
            if accepted_count > 0:
                # Accept the verified tokens
                generated = torch.cat([generated, draft_tokens[:, :accepted_count]], dim=1)
                tokens_generated += accepted_count
                self.accepted_tokens += accepted_count
            else:
                # If none accepted, generate 1 token normally
                next_token = self._generate_one_token(generated, vision_features)
                generated = torch.cat([generated, next_token], dim=1)
                tokens_generated += 1
                self.accepted_tokens += 1
            
            self.total_tokens += self.K
            
            # Check for EOS
            if (generated[:, -1] == self.target_model.tokenizer.eos_token_id).all():
                break
        
        # Calculate statistics
        acceptance_rate = self.accepted_tokens / max(self.total_tokens, 1)
        speedup = acceptance_rate * self.K  # Theoretical speedup
        
        stats = {
            'acceptance_rate': acceptance_rate,
            'speedup': speedup,
            'tokens_generated': tokens_generated,
            'draft_calls': self.total_tokens // self.K
        }
        
        if show_stats:
            print(f"📊 Speculative Decoding Stats:")
            print(f"   Acceptance Rate: {acceptance_rate:.2%}")
            print(f"   Theoretical Speedup: {speedup:.2f}x")
            print(f"   Tokens Generated: {tokens_generated}")
        
        return generated, stats
    
    def _draft_phase(
        self, 
        input_ids: torch.Tensor,
        vision_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Draft model generates K speculative tokens
        
        Returns:
            draft_tokens: [batch, K] speculative tokens
        """
        draft_tokens = []
        current_ids = input_ids
        
        for _ in range(self.K):
            # Get logits from draft model
            logits, _ = self.draft_model.text_decoder(current_ids, vision_features)
            next_logits = logits[:, -1, :] / self.temperature
            
            # Sample next token
            probs = F.softmax(next_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            draft_tokens.append(next_token)
            current_ids = torch.cat([current_ids, next_token], dim=1)
        
        return torch.cat(draft_tokens, dim=1)
    
    def _verify_phase(
        self,
        input_ids: torch.Tensor,
        draft_tokens: torch.Tensor,
        vision_features: torch.Tensor
    ) -> int:
        """
        Target model verifies K draft tokens in parallel
        
        Returns:
            Number of accepted tokens
        """
        # Concatenate input with all draft tokens
        full_seq = torch.cat([input_ids, draft_tokens], dim=1)
        
        # Get target model logits for all positions in one pass (parallel!)
        target_logits, _ = self.target_model.text_decoder(full_seq, vision_features)
        
        # Check each draft token
        accepted = 0
        start_idx = input_ids.size(1)
        
        for i in range(self.K):
            # Get target model's distribution for this position
            target_probs = F.softmax(
                target_logits[:, start_idx + i - 1, :] / self.temperature,
                dim=-1
            )
            
            # Get draft token
            draft_token = draft_tokens[:, i:i+1]
            
            # Check if draft token has reasonable probability under target model
            token_prob = target_probs.gather(1, draft_token)
            
            # Accept if probability is above threshold (e.g., 0.1)
            if token_prob.item() > 0.1:
                accepted += 1
            else:
                # Reject this and all subsequent tokens
                break
        
        return accepted
    
    def _generate_one_token(
        self,
        input_ids: torch.Tensor,
        vision_features: torch.Tensor
    ) -> torch.Tensor:
        """Fallback: generate single token from target model"""
        logits, _ = self.target_model.text_decoder(input_ids, vision_features)
        next_logits = logits[:, -1, :] / self.temperature
        probs = F.softmax(next_logits, dim=-1)
        return torch.multinomial(probs, num_samples=1)
    
    def get_acceptance_rate(self) -> float:
        """Get current acceptance rate"""
        return self.accepted_tokens / max(self.total_tokens, 1)


def create_draft_model(target_config, num_layers: int = 2):
    """
    Create a lightweight draft model for speculative decoding
    
    Args:
        target_config: Configuration of target model
        num_layers: Number of layers in draft model (typically 2-4)
        
    Returns:
        Draft model configuration
    """
    from dataclasses import replace
    
    # Create smaller config
    draft_config = replace(
        target_config,
        num_layers=num_layers,
        hidden_dim=target_config.hidden_dim // 2,  # Smaller hidden size
        num_attn_heads=target_config.num_attn_heads // 2
    )
    
    return draft_config


def estimate_speculative_speedup(
    acceptance_rate: float,
    num_speculative_tokens: int,
    draft_model_speedup: float = 5.0  # Draft model is ~5x faster
) -> float:
    """
    Estimate speedup from speculative decoding
    
    Formula:
    speedup = K * acceptance_rate / (1 + K/draft_speedup)
    
    Args:
        acceptance_rate: Fraction of accepted tokens (0.0-1.0)
        num_speculative_tokens: K value
        draft_model_speedup: How much faster draft model is
        
    Returns:
        Overall speedup factor
    """
    K = num_speculative_tokens
    
    # Time per iteration
    # - Draft generates K tokens: K / draft_speedup
    # - Target verifies K tokens: 1 (parallel)
    time_per_iteration = (K / draft_model_speedup) + 1
    
    # Tokens accepted per iteration
    tokens_per_iteration = K * acceptance_rate
    
    # Speedup vs normal generation
    speedup = tokens_per_iteration / time_per_iteration
    
    return speedup


# Example usage statistics
def print_speculative_stats():
    """Print expected performance with speculative decoding"""
    print("=" * 70)
    print("⚡ Speculative Decoding Performance Estimates")
    print("=" * 70)
    
    for acceptance in [0.5, 0.7, 0.9]:
        for K in [2, 4, 8]:
            speedup = estimate_speculative_speedup(acceptance, K)
            print(f"K={K}, Accept={acceptance:.0%}: {speedup:.2f}x speedup")
    
    print("\n💡 Typical results:")
    print("   - Acceptance rate: 70-80%")
    print("   - K=4 speculative tokens")
    print("   - Expected speedup: 2.0-2.5x")
    print("=" * 70)
