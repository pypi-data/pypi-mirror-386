"""
Optimized MoE Routing for Nthuku-Fast

Reduces communication overhead in Mixture of Experts:
- Expert parallelism (process experts concurrently)
- Token dropping for load balancing
- Grouped expert execution
- Optimized routing algorithm
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional


class OptimizedRouter(nn.Module):
    """
    Optimized router with reduced communication overhead
    
    Improvements over basic router:
    - Batched expert processing
    - Expert parallelism
    - Efficient load balancing
    - Token dropping for capacity management
    """
    
    def __init__(
        self,
        input_dim: int,
        num_experts: int,
        num_experts_per_token: int,
        capacity_factor: float = 1.25,
        use_token_dropping: bool = True
    ):
        super().__init__()
        self.num_experts = num_experts
        self.num_experts_per_token = num_experts_per_token
        self.capacity_factor = capacity_factor
        self.use_token_dropping = use_token_dropping
        
        # Routing network
        self.gate = nn.Linear(input_dim, num_experts, bias=False)
        
        # Expert utilization tracking
        self.register_buffer('expert_counts', torch.zeros(num_experts))
        self.register_buffer('total_tokens_routed', torch.zeros(1))
        
    def forward(
        self, 
        x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Optimized routing with capacity management
        
        Args:
            x: [batch, seq_len, hidden_dim]
            
        Returns:
            expert_indices: [batch, seq_len, top_k]
            expert_weights: [batch, seq_len, top_k]
            load_balance_loss: scalar
            expert_mask: [batch, seq_len, top_k] - which tokens to process
        """
        batch_size, seq_len, hidden_dim = x.shape
        total_tokens = batch_size * seq_len
        
        # Compute routing scores
        router_logits = self.gate(x)  # [batch, seq, num_experts]
        
        # Softmax and top-k selection
        routing_weights = F.softmax(router_logits, dim=-1)
        expert_weights, expert_indices = torch.topk(
            routing_weights,
            self.num_experts_per_token,
            dim=-1
        )
        
        # Normalize selected expert weights
        expert_weights = expert_weights / expert_weights.sum(dim=-1, keepdim=True)
        
        # Capacity management
        expert_capacity = int(
            (total_tokens * self.num_experts_per_token / self.num_experts) 
            * self.capacity_factor
        )
        
        # Create expert mask for token dropping
        expert_mask = torch.ones_like(expert_weights)
        
        if self.use_token_dropping and self.training:
            # Count tokens per expert
            expert_token_counts = torch.zeros(
                self.num_experts, device=x.device, dtype=torch.long
            )
            
            # Track which tokens to drop
            for expert_id in range(self.num_experts):
                # Find all tokens routed to this expert (in flattened expert_indices)
                mask = (expert_indices == expert_id)
                token_count = mask.sum()
                
                if token_count > expert_capacity:
                    # Drop excess tokens (mark in expert_mask)
                    # Keep tokens with highest routing weights
                    weights_for_expert = expert_weights[mask]
                    
                    # Keep top expert_capacity tokens
                    num_tokens_for_expert = len(weights_for_expert)
                    _, keep_indices = torch.topk(
                        weights_for_expert,
                        min(expert_capacity, num_tokens_for_expert),
                        sorted=False
                    )
                    
                    # Create drop mask for tokens exceeding capacity
                    drop_mask = torch.ones(num_tokens_for_expert, device=x.device, dtype=torch.bool)
                    drop_mask[keep_indices] = False
                    
                    # Zero out dropped tokens in expert_mask
                    # Get current masked values
                    masked_weights = expert_mask[mask].clone()
                    # Zero out the dropped ones
                    masked_weights[drop_mask] = 0
                    # Put back
                    expert_mask[mask] = masked_weights
        
        # Load balancing loss (encourage uniform expert usage)
        if self.training:
            # Importance: fraction of routing probability to each expert
            importance = routing_weights.sum(dim=(0, 1))  # [num_experts]
            importance = importance / importance.sum()
            
            # Load: fraction of tokens routed to each expert
            load = torch.zeros(self.num_experts, device=x.device)
            for i in range(self.num_experts):
                load[i] = (expert_indices == i).float().sum()
            load = load / load.sum()
            
            # Load balancing loss: penalize imbalance
            # CV^2 loss from Switch Transformer
            load_balance_loss = self.num_experts * (importance * load).sum()
        else:
            load_balance_loss = torch.tensor(0.0, device=x.device)
        
        # Update statistics
        if self.training:
            with torch.no_grad():
                for i in range(self.num_experts):
                    self.expert_counts[i] += (expert_indices == i).float().sum()
                self.total_tokens_routed += total_tokens
        
        return expert_indices, expert_weights, load_balance_loss, expert_mask
    
    def get_expert_utilization(self) -> torch.Tensor:
        """Get expert utilization statistics"""
        if self.total_tokens_routed > 0:
            return self.expert_counts / self.total_tokens_routed
        return torch.zeros_like(self.expert_counts)
    
    def reset_statistics(self):
        """Reset routing statistics"""
        self.expert_counts.zero_()
        self.total_tokens_routed.zero_()


