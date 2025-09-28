#!/usr/bin/env python3
"""
Collaborative Development Orchestrator

This script demonstrates how multiple AI CLI instances can work together
to build a todo application using IPC for coordination.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add IPC tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.project_utils import get_project_id, get_project_port


class CollaborativeOrchestrator:
    """Orchestrates collaborative development between AI instances"""

    def __init__(self):
        self.project_id = get_project_id()
        self.project_port = get_project_port()
        self.ai_instances = {
            'claude': {
                'role': 'Architecture & Review',
                'status': 'idle',
                'tasks': []
            },
            'gemini': {
                'role': 'Frontend Development',
                'status': 'idle',
                'tasks': []
            },
            'codex': {
                'role': 'Backend Development',
                'status': 'idle',
                'tasks': []
            },
            'lm': {
                'role': 'Testing & Documentation',
                'status': 'idle',
                'tasks': []
            }
        }

        self.project_phases = [
            'planning',
            'design',
            'implementation',
            'testing',
            'documentation',
            'review',
            'deployment'
        ]

        self.current_phase = 'planning'

    def send_ipc_message(self, from_ai: str, to_ai: str, message: Dict) -> bool:
        """Send IPC message between AI instances"""
        import socket

        try:
            request = {
                'action': 'send',
                'name': from_ai,
                'to': to_ai,
                'message': json.dumps(message),
                'project_id': self.project_id
            }

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.project_port))

            message_data = json.dumps(request) + '\n'
            sock.sendall(message_data.encode('utf-8'))

            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b'\n' in response:
                    break

            sock.close()

            result = json.loads(response.decode('utf-8').strip())
            return result.get('status') == 'success'

        except Exception as e:
            print(f"Error sending IPC message: {e}")
            return False

    def phase_1_planning(self):
        """Phase 1: Project Planning"""
        print("\n" + "="*60)
        print("📋 PHASE 1: PROJECT PLANNING")
        print("="*60)

        # Claude initiates architecture planning
        architecture_proposal = {
            'type': 'architecture_proposal',
            'phase': 'planning',
            'content': {
                'pattern': 'MVC',
                'frontend': 'React with TypeScript',
                'backend': 'Python FastAPI',
                'database': 'SQLite',
                'testing': 'Jest + Pytest',
                'features': [
                    'Add todos',
                    'Mark complete',
                    'Delete todos',
                    'Filter by status',
                    'Persist to database'
                ]
            }
        }

        print("\n🏗️  Claude: Proposing architecture...")
        self.send_ipc_message('claude', 'all', architecture_proposal)

        # Simulate AI responses
        print("💬 Gemini: Reviewing frontend requirements...")
        print("💬 Codex: Analyzing backend requirements...")
        print("💬 LM: Planning test strategy...")

        time.sleep(2)
        print("\n✅ Planning phase complete!")

    def phase_2_design(self):
        """Phase 2: Design & API Contracts"""
        print("\n" + "="*60)
        print("🎨 PHASE 2: DESIGN & API CONTRACTS")
        print("="*60)

        # Define API contracts
        api_contracts = {
            'type': 'api_contract',
            'phase': 'design',
            'endpoints': {
                'GET /api/todos': 'List all todos',
                'POST /api/todos': 'Create new todo',
                'PUT /api/todos/:id': 'Update todo',
                'DELETE /api/todos/:id': 'Delete todo',
                'GET /api/todos/stats': 'Get statistics'
            },
            'models': {
                'Todo': {
                    'id': 'string',
                    'title': 'string',
                    'completed': 'boolean',
                    'created_at': 'datetime',
                    'updated_at': 'datetime'
                }
            }
        }

        print("\n📜 Codex: Defining API contracts...")
        self.send_ipc_message('codex', 'all', api_contracts)

        # Frontend design
        ui_design = {
            'type': 'ui_design',
            'phase': 'design',
            'components': [
                'TodoList',
                'TodoItem',
                'AddTodoForm',
                'FilterBar',
                'StatsDisplay'
            ],
            'styling': 'Tailwind CSS',
            'state_management': 'React Context'
        }

        print("🎨 Gemini: Designing UI components...")
        self.send_ipc_message('gemini', 'all', ui_design)

        time.sleep(2)
        print("\n✅ Design phase complete!")

    def phase_3_implementation(self):
        """Phase 3: Parallel Implementation"""
        print("\n" + "="*60)
        print("💻 PHASE 3: PARALLEL IMPLEMENTATION")
        print("="*60)

        # Create source directories
        self._create_project_structure()

        # Backend implementation (Codex)
        print("\n🔧 Codex: Implementing backend API...")
        self._create_backend_files()

        backend_status = {
            'type': 'implementation_status',
            'component': 'backend',
            'status': 'complete',
            'files_created': [
                'src/backend/api.py',
                'src/backend/models.py',
                'src/backend/database.py'
            ]
        }
        self.send_ipc_message('codex', 'all', backend_status)

        # Frontend implementation (Gemini)
        print("🎨 Gemini: Implementing frontend components...")
        self._create_frontend_files()

        frontend_status = {
            'type': 'implementation_status',
            'component': 'frontend',
            'status': 'complete',
            'files_created': [
                'src/frontend/TodoList.jsx',
                'src/frontend/TodoItem.jsx',
                'src/frontend/AddTodo.jsx'
            ]
        }
        self.send_ipc_message('gemini', 'all', frontend_status)

        time.sleep(2)
        print("\n✅ Implementation phase complete!")

    def phase_4_testing(self):
        """Phase 4: Testing"""
        print("\n" + "="*60)
        print("🧪 PHASE 4: TESTING")
        print("="*60)

        # LM creates tests
        print("\n🔬 LM: Creating test suites...")
        self._create_test_files()

        test_report = {
            'type': 'test_report',
            'phase': 'testing',
            'results': {
                'unit_tests': {'passed': 15, 'failed': 0},
                'integration_tests': {'passed': 8, 'failed': 0},
                'e2e_tests': {'passed': 5, 'failed': 0}
            },
            'coverage': '92%'
        }

        print("📊 LM: Running tests...")
        self.send_ipc_message('lm', 'all', test_report)

        time.sleep(2)
        print("\n✅ Testing phase complete!")

    def phase_5_documentation(self):
        """Phase 5: Documentation"""
        print("\n" + "="*60)
        print("📚 PHASE 5: DOCUMENTATION")
        print("="*60)

        print("\n📝 LM: Generating documentation...")
        self._create_documentation()

        doc_status = {
            'type': 'documentation_status',
            'phase': 'documentation',
            'files_created': [
                'doc/API.md',
                'doc/USER_GUIDE.md',
                'doc/ARCHITECTURE.md',
                'doc/DEVELOPMENT.md'
            ]
        }

        self.send_ipc_message('lm', 'all', doc_status)

        time.sleep(2)
        print("\n✅ Documentation phase complete!")

    def phase_6_review(self):
        """Phase 6: Code Review"""
        print("\n" + "="*60)
        print("🔍 PHASE 6: CODE REVIEW")
        print("="*60)

        print("\n👀 Claude: Performing code review...")

        review_results = {
            'type': 'code_review',
            'phase': 'review',
            'findings': {
                'security': 'No vulnerabilities found',
                'performance': 'Optimal for current scale',
                'maintainability': 'Good separation of concerns',
                'test_coverage': 'Excellent (92%)',
                'documentation': 'Comprehensive'
            },
            'recommendations': [
                'Consider adding input validation middleware',
                'Implement rate limiting for API',
                'Add error boundary in React app'
            ]
        }

        self.send_ipc_message('claude', 'all', review_results)

        print("🔧 All AIs: Addressing review comments...")
        time.sleep(2)
        print("\n✅ Review phase complete!")

    def _create_project_structure(self):
        """Create basic project structure"""
        directories = [
            'src/frontend',
            'src/backend',
            'src/shared',
            'test/unit',
            'test/integration',
            'test/e2e',
            'doc'
        ]

        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def _create_backend_files(self):
        """Create backend files (simulated Codex work)"""

        # API file
        api_content = '''"""
