mod utils;

use crate::utils::helpers::{enforce_array, enforce_object, enforce_string, enforce_u64};
use crate::utils::mock_event_logging_adapter::MockEventLoggingAdapter;
use crate::utils::mock_specs_adapter::MockSpecsAdapter;
use chrono::Utc;
use statsig_rust::{Statsig, StatsigOptions, StatsigUser};
use std::sync::Arc;
use std::time::Duration;
use tokio::time::sleep;

#[tokio::test]
async fn test_gate_exposures_initialized() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let _ = statsig.check_gate(&user, "test_public");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let reason = get_reason_from_adapter(&logging_adapter).await;
    assert_eq!(reason, "Bootstrap:Recognized");
}

#[tokio::test]
async fn test_gate_exposures_formatting() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let _ = statsig.check_gate(&user, "test_50_50");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let received = logging_adapter.force_get_received_payloads();

    let statsig_meta = enforce_object(&received.statsig_metadata);
    assert_eq!(statsig_meta["sdkType"], "statsig-server-core");
    assert!(statsig_meta["sdkVersion"].as_str().is_some());

    let exposure = logging_adapter.force_get_first_event();
    assert_eq!(exposure["eventName"], "statsig::gate_exposure");

    let sec_expos = enforce_array(&exposure["secondaryExposures"]);
    let holdout_exposure = enforce_object(&sec_expos[0]);
    assert_eq!(holdout_exposure["gate"], "global_holdout");
    assert_eq!(holdout_exposure["gateValue"], "false");
    assert_eq!(holdout_exposure["ruleID"], "3QoA4ncNdVGBaMt3N1KYjz:0.50:1");
}

#[tokio::test]
async fn test_gate_exposures_uninitialized() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);

    let _ = statsig.check_gate(&user, "test_public");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let reason = get_reason_from_adapter(&logging_adapter).await;
    assert_eq!(reason, "Uninitialized");
}

#[tokio::test]
async fn test_gate_exposures_unrecognized() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let _ = statsig.check_gate(&user, "not_a_gate");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let reason = get_reason_from_adapter(&logging_adapter).await;
    assert_eq!(reason, "Bootstrap:Unrecognized");
}

#[tokio::test]
async fn test_gate_exposures_bad_network() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_trowing_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    let _ = statsig.initialize().await;

    let _ = statsig.check_gate(&user, "not_a_gate");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let reason = get_reason_from_adapter(&logging_adapter).await;
    assert_eq!(reason, "NoValues");
}

#[tokio::test]
async fn test_gate_exposures_not_awaited() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_delayed_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = Arc::new(create_statsig(&specs_adapter, &logging_adapter));

    let shared_statsig = statsig.clone();
    tokio::task::spawn(async move {
        shared_statsig.initialize().await.unwrap();
    });

    sleep(Duration::from_millis(1)).await;

    let _ = statsig.check_gate(&user, "not_a_gate");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let reason = get_reason_from_adapter(&logging_adapter).await;
    assert_eq!(reason, "Loading:Unrecognized");
}

#[tokio::test]
async fn test_check_gate_exposure_with_secondary_exposures() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let _ = statsig.check_gate(&user, "test_nested_gate_condition");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let event = logging_adapter.force_get_first_event();
    let secondary_expo = enforce_array(&event["secondaryExposures"]);

    let one = enforce_object(&secondary_expo[0]);
    assert_eq!(one["gate"], "test_email");
    assert_eq!(one["ruleID"], "default");
    assert_eq!(one["gateValue"], "false");

    let two = enforce_object(&secondary_expo[1]);
    assert_eq!(two["gate"], "test_environment_tier");
    assert_eq!(two["ruleID"], "default");
    assert_eq!(two["gateValue"], "false");
}

#[tokio::test]
async fn test_get_feature_gate_exposure_with_secondary_exposures() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let _ = statsig.get_feature_gate(&user, "test_nested_gate_condition");
    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let event = logging_adapter.force_get_first_event();
    let secondary_expo = enforce_array(&event["secondaryExposures"]);

    let one = enforce_object(&secondary_expo[0]);
    assert_eq!(one["gate"], "test_email");
    assert_eq!(one["ruleID"], "default");
    assert_eq!(one["gateValue"], "false");

    let two = enforce_object(&secondary_expo[1]);
    assert_eq!(two["gate"], "test_environment_tier");
    assert_eq!(two["ruleID"], "default");
    assert_eq!(two["gateValue"], "false");
}

#[tokio::test]
async fn test_get_layer_copies_undelegated_exposures() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("a_user_id");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let layer = statsig.get_layer(&user, "layer_in_global_holdout");
    let _ = layer.get_string("shared_param", String::new());

    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let event = logging_adapter.force_get_first_event();
    let secondary_expo = enforce_array(&event["secondaryExposures"]);

    let one = enforce_object(&secondary_expo[0]);
    assert_eq!(one["gate"], "global_holdout");
    assert_eq!(one["ruleID"], "3QoA4ncNdVGBaMt3N1KYjz:0.50:1");
    assert_eq!(one["gateValue"], "false");
}

