"""
Visualization themes for flow cytometry plots.
"""

from typing import Dict, Any, List
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)


class VisualizationThemes:
    """Provides different visual themes for plots."""
    
    def __init__(self):
        """Initialize themes."""
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
        """Get default theme."""
        return {
            'template': 'plotly_white',
            'font': {
                'family': 'Arial, sans-serif',
                'size': 12,
                'color': '#2c3e50'
            },
            'title': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 16,
                    'color': '#2c3e50'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 14,
                        'color': '#2c3e50'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#2c3e50'
                }
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 14,
                        'color': '#2c3e50'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#2c3e50'
                }
            },
            'legend': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#2c3e50'
                }
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
        }
    
    def _get_scientific_theme(self) -> Dict[str, Any]:
        """Get scientific theme."""
        return {
            'template': 'plotly_white',
            'font': {
                'family': 'Times New Roman, serif',
                'size': 12,
                'color': '#000000'
            },
            'title': {
                'font': {
                    'family': 'Times New Roman, serif',
                    'size': 16,
                    'color': '#000000'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': 'Times New Roman, serif',
                        'size': 14,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': 'Times New Roman, serif',
                    'size': 11,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#e0e0e0',
                'gridwidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': 'Times New Roman, serif',
                        'size': 14,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': 'Times New Roman, serif',
                    'size': 11,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#e0e0e0',
                'gridwidth': 1
            },
            'legend': {
                'font': {
                    'family': 'Times New Roman, serif',
                    'size': 11,
                    'color': '#000000'
                }
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': {'l': 70, 'r': 50, 't': 70, 'b': 70}
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Get dark theme."""
        return {
            'template': 'plotly_dark',
            'font': {
                'family': 'Arial, sans-serif',
                'size': 12,
                'color': '#ffffff'
            },
            'title': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 16,
                    'color': '#ffffff'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 14,
                        'color': '#ffffff'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#ffffff'
                }
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 14,
                        'color': '#ffffff'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#ffffff'
                }
            },
            'legend': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#ffffff'
                }
            },
            'plot_bgcolor': '#1a1a1a',
            'paper_bgcolor': '#1a1a1a',
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
        }
    
    def _get_minimal_theme(self) -> Dict[str, Any]:
        """Get minimal theme."""
        return {
            'template': 'plotly_white',
            'font': {
                'family': 'Arial, sans-serif',
                'size': 10,
                'color': '#333333'
            },
            'title': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 14,
                    'color': '#333333'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 12,
                        'color': '#333333'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 9,
                    'color': '#333333'
                },
                'showgrid': False,
                'showline': True,
                'linecolor': '#333333',
                'linewidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 12,
                        'color': '#333333'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 9,
                    'color': '#333333'
                },
                'showgrid': False,
                'showline': True,
                'linecolor': '#333333',
                'linewidth': 1
            },
            'legend': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 9,
                    'color': '#333333'
                }
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': {'l': 50, 'r': 30, 't': 50, 'b': 50}
        }
    
    def _get_colorful_theme(self) -> Dict[str, Any]:
        """Get colorful theme."""
        return {
            'template': 'plotly_white',
            'font': {
                'family': 'Arial, sans-serif',
                'size': 12,
                'color': '#2c3e50'
            },
            'title': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 16,
                    'color': '#e74c3c'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 14,
                        'color': '#3498db'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#2c3e50'
                },
                'showgrid': True,
                'gridcolor': '#ecf0f1',
                'gridwidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 14,
                        'color': '#3498db'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#2c3e50'
                },
                'showgrid': True,
                'gridcolor': '#ecf0f1',
                'gridwidth': 1
            },
            'legend': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 11,
                    'color': '#2c3e50'
                }
            },
            'plot_bgcolor': '#f8f9fa',
            'paper_bgcolor': 'white',
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
        }
    
    def _get_publication_theme(self) -> Dict[str, Any]:
        """Get publication-ready theme."""
        return {
            'template': 'plotly_white',
            'font': {
                'family': 'Arial, sans-serif',
                'size': 10,
                'color': '#000000'
            },
            'title': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 14,
                    'color': '#000000'
                }
            },
            'xaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 12,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 9,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#cccccc',
                'gridwidth': 0.5,
                'showline': True,
                'linecolor': '#000000',
                'linewidth': 1
            },
            'yaxis': {
                'title': {
                    'font': {
                        'family': 'Arial, sans-serif',
                        'size': 12,
                        'color': '#000000'
                    }
                },
                'tickfont': {
                    'family': 'Arial, sans-serif',
                    'size': 9,
                    'color': '#000000'
                },
                'showgrid': True,
                'gridcolor': '#cccccc',
                'gridwidth': 0.5,
                'showline': True,
                'linecolor': '#000000',
                'linewidth': 1
            },
            'legend': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 9,
                    'color': '#000000'
                }
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
        } 