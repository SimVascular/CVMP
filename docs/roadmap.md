# CVMP Roadmap

> [!NOTE]
> This document is a work in progress and is subject to change

The CVMP represents the next architecture around a public repository for cardiovascular and vascular models.

## Overall aims/strategy

1. Develop new database *alongside* existing VMR.
2. Continue minimal maintenance of existing VMR. This includes allowing for uploads according to the existing procedure.
3. Target "Case View" as first use case to replicate existing VMR features.

## Phases / Milestones

### 1. Prototype phase

Determine feasibility by pressure testing working architecture and design choices

[ ] Establish prototype of new backend and frontend (Alex)

    [ ] Create mock SQLite database covering data tagged with Cases and Papers
    [ ] Create a mockup frontend, allowing for custom filtering Cases and Papers of the same backend
    [ ] Investigate feasibility of client-side parsing of larger SQLite databse in front-end using mocked large database

[ ] Establish prototype of ingestion check scripts (Numi)

    [ ] Create a mesh check abstraction using a single existing check.
    [ ] Assemble a minimal "use case" check by applying a series of primitive (indivisible) steps.
    [ ] Apply the "use case" check to an existing legacy dataset.

[ ] Determine feasibility of parallel

### 2. Migration Phase

Move legacy data into new format, prepare new front end and tools. Improve robustness as we go. End of migration should be the final tools / checks needed.

### 3. Testing phase (Case View)

Parallel systems in place, allow for users to swap between databases and give feedback.

### 3. Switchover Milestone

Legacy VMR should be archived once successful switchover. Switchover migration success should be determined by tests and user feedback/testing.

### 4. Extension Phase

Create new views based on new use cases
