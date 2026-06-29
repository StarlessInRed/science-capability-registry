# Science Capability Registry - AGENTS.md

This file is the repository-level Codex instruction for `science-capability-registry`. It records only rules specific to this repository and extends the parent `D:\Projects\AGENTS.md` rules.

## Project Role

This repository is a personal and MatOS-compatible scientific capability registry.

It converts scientific computing webpages, official examples, documentation, papers, and benchmark cases into structured, executable, verifiable scientific capabilities.

The goal is not to teach the user how to manually operate each scientific software package. The goal is to help the user understand software capabilities, assign implementation tasks to interns or agents, and evaluate whether the resulting capability is scientifically correct and suitable for personal or MatOS integration.

## Core Principle

A webpage is not a tutorial. It is capability evidence.

An official example is not learning material. It is a benchmark candidate.

An intern task is not "run this demo." It is "turn this benchmark into a reusable, parameterized, validated scientific capability."

## Required Output Model

For every scientific software asset, produce:

1. Capability card
2. Problem definition
3. Physics / governing model summary
4. Input parameters
5. Output quantities
6. Benchmark source
7. Validation criteria
8. Intern implementation task
9. Integration pathway
10. Risks and limitations

## Scientific Standards

Do not accept superficial demos.

Every computational capability must be evaluated for:

- governing equations or model class
- boundary conditions
- initial conditions
- mesh or discretization requirements
- solver configuration
- convergence behavior
- conservation or physical constraints
- expected physical trends
- output reproducibility
- failure modes
- automatic validation

## Integration Standards

Each capability should eventually support:

- natural language task input
- structured JSON/YAML parameter schema
- automatic case generation
- solver execution
- result extraction
- plotting
- validation
- report generation
- registration into a capability registry when appropriate

## User Role

The user is the capability owner and evaluator.

The user should not be forced to learn each software as an operator. Instead, provide enough abstraction so the user can judge:

- what the software can do
- what the case proves
- what the intern must implement
- whether the output is scientifically correct
- whether the capability can enter personal workflows or MatOS

## Default Webpage Intake

When the user provides a scientific computing webpage and asks to convert it into a scientific capability asset, do not ask them to restate the project background. Execute this workflow:

1. Determine the correct `software`, `domain`, and `capability`.
2. Search existing assets before creating a new one.
3. Create or update the capability card under `software/<software>/assets/`.
4. If the source is an official example, register it as a benchmark candidate.
5. Generate or update the corresponding intern task under `tasks/`.
6. Generate validation criteria covering numerical output, convergence, physical correctness, and artifact completeness.
7. If a similar capability already exists, update the existing capability card instead of creating a duplicate.
8. Update `software/<software>/examples_index.md` so the source is discoverable.

## Collaboration Model

Use this repository as the durable context shared across local Codex, Codex Web, ChatGPT, GitHub, interns, personal workflows, MatOS integration work, and human reviewers.

- Strategy definition, capability decomposition, and validation logic belong in project conversations and then must be distilled into repository documents.
- Local repository work should create files, run checks, implement packages, and validate outputs directly in this repository.
- Remote collaboration should happen through GitHub, Codex Web, ChatGPT GitHub connectors, pull requests, and review comments after this repository is pushed.
- Do not assume ChatGPT project conversations are automatically available to local Codex or Codex Web. Durable context must be written into this repository.
- Use `AGENTS.md` for execution rules, `docs/` for stable background and methods, `software/` for software-specific assets, `tasks/` for intern work, `schemas/` for contracts, and `reports/` for validation evidence.
- Project-local Codex environment setup may be stored under `.codex/` when it needs to travel with the Git repository.

## Writing Style

Use Chinese for explanation documents unless asked otherwise.

Be precise, technical, and implementation-oriented.

Avoid vague AI slogans.

Avoid treating MatOS as a simple wrapper around software. MatOS is one possible integration target for capabilities organized through knowledge, tools, skills, agents, workflows, and validation loops.
