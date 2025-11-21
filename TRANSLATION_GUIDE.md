# Translation Guide

Thank you for helping translate the Product Knowledge Graph Manager! This guide will help you understand how to add or update translations for the application.

## Overview

The application uses a JavaScript-based internationalization (i18n) system that:
- Loads translations from JSON files
- Supports multiple languages
- Falls back to English for missing translations
- Automatically switches UI language based on user selection

## File Structure

```
static/i18n/
├── en.json       # English (default/fallback)
├── es-ES.json    # Spanish (Spain) - Complete
├── ar.json       # Arabic - Needs translation
├── de.json       # German - Needs translation
├── fr.json       # French - Needs translation
├── pt-BR.json    # Portuguese (Brazil) - Needs translation
└── zh-CN.json    # Chinese (Simplified) - Needs translation
```

## Translation File Format

Each translation file is a JSON file with nested keys:

```json
{
  "section": {
    "key": "Translation text",
    "another_key": "Text with {variable} substitution"
  }
}
```

### Example

```json
{
  "nav": {
    "home": "Home",
    "search_button": "Search",
    "search_placeholder": "Search..."
  },
  "dashboard": {
    "title": "Knowledge Graph Dashboard",
    "total_entities": "Total Entities"
  }
}
```

## Translation Keys Reference

### App-Wide Strings (`app`)

| Key | English | Description |
|-----|---------|-------------|
| `app.title` | Product Knowledge Graph Manager | Application title |
| `app.brand` | Product Knowledge Graph | Brand name in navbar |
| `app.copyright` | © 2025 Product Knowledge Graph Manager | Footer copyright |

### Navigation (`nav`)

| Key | English | Description |
|-----|---------|-------------|
| `nav.home` | Home | Home link |
| `nav.graph` | Graph | Graph visualization link |
| `nav.patterns` | Patterns | Patterns library link |
| `nav.search_placeholder` | Search... | Search input placeholder |
| `nav.search_button` | Search | Search button text |

### Dashboard (`dashboard`)

| Key | English | Description |
|-----|---------|-------------|
| `dashboard.title` | Knowledge Graph Dashboard | Page title |
| `dashboard.total_entity_types` | Total Entity Types | Stat card label |
| `dashboard.product_types` | Product Types | Section title |
| `dashboard.supporting_entities` | Supporting Entities | Section title |
| `dashboard.total_entities` | Total Entities | Stat card label |
| `dashboard.product_badge` | Product | Badge text |
| `dashboard.supporting_badge` | Supporting | Badge text |
| `dashboard.items` | items | Item count suffix |

### Entity List (`entity_list`)

| Key | English | Description |
|-----|---------|-------------|
| `entity_list.back_to_dashboard` | ← Back to Dashboard | Back link |
| `entity_list.create_new` | + Create New | Create button |
| `entity_list.search_placeholder` | Search... | Search input placeholder |
| `entity_list.search_button` | Search | Search button |
| `entity_list.clear` | Clear | Clear search button |
| `entity_list.list_view` | List View | View toggle |
| `entity_list.table_view` | Table View | View toggle |
| `entity_list.actions` | Actions | Table column header |
| `entity_list.edit` | Edit | Edit button |
| `entity_list.previous` | ← Previous | Pagination button |
| `entity_list.next` | Next → | Pagination button |
| `entity_list.page_of` | Page {page} of {total} | Pagination text |
| `entity_list.no_items_found` | No {label} found. | Empty state message |
| `entity_list.clear_search` | Clear search | Link text |
| `entity_list.to_see_all` | to see all items. | Text continuation |

### Entity Detail (`entity_detail`)

| Key | English | Description |
|-----|---------|-------------|
| `entity_detail.back_to_list` | ← Back to {label} | Back link |
| `entity_detail.edit` | Edit | Edit button |
| `entity_detail.delete` | Delete | Delete button |
| `entity_detail.properties` | Properties | Section title |
| `entity_detail.relationships` | Relationships | Section title |
| `entity_detail.related` | Related | Relationship label |
| `entity_detail.type` | Type | Relationship type |
| `entity_detail.direction` | Direction | Relationship direction |
| `entity_detail.outgoing` | Outgoing | Direction label |
| `entity_detail.incoming` | Incoming | Direction label |
| `entity_detail.confirm_delete` | Are you sure you want to delete this {label}? | Confirmation message |
| `entity_detail.delete_warning` | This action cannot be undone. | Warning text |

### Entity Edit (`entity_edit`)

