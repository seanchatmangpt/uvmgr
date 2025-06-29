# Weaver Forge Bulk Generation Examples

This document provides comprehensive examples of Weaver Forge's bulk generation capabilities, demonstrating how to generate multiple features/components at once, similar to Hygen's bulk operations.

## 🚀 Quick Start Examples

### 1. **Bulk Component Generation**

Generate multiple React components at once:

```bash
# Generate 3 components with the same template
uvmgr weaver-forge bulk-generate component UserProfile ProductCard OrderItem

# Generate with custom parameters
uvmgr weaver-forge bulk-generate component Button Input Select --params '{"style": "styled-components", "typescript": true}'

# Parallel generation for better performance
uvmgr weaver-forge bulk-generate component Header Footer Sidebar Nav --parallel

# Dry run to see what would be generated
uvmgr weaver-forge bulk-generate component Modal Dialog Popup --dry-run
```

### 2. **Bulk API Generation**

Generate multiple API endpoints:

```bash
# Generate REST API endpoints
uvmgr weaver-forge bulk-generate api users products orders categories

# Generate with specific parameters
uvmgr weaver-forge bulk-generate api auth profile settings --params '{"framework": "express", "validation": true}'

# Generate with custom output path
uvmgr weaver-forge bulk-generate api posts comments likes --output ./src/api
```

### 3. **Bulk Scaffold Generation**

Create multiple project scaffolds:

```bash
# Create multiple React apps
uvmgr weaver-forge bulk-scaffold react-app frontend admin dashboard

# Create multiple API projects
uvmgr weaver-forge bulk-scaffold node-api users-api products-api orders-api --parallel

# Create Python packages
uvmgr weaver-forge bulk-scaffold python-package utils core models --params '{"testing": "pytest"}'
```

## 📋 Batch Specification Files

### 1. **Simple Batch File (JSON)**

```json
{
  "generations": [
    {
      "template": "component",
      "name": "UserProfile",
      "parameters": {
        "style": "styled-components",
        "typescript": true,
        "props": ["name", "email", "avatar"]
      }
    },
    {
      "template": "component",
      "name": "ProductCard",
      "parameters": {
        "style": "css-modules",
        "typescript": true,
        "props": ["title", "price", "image"]
      }
    },
    {
      "template": "component",
      "name": "OrderItem",
      "parameters": {
        "style": "styled-components",
        "typescript": false,
        "props": ["id", "quantity", "total"]
      }
    }
  ]
}
```

### 2. **Complex Batch File (YAML)**

```yaml
# batch-spec.yaml
generations:
  - template: component
    name: Header
    parameters:
      style: styled-components
      typescript: true
      props: [title, logo, navigation]
    subdir: layout

  - template: component
    name: Footer
    parameters:
      style: css-modules
      typescript: true
      props: [links, copyright]
    subdir: layout

  - template: api
    name: users
    parameters:
      framework: express
      validation: true
      authentication: true
    subdir: api

  - template: api
    name: products
    parameters:
      framework: fastify
      validation: true
      pagination: true
    subdir: api

scaffolds:
  - type: react-app
    name: frontend
    parameters:
      typescript: true
      testing: jest
      styling: styled-components
    subdir: apps

  - type: node-api
    name: backend
    parameters:
      framework: express
      database: postgres
      authentication: jwt
    subdir: apps
```

### 3. **Template Creation Batch File**

```yaml
# template-specs.yaml
- name: react-hook
  type: custom
  description: "Custom React hook template"

- name: redux-slice
  type: custom
  description: "Redux toolkit slice template"

- name: graphql-resolver
  type: api
  description: "GraphQL resolver template"

- name: docker-service
  type: workflow
  description: "Docker service template"
```

## 🎯 Advanced Usage Patterns

### 1. **Conditional Generation**

```yaml
# conditional-batch.yaml
generations:
  - template: component
    name: Button
    parameters:
      variants: [primary, secondary, danger]
      sizes: [small, medium, large]
      disabled: true
    condition: "include_components"

  - template: api
    name: auth
    parameters:
      strategies: [jwt, oauth, session]
      providers: [google, github, facebook]
    condition: "include_auth"
```

