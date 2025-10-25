use std::collections::HashMap;

use crate::{
    observability::{
        observability_client_adapter::{MetricType, ObservabilityEvent},
        ops_stats::{OpsStatsEvent, OpsStatsForInstance},
        ErrorBoundaryEvent,
    },
    StatsigErr,
};

use super::{event_queue::queue::EventQueue, flush_interval::FlushInterval, flush_type::FlushType};

impl OpsStatsForInstance {
    pub fn log_event_request_failure(&self, event_count: u64, flush_type: FlushType) {
        let error = StatsigErr::LogEventError("Log event failed".to_string());
        self.log_error(ErrorBoundaryEvent {
            exception: error.name().to_string(),
            info: serde_json::to_string(&error).unwrap_or_default(),
            tag: "statsig::log_event_failed".to_string(),
            bypass_dedupe: true,
            dedupe_key: None,
            extra: Some(HashMap::from([
                ("eventCount".to_string(), event_count.to_string()),
                ("flushType".to_string(), flush_type.to_string()),
            ])),
        });
    }

    pub fn log_event_request_success(&self, event_count: usize) {
        self.log(OpsStatsEvent::Observability(ObservabilityEvent {
            metric_type: MetricType::Increment,
            metric_name: "events_successfully_sent_count".to_string(),
            value: event_count as f64,
            tags: None,
        }))
    }

    pub fn log_batching_dropped_events(
        &self,
        drop_error: StatsigErr,
        count: u64,
        flush_interval: &FlushInterval,
        queue: &EventQueue,
        flush_type: FlushType,
    ) {
        let curr_flush_interval = flush_interval.get_current_flush_interval_ms();
        let batch_size = queue.batch_size;
        let max_pending_batches_count = queue.max_pending_batches;

        self.log_error(ErrorBoundaryEvent {
            tag: "statsig::log_event_dropped_event_count".to_string(),
            exception: drop_error.name().to_string(),
            info: serde_json::to_string(&drop_error).unwrap_or_default(),
            bypass_dedupe: true,
            dedupe_key: None,
            extra: Some(HashMap::from([
                ("eventCount".to_string(), count.to_string()),
                (
                    "loggingInterval".to_string(),
                    curr_flush_interval.to_string(),
                ),
                ("batchSize".to_string(), batch_size.to_string()),
                (
                    "maxPendingBatches".to_string(),
                    max_pending_batches_count.to_string(),
                ),
                ("flushType".to_string(), flush_type.to_string()),
            ])),
        });
    }
}
