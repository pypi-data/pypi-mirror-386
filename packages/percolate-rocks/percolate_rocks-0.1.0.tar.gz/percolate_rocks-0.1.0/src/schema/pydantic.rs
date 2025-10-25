//! Pydantic JSON Schema parser.
//!
//! Extracts metadata from `json_schema_extra`.

use crate::types::Result;
use crate::schema::category::SchemaCategory;
use serde::{Deserialize, Serialize};

/// MCP tool configuration for agent-lets.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolConfig {
    /// MCP server name (e.g., "carrier", "percolate")
    pub mcp_server: String,

    /// Tool name (e.g., "search_knowledge_base")
    pub tool_name: String,

    /// Usage description (when to use this tool)
    pub usage: String,
}

/// MCP resource configuration for agent-lets.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceConfig {
    /// Resource URI (e.g., "cda://field-definitions")
    pub uri: String,

    /// Usage description (what this resource provides)
    pub usage: String,
}

/// Parser for Pydantic JSON Schema with `json_schema_extra`.
pub struct PydanticSchemaParser;

impl PydanticSchemaParser {
    /// Extract `embedding_fields` from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Vector of field names to embed
    pub fn extract_embedding_fields(schema: &serde_json::Value) -> Vec<String> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("embedding_fields"))
            .and_then(|fields| fields.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(String::from))
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Extract `indexed_fields` from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Vector of field names to index
    pub fn extract_indexed_fields(schema: &serde_json::Value) -> Vec<String> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("indexed_fields"))
            .and_then(|fields| fields.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(String::from))
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Extract `key_field` from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Key field name if configured
    pub fn extract_key_field(schema: &serde_json::Value) -> Option<String> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("key_field"))
            .and_then(|v| v.as_str())
            .map(String::from)
    }

    /// Extract `fully_qualified_name` from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Fully qualified name if present
    pub fn extract_fqn(schema: &serde_json::Value) -> Option<String> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("name"))
            .and_then(|v| v.as_str())
            .map(String::from)
    }

    /// Extract embedding provider config.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Embedding provider config if present
    pub fn extract_embedding_provider(schema: &serde_json::Value) -> Option<String> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("embedding_provider"))
            .and_then(|v| v.as_str())
            .map(String::from)
    }

    /// Extract MCP tools from agent-let schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Vector of tool configurations
    ///
    /// # Example
    ///
    /// ```json
    /// {
    ///   "json_schema_extra": {
    ///     "tools": [
    ///       {
    ///         "mcp_server": "carrier",
    ///         "tool_name": "search_knowledge_base",
    ///         "usage": "Search for mapping evidence"
    ///       }
    ///     ]
    ///   }
    /// }
    /// ```
    pub fn extract_tools(schema: &serde_json::Value) -> Vec<ToolConfig> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("tools"))
            .and_then(|tools| tools.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| serde_json::from_value(v.clone()).ok())
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Extract MCP resources from agent-let schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Vector of resource configurations
    ///
    /// # Example
    ///
    /// ```json
    /// {
    ///   "json_schema_extra": {
    ///     "resources": [
    ///       {
    ///         "uri": "cda://field-definitions",
    ///         "usage": "Get all CDA field definitions"
    ///       }
    ///     ]
    ///   }
    /// }
    /// ```
    pub fn extract_resources(schema: &serde_json::Value) -> Vec<ResourceConfig> {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("resources"))
            .and_then(|resources| resources.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| serde_json::from_value(v.clone()).ok())
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Extract category from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Schema category (defaults to User if not specified)
    ///
    /// # Example
    ///
    /// ```json
    /// {
    ///   "json_schema_extra": {
    ///     "category": "agents"
    ///   }
    /// }
    /// ```
    pub fn extract_category(schema: &serde_json::Value) -> SchemaCategory {
        schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("category"))
            .and_then(|v| v.as_str())
            .and_then(SchemaCategory::from_str)
            .unwrap_or_default()
    }

    /// Extract version from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Semantic version string
    ///
    /// # Note
    ///
    /// Version is required in all schemas.
    pub fn extract_version(schema: &serde_json::Value) -> Option<String> {
        schema
            .get("version")
            .and_then(|v| v.as_str())
            .map(String::from)
    }

    /// Extract short name from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Short name (table name) if present
    pub fn extract_short_name(schema: &serde_json::Value) -> Option<String> {
        schema
            .get("short_name")
            .and_then(|v| v.as_str())
            .map(String::from)
    }

    /// Extract description from schema.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// Schema description (required for all schemas)
    pub fn extract_description(schema: &serde_json::Value) -> Option<String> {
        schema
            .get("description")
            .and_then(|v| v.as_str())
            .map(String::from)
    }

    /// Check if schema is an agent-let.
    ///
    /// # Arguments
    ///
    /// * `schema` - Pydantic JSON Schema
    ///
    /// # Returns
    ///
    /// `true` if schema has tools or resources configured
    pub fn is_agentlet(schema: &serde_json::Value) -> bool {
        let has_tools = schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("tools"))
            .and_then(|v| v.as_array())
            .map(|arr| !arr.is_empty())
            .unwrap_or(false);

        let has_resources = schema
            .get("json_schema_extra")
            .and_then(|extra| extra.get("resources"))
            .and_then(|v| v.as_array())
            .map(|arr| !arr.is_empty())
            .unwrap_or(false);

        has_tools || has_resources
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_extract_category() {
        let schema = json!({
            "json_schema_extra": {
                "category": "agents"
            }
        });

        let category = PydanticSchemaParser::extract_category(&schema);
        assert_eq!(category, SchemaCategory::Agents);
    }

    #[test]
    fn test_is_agentlet() {
        let schema = json!({
            "json_schema_extra": {
                "tools": [
                    {
                        "mcp_server": "carrier",
                        "tool_name": "search",
                        "usage": "Search"
                    }
                ]
            }
        });

        assert!(PydanticSchemaParser::is_agentlet(&schema));
    }
}
