use std::mem;

use llmcc_core::context::CompileUnit;
use llmcc_core::ir::{HirBase, HirId, HirIdent, HirKind, HirNode};
use llmcc_core::symbol::{Scope, ScopeStack, Symbol, SymbolKind};

use crate::descriptor::function::parse_type_expr;
use crate::descriptor::{
    CallDescriptor, EnumDescriptor, FnVisibility, FunctionDescriptor, StructDescriptor, TypeExpr,
    VariableDescriptor,
};
use crate::token::{AstVisitorRust, LangRust};

/// DeclCollector collects all symbol declarations (functions, structs, enums, variables, etc.)
/// from the AST during the first pass of semantic analysis.
///
/// For each symbol encountered:
/// 1. Insert it into the local scope stack for local name resolution
/// 2. If it's public/global, also register it in the global symbol table for cross-file resolution
///
/// This enables later phases to resolve both local names (via scope stack) and qualified names
/// (via global symbol table).
#[derive(Debug)]
struct DeclCollector<'tcx> {
    unit: CompileUnit<'tcx>,
    scopes: ScopeStack<'tcx>,
    functions: Vec<FunctionDescriptor>,
    variables: Vec<VariableDescriptor>,
    calls: Vec<CallDescriptor>,
    structs: Vec<StructDescriptor>,
    enums: Vec<EnumDescriptor>,
}

impl<'tcx> DeclCollector<'tcx> {
    pub fn new(unit: CompileUnit<'tcx>, globals: &'tcx Scope<'tcx>) -> Self {
        let mut scopes = ScopeStack::new(&unit.cc.arena, &unit.cc.interner, &unit.cc.symbol_map);
        // TODO: make create a new symbol assoicate unit file name
        scopes.push_with_symbol(globals, None);
        Self {
            unit,
            scopes,
            functions: Vec::new(),
            variables: Vec::new(),
            calls: Vec::new(),
            structs: Vec::new(),
            enums: Vec::new(),
        }
    }

    fn parent_symbol(&self) -> Option<&'tcx Symbol> {
        self.scopes.scoped_symbol()
    }

    fn scoped_fqn(&self, _node: &HirNode<'tcx>, name: &str) -> String {
        if let Some(parent) = self.parent_symbol() {
            let parent_fqn = parent.fqn_name.borrow();
            if parent_fqn.is_empty() {
                name.to_string()
            } else {
                format!("{}::{}", parent_fqn.as_str(), name)
            }
        } else {
            name.to_string()
        }
    }

    fn take_functions(&mut self) -> Vec<FunctionDescriptor> {
        mem::take(&mut self.functions)
    }

    fn take_variables(&mut self) -> Vec<VariableDescriptor> {
        mem::take(&mut self.variables)
    }

    fn take_calls(&mut self) -> Vec<CallDescriptor> {
        mem::take(&mut self.calls)
    }

    fn take_structs(&mut self) -> Vec<StructDescriptor> {
        mem::take(&mut self.structs)
    }

    fn take_enums(&mut self) -> Vec<EnumDescriptor> {
        mem::take(&mut self.enums)
    }

    fn create_new_symbol(
        &mut self,
        node: &HirNode<'tcx>,
        field_id: u16,
        global: bool,
        kind: SymbolKind,
    ) -> Option<(&'tcx Symbol, &'tcx HirIdent<'tcx>, String)> {
        let ident_node = node.child_by_field(self.unit, field_id);
        let ident = ident_node.as_ident()?;
        let fqn = self.scoped_fqn(node, &ident.name);
        let owner = node.hir_id();

        let symbol = match self.scopes.find_symbol_local(&ident.name) {
            Some(existing) if Self::different_kind(existing.kind(), kind) => {
                self.insert_into_scope(owner, ident, global, &fqn, kind)
            }
            Some(existing) => {
                // self.warn_duplicate_symbol(&ident.name, existing.kind(), kind);
                existing
            }
            None => self.insert_into_scope(owner, ident, global, &fqn, kind),
        };

        Some((symbol, ident, fqn))
    }

    fn different_kind(existing_kind: SymbolKind, new_kind: SymbolKind) -> bool {
        existing_kind != SymbolKind::Unknown && existing_kind != new_kind
    }

    // fn warn_duplicate_symbol(&self, name: &str, existing_kind: SymbolKind, new_kind: SymbolKind) {
    //     eprintln!(
    //         "warning: duplicate symbol '{}' found in the same scope. existing kind: {:?}, new kind: {:?}. skipping insertion.",
    //         name, existing_kind, new_kind
    //     );
    // }

    fn insert_into_scope(
        &mut self,
        owner: HirId,
        ident: &'tcx HirIdent<'tcx>,
        global: bool,
        fqn: &str,
        kind: SymbolKind,
    ) -> &'tcx Symbol {
        let interner = self.unit.interner();
        let unit_index = self.unit.index;

        self.scopes.insert_with(owner, ident, global, |symbol| {
            symbol.set_owner(owner);
            symbol.set_fqn(fqn.to_string(), interner);
            symbol.set_kind(kind);
            symbol.set_unit_index(unit_index);
        })
    }

    fn has_public_visibility(&self, node: &HirNode<'tcx>) -> bool {
        let ts_node = node.inner_ts_node();
        let Some(name_node) = ts_node.child_by_field_name("name") else {
            return false;
        };
        let header = self
            .unit
            .file()
            .opt_get_text(ts_node.start_byte(), name_node.start_byte())
            .unwrap_or_default();

        !matches!(FnVisibility::from_header(&header), FnVisibility::Private)
    }

    fn should_register_globally(&self, node: &HirNode<'tcx>) -> bool {
        self.parent_symbol().is_none() || self.has_public_visibility(node)
    }

    fn enum_variant_should_register_globally(&self, _node: &HirNode<'tcx>) -> bool {
        let Some(enum_symbol) = self.scopes.scoped_symbol() else {
            return false;
        };

        if enum_symbol.kind() != SymbolKind::Enum {
            return false;
        }

        let parent_node = self.unit.hir_node(enum_symbol.owner());
        self.has_public_visibility(&parent_node)
    }

    fn visit_children_new_scope(
        &mut self,
        node: &HirNode<'tcx>,
        scoped_symbol: Option<&'tcx Symbol>,
    ) {
        let depth = self.scopes.depth();
        let scope = self.unit.alloc_scope(node.hir_id());

        let symbol = scoped_symbol.or_else(|| self.scopes.scoped_symbol());
        self.scopes.push_with_symbol(scope, symbol);
        self.visit_children(node);
        self.scopes.pop_until(depth);
    }
}

