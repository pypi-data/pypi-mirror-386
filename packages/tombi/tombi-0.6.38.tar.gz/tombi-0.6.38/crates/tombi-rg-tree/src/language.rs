use crate::SyntaxKind;

pub trait Language: Sized + Copy + std::fmt::Debug + Eq + Ord + std::hash::Hash {
    type Kind: Sized + Copy + std::fmt::Debug + Eq + Ord + std::hash::Hash;

    fn kind_from_raw(raw: SyntaxKind) -> Self::Kind;
    fn kind_to_raw(kind: Self::Kind) -> SyntaxKind;
}
