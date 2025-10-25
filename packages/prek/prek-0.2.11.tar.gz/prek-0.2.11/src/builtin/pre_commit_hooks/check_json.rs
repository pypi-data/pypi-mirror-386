use std::path::Path;

use anyhow::Result;
use futures::StreamExt;
use rustc_hash::FxHashMap;
use serde::{Deserialize, Deserializer};

use crate::hook::Hook;
use crate::run::CONCURRENCY;

#[derive(Debug)]
enum JsonValue {
    Object(FxHashMap<String, JsonValue>),
    Array(Vec<JsonValue>),
    String(String),
    Number(serde_json::Number),
    Bool(bool),
    Null,
}

pub(crate) async fn check_json(hook: &Hook, filenames: &[&Path]) -> Result<(i32, Vec<u8>)> {
    let mut tasks = futures::stream::iter(filenames)
        .map(async |filename| check_file(hook.project().relative_path(), filename).await)
        .buffered(*CONCURRENCY);

    let mut code = 0;
    let mut output = Vec::new();

    while let Some(result) = tasks.next().await {
        let (c, o) = result?;
        code |= c;
        output.extend(o);
    }

    Ok((code, output))
}

async fn check_file(file_base: &Path, filename: &Path) -> Result<(i32, Vec<u8>)> {
    let file_path = file_base.join(filename);
    let content = fs_err::tokio::read(file_path).await?;
    if content.is_empty() {
        return Ok((0, Vec::new()));
    }

    let mut deserializer = serde_json::Deserializer::from_slice(&content);
    deserializer.disable_recursion_limit();
    let deserializer = serde_stacker::Deserializer::new(&mut deserializer);

    // Try to parse with duplicate key detection
    match JsonValue::deserialize(deserializer) {
        Ok(json) => {
            carefully_drop_nested_json(json);
            Ok((0, Vec::new()))
        }
        Err(e) => {
            let error_message = format!("{}: Failed to json decode ({e})\n", filename.display());
            Ok((1, error_message.into_bytes()))
        }
    }
}

// For deeply nested JSON structures, `Drop` can cause stack overflow.
fn carefully_drop_nested_json(value: JsonValue) {
    let mut stack = vec![value];
    let mut map = FxHashMap::default();
    while let Some(value) = stack.pop() {
        match value {
            JsonValue::Array(array) => stack.extend(array),
            JsonValue::Object(object) => map.extend(object),
            _ => {}
        }
    }
}

impl<'de> Deserialize<'de> for JsonValue {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        use serde::de::{self, MapAccess, SeqAccess, Visitor};
        use std::fmt;

        struct JsonValueVisitor;

        impl<'de> Visitor<'de> for JsonValueVisitor {
            type Value = JsonValue;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("a JSON value")
            }

            fn visit_bool<E>(self, v: bool) -> Result<Self::Value, E> {
                Ok(JsonValue::Bool(v))
            }

            fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E> {
                Ok(JsonValue::Number(v.into()))
            }

            fn visit_u64<E>(self, v: u64) -> Result<Self::Value, E> {
                Ok(JsonValue::Number(v.into()))
            }

            fn visit_f64<E>(self, v: f64) -> Result<Self::Value, E> {
                Ok(JsonValue::Number(serde_json::Number::from_f64(v).unwrap()))
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E> {
                Ok(JsonValue::String(v.to_string()))
            }

            fn visit_string<E>(self, v: String) -> Result<Self::Value, E> {
                Ok(JsonValue::String(v))
            }

            fn visit_unit<E>(self) -> Result<Self::Value, E> {
                Ok(JsonValue::Null)
            }

            fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
            where
                A: SeqAccess<'de>,
            {
                let mut vec = Vec::new();
                while let Some(element) = seq.next_element()? {
                    vec.push(element);
                }
                Ok(JsonValue::Array(vec))
            }

            fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
            where
                A: MapAccess<'de>,
            {
                let mut object = FxHashMap::default();
                while let Some(key) = map.next_key::<String>()? {
                    if object.contains_key(&key) {
                        return Err(de::Error::custom(format!("duplicate key `{key}`")));
                    }
                    let value = map.next_value()?;
                    object.insert(key, value);
                }
                Ok(JsonValue::Object(object))
            }
        }

        deserializer.deserialize_any(JsonValueVisitor)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::{Path, PathBuf};
    use tempfile::tempdir;

    async fn create_test_file(
        dir: &tempfile::TempDir,
        name: &str,
        content: &[u8],
    ) -> Result<PathBuf> {
        let file_path = dir.path().join(name);
        fs_err::tokio::write(&file_path, content).await?;
        Ok(file_path)
    }

    #[tokio::test]
    async fn test_valid_json() -> Result<()> {
        let dir = tempdir()?;
        let content = br#"{"key1": "value1", "key2": "value2"}"#;
        let file_path = create_test_file(&dir, "valid.json", content).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 0);
        assert!(output.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_invalid_json() -> Result<()> {
        let dir = tempdir()?;
        let content = br#"{"key1": "value1", "key2": "value2""#;
        let file_path = create_test_file(&dir, "invalid.json", content).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 1);
        assert!(!output.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_duplicate_keys() -> Result<()> {
        let dir = tempdir()?;
        let content = br#"{"key1": "value1", "key1": "value2"}"#;
        let file_path = create_test_file(&dir, "duplicate.json", content).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 1);
        assert!(!output.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_empty_json() -> Result<()> {
        let dir = tempdir()?;
        let content = b"";
        let file_path = create_test_file(&dir, "empty.json", content).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 0);
        assert!(output.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_valid_json_array() -> Result<()> {
        let dir = tempdir()?;
        let content = br#"[{"key1": "value1"}, {"key2": "value2"}]"#;
        let file_path = create_test_file(&dir, "valid_array.json", content).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 0);
        assert!(output.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_duplicate_keys_in_nested_object() -> Result<()> {
        let dir = tempdir()?;
        let content = br#"{"key1": "value1", "key2": {"nested_key": 1, "nested_key": 2}}"#;
        let file_path = create_test_file(&dir, "nested_duplicate.json", content).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 1);
        assert!(!output.is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_recursion_limit() -> Result<()> {
        let dir = tempdir()?;

        let mut json = String::new();
        for _ in 0..10000 {
            json = format!("[{json}]");
        }

        let file_path = create_test_file(&dir, "deeply_nested.json", json.as_bytes()).await?;
        let (code, output) = check_file(Path::new(""), &file_path).await?;
        assert_eq!(code, 0);
        assert!(output.is_empty());

        Ok(())
    }
}