### 2. **Multi-Language Generation**

```yaml
# multi-lang-batch.yaml
generations:
  - template: component
    name: UserCard
    parameters:
      language: typescript
      framework: react
      styling: styled-components

  - template: component
    name: UserCard
    parameters:
      language: javascript
      framework: vue
      styling: scss

  - template: component
    name: UserCard
    parameters:
      language: python
      framework: flask
      styling: jinja2
```

### 3. **Microservices Generation**

```yaml
# microservices-batch.yaml
scaffolds:
  - type: microservice
    name: user-service
    parameters:
      language: node
      framework: express
      database: mongodb
      messaging: redis

  - type: microservice
    name: product-service
    parameters:
      language: python
      framework: fastapi
      database: postgres
      messaging: rabbitmq

  - type: microservice
    name: order-service
    parameters:
      language: go
      framework: gin
      database: mysql
      messaging: kafka
```

## 🔧 CLI Command Examples

### 1. **Batch Generation Commands**

```bash
# Generate from batch file
uvmgr weaver-forge batch batch-spec.json

# Generate with parallel execution
uvmgr weaver-forge batch batch-spec.yaml --parallel

# Dry run to preview
uvmgr weaver-forge batch batch-spec.json --dry-run

# Custom output directory
uvmgr weaver-forge batch batch-spec.yaml --output ./generated
```

### 2. **Bulk Template Management**

```bash
# Create multiple templates
uvmgr weaver-forge bulk-create template-specs.yaml

# Create with interactive mode
uvmgr weaver-forge bulk-create template-specs.yaml --interactive

# Create in custom directory
uvmgr weaver-forge bulk-create template-specs.yaml --output ./custom-templates
```

### 3. **Bulk Validation**

```bash
# Validate all templates
uvmgr weaver-forge bulk-validate

# Validate specific templates
uvmgr weaver-forge bulk-validate --templates component api workflow

# Auto-fix validation issues
uvmgr weaver-forge bulk-validate --fix

# Generate validation report
uvmgr weaver-forge bulk-validate --report validation-report.json
```

## 📊 Performance Optimization

### 1. **Parallel Execution**

```bash
# Enable parallel generation for better performance
uvmgr weaver-forge bulk-generate component A B C D E F --parallel

# Parallel scaffold generation
uvmgr weaver-forge bulk-scaffold react-app app1 app2 app3 --parallel

# Parallel batch processing
uvmgr weaver-forge batch large-batch.yaml --parallel
```

### 2. **Batch Size Optimization**

```yaml
# optimal-batch.yaml - Process in chunks
generations:
  # Chunk 1: Core components
  - template: component
    name: Layout
    parameters: { type: "layout" }
  - template: component
    name: Navigation
    parameters: { type: "navigation" }
  - template: component
    name: Footer
    parameters: { type: "footer" }

  # Chunk 2: Feature components
  - template: component
    name: UserProfile
    parameters: { type: "feature" }
  - template: component
    name: ProductCard
    parameters: { type: "feature" }
  - template: component
    name: OrderItem
    parameters: { type: "feature" }
```

## 🎨 Template Examples for Bulk Generation

### 1. **React Component Template**

```ejs
// _templates/component.ejs.t
import React from 'react';
<% if (typescript) { %>
interface <%= Name %>Props {
  <% props.forEach(prop => { %>
  <%= prop %>: string;
  <% }); %>
}
<% } %>

<% if (style === 'styled-components') { %>
import styled from 'styled-components';

const Styled<%= Name %> = styled.div`
  padding: 1rem;
  border-radius: 4px;
  background-color: #f5f5f5;
`;
<% } %>

export const <%= Name %>: React.FC<<%= Name %>Props> = ({
  <% props.forEach((prop, index) => { %>
  <%= prop %><%= index < props.length - 1 ? ',' : '' %>
  <% }); %>
}) => {
  return (
    <% if (style === 'styled-components') { %>
    <Styled<%= Name %>>
    <% } else { %>
    <div className="<%= name_kebab %>">
    <% } %>
      <h2><%= Name %></h2>
      {/* Add your component content here */}
    <% if (style === 'styled-components') { %>
    </Styled<%= Name %>>
    <% } else { %>
    </div>
    <% } %>
  );
};
```