| Key | English | Description |
|-----|---------|-------------|
| `entity_edit.edit_title` | Edit {label} | Page title |
| `entity_edit.back_to_detail` | ← Back to Details | Back link |
| `entity_edit.save_changes` | Save Changes | Save button |
| `entity_edit.cancel` | Cancel | Cancel button |
| `entity_edit.delete` | Delete | Delete button |
| `entity_edit.confirm_delete` | Are you sure you want to delete this {label}? | Confirmation message |
| `entity_edit.delete_warning` | This action cannot be undone. | Warning text |
| `entity_edit.basic_info` | Basic Information | Section title |
| `entity_edit.additional_properties` | Additional Properties | Section title |

### Entity Create (`entity_create`)

| Key | English | Description |
|-----|---------|-------------|
| `entity_create.create_title` | Create New {label} | Page title |
| `entity_create.back_to_list` | ← Back to {label} List | Back link |
| `entity_create.create` | Create | Create button |
| `entity_create.cancel` | Cancel | Cancel button |
| `entity_create.basic_info` | Basic Information | Section title |
| `entity_create.required_field` | Required | Field marker |

### Search (`search`)

| Key | English | Description |
|-----|---------|-------------|
| `search.title` | Search Results | Page title |
| `search.results_for` | Results for "{query}" | Results header |
| `search.total_results` | {count} total results | Count display |
| `search.no_results` | No results found for "{query}" | Empty state |
| `search.try_different` | Try a different search term. | Suggestion text |
| `search.in` | in | Preposition for "in EntityType" |

### Graph (`graph`)

| Key | English | Description |
|-----|---------|-------------|
| `graph.title` | Graph Visualization | Page title |
| `graph.start_label` | Start Node Label | Input label |
| `graph.start_id` | Start Node ID | Input label |
| `graph.depth` | Depth | Input label |
| `graph.limit` | Limit | Input label |
| `graph.explore` | Explore | Button text |
| `graph.reset` | Reset | Button text |
| `graph.node_count` | {count} nodes | Count display |
| `graph.edge_count` | {count} edges | Count display |
| `graph.zoom_in` | Zoom In | Button tooltip |
| `graph.zoom_out` | Zoom Out | Button tooltip |
| `graph.fit_view` | Fit View | Button tooltip |
| `graph.select_node` | Select a node to start exploring | Empty state |
| `graph.loading` | Loading graph... | Loading message |

### Patterns (`patterns`)

| Key | English | Description |
|-----|---------|-------------|
| `patterns.title` | Query Patterns | Page title |
| `patterns.library` | Pattern Library | Section title |
| `patterns.visual_builder` | Visual Query Builder | Section title |
| `patterns.saved_patterns` | Saved Patterns | Section title |
| `patterns.new_pattern` | + New Pattern | Create button |
| `patterns.name` | Name | Field label |
| `patterns.description` | Description | Field label |
| `patterns.created` | Created | Column header |
| `patterns.execute` | Execute | Button text |
| `patterns.edit` | Edit | Button text |
| `patterns.delete` | Delete | Button text |
| `patterns.save` | Save Pattern | Button text |
| `patterns.cancel` | Cancel | Button text |
| `patterns.cypher_query` | Cypher Query | Field label |
| `patterns.results` | Results | Section title |
| `patterns.no_patterns` | No saved patterns yet. | Empty state |
| `patterns.create_first` | Create your first pattern using the visual builder. | Suggestion text |

### Common (`common`)

Common strings used throughout the application:

| Key | English | Description |
|-----|---------|-------------|
| `common.loading` | Loading... | Loading state |
| `common.error` | Error | Error title |
| `common.success` | Success | Success title |
| `common.confirm` | Confirm | Confirmation button |
| `common.yes` | Yes | Yes button |
| `common.no` | No | No button |
| `common.close` | Close | Close button |
| `common.save` | Save | Save button |
| `common.cancel` | Cancel | Cancel button |
| `common.delete` | Delete | Delete button |
| `common.edit` | Edit | Edit button |
| `common.create` | Create | Create button |
| `common.search` | Search | Search button |
| `common.filter` | Filter | Filter button |
| `common.sort` | Sort | Sort button |
| `common.export` | Export | Export button |
| `common.import` | Import | Import button |
| `common.refresh` | Refresh | Refresh button |
| `common.settings` | Settings | Settings link |
| `common.help` | Help | Help link |
| `common.about` | About | About link |

### Language Selector (`language`)

| Key | English | Description |
|-----|---------|-------------|
| `language.selector_label` | Language | Selector label |
| `language.change_language` | Change Language | Dropdown header |

## Variable Substitution

Some strings contain variables that are replaced at runtime. Variables are wrapped in curly braces: `{variable_name}`.

**Examples:**