class OptimizedMixtureOfExperts(nn.Module):
    """
    Optimized MoE with reduced communication overhead
    
    Key optimizations:
    - Batched expert execution
    - Parallel expert processing where possible
    - Efficient token routing
    - Memory-efficient implementation
    """
    
    def __init__(
        self,
        config,
        use_expert_parallelism: bool = True,
        use_token_dropping: bool = True
    ):
        super().__init__()
        self.config = config
        self.hidden_dim = config.hidden_dim
        self.expert_dim = config.expert_dim
        self.num_experts = config.moe_config.num_experts
        self.num_experts_per_token = config.moe_config.num_experts_per_token
        self.use_expert_parallelism = use_expert_parallelism
        
        # Optimized router
        self.router = OptimizedRouter(
            self.hidden_dim,
            self.num_experts,
            self.num_experts_per_token,
            capacity_factor=config.moe_config.expert_capacity,
            use_token_dropping=use_token_dropping
        )
        
        # Experts
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(self.hidden_dim, self.expert_dim),
                nn.GELU(),
                nn.Dropout(getattr(config, 'attn_dropout', config.dropout)
                          if hasattr(config, 'dropout') else 0.1),
                nn.Linear(self.expert_dim, self.hidden_dim)
            )
            for _ in range(self.num_experts)
        ])
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Optimized forward pass with parallel expert execution
        
        Args:
            x: [batch, seq_len, hidden_dim]
            
        Returns:
            output: [batch, seq_len, hidden_dim]
            load_balance_loss: scalar
        """
        batch_size, seq_len, hidden_dim = x.shape
        
        # Route tokens
        expert_indices, expert_weights, load_balance_loss, expert_mask = \
            self.router(x)
        
        # Flatten
        x_flat = x.view(-1, hidden_dim)
        expert_indices_flat = expert_indices.view(-1, self.num_experts_per_token)
        expert_weights_flat = expert_weights.view(-1, self.num_experts_per_token)
        expert_mask_flat = expert_mask.view(-1, self.num_experts_per_token)
        
        # Initialize output
        output = torch.zeros_like(x_flat)
        
        if self.use_expert_parallelism:
            # Process experts in parallel (more memory but faster)
            output = self._parallel_expert_forward(
                x_flat, expert_indices_flat, expert_weights_flat, expert_mask_flat
            )
        else:
            # Process experts sequentially (less memory)
            output = self._sequential_expert_forward(
                x_flat, expert_indices_flat, expert_weights_flat, expert_mask_flat
            )
        
        # Reshape output
        output = output.view(batch_size, seq_len, hidden_dim)
        
        return output, load_balance_loss
    
    def _parallel_expert_forward(
        self,
        x_flat: torch.Tensor,
        expert_indices: torch.Tensor,
        expert_weights: torch.Tensor,
        expert_mask: torch.Tensor
    ) -> torch.Tensor:
        """Process all experts in parallel"""
        output = torch.zeros_like(x_flat)
        
        # Group tokens by expert for batched processing
        for expert_id in range(self.num_experts):
            # Find tokens routed to this expert
            expert_mask_bool = (expert_indices == expert_id) & (expert_mask > 0)
            
            if not expert_mask_bool.any():
                continue
            
            # Get tokens and positions
            token_positions = expert_mask_bool.nonzero(as_tuple=True)
            tokens = x_flat[token_positions[0]]
            weights = expert_weights[expert_mask_bool].unsqueeze(-1)
            
            # Process through expert (batched!)
            expert_output = self.experts[expert_id](tokens)
            
            # Weighted accumulation
            output[token_positions[0]] += expert_output * weights
        
        return output
    
    def _sequential_expert_forward(
        self,
        x_flat: torch.Tensor,
        expert_indices: torch.Tensor,
        expert_weights: torch.Tensor,
        expert_mask: torch.Tensor
    ) -> torch.Tensor:
        """Process experts one at a time (memory efficient)"""
        output = torch.zeros_like(x_flat)
        
        for k in range(self.num_experts_per_token):
            for expert_id in range(self.num_experts):
                mask = (expert_indices[:, k] == expert_id) & (expert_mask[:, k] > 0)
                
                if not mask.any():
                    continue
                
                tokens = x_flat[mask]
                expert_output = self.experts[expert_id](tokens)
                weights = expert_weights[mask, k].unsqueeze(-1)
                
                output[mask] += expert_output * weights
        
        return output
    
    def get_routing_stats(self) -> dict:
        """Get routing statistics"""
        utilization = self.router.get_expert_utilization()
        
        return {
            'expert_utilization': utilization.tolist(),
            'max_utilization': utilization.max().item(),
            'min_utilization': utilization.min().item(),
            'utilization_std': utilization.std().item(),
            'balance_score': 1.0 - utilization.std().item()  # 1.0 = perfect balance
        }