### 2. **API Endpoint Template**

```ejs
// _templates/api.ejs.t
import { Router } from 'express';
<% if (validation) { %>
import { validateRequest } from '../middleware/validation';
<% } %>
import { <%= Name %>Service } from '../services/<%= name.toLowerCase() %>.service';

const router = Router();

/**
 * @route GET /api/<%= name.toLowerCase() %>
 * @desc Get all <%= name.toLowerCase() %> items
 */
router.get('/', async (req, res) => {
  try {
    const items = await <%= Name %>Service.getAll();
    res.json({ success: true, data: items });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * @route POST /api/<%= name.toLowerCase() %>
 * @desc Create new <%= name.toLowerCase() %> item
 */
router.post('/', <% if (validation) { %>validateRequest, <% } %>async (req, res) => {
  try {
    const item = await <%= Name %>Service.create(req.body);
    res.status(201).json({ success: true, data: item });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

export default router;
```

## 🔍 Validation and Quality Assurance

### 1. **Template Validation Rules**

```yaml
# validation-rules.yaml
rules:
  - name: "template_structure"
    description: "Check template directory structure"
    severity: "error"
    
  - name: "parameter_validation"
    description: "Validate template parameters"
    severity: "warning"
    
  - name: "syntax_check"
    description: "Check template syntax"
    severity: "error"
    
  - name: "naming_convention"
    description: "Enforce naming conventions"
    severity: "warning"
```

### 2. **Quality Metrics**

```bash
# Generate quality report
uvmgr weaver-forge bulk-validate --report quality-report.json

# Auto-fix common issues
uvmgr weaver-forge bulk-validate --fix

# Validate specific quality aspects
uvmgr weaver-forge bulk-validate --templates component --report component-quality.json
```

## 🚀 Migration from Hygen

### 1. **Hygen to Weaver Forge Migration**

```bash
# Old Hygen command
hygen component new UserProfile ProductCard OrderItem

# New Weaver Forge command
uvmgr weaver-forge bulk-generate component UserProfile ProductCard OrderItem

# Old Hygen batch
hygen init self

# New Weaver Forge batch
uvmgr weaver-forge batch batch-spec.json
```

### 2. **Template Migration**

```bash
# Convert Hygen templates
uvmgr weaver-forge migrate --from-hygen --source _templates

# Validate migrated templates
uvmgr weaver-forge bulk-validate --templates migrated-templates

# Test generation
uvmgr weaver-forge bulk-generate component TestComponent --dry-run
```

## 📈 Monitoring and Analytics

### 1. **Generation Metrics**

```bash
# View generation statistics
uvmgr weaver-forge status --metrics

# Detailed performance metrics
uvmgr weaver-forge status --detailed --metrics
```

### 2. **Performance Tracking**

```yaml
# performance-tracking.yaml
metrics:
  - name: "generation_time"
    type: "histogram"
    description: "Time taken for generation"
    
  - name: "success_rate"
    type: "gauge"
    description: "Generation success rate"
    
  - name: "files_created"
    type: "counter"
    description: "Total files created"
```

## 🎯 Best Practices

### 1. **Batch File Organization**

- Keep batch files in version control
- Use descriptive names for batch files
- Document batch file purposes
- Test batch files with `--dry-run`

### 2. **Performance Optimization**

- Use parallel execution for large batches
- Break large batches into smaller chunks
- Monitor generation performance
- Optimize template complexity

### 3. **Quality Assurance**

- Validate templates regularly
- Use auto-fix for common issues
- Generate quality reports
- Monitor success rates

### 4. **Team Collaboration**

- Share batch files with team
- Document batch file usage
- Establish naming conventions
- Review generated code quality

---

*Weaver Forge Bulk Generation: Power and Efficiency Combined* 🚀 