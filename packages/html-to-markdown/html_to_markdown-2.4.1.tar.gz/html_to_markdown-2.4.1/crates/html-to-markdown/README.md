# html-to-markdown-rs

High-performance HTML to Markdown converter built with Rust.

[![Crates.io](https://img.shields.io/crates/v/html-to-markdown-rs.svg)](https://crates.io/crates/html-to-markdown-rs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Goldziher/html-to-markdown/blob/main/LICENSE)
[![docs.rs](https://docs.rs/html-to-markdown-rs/badge.svg)](https://docs.rs/html-to-markdown-rs)

Fast, reliable HTML to Markdown conversion with full CommonMark compliance. Built with `html5ever` for correctness and `ammonia` for safe HTML preprocessing.

## Installation

```toml
[dependencies]
html-to-markdown-rs = "2.3"
```

## Basic Usage

```rust
use html_to_markdown_rs::{convert, ConversionOptions};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let html = r#"
        <h1>Welcome</h1>
        <p>This is <strong>fast</strong> conversion!</p>
        <ul>
            <li>Built with Rust</li>
            <li>CommonMark compliant</li>
        </ul>
    "#;

    let markdown = convert(html, None)?;
    println!("{}", markdown);
    Ok(())
}
```

## Configuration

```rust
use html_to_markdown_rs::{
    convert, ConversionOptions, HeadingStyle, ListIndentType,
    PreprocessingOptions, PreprocessingPreset,
};

let options = ConversionOptions {
    heading_style: HeadingStyle::Atx,
    list_indent_width: 2,
    list_indent_type: ListIndentType::Spaces,
    bullets: "-".to_string(),
    strong_em_symbol: '*',
    escape_asterisks: false,
    escape_underscores: false,
    newline_style: html_to_markdown_rs::NewlineStyle::Backslash,
    code_block_style: html_to_markdown_rs::CodeBlockStyle::Backticks,
    ..Default::default()
};

let markdown = convert(html, Some(options))?;
```

## Web Scraping with Preprocessing

```rust
use html_to_markdown_rs::{convert, ConversionOptions, PreprocessingOptions};

let mut options = ConversionOptions::default();
options.preprocessing.enabled = true;
options.preprocessing.preset = html_to_markdown_rs::PreprocessingPreset::Aggressive;
options.preprocessing.remove_navigation = true;
options.preprocessing.remove_forms = true;

let markdown = convert(scraped_html, Some(options))?;
```

## hOCR Table Extraction

```rust
use html_to_markdown_rs::convert;

// hOCR documents (from Tesseract, etc.) are detected automatically.
// Tables and spatial layout are reconstructed without additional options.
let markdown = convert(hocr_html, None)?;
```

## Inline Image Extraction

```rust
use html_to_markdown_rs::{convert_with_inline_images, InlineImageConfig};

let config = InlineImageConfig::new(5 * 1024 * 1024) // 5MB max
    .with_infer_dimensions(true)
    .with_filename_prefix("img_".to_string());

let extraction = convert_with_inline_images(html, None, config)?;

println!("{}", extraction.markdown);
for (i, img) in extraction.inline_images.iter().enumerate() {
    println!("Image {}: {} ({} bytes)", i, img.format, img.data.len());
}
```

## Other Language Bindings

This is the core Rust library. For other languages:

- **JavaScript/TypeScript**: [@html-to-markdown/node](https://github.com/Goldziher/html-to-markdown/tree/main/crates/html-to-markdown-node) (NAPI-RS) or [@html-to-markdown/wasm](https://github.com/Goldziher/html-to-markdown/tree/main/crates/html-to-markdown-wasm) (WebAssembly)
- **Python**: [html-to-markdown](https://github.com/Goldziher/html-to-markdown/tree/main/crates/html-to-markdown-py) (PyO3)
- **CLI**: [html-to-markdown-cli](https://github.com/Goldziher/html-to-markdown/tree/main/crates/html-to-markdown-cli)

## Documentation

- [Full Documentation](https://github.com/Goldziher/html-to-markdown/blob/main/README.md)
- [API Reference](https://docs.rs/html-to-markdown-rs)
- [Contributing Guide](https://github.com/Goldziher/html-to-markdown/blob/main/CONTRIBUTING.md)

## Performance

10-30x faster than pure Python/JavaScript implementations, delivering 150-210 MB/s throughput.

## License

MIT