#[tokio::test]
async fn test_get_layer_with_holdouts() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("user-in-layer-holdout-4");

    let statsig = create_statsig(&specs_adapter, &logging_adapter);
    statsig.initialize().await.unwrap();

    let layer = statsig.get_layer(&user, "test_layer_in_holdout");
    let _ = layer.get_string("layer_val", String::new());

    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let event = logging_adapter.force_get_first_event();
    let secondary_expo = enforce_array(&event["secondaryExposures"]);

    let one = enforce_object(&secondary_expo[0]);
    assert_eq!(one["gate"], "global_holdout");
    assert_eq!(one["ruleID"], "3QoA4ncNdVGBaMt3N1KYjz:0.50:1");
    assert_eq!(one["gateValue"], "false");

    let two = enforce_object(&secondary_expo[1]);
    assert_eq!(two["gate"], "layer_holdout");
    assert_eq!(two["ruleID"], "2bAVp6R3C85vCYrR6be36n:10.00:5");
    assert_eq!(two["gateValue"], "true");
}

#[tokio::test]
async fn test_exposures_with_environment() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("user-in-layer-holdout-4");

    let statsig =
        create_statsig_with_environment(&specs_adapter, &logging_adapter, Some("dev".to_string()));
    statsig.initialize().await.unwrap();

    let _ = statsig.check_gate(&user, "test_public");
    let _ = statsig.get_dynamic_config(&user, "test_dynamic_config");
    let layer = statsig.get_layer(&user, "test_layer_in_holdout");
    let _ = layer.get_string("layer_val", String::new());

    sleep(Duration::from_millis(1)).await;
    statsig.flush_events().await;

    let events = logging_adapter.force_get_received_payloads();
    let event = enforce_object(&events.events[0]);
    let user = enforce_object(&event["user"]);
    assert_eq!(user["statsigEnvironment"]["tier"], "dev");
}

#[tokio::test]
async fn test_exposure_time() {
    let logging_adapter = Arc::new(MockEventLoggingAdapter::new());
    let specs_adapter = create_bootrapped_specs_adapter();
    let user = StatsigUser::with_user_id("user-in-layer-holdout-4");

    let statsig =
        create_statsig_with_environment(&specs_adapter, &logging_adapter, Some("dev".to_string()));
    statsig.initialize().await.unwrap();

    let _ = statsig.check_gate(&user, "test_public");
    let _ = statsig.get_dynamic_config(&user, "test_email_config");
    let _ = statsig.get_experiment(&user, "test_experiment_no_targeting");
    let _ = statsig
        .get_layer(&user, "layer_with_many_params")
        .get_string("a_string", String::new());

    let was = Utc::now().timestamp_millis() as u64;
    sleep(Duration::from_millis(100)).await;
    statsig.flush_events().await;

    let payload = logging_adapter.force_get_received_payloads();
    let events = enforce_array(&payload.events);

    let gate_expo = enforce_object(&events[0]);
    assert_eq!(gate_expo["eventName"], "statsig::gate_exposure");
    assert_eq!(enforce_u64(&gate_expo["time"]), was);

    let config_expo = enforce_object(&events[1]);
    assert_eq!(config_expo["eventName"], "statsig::config_exposure");
    assert_eq!(enforce_u64(&config_expo["time"]), was);

    let experiment_expo = enforce_object(&events[2]);
    assert_eq!(experiment_expo["eventName"], "statsig::config_exposure");
    assert_eq!(enforce_u64(&experiment_expo["time"]), was);

    let layer_expo = enforce_object(&events[3]);
    assert_eq!(layer_expo["eventName"], "statsig::layer_exposure");
    assert_eq!(enforce_u64(&layer_expo["time"]), was);
}

fn create_bootrapped_specs_adapter() -> Arc<MockSpecsAdapter> {
    Arc::new(MockSpecsAdapter::with_data("tests/data/eval_proj_dcs.json"))
}

fn create_trowing_specs_adapter() -> Arc<MockSpecsAdapter> {
    Arc::new(MockSpecsAdapter::throwing())
}

fn create_delayed_specs_adapter() -> Arc<MockSpecsAdapter> {
    Arc::new(MockSpecsAdapter::delayed(
        "tests/data/eval_proj_dcs.json",
        100,
    ))
}

fn create_statsig(
    specs_adapter: &Arc<MockSpecsAdapter>,
    logging_adapter: &Arc<MockEventLoggingAdapter>,
) -> Statsig {
    create_statsig_with_environment(specs_adapter, logging_adapter, None)
}

fn create_statsig_with_environment(
    specs_adapter: &Arc<MockSpecsAdapter>,
    logging_adapter: &Arc<MockEventLoggingAdapter>,
    environment: Option<String>,
) -> Statsig {
    Statsig::new(
        "secret-shhh",
        Some(Arc::new(StatsigOptions {
            specs_adapter: Some(specs_adapter.clone()),
            event_logging_adapter: Some(logging_adapter.clone()),
            environment,
            ..StatsigOptions::new()
        })),
    )
}

async fn get_reason_from_adapter(logging_adapter: &MockEventLoggingAdapter) -> String {
    let event = logging_adapter.force_get_first_event();
    let metadata = enforce_object(&event["metadata"]);

    enforce_string(&metadata["reason"])
}
