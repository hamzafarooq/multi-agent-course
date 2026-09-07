# DESIGN.md — LUMINA

> Copy this to `DESIGN.md` and answer the five questions **before you open an editor**.
> `eval/build-report.mjs` reads it by heading, so keep the five headings; everything under
> each one is yours. It renders as the design section of your `/evals` page, which means a
> stranger reads it and grades it. Aim for a paragraph each — specific to the choices you
> actually made, not a restatement of the PRD.
>
> Delete this block when you answer.

## Components

What are the pieces of your system, and where does each one run? Name them. Include the
things that are not services — the jobs collection, the search cache, the run logs — if
they carry state or make decisions.

## Responsibilities

For each component: what is it the only one allowed to do? The interesting sentences here
are the exclusions. Which component may hold a provider key? Which may talk to the browser?
Which decides that a request is over its cap?

## Communication

How does each pair of components talk, and why that way? HTTP, SSE, a Mongo collection
polled by a worker. Say what happens to an in-flight request when the thing on the other
end is down.

## State

What is stored, where, and who owns it? Which state is authoritative and which is a cache
you could delete without losing anything? What is the consistency story for a document that
has been written but is not yet searchable?

## Trade-offs

Three or four decisions you made that a reasonable engineer would have made differently,
and what you gave up. "Atlas Vector Search instead of a dedicated vector store: one
document per citation, at the cost of the M0 three-index limit." Include at least one you
are unsure about.
