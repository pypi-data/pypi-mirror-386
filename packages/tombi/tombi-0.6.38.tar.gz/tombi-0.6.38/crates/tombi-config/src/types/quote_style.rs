/// The preferred quote character for strings.
#[derive(Debug, Default, Clone, Copy)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
#[cfg_attr(feature = "serde", serde(rename_all = "lowercase"))]
#[cfg_attr(feature = "jsonschema", derive(schemars::JsonSchema))]
pub enum QuoteStyle {
    /// Prefer the double quote
    #[default]
    Double,

    /// Prefer the single quote
    Single,

    /// Preserve the source quote
    Preserve,
}
