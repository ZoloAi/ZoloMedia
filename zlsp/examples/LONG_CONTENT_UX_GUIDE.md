# Long-Form Content in Lists - UX Guide

## The Problem

When list items contain paragraph-length content, the inline bracket syntax becomes **unreadable**:

```yaml
# ❌ UNREADABLE - All content crammed on one line
items: [The first principle of effective user interface design is clarity. Users should immediately understand what they can do and how to do it. This means using familiar patterns and clear labels and intuitive navigation structures that guide users naturally through their tasks., The second principle focuses on consistency across the entire application. When similar actions produce similar results and similar elements behave in similar ways users can transfer their knowledge from one part of the system to another reducing cognitive load and learning time., [Nested content often requires even more explanation and context. For example when discussing implementation details you might need to provide code examples explain edge cases and describe the rationale behind certain design decisions., Another nested item with substantial content. This could be a detailed explanation of an algorithm a step-by-step tutorial or documentation for a complex feature that requires multiple paragraphs to properly explain.]]
```

## The Solution

Use **block dash syntax** for readable, maintainable list content:

```yaml
# ✅ READABLE - Each item on its own line(s) with clear hierarchy
items:
    - The first principle of effective user interface design is clarity. Users should immediately understand what they can do and how to do it. This means using familiar patterns, clear labels, and intuitive navigation structures that guide users naturally through their tasks.
    - The second principle focuses on consistency across the entire application. When similar actions produce similar results and similar elements behave in similar ways, users can transfer their knowledge from one part of the system to another, reducing cognitive load and learning time.
    -
        - Nested content often requires even more explanation and context. For example, when discussing implementation details, you might need to provide code examples, explain edge cases, and describe the rationale behind certain design decisions.
        - Another nested item with substantial content. This could be a detailed explanation of an algorithm, a step-by-step tutorial, or documentation for a complex feature that requires multiple paragraphs to properly explain.
        -
            - Deeply nested items can also contain long-form content. This is particularly useful for hierarchical documentation, tutorial sequences, or breaking down complex concepts into digestible chunks while maintaining their logical relationships.
    - Back at the root level, we continue with more substantial content. This demonstrates how the syntax gracefully handles transitions between different nesting levels while keeping everything readable and maintainable.
```

## Syntax Rules

### Block Dash Syntax for Nested Lists

1. **Each item starts with a dash (`-`) on its own line**
2. **Content follows the dash** (same line or continued on next lines)
3. **Nested items are indented** by 4 spaces per level
4. **To nest items, use a standalone dash** followed by indented dash items:

```yaml
items:
    - Root item 1
    - Root item 2
    -                    # ← Standalone dash introduces nested list
        - Nested item A
        - Nested item B
        -                # ← Another standalone dash for deeper nesting
            - Deeply nested item
    - Back to root item 3
```

### When to Use Each Syntax

| Syntax | Best For | Example |
|--------|----------|---------|
| **Block Dash** | Long paragraphs, documentation, detailed explanations | `- This is a long explanation...` |
| **Inline Brackets** | Short items, compact lists, simple data | `[item1, item2, item3]` |
| **Hybrid** | Mixed content with both short and long items | See example below |

## Real-World Examples

### ✅ Hybrid Approach (Recommended)

```yaml
zUL:
    style: [bullet, circle, square]
    items:
        - Short item
        - Another brief item
        - This is a longer item that provides substantial information about a particular topic, explaining concepts in detail and providing context that users need to understand the full picture.
        - [Short nested 1, Short nested 2, Short nested 3]  # ← Compact for short items
        -
            - Long nested item that requires multiple lines of explanation to properly convey the necessary information and context for users.
            - [Brief sub-item A, Brief sub-item B]  # ← Mix and match!
            - Another detailed nested explanation with sufficient length to warrant the block dash format rather than cramming it into an inline bracket array.
```

### Documentation Example

