# CardioVascular Modeling Platform

The CardioVascular Modeling Platform (CVMP) is the next generation of the Vascular Model Repository (VMR). This effort is alongside support of the existing VMR until it is mature and then the VMR will be deprecated.

## Working Documentation

> [!NOTE]
> This is a work in progress, and these working documents are intended to represent the latest understanding.

The working roadmap for this effort can be seen in [/docs/roadmap.md](docs/roadmap.md).

The working architecture for this effort can be seen in [/docs/architecture.md](docs/architecture.md).

## Existing Limitations

This effort has identified three main issues with the existing VMR:

1. Existing maintenance is high - current upload procedure has many steps across the front-end and the back-end.

2. No support for immutabilitable records, versioning, and traceability.

3. A case centered database limits extensibility for e.g., machine learning oriented use cases.

## Aims

This effort has two primary aims:

1. Improve maintainability by using mature libraries and implementation workflows.

2. Improve extensibilty by refactoring around an artifact centered database instead of case centered.
