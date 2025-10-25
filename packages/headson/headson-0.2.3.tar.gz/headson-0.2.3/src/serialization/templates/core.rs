use super::super::indent;
use super::{ArrayCtx, ObjectCtx};

// Shared rendering core for all templates.
// - Style controls only empty/omitted decorations.
// - Indentation and newlines come from ctx (depth, indent_unit, newline).
// - When ctx.inline_open is true, no leading indent is emitted before the opener.
pub trait Style {
    fn array_empty(open_indent: &str, ctx: &ArrayCtx<'_>) -> String;
    fn array_push_omitted(_out: &mut String, _ctx: &ArrayCtx<'_>) {}

    fn object_empty(open_indent: &str, ctx: &ObjectCtx<'_>) -> String;
    fn object_push_omitted(_out: &mut String, _ctx: &ObjectCtx<'_>) {}
}

fn push_array_items(out: &mut String, ctx: &ArrayCtx<'_>) {
    for (i, (_, item)) in ctx.children.iter().enumerate() {
        out.push_str(item);
        if i + 1 < ctx.children_len {
            out.push(',');
        }
        out.push_str(ctx.newline);
    }
}

fn push_object_items(out: &mut String, ctx: &ObjectCtx<'_>) {
    for (i, (_, (k, v))) in ctx.children.iter().enumerate() {
        out.push_str(&indent(ctx.depth + 1, ctx.indent_unit));
        out.push_str(k);
        out.push(':');
        out.push_str(ctx.space);
        out.push_str(v);
        if i + 1 < ctx.children_len {
            out.push(',');
        }
        out.push_str(ctx.newline);
    }
}

// Render an array using the shared control flow and style-specific decorations.
pub fn render_array_with<S: Style>(ctx: &ArrayCtx<'_>) -> String {
    let base = indent(ctx.depth, ctx.indent_unit);
    let open_indent = if ctx.inline_open { "" } else { &base };
    if ctx.children_len == 0 {
        return S::array_empty(open_indent, ctx);
    }
    let mut out = String::new();
    out.push_str(open_indent);
    out.push('[');
    out.push_str(ctx.newline);
    push_array_items(&mut out, ctx);
    S::array_push_omitted(&mut out, ctx);
    out.push_str(&base);
    out.push(']');
    out
}

// Render an object using the shared control flow and style-specific decorations.
pub fn render_object_with<S: Style>(ctx: &ObjectCtx<'_>) -> String {
    let base = indent(ctx.depth, ctx.indent_unit);
    let open_indent = if ctx.inline_open { "" } else { &base };
    if ctx.children_len == 0 {
        return S::object_empty(open_indent, ctx);
    }
    let mut out = String::new();
    out.push_str(open_indent);
    out.push('{');
    out.push_str(ctx.newline);
    push_object_items(&mut out, ctx);
    S::object_push_omitted(&mut out, ctx);
    out.push_str(&base);
    out.push('}');
    out
}
