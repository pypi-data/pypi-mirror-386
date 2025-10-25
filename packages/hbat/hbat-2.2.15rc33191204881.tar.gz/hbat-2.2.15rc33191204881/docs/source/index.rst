HBAT Documentation
==================

.. image:: https://img.shields.io/github/v/release/abhishektiwari/hbat
   :alt: GitHub Release
   :target: https://github.com/abhishektiwari/hbat/releases

.. image:: https://img.shields.io/github/actions/workflow/status/abhishektiwari/hbat/test.yml?label=tests
   :alt: GitHub Actions Test Workflow Status
   :target: https://github.com/abhishektiwari/hbat/actions/workflows/test.yml

.. pypi-shield::
   :project: hbat
   :version:

.. pypi-shield::
   :wheel:

.. pypi-shield::
   :py-versions:
   
.. github-shield::
   :username: abhishektiwari
   :repository: hbat
   :branch: main
   :last-commit:

.. image:: https://img.shields.io/pypi/status/hbat
   :alt: PyPI - Status

.. image:: https://img.shields.io/conda/v/hbat/hbat
   :alt: Conda Version

.. github-shield::
   :username: abhishektiwari
   :repository: hbat
   :license:

.. image:: https://img.shields.io/github/downloads/abhishektiwari/hbat/total?label=GitHub%20Downloads
   :alt: GitHub Downloads (all assets, all releases)
   :target: https://github.com/abhishektiwari/hbat/releases

.. image:: https://img.shields.io/sourceforge/dt/hbat?label=SourceForge%20Downloads
   :alt: SourceForge Downloads
   :target: https://sourceforge.net/projects/hbat/files/

.. image:: https://img.shields.io/pepy/dt/hbat?label=PyPI%20Downloads
   :alt: PyPI Downloads
   :target: https://pypi.org/project/hbat/

.. image:: https://codecov.io/gh/abhishektiwari/hbat/graph/badge.svg?token=QSKYLB3M1V 
   :alt: Codecov Coverage
   :target: https://codecov.io/gh/abhishektiwari/hbat

.. image:: https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.juleskreuer.eu%2Fcitation-badge.php%3Fshield%26doi%3D10.3233%2FISI-2007-00337&query=%24.message&style=flat&logo=googlescholar&label=Citations&cacheSeconds=43200
   :alt: Scholar Citations
   :target: https://scholar.google.com/citations?view_op=view_citation&hl=en&user=Mb7eYKYAAAAJ&citation_for_view=Mb7eYKYAAAAJ:u-x6o8ySG0sC

.. image:: https://socket.dev/api/badge/pypi/package/hbat/2.2.11?artifact_id=py3-none-any-whl
   :alt: Socket
   :target: https://socket.dev/api/badge/pypi/package/hbat/2.2.11?artifact_id=py3-none-any-whl

.. image:: https://www.codefactor.io/repository/github/abhishektiwari/hbat/badge/main
   :target: https://www.codefactor.io/repository/github/abhishektiwari/hbat/overview/main
   :alt: CodeFactor

Welcome to HBAT (Hydrogen Bond Analysis Tool) documentation!


.. raw:: html

   <span class="__dimensions_badge_embed__" data-doi="10.3233/isi-2007-00337" data-legend="always" data-style="small_circle"></span><script async src="https://badge.dimensions.ai/badge.js" charset="utf-8"></script>

A Python package to automate the analysis of potential hydrogen bonds and similar type of weak interactions like halogen bonds and non-canonical interactions in macromolecular structures, available in Protein Data Bank (PDB) file format. HBAT uses a geometric approach to identify potential hydrogen bonds by analyzing distance and angular criteria between donor-hydrogen-acceptor triplets.

.. image:: https://static.abhishek-tiwari.com/hbat/hbat-window-v1.png
   :alt: HBAT GUI
   :align: center

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   installation
   quickstart
   cli
   parameters
   presets
   pdbfixing
   license

.. toctree::
   :maxdepth: 1
   :caption: Developer Guide

   api/index
   development
   logic

Quick Start
-----------

Install HBAT
~~~~~~~~~~~~

.. code-block:: bash

   pip install hbat

Run HBAT Command-Line Interface (CLI) using :code:`hbat` or launch HBAT GUI using :code:`hbat-gui`.

See complete installation instructions in :doc:`installation`.

Basic usage
~~~~~~~~~~~

.. code-block:: bash

   hbat input.pdb                                                   # Show results in terminal
   hbat input.pdb -o results.csv                                    # Save results to CSV file (default)
   hbat input.pdb -o results.json  --fix-pdb                        # Apply PDB fixing and Save results to JSON file
   hbat input.pdb -o results.json  --fix-pdb  --fix-method=pdbfixer # Apply PDB fixing using PdbFixer and Save results to JSON file

See full CLI options :doc:`cli`.

Features
--------

- Detect and analyze potential hydrogen bonds, halogen bonds, and X-H...π interactions
- Automated PDB fixing with OpenBabel and PDBFixer integration
- Supports graphical (tkinter), command-line, and programming interfaces
- Use graphical interfaces for interactive analysis, CLI/API for batch processing and automation
- Cooperativity chain visualization using NetworkX/matplotlib and GraphViz
- Export cooperativity chain visualizations to PNG, SVG, PDF formats
- Built-in presets for different structure types (high-resolution, NMR, membrane proteins, etc.)
- Customizable distance cutoffs, angle thresholds, and analysis modes.
- Multiple Output Formats: Text, CSV, and JSON export options
- Optimized algorithms for efficient analysis of large structures
- Cross-Platform: Works on Windows, macOS, and Linux.

.. image:: https://static.abhishek-tiwari.com/hbat/6rsa-pdb-chain-6.png
   :alt: Cooperativity chain visualization
   :align: center

Cite HBAT
---------

.. code-block:: bash

   @article{tiwari2023hbat,
       title={HBAT: A Python Package for Automated Hydrogen Bond Analysis in Macromolecular Structures},
       author={Tiwari, Abhishek and others},
       journal={Journal of Open Research Software},
       volume={11},
       number={1},
       pages={1-8},
       year={2023},
       publisher={Ubiquity Press}
   }

.. code-block:: bash

   Tiwari, A., & Panigrahi, S. K. (2007). HBAT: A Complete Package for Analysing Strong and Weak Hydrogen Bonds in Macromolecular Crystal Structures. In Silico Biology, 7(6). https://doi.org/10.3233/ISI-2007-00337

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`