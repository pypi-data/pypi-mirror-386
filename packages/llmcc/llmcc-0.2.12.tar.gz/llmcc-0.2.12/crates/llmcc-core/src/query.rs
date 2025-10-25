use crate::block::{BlockKind, BlockRelation};
use crate::graph_builder::{GraphNode, ProjectGraph};

/// Query API for semantic code questions built on top of ProjectGraph:
/// - given a function name, find all related code
/// - given a struct name, find all related code
/// - given a module/folder, find related modules
/// - given a file name, extract important structures (functions, types, etc.)
///
/// Output format: plain text suitable for LLM ingestion
/// Represents a semantic code block from the project graph
#[derive(Debug, Clone)]
pub struct GraphBlockInfo {
    pub name: String,
    pub kind: String,
    pub file_path: Option<String>,
    pub source_code: Option<String>,
    pub node: GraphNode,
    pub unit_index: usize,
    pub start_line: usize,
    pub end_line: usize,
}

impl GraphBlockInfo {
    pub fn format_for_llm(&self) -> String {
        let mut output = String::new();

        // Header line with name, kind, and location
        let location = if let Some(path) = &self.file_path {
            use std::path::Path;
            let abs_path = Path::new(path);
            if abs_path.is_absolute() {
                path.clone()
            } else {
                match std::env::current_dir() {
                    Ok(cwd) => cwd.join(path).display().to_string(),
                    Err(_) => path.clone(),
                }
            }
        } else {
            format!("<file_unit_{}>", self.unit_index)
        };

        output.push_str(&format!(
            "┌─ {} [{}] at {}\n",
            self.name, self.kind, location
        ));

        // Source code with line numbers
        if let Some(source) = &self.source_code {
            let lines: Vec<&str> = source.lines().collect();
            let max_line_num = self.end_line;
            let line_num_width = max_line_num.to_string().len();

            for (idx, line) in lines.iter().enumerate() {
                let line_num = self.start_line + idx;
                output.push_str(&format!(
                    "│ [{:width$}] {}\n",
                    line_num,
                    line,
                    width = line_num_width
                ));
            }
        }

        output.push_str("└─\n");
        output
    }
}

/// Query results grouped by relevance and type
#[derive(Debug, Default)]
pub struct QueryResult {
    pub primary: Vec<GraphBlockInfo>,
    pub depends: Vec<GraphBlockInfo>,
    pub depended: Vec<GraphBlockInfo>,
}

impl QueryResult {
    pub fn format_for_llm(&self) -> String {
        let mut output = String::new();

        if !self.primary.is_empty() {
            output.push_str(" ------------- PRIMARY RESULTS ------------------- \n");
            for block in &self.primary {
                output.push_str(&block.format_for_llm());
                output.push('\n');
            }
        }

        if !self.depends.is_empty() {
            output.push_str(" -------------- DEPENDS ON (Dependencies) ----------------- \n");
            for block in &self.depends {
                output.push_str(&block.format_for_llm());
                output.push('\n');
            }
        }

        if !self.depended.is_empty() {
            output.push_str(" -------------- DEPENDED BY (Dependents) ----------------- \n");
            for block in &self.depended {
                output.push_str(&block.format_for_llm());
                output.push('\n');
            }
        }

        output
    }
}

/// Main query interface built on ProjectGraph
pub struct ProjectQuery<'tcx> {
    graph: &'tcx ProjectGraph<'tcx>,
}

impl<'tcx> ProjectQuery<'tcx> {
    pub fn new(graph: &'tcx ProjectGraph<'tcx>) -> Self {
        Self { graph }
    }

    /// Find all blocks with a given name
    pub fn find_by_name(&self, name: &str) -> QueryResult {
        let mut result = QueryResult::default();

        let blocks = self.graph.blocks_by_name(name);
        for node in blocks {
            if let Some(block_info) = self.node_to_block_info(node) {
                result.primary.push(block_info);
            }
        }

        result
    }

    /// Find all functions in the project
    pub fn find_all_functions(&self) -> QueryResult {
        self.find_by_kind(BlockKind::Func)
    }

    /// Find all structs in the project
    pub fn find_all_structs(&self) -> QueryResult {
        self.find_by_kind(BlockKind::Class)
    }

    /// Find all items of a specific kind
    pub fn find_by_kind(&self, kind: BlockKind) -> QueryResult {
        let mut result = QueryResult::default();

        let blocks = self.graph.blocks_by_kind(kind);
        for node in blocks {
            if let Some(block_info) = self.node_to_block_info(node) {
                result.primary.push(block_info.clone());
            }
        }

        result
    }

