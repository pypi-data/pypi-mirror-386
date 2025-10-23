use thiserror::Error;

#[derive(Debug, Error)]
pub enum FeatureError {
    #[error("Insufficient data: need at least {min} points, got {actual}")]
    InsufficientData { min: usize, actual: usize },
    
    #[error("Invalid input: {reason}")]
    InvalidInput { reason: String },
    
    #[error("Computation failed: {source}")]
    ComputationError { source: Box<dyn std::error::Error + Send + Sync> },
    
    #[error("Numerical instability detected")]
    NumericalInstability,
}

pub type FeatureResult<T> = Result<T, FeatureError>;