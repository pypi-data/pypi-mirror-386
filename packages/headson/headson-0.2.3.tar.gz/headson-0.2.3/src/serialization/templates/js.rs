use super::super::indent;
use super::core::{Style, render_array_with, render_object_with};
use super::{ArrayCtx, ObjectCtx};

struct Js;

impl Style for Js {
    fn array_empty(open_indent: &str, ctx: &ArrayCtx<'_>) -> String {
        if ctx.omitted > 0 {
            return format!(
                "{open_indent}[ /* {} more items */ ]",
                ctx.omitted
            );
        }
        format!("{open_indent}[ /* empty */ ]")
    }

    fn array_push_omitted(out: &mut String, ctx: &ArrayCtx<'_>) {
        if ctx.omitted > 0 {
            out.push_str(&indent(ctx.depth + 1, ctx.indent_unit));
            out.push_str(&format!(
                "/* {} more items */{}",
                ctx.omitted, ctx.newline
            ));
        }
    }

    fn object_empty(open_indent: &str, ctx: &ObjectCtx<'_>) -> String {
        if ctx.omitted > 0 {
            let label = if ctx.fileset_root {
                "files"
            } else {
                "properties"
            };
            return format!(
                "{open_indent}{{{space}/* {n} more {label} */{space}}}",
                n = ctx.omitted,
                space = ctx.space
            );
        }
        format!(
            "{open_indent}{{{space}/* empty */{space}}}",
            space = ctx.space
        )
    }

    fn object_push_omitted(out: &mut String, ctx: &ObjectCtx<'_>) {
        if ctx.omitted > 0 {
            out.push_str(&indent(ctx.depth + 1, ctx.indent_unit));
            let label = if ctx.fileset_root {
                "files"
            } else {
                "properties"
            };
            out.push_str(&format!(
                "/* {} more {label} */{}",
                ctx.omitted, ctx.newline
            ));
        }
    }
}

pub fn render_array(ctx: &ArrayCtx<'_>) -> String {
    render_array_with::<Js>(ctx)
}

pub fn render_object(ctx: &ObjectCtx<'_>) -> String {
    render_object_with::<Js>(ctx)
}
