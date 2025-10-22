# A State Space Visualizer

The library provides an interactive visualizer for exploring the state spaces of various games and puzzles. Each game can be visualized with customizable parameters:
- 2048 
    - Customize grid size
- Towers of Hanoi
    - Customize number of towers and number of disks
- Sliding block game
    - Customize grid size
- Klotski
    - Can customize initial block configuration
- Aztec Diamonds
    - Customize order

For each of the games, you can either color nodes in the state space using a game-specific "score" function or based on the probability masses from diffusion. 

# Setup
run 
```zsh
pip install --upgrade vodiboi-state-space-visualizer
```

If you intend to run the flet vizualizer, independently run 

```zsh
pip install flet-webview==0.1.0
```

If you are trying to run in a google colab notebook, instead add this to the top of your notebook:

```zsh
!pip install --upgrade vodiboi-state-space-visualizer
```

# Usage

## Basic Usage

The general pattern for using the visualizer is:

1. Import the game and visualizer classes
2. Create a game instance with desired parameters
3. Create a visualizer instance
4. Launch the interactive interface

```python
import flet as ft
from vodiboi_state_space_visualizer.games import Game2048
from vodiboi_state_space_visualizer.visualizers import FletStateSpaceVisualizer

def main(page: ft.Page):
    # Create a game instance
    game = Game2048(shape=(2, 2))
    
    # Create visualizer (verbose=False to suppress output)
    visualizer = FletStateSpaceVisualizer(
        verbose=False,
        is_directed=True,  # is_directed=False for undirected graph behavior
        diffusion_steps=50  # Number of steps for diffusion computation (default: 50)
    )
    
    # Build the UI
    visualizer.build_ui(page, game)

# Run the app
ft.app(target=main)
```

### Jupyter Notebook Usage

For Jupyter notebooks, use the `JupyterStateSpaceVisualizer`:

```python
from vodiboi_state_space_visualizer.games import Game2048
from vodiboi_state_space_visualizer.visualizers import JupyterStateSpaceVisualizer
# If you are using google colab, you need the below lines to allow for widgets:
from google.colab import output
output.enable_custom_widget_manager()

# Create a game and visualizer
game = Game2048(shape=(2, 2))
visualizer = JupyterStateSpaceVisualizer(
    verbose=False,  # verbose=True for status messages
    is_directed=True,  # is_directed=False for undirected graph behavior
    diffusion_steps=50  # Number of steps for diffusion computation (default: 50)
)

# Launch the visualization
visualizer.visualize(game)
```

## Available Games

### 2048
Visualize the state space of the 2048 game with customizable grid dimensions.

```python
from vodiboi_state_space_visualizer.games import Game2048

# 2x2 grid (default)
game = Game2048(shape=(2, 2))
```

### Towers of Hanoi
Classic Towers of Hanoi puzzle with configurable number of disks and towers.

```python
from vodiboi_state_space_visualizer.games import TowersOfHanoi

# 4 disks, 3 towers (classic)
game = TowersOfHanoi(num_disks=3, num_towers=3)

```

### Sliding Block Puzzle

```python
from vodiboi_state_space_visualizer.games import SlidingBlockPuzzle

# 2x2 sliding puzzle (4-puzzle)
game = SlidingBlockPuzzle(shape=(2, 2))

# 3x3 sliding puzzle (8-puzzle)
game = SlidingBlockPuzzle(shape=(3, 3))
```

### Klotski
Traditional Klotski block puzzle with different layout configurations.

```python
from vodiboi_state_space_visualizer.games import Klotski

# Original Klotski layout
game = Klotski(layout="Original Klotski")

# Alternatively, (easier to visualize) Medium Layout
game = Klotski(layout="Original Klotski")

# Use with reachable states only for performance
visualizer = FletStateSpaceVisualizer(ALL_STATES=False)
```

### Snake
Snake game state space visualization.

```python
from vodiboi_state_space_visualizer.games import Snake

# 3x3 grid
game = Snake(shape=(3, 3))
```

### Aztec Diamond
Aztec Diamond tiling visualizations.

```python
from vodiboi_state_space_visualizer.games import AztecDiamond

# Order 3 Aztec Diamond
game = AztecDiamond(n=3)
```

### Abstract Graph
Allows you to visualize any graph with support for custom node coloring.

