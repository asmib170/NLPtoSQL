"""Generate architecture diagram using Graphviz."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.venv', 'Lib', 'site-packages'))

from graphviz import Digraph

dot = Digraph('NLP-to-SQL Architecture', format='png')
dot.attr(rankdir='LR', dpi='150', bgcolor='white', fontname='Helvetica')
dot.attr('node', fontname='Helvetica', fontsize='11')
dot.attr('edge', fontname='Helvetica', fontsize='9')

# --- Local Laptop cluster ---
with dot.subgraph(name='cluster_local') as local:
    local.attr(label='Local Laptop', style='dashed', color='#6366f1',
               fontcolor='#6366f1', fontsize='13', fontname='Helvetica-Bold')

    # React App
    with local.subgraph(name='cluster_react') as react:
        react.attr(label='React Web App\n(localhost:3000)', style='rounded,filled',
                   color='#3b82f6', fillcolor='#eff6ff', fontsize='11')
        react.node('chat_window', 'Chat Window\n(Markdown + Tables)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')
        react.node('input_bar', 'Input Bar\n(question + session_id)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')
        react.node('sidebar', 'Sidebar\n(Chat History)', shape='box',
                   style='rounded,filled', fillcolor='#dbeafe', color='#3b82f6')

    # FastAPI Server
    with local.subgraph(name='cluster_fastapi') as api:
        api.attr(label='FastAPI Server\n(localhost:8000)', style='rounded,filled',
                 color='#10b981', fillcolor='#ecfdf5', fontsize='11')
        api.node('sse_gen', 'SSE Generator\n(streaming)', shape='box',
                 style='rounded,filled', fillcolor='#d1fae5', color='#10b981')
        api.node('session_mgr', 'Session Manager\n(FileSessionManager)', shape='box',
                 style='rounded,filled', fillcolor='#d1fae5', color='#10b981')

    # Strands Agent
    with local.subgraph(name='cluster_agent') as agent:
        agent.attr(label='Strands Agent\n(with Extended Thinking)', style='rounded,filled',
                   color='#f59e0b', fillcolor='#fffbeb', fontsize='11')
        agent.node('tool1', 'verify_question\n(schema check)', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool2', 'generate_sql\n(NL → SQL)', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool3', 'execute_sql\n(run SELECT)', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')
        agent.node('tool4', 'summarize_results\n(insights + trends)', shape='box',
                   style='rounded,filled', fillcolor='#fef3c7', color='#f59e0b')

    # SQLite DB
    local.node('sqlite', 'SQLite\nDemoECommerceDB\n(9 tables)', shape='cylinder',
               style='filled', fillcolor='#f3e8ff', color='#8b5cf6')

    # Session Storage
    local.node('storage', 'Session Storage\n(JSON files)', shape='folder',
               style='filled', fillcolor='#f1f5f9', color='#64748b')

# --- AWS Cloud cluster ---
with dot.subgraph(name='cluster_aws') as aws:
    aws.attr(label='AWS Cloud', style='dashed', color='#f97316',
             fontcolor='#f97316', fontsize='13', fontname='Helvetica-Bold')
    aws.node('bedrock', 'Amazon Bedrock\n\nClaude Sonnet 4.5\n(Thinking + Tool Use\n+ Streaming)',
             shape='box3d', style='filled', fillcolor='#fff7ed', color='#f97316')

# --- User ---
dot.node('user', '👤 User', shape='none', fontsize='14')

# --- Edges ---
dot.edge('user', 'input_bar', label='types question', color='#6b7280')
dot.edge('input_bar', 'sse_gen', label='POST /api/chat\n{message, thread_id}',
         color='#3b82f6', style='bold')
dot.edge('sse_gen', 'chat_window', label='SSE stream\n(tokens, thinking,\ntools, metrics)',
         color='#10b981', style='bold')
dot.edge('sidebar', 'sse_gen', label='GET /api/threads', color='#6b7280', style='dashed')

dot.edge('sse_gen', 'session_mgr', label='load/save\nsession', color='#64748b')
dot.edge('session_mgr', 'storage', color='#64748b', style='dashed')

dot.edge('sse_gen', 'tool1', label='Step 1', color='#f59e0b')
dot.edge('tool1', 'tool2', label='Step 2', color='#f59e0b')
dot.edge('tool2', 'tool3', label='Step 3', color='#f59e0b')
dot.edge('tool3', 'tool4', label='Step 4', color='#f59e0b')

dot.edge('tool3', 'sqlite', label='SQL query', color='#8b5cf6', style='bold')
dot.edge('tool1', 'sqlite', label='schema\ninspect', color='#8b5cf6', style='dashed')

dot.edge('tool1', 'bedrock', label='LLM call', color='#f97316', style='bold')
dot.edge('tool2', 'bedrock', label='LLM call', color='#f97316', style='bold')
dot.edge('tool4', 'bedrock', label='LLM call', color='#f97316', style='bold')

# Render
output_path = os.path.join(os.path.dirname(__file__), 'architecture')
dot.render(output_path, cleanup=True)
print(f"Diagram saved to: {output_path}.png")
