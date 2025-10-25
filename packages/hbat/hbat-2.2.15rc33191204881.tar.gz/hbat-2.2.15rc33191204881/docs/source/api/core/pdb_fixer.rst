PDB Structure Fixer
===================

Comprehensive PDB structure fixing and enhancement utilities for preparing molecular structures for analysis.

Module Overview
---------------

.. automodule:: hbat.core.pdb_fixer
   :members:
   :undoc-members:
   :show-inheritance:

   This module provides advanced PDB structure enhancement capabilities including missing atom addition, residue standardization, and structure validation. It's designed to prepare raw PDB structures for accurate molecular interaction analysis.

Main Classes
------------

PDBFixer
~~~~~~~~

.. autoclass:: hbat.core.pdb_fixer.PDBFixer
   :members:
   :undoc-members:
   :show-inheritance:

   Comprehensive PDB structure enhancement engine with multiple fixing strategies.

   **Core Capabilities:**

   - **Missing Hydrogen Addition**: Adds missing hydrogen atoms using chemical rules
   - **Heavy Atom Reconstruction**: Reconstructs missing heavy atoms in standard residues
   - **Residue Standardization**: Converts non-standard residues to standard forms
   - **Hetrogen Management**: Removes or retains specific heterogens
   - **Structure Validation**: Comprehensive quality assessment and reporting

   **Fixing Modes:**

   The fixer supports various combinations of fixing operations:

   - ``NONE``: No modifications (validation only)
   - ``ADD_HYDROGENS``: Add missing hydrogen atoms
   - ``CONVERT_RESIDUES``: Standardize residue names
   - ``REMOVE_HETEROGENS``: Remove non-essential heterogens
   - ``ADD_HEAVY_ATOMS``: Reconstruct missing heavy atoms
   - Combined modes for comprehensive fixing

   **Usage Examples:**

   .. code-block:: python

      from hbat.core.pdb_fixer import PDBFixer
      from hbat.constants import PDBFixingModes

      # Basic hydrogen addition
      fixer = PDBFixer()
      fixer.fix_structure_file(
          "input.pdb", 
          "output.pdb",
          mode=PDBFixingModes.ADD_HYDROGENS
      )

      # Comprehensive fixing
      fixer.fix_structure_file(
          "raw_structure.pdb",
          "fixed_structure.pdb", 
          mode=PDBFixingModes.ADD_HYDROGENS_AND_CONVERT_RESIDUES
      )

      # Advanced fixing with custom parameters
      from hbat.constants import ParametersDefault
      
      params = ParametersDefault()
      params.fix_missing_heavy_atoms = True
      params.remove_waters = False
      
      fixer = PDBFixer(params)
      result = fixer.fix_structure_file("complex.pdb", "enhanced.pdb")
      
      print(f"Added {result.hydrogens_added} hydrogen atoms")
      print(f"Converted {result.residues_converted} residues")

Fixing Methods Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~

The PDBFixer supports two different backend methods for hydrogen addition, each with distinct characteristics:

**OpenBabel Method:**

- **Algorithm**: Chemical rules-based hydrogen placement
- **Sensitivity**: More aggressive hydrogen placement, finds ~2x more hydrogen bonds
- **Quality**: More permissive geometry, may include marginal bonds
- **Bond Perception**: Enhanced with ConnectTheDots() and PerceiveBondOrders() for robust aromatic handling
- **Best For**: Screening studies where sensitivity is prioritized
- **Typical Results**: Higher hydrogen bond counts, broader interaction detection

**PDBFixer Method:**

- **Algorithm**: Physics-based hydrogen placement using OpenMM force fields
- **Specificity**: More conservative hydrogen placement, higher-quality geometry
- **Quality**: Stricter geometric criteria, fewer false positives
- **Integration**: Native support for missing heavy atoms and residue standardization
- **Best For**: Detailed studies where accuracy is prioritized
- **Typical Results**: Lower but higher-quality hydrogen bond counts

**Method Selection Guidelines:**

.. code-block:: python

   # For high-sensitivity screening
   fixer = PDBFixer()
   result = fixer.fix_structure_file(
       "structure.pdb", "fixed.pdb", 
       method="openbabel"
   )

   # For high-accuracy analysis
   fixer = PDBFixer()  
   result = fixer.fix_structure_file(
       "structure.pdb", "fixed.pdb",
       method="pdbfixer",
       add_heavy_atoms=True
   )

**Performance Characteristics:**