```yaml
zUL:
    style: [bullet, circle]
    items:
        - Introduction: This guide explains the core principles of the framework.
        -
            - Installation: Follow these steps to get started with the framework in your project.
            - Configuration: The configuration file accepts the following options with detailed explanations for each parameter.
            -
                - Advanced options: These settings are for power users who need fine-grained control over the framework's behavior.
                - Performance tuning: Adjust these parameters to optimize for your specific use case and hardware configuration.
        - Usage: Once installed and configured, you can begin using the framework's features.
```

### Tutorial Sequence Example

```yaml
zOL:
    style: [number, alpha, roman]
    items:
        - Set up your development environment by installing the required dependencies and configuring your IDE with the recommended extensions.
        - Create a new project using the command-line tool, which will scaffold a basic application structure with best-practice defaults.
        -
            - Add database configuration to your environment file
            - Run the migration script to set up tables
            -
                - Review the generated schema
                - Customize as needed for your use case
        - Begin developing your features following the architectural patterns outlined in the documentation.
```

## Key Benefits

✅ **Readable** - Easy to scan and understand hierarchical structure  
✅ **Maintainable** - Simple to edit, add, or remove items  
✅ **Git-friendly** - Line-by-line diffs show exactly what changed  
✅ **Natural** - Feels like writing documentation, not code  
✅ **Flexible** - Mix short and long content as needed  

## Description Lists (zDL) with Long Content

Description lists require special attention when `desc` values are paragraph-length. The same readability principles apply:

### ✅ Readable zDL (Multiline Flow Style)

```yaml
zDL:
    items: [
        {
            term: "User Interface Consistency",
            desc: [
                "Consistency in user interface design means maintaining uniformity in visual elements, interaction patterns, and terminology across the entire application. When users encounter similar elements in different contexts, they should behave predictably, reducing cognitive load and improving usability.",
                "This principle extends beyond just visual consistency to include behavioral consistency, where similar actions produce similar results, and conceptual consistency, where the application's underlying model remains coherent throughout the user experience."
            ]
        },
        {
            term: "Progressive Disclosure",
            desc: "Progressive disclosure is a design technique that sequences information and actions across multiple screens or steps, revealing complexity gradually as users need it."
        }
    ]
```

### ❌ Unreadable zDL (Everything Inline)

```yaml
# DO NOT USE THIS FOR LONG CONTENT!
zDL:
    items: [{term: User Interface Consistency, desc: [Consistency in user interface design means maintaining uniformity in visual elements interaction patterns and terminology across the entire application. When users encounter similar elements in different contexts they should behave predictably reducing cognitive load and improving usability., This principle extends beyond just visual consistency to include behavioral consistency where similar actions produce similar results and conceptual consistency where the applications underlying model remains coherent throughout the user experience.]}, {term: Progressive Disclosure, desc: Progressive disclosure is a design technique that sequences information and actions across multiple screens or steps revealing complexity gradually as users need it.}]
```

### ✅ Hybrid zDL (Recommended)

```yaml
zDL:
    items: [
        {term: "API", desc: "Application Programming Interface"},
        {term: "REST", desc: "Representational State Transfer"},
        {
            term: "Microservices Architecture",
            desc: "Microservices architecture is an approach to building applications as a collection of loosely coupled, independently deployable services. Each service focuses on a specific business capability and can be developed, deployed, and scaled independently, promoting organizational agility and technical flexibility."
        },
        {term: "HTTP", desc: "Hypertext Transfer Protocol"}
    ]
```

**Key Insight:** Use inline `{term: ..., desc: ...}` for short definitions, but break to multiline format when descriptions exceed ~100 characters or need multiple sentences.

## Testing

All formats have been tested and verified:
- ✅ Block dash syntax parses correctly
- ✅ Inline bracket/brace syntax works for compact data
- ✅ Hybrid approach combines both seamlessly
- ✅ Multiline flow style (JSON-like) for structured objects
- ✅ Tokenization is correct for LSP (syntax highlighting)
- ✅ Works in both Terminal and Bifrost rendering modes
- ✅ Description lists (zDL) support paragraph-length content

See `zlsp/examples/advanced.zolo`:
- **Tests 17-19:** Regular list items (zUL) with long content
- **Tests 20-22:** Description lists (zDL) with long term/desc pairs
