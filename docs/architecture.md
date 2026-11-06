# CVMP Architecture

> ![NOTE]
> This document is a work in progress and is subject to change

## Key Takeaways

* Communication between the backend and the frontend is via a versioned SQLite file snapshot representing the current database state
  * Snapshot is generally append only -- stale snapshots should remain valid. Exceptions allowed for data that must be removed, e.g. PHI accidentally uploaded. In this case, as much metadata remains for provenance tracking.
  * Frontends download the SQlite database file and parses locally
  * Database contains links to the artifact downloads, artifacts are not stored directly in the database
* Data stored as relational database between logical artifacts
  * Traditional concepts such as "Case" or "Publication Dataset" represent pre-designed views over the logical artifacts.
  * Views are provided for convenience to the user, but users can design their own views if desired.
* Flexible backend, strict intake (uploads based on use cases, not arbitrary)
  * Artifacts + relationships have minimal requirements for maximum extensibility
  * Curation is peformed at the intake boundary and the checks performed are driven by use cases
  * Use case uploads are strictly controlled
* Artifacts are largely immutable (data content immutable, metadata has controlled mutability) and versioned

``` mermaid
flowchart LR
    subgraph SERVER["Tetralogy Server (Stanford)"]
        direction LR
        ING["Intake Scripts"]
        DB[("SQLite Catalog")]
        DATA[("Artifacts")]

        ING -->|"Update"| DB
        ING -->|"Add/edit/remove"| DATA
    end

    subgraph CLIENTS["Clients"]
        direction TB
        WEB["Github Pages Website"]
        CLI["CLI tool"]
    end

    DB -->|"Download · Local SQL queries"| WEB
    DB -->|"Download · Local SQL queries"| CLI

    DATA -->|"Direct Download"| WEB
    DATA -->|"Direct Download"| CLI

```

## Logical Artifacts

Version 1

* ImageVolumetric
  * 3D MRI, CT
  * 1 Image series, a single Scan can have multiple series, each are considered an “image”
* PathSet
  * All paths, basically everything that you would SV path planning comes out as one “PathSet”
* ContourSegmentationSet (2D)
  * Contour groups, attached to PathSet, downloaded all together (so everything SV “contours folder” → but there can be multiple contour set (e.g., stenosis) attached to PathSet
* SegmentationVolumetric
  * Voxel label maps, attached to images
* GeometrySurfaceMesh
  * Can be with or without IDs
  * Labeled surface mesh
* MeshVolumetric:
  * (seperate)
  * Usually comes after the model
* Centerlines
  * Derivative of Geometric Model / Surface Mesh
* SimulationInput
  * (standalone & runable - including mesh, input file (solver.inp or solver.xml))
* SimulationResult

## Upload / Use Cases

Use Case Groupings Uploads in priority order

1. SV project
2. Image+Segmentation Pair(s)
3. Image+Geometric Model Pair(s) + Volumetric
4. Image(s) only
5. Geometric Model + Volumetric + Simulation Input + Simulation Results
6. Geometric Model only (+ Centerline) (synthetic)
