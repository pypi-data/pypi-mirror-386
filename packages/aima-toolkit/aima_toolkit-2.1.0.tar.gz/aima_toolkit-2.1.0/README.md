# aima_toolkit

**aima_toolkit** is my personal implementation of algorithms and problems from *Artificial Intelligence: A Modern Approach (4th edition)*.  
It serves as both a **learning project** and a **reusable package** that I can import into other projects without copy–pasting code.

---

## 🎯 Why I built this
While studying AIMA, I quickly realized that each chapter builds on a shared set of abstractions (problems, nodes, queues, heuristics, etc.).  
Copying files around between my “Chapter 3 search agents” and my “Chapter 4 local search” projects became repetitive and messy.

This package solves that by:
- Providing a **central library** of reusable AI building blocks.
- Letting me install it locally (or eventually from PyPI) and just `import aima_toolkit`.
- Forcing me to design my code as **modular, tested, and reusable software** rather than scattered scripts.

---

## 📦 What it contains
The package is organized following the structure of AIMA:

- **Problems**  
  - Classic AI problems: 8-queens, Romania map search, simple tree problems.  
- **SearchProblemPackage**  
  - **Uninformed Search**: BFS, DFS, Depth-limited, Iterative Deepening, Uniform Cost.  
  - **Informed Search**: A*.  
  - **Local Search**: Hill Climbing, Stochastic Hill Climbing, Simulated Annealing, Local Beam, Genetic Algorithms.  
  - **Nondeterministic, Online, and Partially Observable Search** (scaffolding for future chapters).  
- **Sampling**  
  - Utilities like reservoir sampling.  
- **Core utilities**  
  - `Node`, `Problem`, `Queue`, `expand` functions, etc.

Tests are included under `tests/` to ensure correctness.

---

## 🚀 Goals
This isn’t just about getting AIMA exercises done—it’s about pushing myself to:
1. **Write library-quality code**  
   - Consistent API  
   - Clear separation of subpackages  
   - MIT licensed for others to learn from.
2. **Cover the book’s progression**  
   - Start with search (Chapters 3–4)  
   - Move into CSPs (Chapter 5), games (Chapter 6), logic (Chapters 7–10), planning (Chapter 11), uncertainty (Chapters 12–16), machine learning (Chapters 19–23), and beyond.
3. **Make it reusable for my own projects**  
   - Example: using the same `Problem` abstraction for both toy textbook problems and custom agents (like N-puzzle solvers or experimental planners).

---

## 🔧 Installation
For now (local development):
```bash
git clone <this-repo>
cd aima_toolkit
python -m pip install -e .
```

Then in Python:
```python
from aima_toolkit.SearchProblemPackage.SearchAlgorithms.InformedSearch.a_star_search import astar
```

---

## 🛠️ Roadmap
- ✅ Chapter 3: Uninformed search  
- ✅ Chapter 4: Local search & optimization  
- 🔜 Chapter 5: CSPs (backtracking, inference, local search)  
- 🔜 Chapter 6: Adversarial search & games  
- 🔜 Chapter 7+: Logic, Planning, Uncertainty, ML, RL…  

My long-term goal is to have a **complete, working reference implementation** of all core algorithms in AIMA 4e, with clean Python packaging and tests.

---

## 📜 License
MIT License — free to use, modify, and learn from, with attribution.