- **OpenBabel**: ~1.85x more hydrogen bonds than PDBFixer
- **Bond Quality**: PDBFixer produces fewer short bonds (<2.0Å) and marginal angles
- **Computational Cost**: Similar processing times for both methods
- **Memory Usage**: Comparable memory requirements

**Scientific Validation:**

Both methods are scientifically valid but optimized for different use cases:

- **Research Publications**: Document which method was used for reproducibility
- **Comparative Studies**: Consider running both methods and comparing results
- **Quality Control**: Monitor bond distance/angle distributions for quality assessment

Troubleshooting
~~~~~~~~~~~~~~~

**Common Warnings and Their Meanings:**

*OpenBabel Kekulization Warning:*

.. code-block:: text

   *** Open Babel Warning in PerceiveBondOrders
   Failed to kekulize aromatic bonds in OBMol::PerceiveBondOrders

**Explanation**: This warning occurs when OpenBabel cannot assign alternating single/double bonds to aromatic rings due to non-ideal geometry in the PDB structure. This is common with real crystal structures and does not prevent successful hydrogen addition.

**Impact**: Minimal - the analysis continues normally and hydrogen bonds are detected correctly.

**Resolution**: No action needed. This is expected behavior for structures with imperfect aromatic ring geometry.

*PDBFixer pH Warnings:*

PDBFixer may issue warnings about protonation states at extreme pH values. These are informational and indicate the tool is making reasonable chemical assumptions.

*Bond Detection Warnings:*

After structure fixing, the analyzer re-detects bonds to ensure proper connectivity. This process may generate informational messages about bond count changes, which are normal and expected.

Exception Classes
~~~~~~~~~~~~~~~~~

.. autoclass:: hbat.core.pdb_fixer.PDBFixerError
   :members:
   :undoc-members:
   :show-inheritance:

   Specialized exception for PDB fixing operations with detailed error reporting.

   **Error Categories:**

   - **File Errors**: Input/output file issues
   - **Chemical Errors**: Invalid molecular structures
   - **Geometric Errors**: Impossible atomic coordinates
   - **Constraint Errors**: Unsatisfiable fixing requirements

Core Fixing Methods
-------------------

The PDBFixer class provides comprehensive structure fixing capabilities through its member methods. All methods are documented through the class autodocumentation above.

**Key Method Categories:**

- **Hydrogen Addition**: `add_missing_hydrogens()` - Uses chemical bonding rules and geometric optimization
- **Heavy Atom Reconstruction**: `add_missing_heavy_atoms()` - Reconstructs missing heavy atoms in standard residues  
- **Residue Standardization**: `convert_nonstandard_residues()` - Converts non-standard and modified residues
- **Hetrogen Management**: `remove_heterogens()` - Manages hetrogen retention based on analysis requirements
- **File Operations**: `fix_structure_file()` - High-level interface for comprehensive PDB fixing

Standalone Functions
--------------------

Module-Level Functions
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: hbat.core.pdb_fixer.add_missing_hydrogens

   Standalone function for adding missing hydrogen atoms to atom lists.

.. autofunction:: hbat.core.pdb_fixer.fix_pdb_file

   Convenience function for fixing PDB files with comprehensive options.

.. autofunction:: hbat.core.pdb_fixer.add_missing_heavy_atoms

   Standalone function for reconstructing missing heavy atoms.

.. autofunction:: hbat.core.pdb_fixer.convert_nonstandard_residues

   Standalone function for converting non-standard residues.

.. autofunction:: hbat.core.pdb_fixer.remove_heterogens

   Standalone function for removing heterogens from atom lists.

Chemical Intelligence
---------------------

Bonding Rules Engine
~~~~~~~~~~~~~~~~~~~~

The fixer uses sophisticated chemical rules for accurate structure enhancement:

**Hybridization Detection:**

.. code-block:: python

   # Determine carbon hybridization
   def determine_hybridization(carbon_atom, neighbors):
       if len(neighbors) == 4:
           return "sp3"  # Tetrahedral
       elif len(neighbors) == 3:
           return "sp2"  # Trigonal planar
       elif len(neighbors) == 2:
           return "sp"   # Linear
       else:
           raise ValueError("Invalid carbon coordination")

**Hydrogen Placement:**

- **Tetrahedral Centers**: Use ideal tetrahedral angles (109.5°)
- **Planar Centers**: Use trigonal planar geometry (120°)
- **Aromatic Systems**: Place hydrogens in ring plane
- **Heteroatoms**: Consider lone pair geometry

