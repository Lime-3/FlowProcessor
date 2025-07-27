from typing import Dict, Any, List
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)


class VisualizationThemes:
    """Provides different visual themes for plots, updated with Apple-inspired design techniques for uniqueness and beauty."""
    
    def __init__(self):
        """Initialize themes with Apple design influences: clean sans-serif typography, subtle color palettes, generous spacing, and adaptive light/dark modes."""
        self.font_family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
        self.themes = {
            'default': self._get_default_theme(),
            'scientific': self._get_scientific_theme(),
            'dark': self._get_dark_theme(),
            'minimal': self._get_minimal_theme(),
            'colorful': self._get_colorful_theme(),
            'publication': self._get_publication_theme()
        }
    
    def apply_theme(self, fig: go.Figure, theme_name: str) -> go.Figure:
        """Apply a theme to a figure."""
        if theme_name not in self.themes:
            logger.warning(f"Unknown theme: {theme_name}. Using default.")
            theme_name = 'default'
        
        theme = self.themes[theme_name]
        fig.update_layout(**theme)
        
        return fig
    
    def get_available_themes(self) -> List[str]:
        """Get list of available themes."""
        return list(self.themes.keys())
    
    def get_theme(self, theme_name: str) -> Dict[str, Any]:
        """Get a specific theme."""
        return self.themes.get(theme_name, self.themes['default'])
    
    def _get_default_theme(self) -> Dict[str, Any]:
        """Get default theme with Apple light mode inspiration: clean, readable, subtle grays."""
        return {
            'template': 'simple_white',
            'font': {
                'family': self.font_family,
                'size': 13,
                'color': '#000000'  # system label light
            },
            'title': {
                'font': {
                    'family': self.font_family,
                    'size': 17,
                    'color': '#000000'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#3C3C43'  # secondary label opaque
                },
                'showgrid': True,
                'gridcolor': '#E5E5EA',  # systemGray5 light
                'gridwidth': 1,
                'linecolor': '#AEAEB2',  # systemGray2 light
                'linewidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#3C3C43'
                },
                'showgrid': True,
                'gridcolor': '#E5E5EA',
                'gridwidth': 1,
                'linecolor': '#AEAEB2',
                'linewidth': 1
            },
            'legend': {
                'font': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#000000'
                },
                'bgcolor': 'rgba(255,255,255,0.8)',
                'bordercolor': '#E5E5EA',
                'borderwidth': 1
            },
            'plot_bgcolor': '#F2F2F7',  # secondarySystemBackground light
            'paper_bgcolor': '#FFFFFF',
            'margin': {'l': 80, 'r': 60, 't': 80, 'b': 80}  # Generous spacing
        }
    
    def _get_scientific_theme(self) -> Dict[str, Any]:
        """Get scientific theme with Apple elegance: sans-serif font, precise lines, subtle grid."""
        return {
            'template': 'simple_white',
            'font': {
                'family': self.font_family,
                'size': 13,
                'color': '#000000'
            },
            'title': {
                'font': {
                    'family': self.font_family,
                    'size': 17,
                    'color': '#000000'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#D1D1D6',  # systemGray4 light
                'gridwidth': 0.5,
                'zeroline': True,
                'zerolinecolor': '#AEAEB2',
                'zerolinewidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#D1D1D6',
                'gridwidth': 0.5,
                'zeroline': True,
                'zerolinecolor': '#AEAEB2',
                'zerolinewidth': 1
            },
            'legend': {
                'font': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#000000'
                }
            },
            'plot_bgcolor': '#FFFFFF',
            'paper_bgcolor': '#FFFFFF',
            'margin': {'l': 80, 'r': 60, 't': 80, 'b': 80}
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Get dark theme inspired by Apple Dark Mode: deep blacks, high contrast text, subtle grays."""
        return {
            'template': 'plotly_dark',
            'font': {
                'family': self.font_family,
                'size': 13,
                'color': '#FFFFFF'  # system label dark
            },
            'title': {
                'font': {
                    'family': self.font_family,
                    'size': 17,
                    'color': '#FFFFFF'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#FFFFFF'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#EBEBF5'  # secondary label opaque
                },
                'showgrid': True,
                'gridcolor': '#2C2C2E',  # systemGray5 dark
                'gridwidth': 1,
                'linecolor': '#636366',  # systemGray2 dark
                'linewidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#FFFFFF'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#EBEBF5'
                },
                'showgrid': True,
                'gridcolor': '#2C2C2E',
                'gridwidth': 1,
                'linecolor': '#636366',
                'linewidth': 1
            },
            'legend': {
                'font': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#FFFFFF'
                },
                'bgcolor': 'rgba(0,0,0,0.8)',
                'bordercolor': '#2C2C2E',
                'borderwidth': 1
            },
            'plot_bgcolor': '#1C1C1E',  # secondarySystemBackground dark
            'paper_bgcolor': '#000000',
            'margin': {'l': 80, 'r': 60, 't': 80, 'b': 80}
        }
    
    def _get_minimal_theme(self) -> Dict[str, Any]:
        """Get minimal theme with Apple minimalism: no grids, thin lines, ample white space."""
        return {
            'template': 'simple_white',
            'font': {
                'family': self.font_family,
                'size': 11,
                'color': '#3C3C43'  # secondary label
            },
            'title': {
                'font': {
                    'family': self.font_family,
                    'size': 15,
                    'color': '#000000'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 13,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 10,
                    'color': '#3C3C43'
                },
                'showgrid': False,
                'showline': True,
                'linecolor': '#C7C7CC',  # systemGray3 light
                'linewidth': 0.5,
                'zeroline': False
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 13,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 10,
                    'color': '#3C3C43'
                },
                'showgrid': False,
                'showline': True,
                'linecolor': '#C7C7CC',
                'linewidth': 0.5,
                'zeroline': False
            },
            'legend': {
                'font': {
                    'family': self.font_family,
                    'size': 10,
                    'color': '#3C3C43'
                },
                'borderwidth': 0
            },
            'plot_bgcolor': '#FFFFFF',
            'paper_bgcolor': '#FFFFFF',
            'margin': {'l': 100, 'r': 80, 't': 100, 'b': 100}  # Extra space for beauty
        }
    
    def _get_colorful_theme(self) -> Dict[str, Any]:
        """Get colorful theme using Apple system accents: vibrant yet harmonious colors for emphasis."""
        return {
            'template': 'simple_white',
            'font': {
                'family': self.font_family,
                'size': 13,
                'color': '#000000'
            },
            'title': {
                'font': {
                    'family': self.font_family,
                    'size': 17,
                    'color': '#007AFF'  # systemBlue light
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#34C759'  # systemGreen light
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#3C3C43'
                },
                'showgrid': True,
                'gridcolor': '#F2F2F7',  # systemGray6 light
                'gridwidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 15,
                        'color': '#34C759'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#3C3C43'
                },
                'showgrid': True,
                'gridcolor': '#F2F2F7',
                'gridwidth': 1
            },
            'legend': {
                'font': {
                    'family': self.font_family,
                    'size': 12,
                    'color': '#000000'
                }
            },
            'plot_bgcolor': '#FFFFFF',
            'paper_bgcolor': '#F2F2F7',
            'margin': {'l': 80, 'r': 60, 't': 80, 'b': 80}
        }
    
    def _get_publication_theme(self) -> Dict[str, Any]:
        """Get publication-ready theme with Apple precision: high contrast, fine lines for print."""
        return {
            'template': 'simple_white',
            'font': {
                'family': self.font_family,
                'size': 10,
                'color': '#000000'
            },
            'title': {
                'font': {
                    'family': self.font_family,
                    'size': 14,
                    'color': '#000000'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 12,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 9,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#D1D1D6',  # systemGray4 light
                'gridwidth': 0.5,
                'showline': True,
                'linecolor': '#000000',
                'linewidth': 1,
                'ticks': 'outside',
                'ticklen': 5
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': self.font_family,
                        'size': 12,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': self.font_family,
                    'size': 9,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#D1D1D6',
                'gridwidth': 0.5,
                'showline': True,
                'linecolor': '#000000',
                'linewidth': 1,
                'ticks': 'outside',
                'ticklen': 5
            },
            'legend': {
                'font': {
                    'family': self.font_family,
                    'size': 9,
                    'color': '#000000'
                }
            },
            'plot_bgcolor': '#FFFFFF',
            'paper_bgcolor': '#FFFFFF',
            'margin': {'l': 70, 'r': 50, 't': 70, 'b': 70}
        }