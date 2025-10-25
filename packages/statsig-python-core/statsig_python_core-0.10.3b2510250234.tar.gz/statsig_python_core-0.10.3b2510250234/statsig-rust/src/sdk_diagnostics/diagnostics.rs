use super::diagnostics_utils::DiagnosticsUtils;
use super::marker::{KeyType, Marker};

use crate::event_logging::event_queue::queued_passthrough::EnqueuePassthroughOp;
use crate::event_logging::statsig_event_internal::StatsigEventInternal;
use crate::global_configs::{GlobalConfigs, MAX_SAMPLING_RATE};

use crate::log_w;

use crate::event_logging::event_logger::EventLogger;
use parking_lot::Mutex;
use rand::Rng;
use serde::Serialize;
use std::collections::HashMap;
use std::fmt;
use std::sync::Arc;
use std::time::Duration;

const MAX_MARKER_COUNT: usize = 50;
pub const DIAGNOSTICS_EVENT: &str = "statsig::diagnostics";

#[derive(Eq, Hash, PartialEq, Clone, Serialize, Debug, Copy)]
pub enum ContextType {
    Initialize,
    ConfigSync,
    Unknown,
}

impl fmt::Display for ContextType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ContextType::Initialize => write!(f, "initialize"),
            ContextType::ConfigSync => write!(f, "config_sync"),
            ContextType::Unknown => write!(f, "unknown"),
        }
    }
}

const TAG: &str = stringify!(Diagnostics);
const DEFAULT_SAMPLING_RATE: f64 = 100.0;

pub struct Diagnostics {
    marker_map: Mutex<HashMap<ContextType, Vec<Marker>>>,
    event_logger: Arc<EventLogger>,
    global_configs: Arc<GlobalConfigs>,
    context: Mutex<ContextType>,
}

impl Diagnostics {
    pub fn new(event_logger: Arc<EventLogger>, sdk_key: &str) -> Self {
        Self {
            event_logger,
            marker_map: Mutex::new(HashMap::new()),
            global_configs: GlobalConfigs::get_instance(sdk_key),
            context: Mutex::new(ContextType::Initialize),
        }
    }

    pub fn set_context(&self, context: &ContextType) {
        match self.context.try_lock_for(Duration::from_secs(5)) {
            Some(mut ctx) => {
                *ctx = *context;
            }
            None => {
                log_w!(TAG, "Failed to set context: Failed to lock context");
            }
        }
    }

    pub fn get_markers(&self, context_type: &ContextType) -> Option<Vec<Marker>> {
        match self.marker_map.try_lock_for(Duration::from_secs(5)) {
            Some(map) => {
                if let Some(markers) = map.get(context_type) {
                    return Some(markers.clone());
                }
            }
            None => {
                log_w!(TAG, "Failed to get markers: Failed to lock marker_map");
            }
        }

        None
    }

    pub fn add_marker(&self, context_type: Option<&ContextType>, marker: Marker) {
        let context_type = self.get_context(context_type);

        match self.marker_map.try_lock_for(Duration::from_secs(5)) {
            Some(mut map) => {
                let entry = map.entry(context_type).or_insert_with(Vec::new);
                if entry.len() < MAX_MARKER_COUNT {
                    entry.push(marker);
                }
            }
            None => {
                log_w!(TAG, "Failed to add marker: Failed to lock marker_map");
            }
        }
    }

    pub fn clear_markers(&self, context_type: &ContextType) {
        match self.marker_map.try_lock_for(Duration::from_secs(5)) {
            Some(mut map) => {
                if let Some(markers) = map.get_mut(context_type) {
                    markers.clear();
                }
            }
            None => {
                log_w!(TAG, "Failed to clear markers: Failed to lock marker_map");
            }
        }
    }

    pub fn enqueue_diagnostics_event(
        &self,
        context_type: Option<&ContextType>,
        key: Option<KeyType>,
    ) {
        let context_type: ContextType = self.get_context(context_type);
        let markers = match self.get_markers(&context_type) {
            Some(m) => m,
            None => return,
        };

        if markers.is_empty() {
            return;
        }

        if !self.should_sample(&context_type, key) {
            self.clear_markers(&context_type);
            return;
        }

        let metadata = match DiagnosticsUtils::format_diagnostics_metadata(&context_type, &markers)
        {
            Ok(data) => data,
            Err(err) => {
                log_w!(TAG, "Failed to format diagnostics metadata: {}", err);
                return;
            }
        };

        self.event_logger.enqueue(EnqueuePassthroughOp {
            event: StatsigEventInternal::new_diagnostic_event(metadata),
        });
        self.clear_markers(&context_type);
    }

    pub fn should_sample(&self, context: &ContextType, key: Option<KeyType>) -> bool {
        fn check_sampling_rate(sampling_rate: Option<&f64>) -> bool {
            let mut rng = rand::thread_rng();
            let rand_value = rng.gen::<f64>() * MAX_SAMPLING_RATE;

            match sampling_rate {
                Some(sampling_rate) => rand_value < *sampling_rate,
                None => rand_value < DEFAULT_SAMPLING_RATE,
            }
        }

        if *context == ContextType::Initialize {
            return self
                .global_configs
                .use_diagnostics_sampling_rate("initialize", check_sampling_rate);
        }

        if let Some(key) = key {
            match key {
                KeyType::GetIDListSources => {
                    return self
                        .global_configs
                        .use_diagnostics_sampling_rate("get_id_list", check_sampling_rate);
                }
                KeyType::DownloadConfigSpecs => {
                    return self
                        .global_configs
                        .use_diagnostics_sampling_rate("dcs", check_sampling_rate);
                }
                _ => {}
            }
        }

        check_sampling_rate(None)
    }

    fn get_context(&self, maybe_context: Option<&ContextType>) -> ContextType {
        maybe_context
            .copied()
            .or_else(|| match self.context.try_lock_for(Duration::from_secs(5)) {
                Some(c) => Some(*c),
                None => {
                    log_w!(TAG, "Failed to lock context");
                    None
                }
            })
            .unwrap_or(ContextType::Unknown)
    }
}