impl<'tcx> AstVisitorRust<'tcx> for DeclCollector<'tcx> {
    fn unit(&self) -> CompileUnit<'tcx> {
        self.unit
    }

    fn visit_source_file(&mut self, node: HirNode<'tcx>) {
        self.visit_children_new_scope(&node, None);
    }

    fn visit_function_item(&mut self, node: HirNode<'tcx>) {
        let register_globally = self.should_register_globally(&node);
        if let Some((symbol, _ident, fqn)) = self.create_new_symbol(
            &node,
            LangRust::field_name,
            register_globally,
            SymbolKind::Function,
        ) {
            if let Some(desc) = FunctionDescriptor::from_hir(self.unit, &node, fqn.clone()) {
                self.functions.push(desc);
            }
            self.visit_children_new_scope(&node, Some(symbol));
        } else {
            self.visit_children(&node);
        }
    }

    fn visit_let_declaration(&mut self, node: HirNode<'tcx>) {
        if let Some((_symbol, ident, fqn)) =
            self.create_new_symbol(&node, LangRust::field_pattern, false, SymbolKind::Variable)
        {
            let var =
                VariableDescriptor::from_let(self.unit, &node, ident.name.clone(), fqn.clone());
            self.variables.push(var);
        }
        self.visit_children(&node);
    }

    fn visit_block(&mut self, node: HirNode<'tcx>) {
        self.visit_children_new_scope(&node, None);
    }

    fn visit_parameter(&mut self, node: HirNode<'tcx>) {
        let _ = self.create_new_symbol(&node, LangRust::field_pattern, false, SymbolKind::Variable);
        self.visit_children(&node);
    }

    fn visit_mod_item(&mut self, node: HirNode<'tcx>) {
        let symbol = self
            .create_new_symbol(&node, LangRust::field_name, true, SymbolKind::Module)
            .map(|(symbol, _ident, _)| symbol);
        self.visit_children_new_scope(&node, symbol);
    }

    fn visit_impl_item(&mut self, node: HirNode<'tcx>) {
        let symbol = node
            .opt_child_by_field(self.unit, LangRust::field_type)
            .and_then(|type_node| {
                let segments = impl_type_segments(self.unit, &type_node)?;
                if segments.is_empty() {
                    return None;
                }

                let keys: Vec<_> = segments
                    .iter()
                    .map(|segment| self.unit.interner().intern(segment))
                    .collect();

                if let Some(symbol) = self.scopes.find_global_suffix(&keys) {
                    symbol.set_owner(node.hir_id());
                    symbol.set_unit_index(self.unit.index);
                    Some(symbol)
                } else {
                    let fqn = segments.join("::");
                    let owner = node.hir_id();

                    // For impl blocks with qualified types like `impl From<T> for module::Type`,
                    // use the last segment (the actual type name) as the symbol name.
                    // This ensures proper trie indexing.
                    let impl_name = segments
                        .last()
                        .cloned()
                        .unwrap_or_else(|| "impl".to_string());

                    // Create a synthetic identifier using the impl target type name
                    let synthetic_ident = self.unit.cc.arena.alloc(HirIdent::new(
                        // Create a minimal HirBase using the impl node's information
                        HirBase {
                            hir_id: owner,
                            parent: node.parent(),
                            node: node.inner_ts_node(),
                            kind: HirKind::Identifier,
                            field_id: u16::MAX,
                            children: Vec::new(),
                        },
                        impl_name,
                    ));

                    let global = false;
                    let kind = SymbolKind::Impl;
                    let symbol =
                        self.scopes
                            .insert_with(owner, synthetic_ident, global, |symbol| {
                                symbol.set_owner(owner);
                                symbol.set_fqn(fqn, self.unit.interner());
                                symbol.set_kind(kind);
                                symbol.set_unit_index(self.unit.index);
                            });
                    Some(symbol)
                }
            });
        self.visit_children_new_scope(&node, symbol);
    }

    fn visit_trait_item(&mut self, node: HirNode<'tcx>) {
        self.visit_children_new_scope(&node, None);
    }

    fn visit_call_expression(&mut self, node: HirNode<'tcx>) {
        let enclosing = self
            .parent_symbol()
            .map(|symbol| symbol.fqn_name.borrow().clone());
        let desc = CallDescriptor::from_call(self.unit, &node, enclosing);
        self.calls.push(desc);
        self.visit_children(&node);
    }

    fn visit_const_item(&mut self, node: HirNode<'tcx>) {
        let kind = node.inner_ts_node().kind();
        if let Some((symbol, ident, fqn)) =
            self.create_new_symbol(&node, LangRust::field_name, true, SymbolKind::Const)
        {
            let variable = match kind {
                "const_item" => VariableDescriptor::from_const_item(
                    self.unit,
                    &node,
                    ident.name.clone(),
                    fqn.clone(),
                ),
                "static_item" => VariableDescriptor::from_static_item(
                    self.unit,
                    &node,
                    ident.name.clone(),
                    fqn.clone(),
                ),
                _ => return,
            };
            self.variables.push(variable);
            self.visit_children_new_scope(&node, Some(symbol));
        } else {
            self.visit_children(&node);
        }
    }

    fn visit_static_item(&mut self, node: HirNode<'tcx>) {
        self.visit_const_item(node);
    }

    fn visit_struct_item(&mut self, node: HirNode<'tcx>) {
        let register_globally = self.should_register_globally(&node);
        if let Some((symbol, _ident, fqn)) = self.create_new_symbol(
            &node,
            LangRust::field_name,
            register_globally,
            SymbolKind::Struct,
        ) {
            if let Some(desc) = StructDescriptor::from_struct(self.unit, &node, fqn.clone()) {
                self.structs.push(desc);
            }
            self.visit_children_new_scope(&node, Some(symbol));
        } else {
            eprintln!("Failed to create struct descriptor for: {:?}", node);
            self.visit_children(&node);
        }
    }

    fn visit_enum_item(&mut self, node: HirNode<'tcx>) {
        let register_globally = self.should_register_globally(&node);
        if let Some((symbol, _ident, fqn)) = self.create_new_symbol(
            &node,
            LangRust::field_name,
            register_globally,
            SymbolKind::Enum,
        ) {
            if let Some(desc) = EnumDescriptor::from_enum(self.unit, &node, fqn.clone()) {
                self.enums.push(desc);
            }
            self.visit_children_new_scope(&node, Some(symbol));
        } else {
            self.visit_children(&node);
        }
    }

    fn visit_enum_variant(&mut self, node: HirNode<'tcx>) {
        let register_globally = self.enum_variant_should_register_globally(&node);
        let _ = self.create_new_symbol(
            &node,
            LangRust::field_name,
            register_globally,
            SymbolKind::EnumVariant,
        );
        self.visit_children(&node);
    }

    fn visit_unknown(&mut self, node: HirNode<'tcx>) {
        self.visit_children(&node);
    }
}