```python
from vodiboi_state_space_visualizer.games import AbstractGraph
import networkx as nx

# Basic usage with a random graph
G = nx.erdos_renyi_graph(10, 0.3)
game = AbstractGraph(G)

# Custom coloring via parameter
custom_colors = {0: 10.0, 1: 20.0, 2: 30.0}  # Node -> color value
game = AbstractGraph(G, custom_coloring=custom_colors)

# Custom coloring via NetworkX node attributes  
nx.set_node_attributes(G, {0: 5.0, 1: 15.0}, 'color')
game = AbstractGraph(G)  # Automatically detects 'color' attribute

# Additional customization
node_labels = {0: "Start", 1: "Middle", 2: "End"}
edge_weights = {(0, 1): 2.0, (1, 2): 1.5}
game = AbstractGraph(G, 
                    node_labels=node_labels,
                    edge_weights=edge_weights, 
                    custom_coloring=custom_colors,
                    initial_node=0)
```

**Custom Coloring Features:**
- Pass `custom_coloring` dict mapping nodes to color values
- Or use NetworkX `'color'` node attribute
- Both visualizers automatically use custom colors
- Colorbar title changes to "Custom Color" when enabled
- Hover text includes color information

## Visualizer Options

The `FletStateSpaceVisualizer` accepts several customization parameters:

```python
visualizer = FletStateSpaceVisualizer(
    node_size=4,              # Size of nodes in the graph
    all_edge_width=1,         # Width of edges
    all_edge_opacity=0.08,    # Opacity of edges
    layout_seed=23,           # Random seed for layout
    ignore_leaves=True,       # Whether to ignore leaf nodes
    ALL_STATES=True,          # Use all states vs reachable only
    colorscale='Plasma',      # Color scheme for visualization
    dimension=3               # 2D or 3D visualization
)
```

## Complete Example

Here's a complete example that creates an interactive 2048 visualizer:

```python
import flet as ft
from vodiboi_state_space_visualizer.games import Game2048
from vodiboi_state_space_visualizer.visualizers import FletStateSpaceVisualizer

def run_2048_visualizer():
    def main(page: ft.Page):
        page.title = "2048 State Space Visualizer"
        
        # Create 2x2 2048 game
        game = Game2048(shape=(2, 2))
        
        # Create visualizer with custom settings
        visualizer = FletStateSpaceVisualizer(
            node_size=6,
            colorscale='Viridis',
            dimension=3,
            diffusion_steps=75  # Custom diffusion computation steps
        )
        
        # Build and display the UI
        visualizer.build_ui(page, game)
    
    ft.app(target=main)

if __name__ == "__main__":
    run_2048_visualizer()
```

## Configuration Options

### Graph Directionality

Both visualizers support an `is_directed` parameter that affects how diffusion coloring and random moves work:

- **`is_directed=True`** (default): Treats the state space graph as directed
  - Diffusion follows edge directions (probability flows only in the direction of allowed moves)
  - Random moves in Jupyter visualizer only follow outgoing edges from current node
  - More realistic for most games where moves are not reversible

- **`is_directed=False`**: Treats the state space graph as undirected
  - Diffusion becomes bidirectional (probability flows in both directions)  
  - Random moves can traverse edges in either direction
  - Useful for analyzing symmetric or reversible game mechanics

```python
# Directed behavior (default) - realistic game flow
visualizer = JupyterStateSpaceVisualizer(is_directed=True)

# Undirected behavior - symmetric analysis
visualizer = JupyterStateSpaceVisualizer(is_directed=False)
```

### Diffusion Steps

The `diffusion_steps` parameter controls how many iterations the diffusion simulation runs when computing probability distributions:

- **Higher values** (e.g., 100, 200): More accurate probability convergence, but slower computation
- **Lower values** (e.g., 20, 30): Faster computation, but may not fully converge
- **Default: 50**: Good balance between accuracy and speed for most use cases

```python
# Fast computation - good for large graphs or quick exploration
visualizer = JupyterStateSpaceVisualizer(diffusion_steps=20)

# High accuracy - for final analysis or research
visualizer = JupyterStateSpaceVisualizer(diffusion_steps=200)

# Default balanced approach
visualizer = JupyterStateSpaceVisualizer(diffusion_steps=50)
```

## Features

- **Interactive State Space**: Click on nodes to explore different game states
- **Multiple Coloring Modes**: Color nodes by game score or diffusion probability
- **Game Controls**: Use move buttons to navigate through the game
- **3D/2D Visualization**: Switch between 2D and 3D graph layouts
- **Real-time Updates**: See how your moves affect the state space in real-time

The visualizer opens in a web browser window and provides an interactive interface where you can:
- Explore the complete state space graph of the game
- Click on nodes to see the corresponding game state
- Use game controls to make moves and see transitions
- Toggle between different coloring schemes
- Restart or use "luck mode" for random exploration


