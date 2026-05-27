"""ToolSym TCM — analysis app.

Tabs:

* **Image to Signal** — port of the existing PyQt6 ``image_to_signal``
  GUI. Runs the full hybrid pipeline (Falah 2025) from a folder of
  masks to a fracture decision.
* **Symmetry** — port of the Tkinter symmetry analyser. Computes the
  D̄ metric and renders the three-zone classification.
* **Visual Hull** — port of the Tkinter 3D-reconstruction GUI. Carves
  a 128³ hull from real masks.
* **Dataset Browser** — replaces ``tool_profile_viz`` — visualises any
  tool in the DATA folder.
"""
