mod utils;

use crate::utils::mock_event_logging_adapter::MockEventLoggingAdapter;
use crate::utils::mock_specs_adapter::MockSpecsAdapter;
use statsig_rust::{Statsig, StatsigOptions, StatsigUser};
use std::sync::Arc;

async fn setup() -> Statsig {
    let mut options = StatsigOptions::new();
    options.specs_adapter = Some(Arc::new(MockSpecsAdapter::with_data(
        "tests/data/big_number_dcs.json",
    )));
    options.event_logging_adapter = Some(Arc::new(MockEventLoggingAdapter::new()));

    let statsig = Statsig::new("secret-key", Some(Arc::new(options)));
    statsig.initialize().await.unwrap();
    statsig
}

#[tokio::test]
async fn test_dynamic_config_getters() {
    let statsig = setup().await;
    let user = StatsigUser::with_user_id("a_user_id");

    let config = statsig.get_dynamic_config(&user, "big_number");

    let expected = 0.999_999_999_999_999_1;
    assert_eq!(config.get_f64("f64", 111f64), expected);
}