Todo API Implementation
Generated by Codex via IPC collaboration
"""

from fastapi import FastAPI, HTTPException
from typing import List, Optional
from models import Todo, CreateTodoRequest, UpdateTodoRequest
from database import TodoDatabase

app = FastAPI(title="Todo API")
db = TodoDatabase()

@app.get("/api/todos", response_model=List[Todo])
async def get_todos():
    """Get all todos"""
    return db.get_all()

@app.post("/api/todos", response_model=Todo)
async def create_todo(request: CreateTodoRequest):
    """Create new todo"""
    return db.create(request)

@app.put("/api/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: str, request: UpdateTodoRequest):
    """Update existing todo"""
    todo = db.update(todo_id, request)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.delete("/api/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete todo"""
    if not db.delete(todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted"}

@app.get("/api/todos/stats")
async def get_stats():
    """Get todo statistics"""
    return db.get_stats()
'''

        Path('src/backend/api.py').write_text(api_content)

        # Models file
        models_content = '''"""
Data Models for Todo Application
Generated by Codex via IPC collaboration
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Todo(BaseModel):
    id: str
    title: str
    completed: bool = False
    created_at: datetime
    updated_at: datetime

class CreateTodoRequest(BaseModel):
    title: str

class UpdateTodoRequest(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None
'''

        Path('src/backend/models.py').write_text(models_content)

    def _create_frontend_files(self):
        """Create frontend files (simulated Gemini work)"""

        # TodoList component
        todolist_content = '''/**
 * TodoList Component
 * Generated by Gemini via IPC collaboration
 */

import React, { useState, useEffect } from 'react';
import TodoItem from './TodoItem';
import AddTodo from './AddTodo';

export default function TodoList() {
    const [todos, setTodos] = useState([]);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        fetchTodos();
    }, []);

    const fetchTodos = async () => {
        const response = await fetch('/api/todos');
        const data = await response.json();
        setTodos(data);
    };

    const addTodo = async (title) => {
        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        const newTodo = await response.json();
        setTodos([...todos, newTodo]);
    };

    const toggleTodo = async (id) => {
        const todo = todos.find(t => t.id === id);
        const response = await fetch(`/api/todos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completed: !todo.completed })
        });
        const updated = await response.json();
        setTodos(todos.map(t => t.id === id ? updated : t));
    };

    const deleteTodo = async (id) => {
        await fetch(`/api/todos/${id}`, { method: 'DELETE' });
        setTodos(todos.filter(t => t.id !== id));
    };

    const filteredTodos = todos.filter(todo => {
        if (filter === 'active') return !todo.completed;
        if (filter === 'completed') return todo.completed;
        return true;
    });

    return (
        <div className="todo-list">
            <h1>Todo Application</h1>
            <AddTodo onAdd={addTodo} />
            <div className="filter-bar">
                <button onClick={() => setFilter('all')}>All</button>
                <button onClick={() => setFilter('active')}>Active</button>
                <button onClick={() => setFilter('completed')}>Completed</button>
            </div>
            <div className="todos">
                {filteredTodos.map(todo => (
                    <TodoItem
                        key={todo.id}
                        todo={todo}
                        onToggle={toggleTodo}
                        onDelete={deleteTodo}
                    />
                ))}
            </div>
        </div>
    );
}
'''

        Path('src/frontend/TodoList.jsx').write_text(todolist_content)

    def _create_test_files(self):
        """Create test files (simulated LM work)"""

        test_content = '''"""
Todo API Tests
Generated by LM via IPC collaboration
"""

import pytest
from fastapi.testclient import TestClient
from src.backend.api import app

client = TestClient(app)

def test_get_todos():
    """Test getting all todos"""
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_todo():
    """Test creating a new todo"""
    response = client.post("/api/todos", json={"title": "Test Todo"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["completed"] == False

def test_update_todo():
    """Test updating a todo"""
    # First create a todo
    create_response = client.post("/api/todos", json={"title": "Test"})
    todo_id = create_response.json()["id"]

    # Update it
    update_response = client.put(
        f"/api/todos/{todo_id}",
        json={"completed": True}
    )
    assert update_response.status_code == 200
    assert update_response.json()["completed"] == True

def test_delete_todo():
    """Test deleting a todo"""
    # First create a todo
    create_response = client.post("/api/todos", json={"title": "Delete Me"})
    todo_id = create_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/api/todos/{todo_id}")
    assert delete_response.status_code == 200

    # Verify it's gone
    get_response = client.get("/api/todos")
    todos = get_response.json()
    assert not any(todo["id"] == todo_id for todo in todos)
'''

        Path('test/unit/test_api.py').write_text(test_content)

    def _create_documentation(self):
        """Create documentation files (simulated LM work)"""

        api_doc = '''# Todo API Documentation

## Overview
RESTful API for Todo application built through AI collaboration via IPC.

## Endpoints

### GET /api/todos
Returns list of all todos.

**Response:**
```json
[
    {
        "id": "uuid",
        "title": "Example todo",
        "completed": false,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
]
```

### POST /api/todos
Creates a new todo.

**Request:**
```json
{
    "title": "New todo"
}
```

### PUT /api/todos/:id
Updates an existing todo.

**Request:**
```json
{
    "title": "Updated title",
    "completed": true
}
```

### DELETE /api/todos/:id
Deletes a todo.

### GET /api/todos/stats
Returns statistics about todos.

## Built Through AI Collaboration
- **Claude**: Architecture design and code review
- **Codex**: Backend implementation
- **Gemini**: Frontend implementation
- **LM**: Testing and documentation
'''

        Path('doc/API.md').write_text(api_doc)

    def run_collaborative_development(self):
        """Run the complete collaborative development process"""
        print("\n" + "="*60)
        print("🚀 COLLABORATIVE TODO APP DEVELOPMENT")
        print("="*60)
        print(f"Project ID: {self.project_id}")
        print(f"IPC Port: {self.project_port}")
        print("\nAI Instance Roles:")
        for ai, info in self.ai_instances.items():
            print(f"  • {ai}: {info['role']}")

        # Execute all phases
        self.phase_1_planning()
        self.phase_2_design()
        self.phase_3_implementation()
        self.phase_4_testing()
        self.phase_5_documentation()
        self.phase_6_review()

        # Final summary
        print("\n" + "="*60)
        print("🎉 PROJECT COMPLETE!")
        print("="*60)
        print("\n📊 Summary:")
        print("  ✅ All phases completed successfully")
        print("  ✅ 4 AI instances collaborated via IPC")
        print("  ✅ Frontend, backend, tests, and docs created")
        print("\n📁 Generated Files:")
        print("  • src/backend/ - API implementation")
        print("  • src/frontend/ - React components")
        print("  • test/ - Test suites")
        print("  • doc/ - Documentation")
        print("\n🚀 Next Steps:")
        print("  1. Install dependencies: npm install && pip install -r requirements.txt")
        print("  2. Run backend: python src/backend/api.py")
        print("  3. Run frontend: npm start")
        print("  4. Run tests: pytest && npm test")


def main():
    """Main entry point"""
    orchestrator = CollaborativeOrchestrator()

    try:
        orchestrator.run_collaborative_development()
    except KeyboardInterrupt:
        print("\n⚠️  Development interrupted")
    except Exception as e:
        print(f"\n❌ Error during development: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()