    /// Get all blocks defined in a specific file/unit
    pub fn file_structure(&self, unit_index: usize) -> QueryResult {
        let mut result = QueryResult::default();

        let blocks = self.graph.blocks_in(unit_index);
        for node in blocks {
            if let Some(block_info) = self.node_to_block_info(node) {
                result.primary.push(block_info.clone());
            }
        }

        result
    }

    /// Find all blocks that this block depends on
    pub fn find_depends(&self, name: &str) -> QueryResult {
        let mut result = QueryResult::default();

        // Find the primary block
        if let Some(primary_node) = self.graph.block_by_name(name) {
            if let Some(block_info) = self.node_to_block_info(primary_node) {
                result.primary.push(block_info);

                // Find all blocks this one depends on
                let depends_blocks = self
                    .graph
                    .find_related_blocks(primary_node, vec![BlockRelation::DependsOn]);
                for depends_node in depends_blocks {
                    if let Some(depends_info) = self.node_to_block_info(depends_node) {
                        result.depends.push(depends_info);
                    }
                }
            }
        }

        result
    }

    /// Find all blocks that depend on this block (dependents)
    pub fn find_depended(&self, name: &str) -> QueryResult {
        let mut result = QueryResult::default();

        // Find the primary block
        if let Some(primary_node) = self.graph.block_by_name(name) {
            if let Some(block_info) = self.node_to_block_info(primary_node) {
                result.primary.push(block_info);

                // Find all blocks that depend on this one
                let depended_blocks = self
                    .graph
                    .find_related_blocks(primary_node, vec![BlockRelation::DependedBy]);
                for depended_node in depended_blocks {
                    if let Some(depended_info) = self.node_to_block_info(depended_node) {
                        result.depended.push(depended_info);
                    }
                }
            }
        }

        result
    }

    /// Find all blocks that are related to a given block recursively
    pub fn find_depends_recursive(&self, name: &str) -> QueryResult {
        let mut result = QueryResult::default();

        // Find the primary block
        if let Some(primary_node) = self.graph.block_by_name(name) {
            if let Some(block_info) = self.node_to_block_info(primary_node) {
                result.primary.push(block_info);

                // Find all related blocks recursively
                let all_related = self.graph.find_dpends_blocks_recursive(primary_node);
                for related_node in all_related {
                    if let Some(related_info) = self.node_to_block_info(related_node) {
                        result.depends.push(related_info);
                    }
                }
            }
        }

        result
    }

    /// Traverse graph with BFS from a starting block
    pub fn traverse_bfs(&self, start_name: &str) -> Vec<GraphBlockInfo> {
        let mut results = Vec::new();

        if let Some(start_node) = self.graph.block_by_name(start_name) {
            self.graph.traverse_bfs(start_node, |node| {
                if let Some(block_info) = self.node_to_block_info(node) {
                    results.push(block_info);
                }
            });
        }

        results
    }

    /// Traverse graph with DFS from a starting block
    pub fn traverse_dfs(&self, start_name: &str) -> Vec<GraphBlockInfo> {
        let mut results = Vec::new();

        if let Some(start_node) = self.graph.block_by_name(start_name) {
            self.graph.traverse_dfs(start_node, |node| {
                if let Some(block_info) = self.node_to_block_info(node) {
                    results.push(block_info);
                }
            });
        }

        results
    }

    /// Find all blocks by kind in a specific unit
    pub fn find_by_kind_in_unit(&self, kind: BlockKind, unit_index: usize) -> QueryResult {
        let mut result = QueryResult::default();

        let blocks = self.graph.blocks_by_kind_in(kind, unit_index);
        for node in blocks {
            if let Some(block_info) = self.node_to_block_info(node) {
                result.primary.push(block_info.clone());
            }
        }

        result
    }

    /// Helper: convert a GraphNode to block info
    fn node_to_block_info(&self, node: GraphNode) -> Option<GraphBlockInfo> {
        let (unit_index, name, kind) = self.graph.block_info(node.block_id)?;

        // Try to get the fully qualified name from the symbol if available
        let display_name =
            if let Some(symbol) = self.graph.cc.find_symbol_by_block_id(node.block_id) {
                let fqn = symbol.fqn_name.borrow();
                if !fqn.is_empty() && *fqn != symbol.name {
                    fqn.clone()
                } else {
                    name.unwrap_or_else(|| format!("_unnamed_{}", node.block_id.0))
                }
            } else {
                name.unwrap_or_else(|| format!("_unnamed_{}", node.block_id.0))
            };

        // Get file path from compile context
        let file_path = self
            .graph
            .cc
            .files
            .get(unit_index)
            .and_then(|file| file.path().map(|s| s.to_string()));

        // Extract source code for this block
        let source_code = self.get_block_source_code(node, unit_index);

        // Calculate line numbers
        let (start_line, end_line) = self.get_line_numbers(node, unit_index);

        Some(GraphBlockInfo {
            name: display_name,
            kind: format!("{:?}", kind),
            file_path,
            source_code,
            node,
            unit_index,
            start_line,
            end_line,
        })
    }

