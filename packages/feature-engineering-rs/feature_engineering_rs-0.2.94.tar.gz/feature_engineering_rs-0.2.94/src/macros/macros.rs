/// Macro for defining a feature
#[macro_export]
macro_rules! define_feature {
    ($struct_name:ident, $fn_name:ident, $feature_name:expr) => {
        pub struct $struct_name;
        impl $crate::parallel::common::FeatureCompute for $struct_name {
            fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
                $fn_name(y)
            }
            fn name(&self) -> String {
                $feature_name.to_string()
            }
        }
    };
}

/// Macro for getting all features
#[macro_export]
macro_rules! feature_registry {
    ($($struct_name:ident),* $(,)?) => {
        pub fn get_features() -> Vec<Box<dyn $crate::parallel::common::FeatureCompute>> {
            vec![
                $(Box::new($struct_name),)*
            ]
        }
    };
}


/// Macro for boxing feature structs
#[macro_export]
macro_rules! boxed_features {
    ($($feature:expr),* $(,)?) => {
        vec![$(Box::new($feature) as Box<dyn $crate::parallel::common::FeatureCompute>),*]
    };
}