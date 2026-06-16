---
name: add-doc
description: Add XML documentation to selected project
disable-model-invocations: false
---

Add XML documentation to all classes, records, structs and their public and protected members in the project at "<project full path>".

## Rules

- Describe purpose and intent (what, not how)
- Always include a concise <summary>
- Add <remarks> or <example> only if the member name and parameters alone don't make usage clear
- For booleans, keywords and literals: prefer <see langword="..."/>
- For references to other types or members: prefer <see cref="..."/> over plain text
- For parameters and return values: always add <param> and <returns> when non-obvious
- Do not document private or internal members
- On partial classes, document only the primary declaration
