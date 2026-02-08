# Persistent Memory System Guide
## Enterprise AI Platform - Never Forget Feature

---

## Overview

The Enterprise AI Platform features a **Persistent Memory System** that allows the AI to remember everything about employees, teams, projects, and past conversations - **forever**. This memory survives:

- ✅ Chat session closures
- ✅ Browser restarts
- ✅ User logout/login
- ✅ Days, weeks, months of inactivity
- ✅ Employee returning after leaving the job

---

## How It Works

### Memory Storage

When a user interacts with the AI, the system automatically extracts and stores:

1. **Employee Profile Facts**
   - Name, hire date, specializations
   - Previous companies, skills
   - Certifications and training

2. **Team & Company Context**
   - Team name, manager, teammates
   - Department, role
   - Company-specific knowledge

3. **Active Projects**
   - Current projects with status
   - Project descriptions
   - Last discussed date

4. **Project History**
   - Completed projects
   - Role in each project
   - Outcomes and learnings

5. **Conversation Summaries**
   - Key topics discussed
   - Resolutions reached
   - Decisions made
   - Action items

6. **Domain Expertise**
   - Familiar WC class codes
   - States worked on
   - WC systems experience

7. **Technical Preferences**
   - Preferred languages
   - Favorite tools
   - Development environment

8. **Frequent Topics**
   - Most discussed subjects
   - Areas of interest

---

## Using Persistent Memory

### For Users

#### Automatic Memory
The AI automatically remembers context from conversations:

```
User: "I'm working on the California WC policy migration project"
AI: [Stores: Active Project = "California WC Policy Migration"]

[User closes chat, comes back next week]

User: "What's the status of my project?"
AI: "Based on your work with the California WC Policy Migration project, 
     let me check the current status..."
```

#### Memory-Aware Responses

The AI references past conversations:

```
User: "How do I map class codes?"

AI: "As we discussed in your previous conversations about the California 
     WC Policy Migration project, class code mapping involves...
     
     Since you're familiar with class codes 8810 and 8820 from your 
     previous work, I'll focus on the mapping process..."
```

### For Developers

#### API Endpoints

**Get User Memory**
```http
GET /api/chat/memory
Authorization: Bearer <token>
```

**Update Employee Facts**
```http
POST /api/chat/memory/employee
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "hire_date": "2022-03-15",
  "specializations": ["data conversion", "WC policies"],
  "previous_companies": ["ABC Insurance"]
}
```

**Add Active Project**
```http
POST /api/chat/memory/project
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "WC Migration Phase 2",
  "status": "in_progress",
  "description": "Migrating California WC policies to Sapiens"
}
```

**Create Conversation Context**
```http
POST /api/chat/conversations
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "WC Migration Discussion",
  "context_key": "WC_Migration_Phase2"
}
```

**List Conversation Contexts**
```http
GET /api/chat/memory/contexts
Authorization: Bearer <token>
```

#### Memory Service Methods

```python
from app.services.memory_service import memory_service

# Get or create user memory
memory = await memory_service.get_or_create_user_memory(db, user_id)

# Update employee facts
await memory_service.update_employee_facts(db, user_id, {
    "full_name": "Jane Doe",
    "specializations": ["data conversion"]
})

# Add active project
await memory_service.add_active_project(db, user_id, {
    "name": "NY WC Implementation",
    "status": "planning"
})

# Add conversation summary
await memory_service.add_conversation_summary(
    db, user_id,
    topic="Rating algorithm issue",
    resolution="Fixed by updating the factor table"
)

# Update domain expertise
await memory_service.update_domain_expertise(db, user_id, {
    "familiar_class_codes": ["8810", "8820", "8832"],
    "states_worked": ["CA", "NY", "TX"]
})

# Get memory context for LLM
context = await memory_service.get_memory_context_for_llm(
    db, user_id, 
    include_conversation_context="WC_Migration_Phase2"
)
```

---

## Memory in Action

### Example 1: Returning User

```
[January 15, 2024 - First conversation]
User: "Hi, I'm Sarah from the Data Conversion team. I'm working on the 
       California WC policy migration."

AI: "Hello Sarah! I'll remember that you're on the Data Conversion team 
     working on California WC policy migration. How can I help you today?"

[User closes chat]

[February 20, 2024 - User returns after 5 weeks]
User: "Hi again"

AI: "Welcome back, Sarah! I remember you're with the Data Conversion team 
     working on the California WC policy migration project. 
     
     Last time we discussed class code validation. Would you like to 
     continue with that or is there something new I can help you with 
     for your migration project?"
```

### Example 2: Project Context

```
User: "I'm having issues with the rating calculation for class code 8810"

AI: "I see you're working on the California WC policy migration project. 
     For class code 8810 (Clerical) in California, the current base rate 
     is $0.25 per $100 of payroll.
     
     Since this is for your migration project, let me also check if there 
     are any special considerations for converted policies..."
```

### Example 3: Cross-Conversation Continuity