**Energy Minimization:**

The fixer includes basic energy minimization to resolve steric clashes:

.. code-block:: python

   # Simple steepest descent minimization
   def minimize_hydrogen_positions(atoms, max_iterations=100):
       for iteration in range(max_iterations):
           forces = calculate_forces(atoms)
           move_atoms(atoms, forces, step_size=0.01)
           
           if convergence_reached(forces):
               break
       
       return atoms

Performance and Scalability
---------------------------

**Computational Complexity:**

- **Hydrogen Addition**: O(n) where n is number of heavy atoms
- **Heavy Atom Reconstruction**: O(n log n) for template matching
- **Residue Conversion**: O(n) linear scan and replacement
- **Validation**: O(n) comprehensive structure checking

**Memory Usage:**

- Minimal memory overhead beyond original structure
- Efficient data structures for large protein complexes
- Streaming processing for very large structures

**Benchmarks:**

Typical performance on modern hardware:

- **Small proteins** (<1000 atoms): <100 ms fixing time
- **Medium proteins** (1000-10000 atoms): 100-1000 ms fixing time
- **Large complexes** (10000+ atoms): 1-10 seconds fixing time

Integration Examples
--------------------

Analysis Pipeline Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hbat.core.analyzer import MolecularInteractionAnalyzerractionAnalyzer
   from hbat.core.pdb_fixer import PDBFixer
   from hbat.constants import PDBFixingModes, ParametersDefault

   # Complete analysis pipeline with fixing
   def analyze_structure_with_fixing(pdb_file):
       # Step 1: Fix structure
       fixer = PDBFixer()
       fixed_file = "temp_fixed.pdb"
       
       fix_result = fixer.fix_structure_file(
           pdb_file, 
           fixed_file,
           mode=PDBFixingModes.ADD_HYDROGENS_AND_CONVERT_RESIDUES
       )
       
       print(f"Structure fixing completed:")
       print(f"  Added {fix_result.hydrogens_added} hydrogens")
       print(f"  Converted {fix_result.residues_converted} residues")
       
       # Step 2: Analyze fixed structure
       analyzer = MolecularInteractionAnalyzerractionAnalyzer(ParametersDefault())
       results = analyzer.analyze_file(fixed_file)
       
       print(f"Analysis results:")
       print(f"  Hydrogen bonds: {len(results.hydrogen_bonds)}")
       print(f"  Halogen bonds: {len(results.halogen_bonds)}")
       
       return results, fix_result

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   import os
   from concurrent.futures import ProcessPoolExecutor

   def fix_structure_batch(pdb_files, output_dir):
       """Fix multiple PDB structures in parallel."""
       
       def fix_single_file(pdb_file):
           fixer = PDBFixer()
           output_file = os.path.join(output_dir, f"fixed_{os.path.basename(pdb_file)}")
           
           try:
               result = fixer.fix_structure_file(pdb_file, output_file)
               return {"file": pdb_file, "success": True, "result": result}
           except Exception as e:
               return {"file": pdb_file, "success": False, "error": str(e)}
       
       # Process files in parallel
       with ProcessPoolExecutor() as executor:
           results = list(executor.map(fix_single_file, pdb_files))
       
       # Summarize results
       successful = [r for r in results if r["success"]]
       failed = [r for r in results if not r["success"]]
       
       print(f"Successfully fixed {len(successful)} structures")
       print(f"Failed to fix {len(failed)} structures")
       
       return results

Quality Control
---------------

**Validation Metrics:**

The fixer provides comprehensive quality metrics:

.. code-block:: python

   # Quality assessment after fixing
   validation_result = fixer.validate_structure("fixed_structure.pdb")
   
   print(f"Structure Quality Metrics:")
   print(f"  Completeness: {validation_result.completeness:.1%}")
   print(f"  Geometric validity: {validation_result.geometry_score:.2f}")
   print(f"  Chemical consistency: {validation_result.chemistry_score:.2f}")
   print(f"  Overall quality: {validation_result.overall_score:.2f}")

**Common Issues and Solutions:**

- **Missing Atoms**: Automatically detected and reconstructed
- **Steric Clashes**: Resolved through geometric optimization
- **Invalid Residues**: Converted to standard equivalents
- **Chain Breaks**: Flagged for manual inspection
- **Unusual Geometries**: Validated against chemical expectations