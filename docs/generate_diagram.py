"""Generate updated architecture diagram using Graphviz."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.venv', 'Lib', 'site-packages'))

from graphviz import Digraph

dot = Digraph('NLP-to-SQL Architecture', format='png')
dot.attr(rankdir='TB', dpi='150', bgcolor='white', fontname='Helvetica')
dot.attr('node', fontname='Helvetica', fontsize='10')
dot.attr('edge', fontname='Helvetica', fontsize='8')

# --- User ---
dot.node('user', '👤 User\n(Browser)', shape='none', fontsize='12')

# --- Local Laptop cluster ---
with dot.subgraph(name='cluster_local') as local:
    local.attr(label='Local Laptop', style='dashed', color='#6366f1',
               fontcolor='#6366f1', fontsize='12', fontname='Helvetica-Bold')

    # React App
    with local.subgraph(name='cluster_react') as react:
        react.attr(label='React Web App (port 3000)', style='rounded,filled',
                   color='#3b82f6', fillcolor='#eff6ff', fontsize='10')
        react.node('chat_ui', 'Chat UI\n(Markdown + Tables\n+ Charts)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')
        react.node('whisper', 'Whisper STT\n(In-Browser)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')
        react.node('sidebar', 'Sidebar\n(History + Input)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')
        react.node('export', 'Export\n(HTML/MD + Charts)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')

    # FastAPI Server
    with local.subgraph(name='cluster_fastapi') as api:
        api.attr(label='FastAPI Server (port 8000)', style='rounded,filled',
                 color='#10b981', fillcolor='#ecfdf5', fontsize='10')
        api.node('routes', 'Routes\n(/chat /threads\n/context /charts)', shape='box',
                 style='rounded,filled', fillcolor='#d1fae5', color='#10b981')
        api.node('session_mgr', 'Session Factory\n(FileSessionManager)', shape='box',
                 style='rounded,filled', fillcolor='#d1fae5', color='#10b981')
        api.node('config', 'Config Provider\n(dev.json / AWS)', shape='box',
                 style='rounded,filled', fillcolor='#d1fae5', color='#10b981')

    # Strands Agent
    with local.subgraph(name='cluster_agent') as agent:
        agent.attr(label='Strands Agent (Extended Thinking)', style='rounded,filled',
                   color='#f59e0b', fillcolor='#fffbeb', fontsize='10')
        agent.node('tool1', '1. verify_question', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool2', '2. generate_sql', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool3', '3. execute_sql\n(read-only)', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool4', '4. summarize_results', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool5', '5. generate_chart\n(matplotlib)', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')

    # Storage
    with local.subgraph(name='cluster_storage') as storage:
        storage.attr(label='Storage Layer', style='rounded,filled',
                     color='#8b5cf6', fillcolor='#f5f3ff', fontsize='10')
        storage.node('sqlite', 'SQLite DB\n(9 tables)', shape='cylinder',
                     style='filled', fillcolor='#ede9fe', color='#8b5cf6')
        storage.node('sessions', 'Sessions\n(conversation\nmemory)', shape='folder',
                     style='filled', fillcolor='#ede9fe', color='#8b5cf6')
        storage.node('threads', 'Thread Index\n(metadata)', shape='folder',
                     style='filled', fillcolor='#ede9fe', color='#8b5cf6')
        storage.node('charts', 'Charts\n(PNG files)', shape='folder',
                     style='filled', fillcolor='#ede9fe', color='#8b5cf6')

# --- AWS Cloud ---
with dot.subgraph(name='cluster_aws') as aws:
    aws.attr(label='AWS Cloud', style='dashed', color='#f97316',
             fontcolor='#f97316', fontsize='12', fontname='Helvetica-Bold')
    aws.node('bedrock', 'Amazon Bedrock\n\nClaude Sonnet 4.5\n• Extended Thinking\n• Tool Use\n• Streaming',
             shape='box3d', style='filled', fillcolor='#fff7ed', color='#f97316')

# --- Edges: User → Frontend ---
dot.edge('user', 'chat_ui', label='questions\n(text/voice)', color='#6b7280')
dot.edge('user', 'whisper', label='voice', color='#6b7280', style='dashed')
dot.edge('whisper', 'chat_ui', label='transcript', color='#6b7280', style='dashed')

# --- Frontend → Backend ---
dot.edge('chat_ui', 'routes', label='POST /api/chat\n(SSE stream)', color='#3b82f6', style='bold')
dot.edge('routes', 'chat_ui', label='tokens +\nthinking +\nmetrics', color='#10b981', style='bold')
dot.edge('sidebar', 'routes', label='GET/POST\n/api/threads', color='#6b7280', style='dashed')
dot.edge('export', 'routes', label='GET\n/api/charts/*', color='#6b7280', style='dashed')

# --- Backend → Agent ---
dot.edge('routes', 'session_mgr', color='#10b981')
dot.edge('session_mgr', 'tool1', label='session\nloaded', color='#f59e0b')

# --- Agent tool flow ---
dot.edge('tool1', 'tool2', color='#f59e0b')
dot.edge('tool2', 'tool3', color='#f59e0b')
dot.edge('tool3', 'tool4', label='parallel', color='#f59e0b')
dot.edge('tool3', 'tool5', label='parallel', color='#f59e0b')

# --- Agent → Storage ---
dot.edge('tool1', 'sqlite', label='schema', color='#8b5cf6', style='dashed')
dot.edge('tool3', 'sqlite', label='SELECT', color='#8b5cf6', style='bold')
dot.edge('tool5', 'charts', label='save PNG', color='#8b5cf6')
dot.edge('session_mgr', 'sessions', color='#8b5cf6', style='dashed')
dot.edge('routes', 'threads', color='#8b5cf6', style='dashed')

# --- Agent → AWS Bedrock ---
dot.edge('tool1', 'bedrock', label='LLM', color='#f97316', style='bold')
dot.edge('tool2', 'bedrock', label='LLM', color='#f97316', style='bold')
dot.edge('tool4', 'bedrock', label='LLM', color='#f97316', style='bold')
dot.edge('tool5', 'bedrock', label='LLM\n(code gen)', color='#f97316', style='bold')

# --- Config ---
dot.edge('config', 'routes', color='#6b7280', style='dotted')

# Render
output_path = os.path.join(os.path.dirname(__file__), 'architecture')
dot.render(output_path, cleanup=True)
print(f"Diagram saved to: {output_path}.png")