fn impl_type_segments<'tcx>(
    unit: CompileUnit<'tcx>,
    type_node: &HirNode<'tcx>,
) -> Option<Vec<String>> {
    let ts_node = type_node.inner_ts_node();
    let expr = parse_type_expr(unit, ts_node);
    extract_path_segments(&expr)
}

fn extract_path_segments(expr: &TypeExpr) -> Option<Vec<String>> {
    match expr {
        TypeExpr::Path { segments, .. } => Some(segments.clone()),
        TypeExpr::Reference { inner, .. } => extract_path_segments(inner),
        TypeExpr::Tuple(items) if items.len() == 1 => extract_path_segments(&items[0]),
        _ => None,
    }
}

pub struct CollectionResult {
    pub functions: Vec<FunctionDescriptor>,
    pub variables: Vec<VariableDescriptor>,
    pub calls: Vec<CallDescriptor>,
    pub structs: Vec<StructDescriptor>,
    pub enums: Vec<EnumDescriptor>,
}

pub fn collect_symbols<'tcx>(
    unit: CompileUnit<'tcx>,
    globals: &'tcx Scope<'tcx>,
) -> CollectionResult {
    let root = unit.file_start_hir_id().unwrap();
    let node = unit.hir_node(root);
    let mut decl_finder = DeclCollector::new(unit, globals);
    decl_finder.visit_node(node);
    CollectionResult {
        functions: decl_finder.take_functions(),
        variables: decl_finder.take_variables(),
        calls: decl_finder.take_calls(),
        structs: decl_finder.take_structs(),
        enums: decl_finder.take_enums(),
    }
}
