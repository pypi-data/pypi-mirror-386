use super::StatsigUserLoggable;
use crate::evaluation::dynamic_value::DynamicValue;
use crate::hashing::djb2_number;
use crate::StatsigUser;
use crate::{evaluation::dynamic_string::DynamicString, Statsig};

pub type FullUserKey = (
    u64,      // app_version
    u64,      // country
    u64,      // email
    u64,      // ip
    u64,      // locale
    u64,      // user_agent
    u64,      // user_id
    Vec<u64>, // custom_ids
    Vec<u64>, // custom
    Vec<u64>, // private_attributes
    Vec<u64>, // statsig_env
);

#[derive(Clone)]
pub struct StatsigUserInternal<'statsig, 'user> {
    pub user_ref: &'user StatsigUser,
    pub statsig_instance: Option<&'statsig Statsig>,
}

impl<'statsig, 'user> StatsigUserInternal<'statsig, 'user> {
    pub fn new(user: &'user StatsigUser, statsig_instance: Option<&'statsig Statsig>) -> Self {
        Self {
            user_ref: user,
            statsig_instance,
        }
    }

    pub fn get_unit_id(&self, id_type: &DynamicString) -> Option<&DynamicValue> {
        self.user_ref.get_unit_id(id_type)
    }

    pub fn get_user_value(&self, field: &Option<DynamicString>) -> Option<&DynamicValue> {
        let field = field.as_ref()?;

        let lowered_field = &field.lowercased_value;

        let str_value = match lowered_field as &str {
            "userid" => &self.user_ref.data.user_id,
            "email" => &self.user_ref.data.email,
            "ip" => &self.user_ref.data.ip,
            "country" => &self.user_ref.data.country,
            "locale" => &self.user_ref.data.locale,
            "appversion" => &self.user_ref.data.app_version,
            "useragent" => &self.user_ref.data.user_agent,
            _ => &None,
        };

        if let Some(value) = str_value {
            if let Some(str_val) = &value.string_value {
                if !str_val.value.is_empty() {
                    return Some(value);
                }
            }
        }

        if let Some(custom) = &self.user_ref.data.custom {
            if let Some(found) = custom.get(field.value.as_str()) {
                return Some(found);
            }
            if let Some(lowered_found) = custom.get(lowered_field.as_str()) {
                return Some(lowered_found);
            }
        }

        if let Some(instance) = &self.statsig_instance {
            if let Some(val) = instance.get_value_from_global_custom_fields(&field.value) {
                return Some(val);
            }

            if let Some(val) = instance.get_value_from_global_custom_fields(&field.lowercased_value)
            {
                return Some(val);
            }
        }

        if let Some(private_attributes) = &self.user_ref.data.private_attributes {
            if let Some(found) = private_attributes.get(field.value.as_str()) {
                return Some(found);
            }
            if let Some(lowered_found) = private_attributes.get(lowered_field.as_str()) {
                return Some(lowered_found);
            }
        }

        let str_value_alt = match lowered_field as &str {
            "user_id" => &self.user_ref.data.user_id,
            "app_version" => &self.user_ref.data.app_version,
            "user_agent" => &self.user_ref.data.user_agent,
            _ => &None,
        };

        if str_value_alt.is_some() {
            return str_value_alt.as_ref();
        }

        None
    }

    pub fn get_value_from_environment(
        &self,
        field: &Option<DynamicString>,
    ) -> Option<DynamicValue> {
        let field = field.as_ref()?;

        if let Some(result) = self.statsig_instance?.get_from_statsig_env(&field.value) {
            return Some(result);
        }

        self.statsig_instance?
            .get_from_statsig_env(&field.lowercased_value)
    }

    pub fn to_loggable(&self) -> StatsigUserLoggable {
        let (environment, global_custom) = match self.statsig_instance {
            Some(statsig) => (
                statsig.use_statsig_env(|e| e.cloned()),
                statsig.use_global_custom_fields(|gc| gc.cloned()),
            ),
            None => (None, None),
        };

        StatsigUserLoggable::new(&self.user_ref.data, environment, global_custom)
    }

    pub fn get_hashed_private_attributes(&self) -> Option<String> {
        let private_attributes = match &self.user_ref.data.private_attributes {
            Some(attrs) => attrs,
            None => return None,
        };

        if private_attributes.is_empty() {
            return None;
        }

        let mut val: i64 = 0;
        for (key, value) in private_attributes {
            let hash_key = match value.string_value {
                Some(ref s) => key.to_owned() + ":" + &s.value,
                None => key.to_owned() + ":",
            };
            val += djb2_number(&hash_key);
            val &= 0xFFFF_FFFF;
        }
        Some(val.to_string())
    }
}