```
[Conversation 1 - Monday]
User: "How do I validate FEINs during conversion?"
AI: [Explains FEIN validation, stores topic]

[Conversation 2 - Wednesday]
User: "I'm getting errors on some of those validations"
AI: "Regarding the FEIN validations we discussed on Monday, the errors 
     might be due to... Let me help you troubleshoot."
```

---

## Memory Database Schema

### UserMemory Table
```sql
CREATE TABLE user_memories (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id),
    employee_facts JSONB,
    team_info JSONB,
    company_knowledge JSONB,
    active_projects JSONB,
    project_history JSONB,
    conversation_summaries JSONB,
    domain_expertise JSONB,
    tech_preferences JSONB,
    learning_progress JSONB,
    frequent_topics JSONB,
    custom_notes TEXT,
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### MemoryEntry Table (Granular Storage)
```sql
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    category VARCHAR(50),  -- employee, project, domain, etc.
    key VARCHAR(200),
    value TEXT,
    source_conversation_id UUID,
    confidence INTEGER DEFAULT 100,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### ConversationContext Table
```sql
CREATE TABLE conversation_contexts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    context_type VARCHAR(50),
    context_key VARCHAR(200),
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    conversation_ids JSONB,
    key_facts JSONB,
    decisions_made JSONB,
    action_items JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_conversation_at TIMESTAMP
);
```

---

## Testing Persistent Memory

### Test Case 1: Basic Memory Persistence

```python
# Step 1: User starts conversation and shares info
response = await client.post("/api/chat/messages", json={
    "content": "I'm John from Data Conversion, working on WC migration"
})

# Step 2: Close chat (simulate)
# Step 3: Start new conversation
response = await client.get("/api/chat/memory")
assert "Data Conversion" in response.json()["team_info"]["team"]
```

### Test Case 2: Project Memory

```python
# Add project
await client.post("/api/chat/memory/project", json={
    "name": "Test Project",
    "status": "active"
})

# Ask about project
response = await client.post("/api/chat/messages", json={
    "content": "What's the status of my project?"
})
assert "Test Project" in response.json()["content"]
```

### Test Case 3: Conversation Context

```python
# Create conversation with context
conv = await client.post("/api/chat/conversations", json={
    "context_key": "TEST_CONTEXT"
})

# Add messages
await client.post("/api/chat/messages", json={
    "conversation_id": conv.json()["id"],
    "content": "We decided to use approach A"
})

# Start new conversation in same context
response = await client.get("/api/chat/memory/contexts/TEST_CONTEXT")
assert len(response.json()["key_facts"]) > 0
```

---

## Privacy & Security

### Data Protection
- Memory data is encrypted at rest
- Access controlled by user authentication
- Users can view and delete their own memory
- Admins can manage memory for compliance

### Data Retention
- Memory persists indefinitely by default
- Configurable retention policies
- Automatic cleanup of expired entries
- Audit trail for memory changes

### Compliance
- GDPR compliant - right to be forgotten
- SOC 2 audit logging
- Data encryption in transit and at rest
- Access controls and permissions

---

## Configuration

### Environment Variables
```bash
# Memory settings
MEMORY_ENABLED=true
MEMORY_MAX_ENTRIES_PER_USER=1000
MEMORY_SUMMARY_MAX_ITEMS=50
MEMORY_CONTEXT_EXPIRY_DAYS=365
```

### Memory Limits
- Maximum 1000 memory entries per user
- Maximum 50 conversation summaries
- Maximum 20 frequent topics
- Maximum 20 active projects

---

## Troubleshooting

### Memory Not Working
1. Check if `memory_service` is imported correctly
2. Verify database tables exist
3. Check user authentication
4. Review application logs

### Memory Too Large
1. Reduce `MEMORY_MAX_ENTRIES_PER_USER`
2. Enable automatic cleanup
3. Archive old conversation summaries

### Performance Issues
1. Add indexes to memory tables
2. Enable caching for frequently accessed memory
3. Optimize memory context generation

---

## Future Enhancements

### Planned Features
1. **AI-Powered Memory Extraction** - Use LLM to automatically extract facts
2. **Memory Search** - Search through all stored memories
3. **Memory Sharing** - Share memories with team members
4. **Memory Analytics** - Insights into user interests and expertise
5. **Memory Import/Export** - Backup and restore memory data

### Advanced Memory Types
1. **Semantic Memory** - Conceptual knowledge
2. **Episodic Memory** - Specific event details
3. **Procedural Memory** - How-to knowledge
4. **Emotional Memory** - User preferences and sentiment

---

## Summary

The Persistent Memory System transforms the Enterprise AI Platform from a stateless chatbot into a truly intelligent assistant that:

- **Remembers who you are** - Employee profile, team, role
- **Remembers what you do** - Projects, expertise, preferences
- **Remembers what you talked about** - Past conversations, decisions, action items
- **Builds on past interactions** - Every conversation makes the AI smarter about you

**The AI never forgets. Neither should your platform.**

---

*For questions or support, contact the Enterprise AI Platform team.*
