"""
Graphviz exporter for Code2Flow.

This module provides the GraphvizExporter class that converts CodeFlow objects
into Graphviz DOT format for high-quality diagram generation.
"""

from typing import Dict, List, Optional
import re
from ..core.flow import CodeFlow, FlowNode, FlowEdge, NodeType


class GraphvizExporter:
    """Exports CodeFlow objects as Graphviz DOT format."""
    
    def __init__(self, flow: CodeFlow):
        """
        Initialize GraphvizExporter.
        
        Args:
            flow: CodeFlow object to export
        """
        self.flow = flow
        
    def export(self, filename: Optional[str] = None) -> str:
        """
        Export the flow as a Graphviz DOT diagram.
        
        Args:
            filename: Optional filename to save the diagram to
            
        Returns:
            Graphviz DOT diagram as a string
        """
        if not self.flow.nodes:
            return "digraph G { A [label=\"No flow data available\"]; }"
            
        dot_content = self._generate_dot_diagram()
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(dot_content)
                
        return dot_content
        
    def _generate_dot_diagram(self) -> str:
        """Generate the complete Graphviz DOT diagram."""
        lines = []
        
        # Header
        lines.append("digraph G {")
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box, style=filled, fillcolor=white];")
        lines.append("    edge [color=black];")
        lines.append("")
        
        # Add node definitions
        lines.extend(self._generate_node_definitions())
        
        # Add blank line
        lines.append("")
        
        # Add edge definitions
        lines.extend(self._generate_edge_definitions())
        
        # Footer
        lines.append("}")
        
        return "\n".join(lines)
        
    def _generate_node_definitions(self) -> List[str]:
        """Generate Graphviz node definitions."""
        lines = []
        
        for node in self.flow.nodes.values():
            dot_id = self._sanitize_id(node.node_id)
            label = self._format_node_label(node)
            style = self._get_node_style(node)
            
            line = f"    {dot_id} [{style}, label=\"{label}\"];"
            lines.append(line)
            
        return lines
        
    def _generate_edge_definitions(self) -> List[str]:
        """Generate Graphviz edge definitions."""
        lines = []
        
        for edge in self.flow.edges:
            source_id = self._sanitize_id(edge.source)
            target_id = self._sanitize_id(edge.target)
            
            # Determine edge style and label
            edge_attrs = []
            if edge.label:
                edge_attrs.append(f"label=\"{edge.label}\"")
            if edge.color and edge.color != "#000000":
                edge_attrs.append(f"color=\"{edge.color}\"")
            if edge.style and edge.style != "solid":
                edge_attrs.append(f"style=\"{edge.style}\"")
                
            if edge_attrs:
                attrs_str = ", ".join(edge_attrs)
                line = f"    {source_id} -> {target_id} [{attrs_str}];"
            else:
                line = f"    {source_id} -> {target_id};"
                
            lines.append(line)
            
        return lines
        
    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for Graphviz compatibility."""
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
        
        # Ensure it starts with a letter or underscore
        if not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = 'node_' + sanitized
            
        return sanitized
        
    def _format_node_label(self, node: FlowNode) -> str:
        """Format node label for Graphviz display."""
        label = node.label
        
        # Escape special characters for Graphviz
        label = label.replace('"', '\\"')
        label = label.replace('\n', '\\n')
        label = label.replace('<', '\\<')
        label = label.replace('>', '\\>')
        
        # Truncate if too long
        if len(label) > 100:
            label = label[:97] + "..."
            
        # Add variable information for process nodes
        if node.node_type == NodeType.PROCESS and node.variables:
            var_info = []
            for var_name, var_value in list(node.variables.items())[:2]:
                if not var_name.startswith('_'):
                    var_info.append(f"{var_name}={var_value}")
                    
            if var_info:
                var_str = "\\n".join(var_info)
                label += f"\\n{var_str}"
                
        return label
        
    def _get_node_style(self, node: FlowNode) -> str:
        """Get appropriate Graphviz style for node type."""
        # Base style attributes
        attrs = []
        
        # Set shape based on node type
        shape_map = {
            NodeType.START: "ellipse",
            NodeType.END: "ellipse", 
            NodeType.DECISION: "diamond",
            NodeType.PROCESS: "box",
            NodeType.CALL: "box",
            NodeType.RETURN: "box",
            NodeType.LOOP: "box",
            NodeType.EXCEPTION: "box"
        }
        
        shape = shape_map.get(node.node_type, "box")
        attrs.append(f"shape={shape}")
        
        # Set color based on node type
        color_map = {
            NodeType.START: "lightgreen",
            NodeType.END: "lightpink",
            NodeType.DECISION: "moccasin",
            NodeType.CALL: "skyblue",
            NodeType.EXCEPTION: "lightsalmon"
        }
        
        if node.node_type in color_map:
            color = color_map[node.node_type]
            attrs.append(f"fillcolor={color}")
        else:
            attrs.append("fillcolor=white")
            
        # Add style
        attrs.append("style=filled")
        
        return ", ".join(attrs)
