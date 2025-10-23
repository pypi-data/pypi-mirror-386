// src/core/mod.rs
pub mod boolean_algebra;
pub mod data_structures;
pub mod conversions;
pub mod matrixes;
pub mod networking;
pub mod decision_theory;
pub mod formatting;

// Re-export para fácil acceso
pub use boolean_algebra::{BooleanExpr, TruthTable};
pub use conversions::{NumberConverter};
pub use networking::subnets::{FLSMCalculator, SubnetRow, VLSMCalculator, BaseCalculator};