    /// Calculate line numbers from byte offsets
    fn get_line_numbers(&self, node: GraphNode, unit_index: usize) -> (usize, usize) {
        let file = match self.graph.cc.files.get(unit_index) {
            Some(f) => f,
            None => return (0, 0),
        };

        let unit = self.graph.cc.compile_unit(unit_index);

        // Get the BasicBlock to access its HIR node
        let bb = match unit.opt_bb(node.block_id) {
            Some(b) => b,
            None => return (0, 0),
        };

        // Get the base which contains the HirNode
        let base = match bb.base() {
            Some(b) => b,
            None => return (0, 0),
        };

        let hir_node = base.node;
        let start_byte = hir_node.start_byte();
        let end_byte = hir_node.end_byte();

        // Get the file content and count lines
        if let Some(content) = file.file.content.as_ref() {
            let start_line = content[..start_byte.min(content.len())]
                .iter()
                .filter(|&&b| b == b'\n')
                .count()
                + 1;
            let end_line = content[..end_byte.min(content.len())]
                .iter()
                .filter(|&&b| b == b'\n')
                .count()
                + 1;
            (start_line, end_line)
        } else {
            (0, 0)
        }
    }

    /// Extract the source code for a given block
    fn get_block_source_code(&self, node: GraphNode, unit_index: usize) -> Option<String> {
        let file = self.graph.cc.files.get(unit_index)?;
        let unit = self.graph.cc.compile_unit(unit_index);

        // Get the BasicBlock to access its HIR node
        let bb = unit.opt_bb(node.block_id)?;

        // Get the base which contains the HirNode
        let base = bb.base()?;
        let hir_node = base.node;

        // Get the span information from the HirNode
        let start_byte = hir_node.start_byte();
        let end_byte = hir_node.end_byte();

        // Special handling for Class blocks: filter out method implementations
        if let crate::block::BasicBlock::Class(class_block) = bb {
            return self.extract_class_definition(class_block, unit, file, start_byte, end_byte);
        }

        file.opt_get_text(start_byte, end_byte)
    }

    /// Extract only the class definition without method implementations
    /// This handles classes where methods are defined inside the class body (Python-style)
    fn extract_class_definition(
        &self,
        class_block: &crate::block::BlockClass,
        unit: crate::context::CompileUnit,
        file: &crate::file::File,
        class_start_byte: usize,
        class_end_byte: usize,
    ) -> Option<String> {
        // Get the full class source
        let full_text = file.opt_get_text(class_start_byte, class_end_byte)?;

        // Collect byte positions of all methods (BlockKind::Func children)
        let mut method_start_bytes = Vec::new();

        for child_id in &class_block.base.children {
            let child_bb = unit.opt_bb(*child_id)?;
            let child_kind = child_bb.kind();

            // If this child is a method (Func block), record its start byte
            if child_kind == BlockKind::Func {
                if let Some(child_base) = child_bb.base() {
                    let child_node = child_base.node;
                    let child_start = child_node.start_byte();
                    if child_start > class_start_byte {
                        method_start_bytes.push(child_start);
                    }
                }
            }
        }

        // If there are no methods, return the full text
        if method_start_bytes.is_empty() {
            return Some(full_text);
        }

        // Find the byte position of the first method
        method_start_bytes.sort();
        let first_method_start = method_start_bytes[0];

        // Calculate the offset relative to class start
        let offset = first_method_start - class_start_byte;
        if offset >= full_text.len() {
            return Some(full_text);
        }

        // Extract text up to the first method
        let class_def = full_text[..offset].to_string();

        // Clean up trailing whitespace and incomplete lines
        let trimmed = class_def.trim_end();

        // Try to find the last complete line (before the first method starts)
        if let Some(last_newline) = trimmed.rfind('\n') {
            Some(trimmed[..=last_newline].to_string())
        } else {
            Some(trimmed.to_string())
        }
    }
}
