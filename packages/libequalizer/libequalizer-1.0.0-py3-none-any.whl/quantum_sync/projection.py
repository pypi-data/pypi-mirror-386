"""
Projection Layers для квантовой синхронизации

Аналог проекционного слоя из multimodal_braindler

© 2025 NativeMind
"""

import torch
import torch.nn as nn


class ProjectionLayer(nn.Module):
    """
    Базовый проекционный слой
    
    Преобразует представление одной модели в пространство другой
    """
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dim: Optional[int] = None
    ):
        super().__init__()
        
        if hidden_dim is None:
            hidden_dim = (input_dim + output_dim) // 2
        
        self.projection = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.projection(x)


class AdaptiveProjection(nn.Module):
    """
    Адаптивная проекция с attention
    
    Более продвинутая версия для лучшей синхронизации
    """
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 4
    ):
        super().__init__()
        
        self.projection = ProjectionLayer(input_dim, output_dim)
        
        self.attention = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=num_heads,
            batch_first=True
        )
        
        self.norm = nn.LayerNorm(output_dim)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Базовая проекция
        projected = self.projection(x)
        
        # Self-attention
        if projected.dim() == 2:
            projected = projected.unsqueeze(1)
        
        attn_out, _ = self.attention(projected, projected, projected)
        output = self.norm(projected + attn_out)
        
        if output.size(1) == 1:
            output = output.squeeze(1)
        
        return output