```json
{
  "entity_list.page_of": "Page {page} of {total}",
  "search.results_for": "Results for \"{query}\"",
  "entity_detail.back_to_list": "← Back to {label}"
}
```

**Important:** Keep the variable names exactly as they appear in English. Only translate the text around them.

❌ Wrong:
```json
"entity_list.page_of": "Página {página} de {total}"
```

✅ Correct:
```json
"entity_list.page_of": "Página {page} de {total}"
```

## How to Add a Translation

### Step 1: Choose Your Language File

Open the appropriate JSON file from `static/i18n/`:
- Arabic: `ar.json`
- German: `de.json`
- French: `fr.json`
- Portuguese (Brazil): `pt-BR.json`
- Chinese (Simplified): `zh-CN.json`

### Step 2: Translate the Strings

Replace the English text with your translation, keeping:
- ✅ The same JSON structure
- ✅ The same key names
- ✅ Variable placeholders (`{variable}`)
- ✅ Special characters like arrows (←, →)
- ✅ Proper punctuation for your language

### Step 3: Test Your Translation

1. Save your JSON file
2. Start the application
3. Use the language selector (globe icon in navbar)
4. Check that:
   - All text appears in your language
   - Variables are replaced correctly
   - Layout looks good (no text overflow)
   - Special characters display correctly

### Step 4: Submit Your Translation

Create a pull request or send the translated file to the project maintainer.

## Translation Tips

### 1. Context Matters

Consider where the text appears:
- **Buttons**: Keep translations short (1-2 words if possible)
- **Titles**: Can be longer and more descriptive
- **Messages**: Should be complete sentences

### 2. Consistent Terminology

Use the same translation for the same term throughout:
- "Entity" → Choose one translation and stick with it
- "Property" → Use consistently
- "Search" → Use the same verb form

### 3. Formal vs. Informal

Choose an appropriate tone for your audience:
- Technical applications → More formal
- Consumer apps → More casual

Be consistent with your choice.

### 4. Text Length

Keep in mind that translations might be longer or shorter than English:
- Test in the UI to ensure text doesn't overflow
- Buttons should still look good with longer text
- Adjust spacing if needed

### 5. Right-to-Left (RTL) Languages

For Arabic:
- The app automatically handles RTL layout
- Focus on accurate translation
- The UI will flip direction automatically

### 6. Pluralization

Some languages have complex plural rules. For now:
- Use generic forms that work with any number
- Example: "items" instead of "1 item" / "2 items"
- Future versions may add plural support

### 7. Date and Number Formats

Currently not locale-specific. Future updates may include:
- Number formatting (1,000 vs 1.000)
- Date formatting (MM/DD/YYYY vs DD/MM/YYYY)
- Currency symbols

## Testing Checklist

Before submitting your translation:

- [ ] All strings are translated (no English text remains)
- [ ] Variables (`{var}`) are preserved exactly
- [ ] JSON syntax is valid (use a JSON validator)
- [ ] Text fits in UI elements (no overflow)
- [ ] Special characters display correctly
- [ ] Punctuation follows language conventions
- [ ] Terminology is consistent throughout
- [ ] Tone/formality is appropriate
- [ ] Tested in actual application

## Need Help?

If you have questions about:
- **Context**: Ask which part of the UI a string appears in
- **Technical terms**: Ask for screenshots or explanations
- **Variables**: Ask what value will replace the placeholder
- **Best practices**: Discuss with other translators

## Example: Complete Translation

Here's an example of translating a section to French:

**English (en.json):**
```json
{
  "nav": {
    "home": "Home",
    "graph": "Graph",
    "patterns": "Patterns",
    "search_placeholder": "Search...",
    "search_button": "Search"
  }
}
```

**French (fr.json):**
```json
{
  "nav": {
    "home": "Accueil",
    "graph": "Graphe",
    "patterns": "Modèles",
    "search_placeholder": "Rechercher...",
    "search_button": "Rechercher"
  }
}
```

## Current Translation Status

| Language | File | Status | Translator |
|----------|------|--------|------------|
| English | en.json | ✅ Complete | Built-in |
| Spanish (Spain) | es-ES.json | ✅ Complete | Built-in |
| Arabic | ar.json | ⏳ Needs Translation | You? |
| German | de.json | ⏳ Needs Translation | You? |
| French | fr.json | ⏳ Needs Translation | You? |
| Portuguese (Brazil) | pt-BR.json | ⏳ Needs Translation | You? |
| Chinese (Simplified) | zh-CN.json | ⏳ Needs Translation | You? |

## Thank You!

Your translation work helps make this application accessible to users around the world. We appreciate your contribution! 🌍

---

**Last Updated**: 2024-11-21
**Version**: 1.0.0
