# Task 1 uncommitted review package

No commits made. Service base 62092ac5b72f34e26844e2a392d7feb391936ee0; database base e4f6d4d4c1a8c7857a1e65c93eff1439ff070c51. Only Task1-owned paths included; unrelated dirty work excluded.

## D:/work/heliorventures/hrms-svc

warning: in the working copy of 'crates/kabipay-attendance/Cargo.toml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/lib.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/services/mod.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/Cargo.toml b/crates/kabipay-attendance/Cargo.toml
index 09da94c..1f6d9cc 100644
--- a/crates/kabipay-attendance/Cargo.toml
+++ b/crates/kabipay-attendance/Cargo.toml
@@ -26,10 +26,13 @@ base64.workspace = true
 uuid.workspace = true
 chrono.workspace = true
 chrono-tz.workspace = true
 tracing.workspace = true
 tracing-subscriber.workspace = true
 thiserror.workspace = true
 anyhow.workspace = true
 dotenvy.workspace = true
 rust_decimal.workspace = true
 ipnet.workspace = true
+
+[dev-dependencies]
+sea-orm = { workspace = true, features = ["proxy"] }
diff --git a/crates/kabipay-attendance/src/lib.rs b/crates/kabipay-attendance/src/lib.rs
index ace1fad..0947fa2 100644
--- a/crates/kabipay-attendance/src/lib.rs
+++ b/crates/kabipay-attendance/src/lib.rs
@@ -1,16 +1,17 @@
 //! Attendance domain library used by the subgraph binary and integration tests.
 
 mod resolvers;
 mod services;
 
 pub use resolvers::{MutationRoot, QueryRoot};
+pub use services::attendance_day;
 
 /// Public attendance-management types supported for integration consumers.
 ///
 /// Keep this facade intentionally narrow. Task 4B may add only the
 /// regularization-specific types or functions its integration tests require.
 pub mod attendance_management {
     pub use crate::services::attendance_management_service::AttendancePage;
     pub use crate::services::attendance_regularization_service::{
         create_managed_attendance_segment_in_transaction, ManagedCreateCommand, SegmentInstants,
         SegmentTimes,
diff --git a/crates/kabipay-attendance/src/services/mod.rs b/crates/kabipay-attendance/src/services/mod.rs
index e6a9c2b..71a5c68 100644
--- a/crates/kabipay-attendance/src/services/mod.rs
+++ b/crates/kabipay-attendance/src/services/mod.rs
@@ -4,10 +4,11 @@ pub mod attendance_management_service;
 pub mod attendance_report_service;
 pub mod attendance_summary_service;
 pub mod attendance_duration;
 pub mod hrms_master_service;
 pub mod punch_policy;
 pub mod timesheet_batch_service;
 pub mod timesheet_dates;
 pub mod timesheet_notification_service;
 pub mod timesheet_policy;
 pub mod timesheet_project_assignment_service;
+pub mod attendance_day;
diff --git a/crates/kabipay-db-entities/src/tenant/mod.rs b/crates/kabipay-db-entities/src/tenant/mod.rs
index 4d9bb44..d77863d 100644
--- a/crates/kabipay-db-entities/src/tenant/mod.rs
+++ b/crates/kabipay-db-entities/src/tenant/mod.rs
@@ -41,10 +41,11 @@ pub mod d0059_file_upload_stage;
 pub mod d0060_private_file_cleanup;
 pub mod d0063_attendance_management;
 pub mod d0074_automated_employee_notifications;
 pub mod d0075_performance_appraisal_lifecycle;
 pub mod d0076_anonymous_surveys;
 pub mod d0077_unpaid_leave_payroll;
 pub mod d0078_comp_off;
 pub mod d0079_announcement_video;
 pub mod d0080_prejoining;
 pub mod d0084_survey_targeting_corrections;
+pub mod d0087_attendance_day_boundary;


warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day/calendar.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day/calendar.rs b/crates/kabipay-attendance/src/services/attendance_day/calendar.rs
new file mode 100644
index 0000000..e8e4f55
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/calendar.rs
@@ -0,0 +1,129 @@
+use chrono::{DateTime, Duration, LocalResult, NaiveDate, TimeZone, Utc};
+use chrono_tz::Tz;
+use kabipay_common::{KabiPayError, KabiPayResult};
+use uuid::Uuid;
+
+#[derive(Clone, Debug, PartialEq, Eq)]
+pub struct AttendanceDayWindow {
+    pub work_date: NaiveDate,
+    pub starts_at: DateTime<Utc>,
+    pub ends_at: DateTime<Utc>,
+    pub timezone: String,
+    pub boundary_minutes: i32,
+    pub policy_version_id: Uuid,
+}
+
+#[derive(Clone, Debug, PartialEq, Eq)]
+pub struct PolicyVersion {
+    pub id: Uuid,
+    pub effective_work_date: NaiveDate,
+    pub boundary_minutes: i32,
+    pub timezone: String,
+}
+
+pub fn parse_boundary_minutes(value: &str) -> KabiPayResult<i32> {
+    let bytes = value.as_bytes();
+    if bytes.len() != 5
+        || bytes[2] != b':'
+        || ![bytes[0], bytes[1], bytes[3], bytes[4]].iter().all(u8::is_ascii_digit)
+    {
+        return Err(invalid("attendance start time must use HH:MM"));
+    }
+    let hours = i32::from(bytes[0] - b'0') * 10 + i32::from(bytes[1] - b'0');
+    let minutes = i32::from(bytes[3] - b'0') * 10 + i32::from(bytes[4] - b'0');
+    if hours > 23 || minutes > 59 {
+        return Err(invalid("attendance start time is outside the day"));
+    }
+    Ok(hours * 60 + minutes)
+}
+
+pub(super) fn invalid(message: &str) -> KabiPayError {
+    KabiPayError::Validation(message.into())
+}
+
+pub(super) fn validate_minutes(minutes: i32) -> KabiPayResult<()> {
+    if !(0..1440).contains(&minutes) {
+        return Err(invalid("attendance boundary minutes must be between 0 and 1439"));
+    }
+    Ok(())
+}
+
+fn selected(versions: &[PolicyVersion], date: NaiveDate) -> KabiPayResult<&PolicyVersion> {
+    versions.iter()
+        .filter(|v| v.effective_work_date <= date)
+        .max_by_key(|v| v.effective_work_date)
+        .ok_or_else(|| invalid("no attendance policy covers this work date"))
+}
+
+fn boundary(date: NaiveDate, policy: &PolicyVersion) -> KabiPayResult<DateTime<Utc>> {
+    validate_minutes(policy.boundary_minutes)?;
+    let timezone = policy.timezone.parse::<Tz>()
+        .map_err(|_| invalid("invalid attendance timezone"))?;
+    let minutes = u32::try_from(policy.boundary_minutes)
+        .map_err(|_| invalid("invalid attendance boundary"))?;
+    let mut local = date.and_hms_opt(minutes / 60, minutes % 60, 0)
+        .ok_or_else(|| invalid("attendance boundary overflows"))?;
+    // IANA transitions include historical second offsets and skipped whole dates.
+    // Advance by seconds so the result is the first valid instant, not merely the next valid minute.
+    for _ in 0..=172_800 {
+        match timezone.from_local_datetime(&local) {
+            LocalResult::Single(value) => return Ok(value.with_timezone(&Utc)),
+            LocalResult::Ambiguous(a, b) => return Ok(a.min(b).with_timezone(&Utc)),
+            LocalResult::None => {
+                local = local.checked_add_signed(Duration::seconds(1))
+                    .ok_or_else(|| invalid("attendance boundary overflows"))?;
+            }
+        }
+    }
+    Err(invalid("attendance timezone gap exceeds supported two-day search"))
+}
+
+/// Resolve a day with its predecessor's endpoint as the inherited start.
+pub fn resolve_window(versions: &[PolicyVersion], date: NaiveDate) -> KabiPayResult<AttendanceDayWindow> {
+    let next_date = date.succ_opt()
+        .ok_or_else(|| invalid("attendance date overflows"))?;
+    let previous_date = date.pred_opt()
+        .ok_or_else(|| invalid("attendance date overflows"))?;
+    let current = selected(versions, date)?;
+    let previous = if current.effective_work_date == date {
+        selected(versions, previous_date).unwrap_or(current)
+    } else {
+        current
+    };
+    let starts_at = boundary(date, previous)?;
+    let ends_at = boundary(next_date, current)?;
+    if starts_at >= ends_at {
+        return Err(invalid("attendance window must have increasing endpoints"));
+    }
+    Ok(AttendanceDayWindow {
+        work_date: date,
+        starts_at,
+        ends_at,
+        timezone: current.timezone.clone(),
+        boundary_minutes: current.boundary_minutes,
+        policy_version_id: current.id,
+    })
+}
+
+/// UTC-neighbor candidates also cover transition days across timezone changes.
+pub fn resolve_current_window(
+    versions: &[PolicyVersion],
+    now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayWindow> {
+    let mut found = None;
+    for offset in -3..=3 {
+        let Some(date) = now.date_naive().checked_add_signed(Duration::days(offset)) else {
+            continue;
+        };
+        // A skipped local date can have no window. Nearby valid days remain candidates.
+        if let Ok(window) = resolve_window(versions, date) {
+            if window.starts_at <= now && now < window.ends_at {
+                if found.is_some() {
+                    return Err(invalid("attendance policy produces overlapping windows"));
+                }
+                found = Some(window);
+            }
+        }
+    }
+    found.ok_or_else(|| invalid("no attendance window contains the current instant"))
+}


warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day/mod.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day/mod.rs b/crates/kabipay-attendance/src/services/attendance_day/mod.rs
new file mode 100644
index 0000000..3bbfab7
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/mod.rs
@@ -0,0 +1,7 @@
+//! Effective-dated attendance policy and immutable UTC windows.
+mod calendar;
+pub use calendar::*;
+mod repository;
+pub use repository::*;
+#[cfg(test)]
+mod tests;


warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day/repository.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day/repository.rs b/crates/kabipay-attendance/src/services/attendance_day/repository.rs
new file mode 100644
index 0000000..0513298
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/repository.rs
@@ -0,0 +1,283 @@
+//! Transaction-owned policy activation, scheduling and window freezing.
+use super::{calendar::{invalid, validate_minutes}, *};
+use chrono::{DateTime, NaiveDate, Utc};
+use kabipay_common::{context::{ClientClaims, ScopeType, PERM_ATTENDANCE_PUNCH_POLICY}, tenant_business_clock::TenantBusinessClock, KabiPayError, KabiPayResult};
+use sea_orm::{ConnectionTrait, DatabaseTransaction, DbBackend, QueryResult, Statement, Value};
+use uuid::Uuid;
+
+#[derive(Clone, Debug)]
+pub struct AttendanceDayPolicy {
+    pub revision: i64,
+    pub initialized: bool,
+    pub legacy_activation_pending: bool,
+    pub legacy_activation_date: Option<NaiveDate>,
+    pub versions: Vec<PolicyVersion>,
+}
+#[derive(Clone, Debug)]
+pub struct SchedulePolicyCommand {
+    pub expected_revision: i64,
+    pub effective_work_date: NaiveDate,
+    pub boundary_minutes: i32,
+}
+fn sql(query: &str, values: Vec<Value>) -> Statement {
+    Statement::from_sql_and_values(DbBackend::Postgres, query, values)
+}
+
+fn frozen_row(row: QueryResult) -> KabiPayResult<AttendanceDayWindow> {
+    Ok(AttendanceDayWindow {
+        work_date: row.try_get("", "work_date")?,
+        starts_at: row.try_get("", "starts_at")?,
+        ends_at: row.try_get("", "ends_at")?,
+        timezone: row.try_get("", "timezone")?,
+        boundary_minutes: row.try_get("", "boundary_minutes")?,
+        policy_version_id: row.try_get("", "policy_version_id")?,
+    })
+}
+
+async fn frozen_for_date<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, work_date: NaiveDate,
+) -> KabiPayResult<Option<AttendanceDayWindow>> {
+    db.query_one(sql(
+        "SELECT work_date, starts_at, ends_at, timezone, boundary_minutes, policy_version_id FROM attendance_day_window WHERE tenant_id = $1 AND work_date = $2",
+        vec![tenant_id.into(), work_date.into()],
+    )).await?.map(frozen_row).transpose()
+}
+
+/// Read-only snapshot; a missing profile never creates a moving activation anchor.
+pub async fn policy<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, clock: TenantBusinessClock, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayPolicy> {
+    // One statement observes revision and live versions from one MVCC snapshot.
+    // LEFT JOIN makes a corrupt profile without versions fail closed.
+    let rows = db.query_all(sql(
+        "SELECT p.revision, p.legacy_activation_date, v.id, v.effective_work_date, v.boundary_minutes, v.timezone FROM attendance_day_profile p LEFT JOIN attendance_day_policy_version v ON v.tenant_id = p.tenant_id AND v.superseded_at IS NULL WHERE p.tenant_id = $1 ORDER BY v.effective_work_date",
+        vec![tenant_id.into()],
+    )).await?;
+    if let Some(first) = rows.first() {
+        let revision = first.try_get("", "revision")?;
+        let legacy_activation_date: Option<NaiveDate> = first.try_get("", "legacy_activation_date")?;
+        let versions = rows.iter().map(|row| Ok(PolicyVersion {
+            id: row.try_get("", "id")?,
+            effective_work_date: row.try_get("", "effective_work_date")?,
+            boundary_minutes: row.try_get("", "boundary_minutes")?,
+            timezone: row.try_get("", "timezone")?,
+        })).collect::<KabiPayResult<Vec<_>>>()?;
+        let active = resolve_current_window(&versions, now)?;
+        let legacy_activation_pending = legacy_activation_date.is_some()
+            && versions.first().is_some_and(|v| v.id == active.policy_version_id);
+        return Ok(AttendanceDayPolicy {
+            revision, initialized: true, legacy_activation_pending,
+            legacy_activation_date, versions,
+        });
+    }
+    // Deleted historical rows still establish legacy interpretation.
+    let has_attendance: bool = db.query_one(sql(
+        "SELECT EXISTS (SELECT 1 FROM attendance WHERE tenant_id = $1) AS has_attendance",
+        vec![tenant_id.into()],
+    )).await?.ok_or_else(|| invalid("attendance existence query returned no result"))?
+        .try_get("", "has_attendance")?;
+    Ok(AttendanceDayPolicy {
+        revision: 0, initialized: false,
+        legacy_activation_pending: has_attendance, legacy_activation_date: None,
+        versions: vec![PolicyVersion {
+            id: Uuid::nil(),
+            effective_work_date: NaiveDate::from_ymd_opt(1, 1, 1)
+                .ok_or_else(|| invalid("attendance baseline date is invalid"))?,
+            boundary_minutes: if has_attendance { 0 } else { 300 },
+            timezone: clock.timezone_name().into(),
+        }],
+    })
+}
+
+pub async fn window_for_date<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, clock: TenantBusinessClock,
+    work_date: NaiveDate, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayWindow> {
+    if let Some(window) = frozen_for_date(db, tenant_id, work_date).await? {
+        return Ok(window);
+    }
+    resolve_window(&policy(db, tenant_id, clock, now).await?.versions, work_date)
+}
+
+pub async fn current_window<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, clock: TenantBusinessClock, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayWindow> {
+    if let Some(row) = db.query_one(sql(
+        "SELECT work_date, starts_at, ends_at, timezone, boundary_minutes, policy_version_id FROM attendance_day_window WHERE tenant_id = $1 AND starts_at <= $2 AND ends_at > $2 ORDER BY starts_at DESC LIMIT 1",
+        vec![tenant_id.into(), now.into()],
+    )).await? {
+        return frozen_row(row);
+    }
+    resolve_current_window(&policy(db, tenant_id, clock, now).await?.versions, now)
+}
+
+/// Acquire before employee/day locks, then sample the caller's clock after all locks.
+pub async fn lock_policy(db: &DatabaseTransaction, tenant_id: Uuid) -> KabiPayResult<()> {
+    db.execute(sql(
+        "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
+        vec![format!("attendance-day-policy:{tenant_id}").into()],
+    )).await?;
+    Ok(())
+}
+
+async fn insert_version(
+    db: &DatabaseTransaction, tenant_id: Uuid, version: &PolicyVersion, now: DateTime<Utc>,
+) -> KabiPayResult<()> {
+    db.execute(sql(
+        "INSERT INTO attendance_day_policy_version (id, tenant_id, effective_work_date, boundary_minutes, timezone, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
+        vec![version.id.into(), tenant_id.into(), version.effective_work_date.into(),
+            version.boundary_minutes.into(), version.timezone.clone().into(), now.into()],
+    )).await?;
+    Ok(())
+}
+
+async fn initialize(
+    db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
+    mut state: AttendanceDayPolicy, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayPolicy> {
+    if state.initialized { return Ok(state); }
+    if state.legacy_activation_pending {
+        let activation = clock.business_date(now).succ_opt()
+            .ok_or_else(|| invalid("attendance activation date overflows"))?;
+        state.legacy_activation_date = Some(activation);
+        state.versions.push(PolicyVersion {
+            id: Uuid::new_v4(), effective_work_date: activation,
+            boundary_minutes: 300, timezone: clock.timezone_name().into(),
+        });
+    }
+    state.versions.first_mut()
+        .ok_or_else(|| invalid("attendance baseline policy is missing"))?.id = Uuid::new_v4();
+    state.revision = 1;
+    state.initialized = true;
+    db.execute(sql(
+        "INSERT INTO attendance_day_profile (tenant_id, revision, legacy_activation_date, initialized_at) VALUES ($1, 1, $2, $3)",
+        vec![tenant_id.into(), state.legacy_activation_date.into(), now.into()],
+    )).await?;
+    for version in &state.versions { insert_version(db, tenant_id, version, now).await?; }
+    Ok(state)
+}
+
+/// Freeze within the caller's transaction; on error the caller must roll back.
+pub async fn ensure_window(
+    db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
+    work_date: NaiveDate, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayWindow> {
+    lock_policy(db, tenant_id).await?;
+    if let Some(window) = frozen_for_date(db, tenant_id, work_date).await? {
+        return Ok(window);
+    }
+    let state = policy(db, tenant_id, clock, now).await?;
+    let state = initialize(db, tenant_id, clock, state, now).await?;
+    let window = resolve_window(&state.versions, work_date)?;
+    let previous = work_date.pred_opt().ok_or_else(|| invalid("attendance date overflows"))?;
+    let next = work_date.succ_opt().ok_or_else(|| invalid("attendance date overflows"))?;
+    let neighbors = db.query_all(sql(
+        "SELECT work_date, starts_at, ends_at FROM attendance_day_window WHERE tenant_id = $1 AND work_date IN ($2, $3)",
+        vec![tenant_id.into(), previous.into(), next.into()],
+    )).await?;
+    for row in neighbors {
+        let date: NaiveDate = row.try_get("", "work_date")?;
+        let starts_at: DateTime<Utc> = row.try_get("", "starts_at")?;
+        let ends_at: DateTime<Utc> = row.try_get("", "ends_at")?;
+        if (date == previous && ends_at != window.starts_at)
+            || (date == next && starts_at != window.ends_at)
+        {
+            return Err(KabiPayError::Conflict("attendance window disagrees with frozen neighbor".into()));
+        }
+    }
+    db.execute(sql(
+        "INSERT INTO attendance_day_window (id, tenant_id, work_date, starts_at, ends_at, timezone, boundary_minutes, policy_version_id, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
+        vec![Uuid::new_v4().into(), tenant_id.into(), work_date.into(), window.starts_at.into(),
+            window.ends_at.into(), window.timezone.clone().into(), window.boundary_minutes.into(),
+            window.policy_version_id.into(), now.into()],
+    )).await?;
+    Ok(window)
+}
+
+fn audit_state(state: &AttendanceDayPolicy) -> serde_json::Value {
+    serde_json::json!({
+        "revision": state.revision, "initialized": state.initialized,
+        "legacy_activation_date": state.legacy_activation_date,
+        "versions": state.versions.iter().map(|v| serde_json::json!({
+            "id": v.id, "effective_work_date": v.effective_work_date,
+            "boundary_minutes": v.boundary_minutes, "timezone": v.timezone,
+        })).collect::<Vec<_>>()
+    })
+}
+
+/// Schedule one future replacement, preserving superseded rows and auditing the actor.
+/// Caller owns commit/rollback and must pass a timestamp sampled after locks.
+pub async fn schedule_policy(
+    db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
+    claims: &ClientClaims, command: SchedulePolicyCommand, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayPolicy> {
+    if claims.tenant_id != tenant_id
+        || !claims.has_any_permission(&[PERM_ATTENDANCE_PUNCH_POLICY])
+        || claims.explicit_scope_for_permission(PERM_ATTENDANCE_PUNCH_POLICY) != Some(ScopeType::All)
+    {
+        return Err(KabiPayError::Forbidden("attendance day policy requires tenant-wide configuration authority".into()));
+    }
+    validate_minutes(command.boundary_minutes)?;
+    lock_policy(db, tenant_id).await?;
+    let state = policy(db, tenant_id, clock, now).await?;
+    if command.expected_revision != state.revision {
+        return Err(KabiPayError::Conflict("attendance day policy changed; refresh before retrying".into()));
+    }
+    let active = resolve_current_window(&state.versions, now)?;
+    if command.effective_work_date <= active.work_date {
+        return Err(invalid("attendance day policy must take effect after the active work date"));
+    }
+    let before = audit_state(&state);
+    let mut state = initialize(db, tenant_id, clock, state, now).await?;
+    let pending: Vec<_> = state.versions.iter()
+        .filter(|v| v.effective_work_date > active.work_date).cloned().collect();
+    let affected_date = pending.iter().map(|v| v.effective_work_date)
+        .fold(command.effective_work_date, NaiveDate::min);
+    if db.query_one(sql(
+        "SELECT work_date FROM attendance_day_window WHERE tenant_id = $1 AND work_date >= $2 LIMIT 1",
+        vec![tenant_id.into(), affected_date.into()],
+    )).await?.is_some() {
+        return Err(KabiPayError::Conflict("attendance day policy would alter a frozen window".into()));
+    }
+    let version = PolicyVersion {
+        id: Uuid::new_v4(), effective_work_date: command.effective_work_date,
+        boundary_minutes: command.boundary_minutes, timezone: clock.timezone_name().into(),
+    };
+    let mut proposed: Vec<_> = state.versions.iter()
+        .filter(|v| v.effective_work_date <= active.work_date).cloned().collect();
+    proposed.push(version.clone());
+    let transition = resolve_window(&proposed, command.effective_work_date)?;
+    let following = command.effective_work_date.succ_opt()
+        .ok_or_else(|| invalid("attendance effective date overflows"))?;
+    let next = resolve_window(&proposed, following)?;
+    if transition.starts_at <= now || transition.ends_at != next.starts_at {
+        return Err(invalid("attendance policy transition must be future and continuous"));
+    }
+    let revision = state.revision.checked_add(1)
+        .ok_or_else(|| invalid("attendance policy revision overflows"))?;
+    let update = db.execute(sql(
+        "UPDATE attendance_day_profile SET revision = $2 WHERE tenant_id = $1 AND revision = $3",
+        vec![tenant_id.into(), revision.into(), state.revision.into()],
+    )).await?;
+    if update.rows_affected() != 1 {
+        return Err(KabiPayError::Conflict("attendance day policy changed; refresh before retrying".into()));
+    }
+    for prior in pending {
+        let update = db.execute(sql(
+            "UPDATE attendance_day_policy_version SET superseded_at = $3 WHERE tenant_id = $1 AND id = $2 AND superseded_at IS NULL",
+            vec![tenant_id.into(), prior.id.into(), now.into()],
+        )).await?;
+        if update.rows_affected() != 1 {
+            return Err(KabiPayError::Conflict("attendance pending policy changed".into()));
+        }
+    }
+    insert_version(db, tenant_id, &version, now).await?;
+    state.versions = proposed;
+    state.revision = revision;
+    db.execute(sql(
+        "INSERT INTO audit_log (id, tenant_id, user_id, entity_type, entity_id, action, before_state, after_state, created_at) VALUES ($1, $2, $3, 'ATTENDANCE_DAY_POLICY', $2, 'SCHEDULE', $4, $5, $6)",
+        vec![Uuid::new_v4().into(), tenant_id.into(), claims.sub.into(), before.into(),
+            audit_state(&state).into(), now.into()],
+    )).await?;
+    Ok(state)
+}


warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day/tests.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day/tests.rs b/crates/kabipay-attendance/src/services/attendance_day/tests.rs
new file mode 100644
index 0000000..a88837a
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/tests.rs
@@ -0,0 +1,80 @@
+use super::*;
+use chrono::{DateTime, NaiveDate, Utc};
+use uuid::Uuid;
+fn date(s: &str) -> NaiveDate { s.parse().unwrap() }
+fn utc(s: &str) -> DateTime<Utc> { s.parse().unwrap() }
+fn version(effective: &str, minutes: i32, timezone: &str) -> PolicyVersion {
+    PolicyVersion { id: Uuid::new_v4(), effective_work_date: date(effective), boundary_minutes: minutes, timezone: timezone.into() }
+}
+#[test]
+fn attendance_day_boundary_validation() {
+    assert_eq!(parse_boundary_minutes("05:00").unwrap(), 300);
+    assert_eq!(parse_boundary_minutes("23:59").unwrap(), 1439);
+    for bad in ["24:00", "5:00", "05:60", "-1:00", "05:00:00", " 05:00", "aa:bb"] { assert!(parse_boundary_minutes(bad).is_err()); }
+}
+#[test]
+fn attendance_day_literal_kolkata_boundary() {
+    let policies = [version("0001-01-01", 300, "Asia/Kolkata")];
+    let w = resolve_window(&policies, date("2026-09-11")).unwrap();
+    assert_eq!(w.starts_at, utc("2026-09-10T23:30:00Z"));
+    assert_eq!(w.ends_at, utc("2026-09-11T23:30:00Z"));
+    for (instant, expected) in [("2026-09-11T23:29:59Z", "2026-09-11"), ("2026-09-11T23:30:00Z", "2026-09-12"), ("2026-12-31T23:30:00Z", "2027-01-01")] {
+        let now = utc(instant);
+        let current = resolve_current_window(&policies, now).unwrap();
+        assert_eq!(current.work_date, date(expected));
+        assert!(current.starts_at <= now && now < current.ends_at);
+    }
+}
+#[test]
+fn attendance_day_transition_inherits_start_and_preserves_active_day() {
+    for (minutes, end, hours) in [(360, "2026-09-13T00:30:00Z", 25), (240, "2026-09-12T22:30:00Z", 23)] {
+        let baseline = version("0001-01-01", 300, "Asia/Kolkata");
+        let active = resolve_window(&[baseline.clone()], date("2026-09-11")).unwrap();
+        let policies = [baseline, version("2026-09-12", minutes, "Asia/Kolkata")];
+        assert_eq!(resolve_window(&policies, date("2026-09-11")).unwrap(), active);
+        let transition = resolve_window(&policies, date("2026-09-12")).unwrap();
+        assert_eq!(transition.starts_at, utc("2026-09-11T23:30:00Z"));
+        assert_eq!(transition.ends_at, utc(end));
+        assert_eq!((transition.ends_at - transition.starts_at).num_hours(), hours);
+        assert_eq!(active.ends_at, transition.starts_at);
+        assert_eq!(transition.ends_at, resolve_window(&policies, date("2026-09-13")).unwrap().starts_at);
+    }
+}
+#[test]
+fn attendance_day_dst_resolves_gap_and_overlap_deterministically() {
+    for (minutes, day, start, end) in [
+        (150, "2026-03-08", "2026-03-08T07:00:00Z", "2026-03-09T06:30:00Z"),
+        (90, "2026-11-01", "2026-11-01T05:30:00Z", "2026-11-02T06:30:00Z")
+    ] {
+        let policies = [version("0001-01-01", minutes, "America/New_York")];
+        let w = resolve_window(&policies, date(day)).unwrap();
+        assert_eq!(w.starts_at, utc(start)); assert_eq!(w.ends_at, utc(end));
+    }
+}
+#[test]
+fn attendance_day_rejects_overflow_invalid_policy_and_nonincreasing_skipped_date() {
+    assert!(resolve_window(&[], date("2026-09-11")).is_err());
+    assert!(resolve_window(&[version("0001-01-01", 1440, "UTC")], date("2026-09-11")).is_err());
+    assert!(resolve_window(&[version("0001-01-01", 0, "UTC")], NaiveDate::MAX).is_err());
+    assert!(resolve_window(&[version("0001-01-01", 0, "Pacific/Apia")], date("2011-12-30")).is_err());
+}
+#[test]
+fn attendance_day_midnight_custom_and_month_boundary_literals() {
+    for (minutes, day, start, end) in [
+        (0, "2026-10-01", "2026-09-30T18:30:00Z", "2026-10-01T18:30:00Z"),
+        (345, "2026-10-01", "2026-10-01T00:15:00Z", "2026-10-02T00:15:00Z"),
+        (1439, "2026-12-31", "2026-12-31T18:29:00Z", "2027-01-01T18:29:00Z")
+    ] {
+        let w = resolve_window(&[version("0001-01-01", minutes, "Asia/Kolkata")], date(day)).unwrap();
+        assert_eq!(w.starts_at, utc(start)); assert_eq!(w.ends_at, utc(end));
+    }
+}
+#[test]
+fn attendance_day_timezone_transition_keeps_predecessor_endpoint() {
+    let versions = [version("0001-01-01", 300, "Asia/Kolkata"), version("2026-09-12", 300, "America/New_York")];
+    let w = resolve_window(&versions, date("2026-09-12")).unwrap();
+    assert_eq!(w.starts_at, utc("2026-09-11T23:30:00Z"));
+    assert_eq!(w.ends_at, utc("2026-09-13T09:00:00Z"));
+    let current = resolve_current_window(&versions, utc("2026-09-12T00:00:00Z")).unwrap();
+    assert_eq!(current.work_date, date("2026-09-12"));
+}


warning: in the working copy of 'crates/kabipay-attendance/tests/attendance_day_policy.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/tests/attendance_day_policy.rs b/crates/kabipay-attendance/tests/attendance_day_policy.rs
new file mode 100644
index 0000000..e3e3167
--- /dev/null
+++ b/crates/kabipay-attendance/tests/attendance_day_policy.rs
@@ -0,0 +1,226 @@
+use kabipay_attendance::attendance_day::*;
+use kabipay_common::tenant_business_clock::TenantBusinessClock;
+use chrono::{DateTime, NaiveDate, Utc};
+use sea_orm::{entity::prelude::async_trait, Database, DbBackend, DbErr, ProxyDatabaseTrait, ProxyExecResult, ProxyRow, Statement, TransactionTrait};
+use std::{collections::{BTreeMap, VecDeque}, sync::{Arc, Mutex}};
+use uuid::Uuid;
+fn date(s: &str) -> NaiveDate { s.parse().unwrap() }
+fn utc(s: &str) -> DateTime<Utc> { s.parse().unwrap() }
+fn clock() -> TenantBusinessClock { TenantBusinessClock::from_name("Asia/Kolkata").unwrap() }
+#[derive(Debug)]
+struct Fixture { rows: Mutex<VecDeque<Vec<ProxyRow>>>, statements: Arc<Mutex<Vec<Statement>>>, fail_audit: bool }
+#[async_trait::async_trait]
+impl ProxyDatabaseTrait for Fixture {
+    async fn query(&self, s: Statement) -> Result<Vec<ProxyRow>, DbErr> {
+        self.statements.lock().unwrap().push(s);
+        Ok(self.rows.lock().unwrap().pop_front().expect("unexpected SQL query"))
+    }
+    async fn execute(&self, s: Statement) -> Result<ProxyExecResult, DbErr> {
+        let fail = self.fail_audit && s.sql.starts_with("INSERT INTO audit_log");
+        self.statements.lock().unwrap().push(s);
+        if fail { return Err(DbErr::Custom("audit unavailable".into())); }
+        Ok(ProxyExecResult { last_insert_id: 0, rows_affected: 1 })
+    }
+}
+async fn db(rows: Vec<Vec<ProxyRow>>) -> (sea_orm::DatabaseConnection, Arc<Mutex<Vec<Statement>>>) {
+    db_with_audit_failure(rows, false).await
+}
+async fn db_with_audit_failure(rows: Vec<Vec<ProxyRow>>, fail_audit: bool) -> (sea_orm::DatabaseConnection, Arc<Mutex<Vec<Statement>>>) {
+    let statements = Arc::new(Mutex::new(Vec::new()));
+    let db = Database::connect_proxy(DbBackend::Postgres, Arc::new(Box::new(Fixture { rows: Mutex::new(rows.into()), statements: statements.clone(), fail_audit }))).await.unwrap();
+    (db, statements)
+}
+fn exists(value: bool) -> Vec<ProxyRow> { vec![ProxyRow::new(BTreeMap::from([("has_attendance".into(), value.into())]))] }
+#[tokio::test]
+async fn attendance_day_missing_profile_reads_are_write_free_and_legacy_aware() {
+    for (has_attendance, boundary, expected_start) in [(true, 0, "2026-09-10T18:30:00Z"), (false, 300, "2026-09-10T23:30:00Z")] {
+        let tenant = Uuid::new_v4();
+        let (db, statements) = db(vec![vec![], exists(has_attendance)]).await;
+        let policy = policy(&db, tenant, clock(), utc("2026-09-11T10:00:00Z")).await.unwrap();
+        assert!(!policy.initialized);
+        assert_eq!(policy.legacy_activation_pending, has_attendance);
+        assert_eq!(policy.revision, 0);
+        let w = resolve_window(&policy.versions, date("2026-09-11")).unwrap();
+        assert_eq!(w.boundary_minutes, boundary);
+        assert_eq!(w.starts_at, utc(expected_start));
+        for statement in statements.lock().unwrap().iter() {
+            assert!(statement.sql.trim_start().starts_with("SELECT"));
+            assert!(statement.to_string().contains(&tenant.to_string()), "tenant must qualify every read");
+        }
+    }
+}
+fn frozen(tenant: Uuid) -> Vec<ProxyRow> {
+    vec![ProxyRow::new(BTreeMap::from([
+        ("tenant_id".into(), tenant.into()),
+        ("work_date".into(), date("2026-09-11").into()),
+        ("starts_at".into(), utc("2026-09-10T23:30:00Z").into()),
+        ("ends_at".into(), utc("2026-09-11T23:30:00Z").into()),
+        ("timezone".into(), "Asia/Kolkata".into()),
+        ("boundary_minutes".into(), 300.into()),
+        ("policy_version_id".into(), Uuid::new_v4().into()),
+    ]))]
+}
+#[tokio::test]
+async fn attendance_day_frozen_history_ignores_later_timezone() {
+    let tenant = Uuid::new_v4();
+    let (db, statements) = db(vec![frozen(tenant)]).await;
+    let w = window_for_date(&db, tenant, TenantBusinessClock::from_name("America/New_York").unwrap(), date("2026-09-11"), utc("2026-10-01T10:00:00Z")).await.unwrap();
+    assert_eq!(w.starts_at, utc("2026-09-10T23:30:00Z"));
+    assert_eq!(w.timezone, "Asia/Kolkata");
+    assert_eq!(statements.lock().unwrap().len(), 1);
+}
+#[tokio::test]
+async fn attendance_day_freeze_existing_window_is_idempotent_and_locks_tenant() {
+    let tenant = Uuid::new_v4();
+    let (db, statements) = db(vec![frozen(tenant)]).await;
+    let tx = db.begin().await.unwrap();
+    let w = ensure_window(&tx, tenant, clock(), date("2026-09-11"), utc("2026-09-11T10:00:00Z")).await.unwrap();
+    assert_eq!(w.ends_at, utc("2026-09-11T23:30:00Z"));
+    let sql = statements.lock().unwrap();
+    assert!(sql[0].sql.contains("pg_advisory_xact_lock"));
+    assert!(sql.iter().all(|s| !s.sql.starts_with("INSERT")));
+    assert!(sql.iter().all(|s| s.to_string().contains(&tenant.to_string())));
+}
+
+fn claims(tenant: Uuid, scope: &str) -> kabipay_common::context::ClientClaims {
+    serde_json::from_value(serde_json::json!({"sub":Uuid::new_v4(),"iss":"kabipay-client","exp":0,"iat":0,"tenant_id":tenant,"permissions":["attendance:punch_policy"],"permission_scopes":{"attendance:punch_policy":scope}})).unwrap()
+}
+fn command(revision: i64, effective: &str) -> SchedulePolicyCommand {
+    SchedulePolicyCommand { expected_revision: revision, effective_work_date: date(effective), boundary_minutes: 360 }
+}
+fn policy_rows(versions: &[(&str, i32)], activation: Option<NaiveDate>) -> Vec<ProxyRow> {
+    versions.iter().map(|(effective, minutes)| ProxyRow::new(BTreeMap::from([
+        ("revision".into(), 7_i64.into()),
+        ("legacy_activation_date".into(), activation.into()),
+        ("id".into(), Uuid::new_v4().into()),
+        ("effective_work_date".into(), date(effective).into()),
+        ("boundary_minutes".into(), (*minutes).into()),
+        ("timezone".into(), "Asia/Kolkata".into()),
+    ]))).collect()
+}
+#[tokio::test]
+async fn attendance_day_policy_rejects_unauthorized_and_foreign_tenants_before_sql() {
+    let tenant = Uuid::new_v4();
+    for claimant in [claims(tenant, "TEAM"), claims(Uuid::new_v4(), "ALL")] {
+        let (db, statements) = db(vec![]).await;
+        let tx = db.begin().await.unwrap();
+        let err = schedule_policy(&tx, tenant, clock(), &claimant, command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap_err();
+        assert!(matches!(err, kabipay_common::KabiPayError::Forbidden(_)));
+        assert!(statements.lock().unwrap().is_empty());
+    }
+}
+#[tokio::test]
+async fn attendance_day_policy_stale_revision_and_active_day_rejected_without_writes() {
+    for cmd in [command(6, "2026-09-12"), command(7, "2026-09-11"), command(7, "2026-09-10")] {
+        let tenant = Uuid::new_v4();
+        let (db, statements) = db(vec![policy_rows(&[("0001-01-01", 300)], None)]).await;
+        let tx = db.begin().await.unwrap();
+        let err = schedule_policy(&tx, tenant, clock(), &claims(tenant, "ALL"), cmd.clone(), utc("2026-09-11T10:00:00Z")).await.unwrap_err();
+        if cmd.expected_revision == 6 { assert!(matches!(err, kabipay_common::KabiPayError::Conflict(_))); }
+        else { assert!(matches!(err, kabipay_common::KabiPayError::Validation(_))); }
+        assert!(statements.lock().unwrap().iter().all(|s| !s.sql.starts_with("INSERT") && !s.sql.starts_with("UPDATE")));
+    }
+}
+#[tokio::test]
+async fn attendance_day_policy_frozen_future_rejects_replacement() {
+    let tenant = Uuid::new_v4();
+    let (db, statements) = db(vec![policy_rows(&[("0001-01-01", 300), ("2026-09-13", 240)], None), vec![ProxyRow::new(BTreeMap::from([("work_date".into(), date("2026-09-13").into())]))]]).await;
+    let tx = db.begin().await.unwrap();
+    let err = schedule_policy(&tx, tenant, clock(), &claims(tenant, "ALL"), command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap_err();
+    assert!(matches!(err, kabipay_common::KabiPayError::Conflict(_)));
+    assert!(statements.lock().unwrap().iter().all(|s| !s.sql.starts_with("INSERT") && !s.sql.starts_with("UPDATE")));
+}
+#[tokio::test]
+async fn attendance_day_policy_replacement_audits_and_preserves_history() {
+    let tenant = Uuid::new_v4();
+    let claimant = claims(tenant, "ALL");
+    let (db, statements) = db(vec![policy_rows(&[("0001-01-01", 300), ("2026-09-13", 240)], None), vec![]]).await;
+    let tx = db.begin().await.unwrap();
+    let result = schedule_policy(&tx, tenant, clock(), &claimant, command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap();
+    assert_eq!(result.revision, 8);
+    assert_eq!(result.versions.len(), 2);
+    assert_eq!(result.versions[0].boundary_minutes, 300);
+    assert_eq!(result.versions[1].effective_work_date, date("2026-09-12"));
+    assert_eq!(resolve_window(&result.versions, date("2026-09-12")).unwrap().ends_at, utc("2026-09-13T00:30:00Z"));
+    let sql = statements.lock().unwrap();
+    assert!(sql.iter().all(|s| s.to_string().contains(&tenant.to_string())));
+    assert!(!sql.iter().any(|s| s.sql.starts_with("DELETE")));
+    let audit = sql.iter().find(|s| s.sql.starts_with("INSERT INTO audit_log")).expect("same-transaction policy audit");
+    assert!(audit.to_string().contains(&claimant.sub.to_string()));
+    assert!(audit.to_string().contains("before_state") && audit.to_string().contains("after_state"));
+}
+#[tokio::test]
+async fn attendance_day_initialization_preserves_legacy_active_day_and_freezes_explicit_transition() {
+    for (work_date, start, end) in [
+        ("2026-09-11", "2026-09-10T18:30:00Z", "2026-09-11T18:30:00Z"),
+        ("2026-09-12", "2026-09-11T18:30:00Z", "2026-09-12T23:30:00Z")
+    ] {
+        let tenant = Uuid::new_v4();
+        let (db, statements) = db(vec![vec![], vec![], exists(true), vec![]]).await;
+        let tx = db.begin().await.unwrap();
+        let result = ensure_window(&tx, tenant, clock(), date(work_date), utc("2026-09-11T10:00:00Z")).await.unwrap();
+        assert_eq!(result.starts_at, utc(start)); assert_eq!(result.ends_at, utc(end));
+        let sql = statements.lock().unwrap();
+        assert!(sql.iter().all(|s| s.to_string().contains(&tenant.to_string())));
+        let profile = sql.iter().find(|s| s.sql.starts_with("INSERT INTO attendance_day_profile")).unwrap();
+        assert!(profile.to_string().contains("2026-09-12"));
+        assert_eq!(sql.iter().filter(|s| s.sql.starts_with("INSERT INTO attendance_day_policy_version")).count(), 2);
+        assert!(sql.iter().any(|s| s.sql.starts_with("INSERT INTO attendance_day_window")));
+    }
+}
+#[tokio::test]
+async fn attendance_day_initialization_fresh_tenant_uses_five_without_conversion() {
+    let tenant = Uuid::new_v4();
+    let (db, statements) = db(vec![vec![], vec![], exists(false), vec![]]).await;
+    let tx = db.begin().await.unwrap();
+    let result = ensure_window(&tx, tenant, clock(), date("2026-09-11"), utc("2026-09-11T10:00:00Z")).await.unwrap();
+    assert_eq!(result.starts_at, utc("2026-09-10T23:30:00Z"));
+    assert_eq!(result.ends_at, utc("2026-09-11T23:30:00Z"));
+    assert_eq!(statements.lock().unwrap().iter().filter(|s| s.sql.starts_with("INSERT INTO attendance_day_policy_version")).count(), 1);
+}
+#[tokio::test]
+async fn attendance_day_current_read_uses_frozen_interval_and_exclusive_end_query() {
+    let tenant = Uuid::new_v4();
+    let (db, statements) = db(vec![frozen(tenant)]).await;
+    let now = utc("2026-09-11T23:29:59Z");
+    let result = current_window(&db, tenant, clock(), now).await.unwrap();
+    assert_eq!(result.work_date, date("2026-09-11"));
+    let sql = statements.lock().unwrap();
+    assert_eq!(sql.len(), 1);
+    assert!(sql[0].sql.contains("starts_at <= $2") && sql[0].sql.contains("ends_at > $2"));
+    assert!(sql[0].to_string().contains(&tenant.to_string()));
+}
+#[tokio::test]
+async fn attendance_day_current_read_after_end_resolves_next_window_without_writes() {
+    let tenant = Uuid::new_v4();
+    let (db, statements) = db(vec![vec![], policy_rows(&[("0001-01-01", 300)], None)]).await;
+    let result = current_window(&db, tenant, clock(), utc("2026-09-11T23:30:00Z")).await.unwrap();
+    assert_eq!(result.work_date, date("2026-09-12"));
+    assert_eq!(result.starts_at, utc("2026-09-11T23:30:00Z"));
+    assert!(statements.lock().unwrap().iter().all(|s| s.sql.starts_with("SELECT")));
+}
+#[tokio::test]
+async fn attendance_day_policy_audit_failure_propagates_for_transaction_rollback() {
+    let tenant = Uuid::new_v4();
+    let (db, _) = db_with_audit_failure(vec![policy_rows(&[("0001-01-01", 300)], None), vec![]], true).await;
+    let tx = db.begin().await.unwrap();
+    let err = schedule_policy(&tx, tenant, clock(), &claims(tenant, "ALL"), command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap_err();
+    assert!(matches!(err, kabipay_common::KabiPayError::Database(_)));
+    tx.rollback().await.unwrap();
+}
+#[tokio::test]
+async fn attendance_day_pending_legacy_activation_can_be_delayed_without_moving_original_anchor() {
+    let tenant = Uuid::new_v4();
+    let (db, _) = db(vec![policy_rows(&[("0001-01-01", 0), ("2026-09-12", 300)], Some(date("2026-09-12"))), vec![]]).await;
+    let tx = db.begin().await.unwrap();
+    let result = schedule_policy(&tx, tenant, clock(), &claims(tenant, "ALL"), command(7, "2026-09-13"), utc("2026-09-11T10:00:00Z")).await.unwrap();
+    assert_eq!(result.legacy_activation_date, Some(date("2026-09-12")));
+    assert!(result.legacy_activation_pending);
+    assert_eq!(result.versions.last().unwrap().effective_work_date, date("2026-09-13"));
+    let still_legacy = resolve_window(&result.versions, date("2026-09-12")).unwrap();
+    assert_eq!(still_legacy.starts_at, utc("2026-09-11T18:30:00Z"));
+    assert_eq!(still_legacy.ends_at, utc("2026-09-12T18:30:00Z"));
+    let transition = resolve_window(&result.versions, date("2026-09-13")).unwrap();
+    assert_eq!(transition.starts_at, utc("2026-09-12T18:30:00Z"));
+    assert_eq!(transition.ends_at, utc("2026-09-14T00:30:00Z"));
+}


diff --git a/crates/kabipay-db-entities/src/tenant/d0087_attendance_day_boundary.rs b/crates/kabipay-db-entities/src/tenant/d0087_attendance_day_boundary.rs
new file mode 100644
index 0000000..e307a53
--- /dev/null
+++ b/crates/kabipay-db-entities/src/tenant/d0087_attendance_day_boundary.rs
@@ -0,0 +1,66 @@
+//! Auto-generated from `hrms-database/changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml`.
+
+pub mod attendance_day_profile {
+    use crate::tenant::prelude::*;
+
+    #[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
+    #[sea_orm(table_name = "attendance_day_profile")]
+    pub struct Model {
+        #[sea_orm(primary_key, auto_increment = false)]
+        pub tenant_id: Uuid,
+        pub revision: i64,
+        pub legacy_activation_date: Option<NaiveDate>,
+        pub initialized_at: DateTimeUtc,
+    }
+
+    impl ActiveModelBehavior for ActiveModel {}
+
+    #[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
+    pub enum Relation {}
+}
+
+pub mod attendance_day_policy_version {
+    use crate::tenant::prelude::*;
+
+    #[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
+    #[sea_orm(table_name = "attendance_day_policy_version")]
+    pub struct Model {
+        #[sea_orm(primary_key, auto_increment = false)]
+        pub id: Uuid,
+        pub tenant_id: Uuid,
+        pub effective_work_date: NaiveDate,
+        pub boundary_minutes: i32,
+        pub timezone: String,
+        pub superseded_at: Option<DateTimeUtc>,
+        pub created_at: DateTimeUtc,
+    }
+
+    impl ActiveModelBehavior for ActiveModel {}
+
+    #[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
+    pub enum Relation {}
+}
+
+pub mod attendance_day_window {
+    use crate::tenant::prelude::*;
+
+    #[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
+    #[sea_orm(table_name = "attendance_day_window")]
+    pub struct Model {
+        #[sea_orm(primary_key, auto_increment = false)]
+        pub id: Uuid,
+        pub tenant_id: Uuid,
+        pub work_date: NaiveDate,
+        pub starts_at: DateTimeUtc,
+        pub ends_at: DateTimeUtc,
+        pub timezone: String,
+        pub boundary_minutes: i32,
+        pub policy_version_id: Uuid,
+        pub created_at: DateTimeUtc,
+    }
+
+    impl ActiveModelBehavior for ActiveModel {}
+
+    #[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
+    pub enum Relation {}
+}


## D:/work/heliorventures/hrms-database

warning: in the working copy of 'changelog/tenant.changelog-master.xml', LF will be replaced by CRLF the next time Git touches it
diff --git a/changelog/tenant.changelog-master.xml b/changelog/tenant.changelog-master.xml
index 8991516..ad8ece1 100644
--- a/changelog/tenant.changelog-master.xml
+++ b/changelog/tenant.changelog-master.xml
@@ -95,11 +95,12 @@
     <include file="migrations/0077_unpaid_leave_payroll/unpaid_leave_payroll.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0078_comp_off/comp_off.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0079_announcement_video/announcement_video.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0080_prejoining/prejoining.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0081_leave_approval_queue_index/leave_approval_queue_index.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0082_survey_privacy_snapshots/survey_privacy_snapshots.xml" relativeToChangelogFile="true"/>
 
     <include file="migrations/0084_survey_targeting_corrections/survey_targeting_corrections.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0085_admin_hr_permission_defaults/admin_hr_permission_defaults.xml" relativeToChangelogFile="true"/>
     <include file="migrations/0086_survey_response_review/survey_response_review.xml" relativeToChangelogFile="true"/>
+    <include file="migrations/0087_attendance_day_boundary/attendance_day_boundary.xml" relativeToChangelogFile="true"/>
 </databaseChangeLog>


warning: in the working copy of 'changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml', LF will be replaced by CRLF the next time Git touches it
diff --git a/changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml b/changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml
new file mode 100644
index 0000000..ae07e46
--- /dev/null
+++ b/changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml
@@ -0,0 +1,72 @@
+<?xml version="1.0" encoding="UTF-8"?>
+<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
+    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
+    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.27.xsd">
+    <changeSet id="0087-001-attendance-day-boundary" author="kabipay-dev">
+        <!-- No data activation/backfill: mutation/worker transactions initialize once. -->
+        <createTable tableName="attendance_day_profile" schemaName="${schema}">
+            <column name="tenant_id" type="UUID"><constraints nullable="false"/></column>
+            <column name="revision" type="BIGINT"><constraints nullable="false"/></column>
+            <column name="legacy_activation_date" type="DATE"/>
+            <column name="initialized_at" type="TIMESTAMPTZ"><constraints nullable="false"/></column>
+        </createTable>
+        <addPrimaryKey schemaName="${schema}" tableName="attendance_day_profile" columnNames="tenant_id" constraintName="pk_attendance_day_profile"/>
+        <createTable tableName="attendance_day_policy_version" schemaName="${schema}">
+            <column name="id" type="UUID"><constraints primaryKey="true" nullable="false"/></column>
+            <column name="tenant_id" type="UUID"><constraints nullable="false"/></column>
+            <column name="effective_work_date" type="DATE"><constraints nullable="false"/></column>
+            <column name="boundary_minutes" type="INT"><constraints nullable="false"/></column>
+            <column name="timezone" type="VARCHAR(100)"><constraints nullable="false"/></column>
+            <column name="superseded_at" type="TIMESTAMPTZ"/>
+            <column name="created_at" type="TIMESTAMPTZ"><constraints nullable="false"/></column>
+        </createTable>
+        <createTable tableName="attendance_day_window" schemaName="${schema}">
+            <column name="id" type="UUID"><constraints primaryKey="true" nullable="false"/></column>
+            <column name="tenant_id" type="UUID"><constraints nullable="false"/></column>
+            <column name="work_date" type="DATE"><constraints nullable="false"/></column>
+            <column name="starts_at" type="TIMESTAMPTZ"><constraints nullable="false"/></column>
+            <column name="ends_at" type="TIMESTAMPTZ"><constraints nullable="false"/></column>
+            <column name="timezone" type="VARCHAR(100)"><constraints nullable="false"/></column>
+            <column name="boundary_minutes" type="INT"><constraints nullable="false"/></column>
+            <column name="policy_version_id" type="UUID"><constraints nullable="false"/></column>
+            <column name="created_at" type="TIMESTAMPTZ"><constraints nullable="false"/></column>
+        </createTable>
+        <addUniqueConstraint schemaName="${schema}" tableName="attendance_day_policy_version" columnNames="tenant_id,id" constraintName="uq_attendance_day_version_tenant_id"/>
+        <addUniqueConstraint schemaName="${schema}" tableName="attendance_day_window" columnNames="tenant_id,work_date" constraintName="uq_attendance_day_window_tenant_date"/>
+        <addForeignKeyConstraint baseTableSchemaName="${schema}" baseTableName="attendance_day_policy_version" baseColumnNames="tenant_id" referencedTableSchemaName="${schema}" referencedTableName="attendance_day_profile" referencedColumnNames="tenant_id" constraintName="fk_attendance_day_version_profile" onDelete="RESTRICT"/>
+        <addForeignKeyConstraint baseTableSchemaName="${schema}" baseTableName="attendance_day_window" baseColumnNames="tenant_id,policy_version_id" referencedTableSchemaName="${schema}" referencedTableName="attendance_day_policy_version" referencedColumnNames="tenant_id,id" constraintName="fk_attendance_day_window_version" onDelete="RESTRICT"/>
+        <sql splitStatements="false"><![CDATA[
+ALTER TABLE "${schema}".attendance_day_profile ADD CONSTRAINT chk_attendance_day_revision CHECK (revision >= 1);
+ALTER TABLE "${schema}".attendance_day_policy_version ADD CONSTRAINT chk_attendance_day_version_minutes CHECK (boundary_minutes BETWEEN 0 AND 1439), ADD CONSTRAINT chk_attendance_day_version_timezone CHECK (length(trim(timezone)) > 0);
+ALTER TABLE "${schema}".attendance_day_window ADD CONSTRAINT chk_attendance_day_window_increasing CHECK (starts_at < ends_at), ADD CONSTRAINT chk_attendance_day_window_minutes CHECK (boundary_minutes BETWEEN 0 AND 1439);
+CREATE UNIQUE INDEX uq_attendance_day_live_effective ON "${schema}".attendance_day_policy_version (tenant_id,effective_work_date) WHERE superseded_at IS NULL;
+CREATE INDEX idx_attendance_day_window_instants ON "${schema}".attendance_day_window (tenant_id,starts_at,ends_at);
+CREATE FUNCTION "${schema}".prevent_attendance_day_window_mutation() RETURNS trigger LANGUAGE plpgsql AS $fn$
+BEGIN
+    RAISE EXCEPTION 'attendance day windows are immutable';
+END;
+$fn$;
+CREATE TRIGGER trg_attendance_day_window_immutable BEFORE UPDATE OR DELETE ON "${schema}".attendance_day_window FOR EACH ROW EXECUTE FUNCTION "${schema}".prevent_attendance_day_window_mutation();
+CREATE FUNCTION "${schema}".protect_attendance_day_policy_version() RETURNS trigger LANGUAGE plpgsql AS $fn$
+BEGIN
+    IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'attendance day policy versions cannot be deleted'; END IF;
+    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.effective_work_date IS DISTINCT FROM OLD.effective_work_date OR NEW.boundary_minutes IS DISTINCT FROM OLD.boundary_minutes OR NEW.timezone IS DISTINCT FROM OLD.timezone OR NEW.created_at IS DISTINCT FROM OLD.created_at OR OLD.superseded_at IS NOT NULL OR NEW.superseded_at IS NULL THEN
+        RAISE EXCEPTION 'attendance day policy version is immutable except initial supersession';
+    END IF;
+    RETURN NEW;
+END;
+$fn$;
+CREATE TRIGGER trg_attendance_day_policy_version_immutable BEFORE UPDATE OR DELETE ON "${schema}".attendance_day_policy_version FOR EACH ROW EXECUTE FUNCTION "${schema}".protect_attendance_day_policy_version();
+CREATE FUNCTION "${schema}".protect_attendance_day_activation() RETURNS trigger LANGUAGE plpgsql AS $fn$
+BEGIN
+    IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'attendance day activation cannot be deleted'; END IF;
+    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.legacy_activation_date IS DISTINCT FROM OLD.legacy_activation_date OR NEW.initialized_at IS DISTINCT FROM OLD.initialized_at OR NEW.revision <= OLD.revision THEN
+        RAISE EXCEPTION 'attendance day activation is immutable and revision must increase';
+    END IF;
+    RETURN NEW;
+END;
+$fn$;
+CREATE TRIGGER trg_attendance_day_activation_immutable BEFORE UPDATE OR DELETE ON "${schema}".attendance_day_profile FOR EACH ROW EXECUTE FUNCTION "${schema}".protect_attendance_day_activation();
+        ]]></sql>
+    </changeSet>
+</databaseChangeLog>


warning: in the working copy of 'scripts/test-attendance-day-contract.ps1', LF will be replaced by CRLF the next time Git touches it
diff --git a/scripts/test-attendance-day-contract.ps1 b/scripts/test-attendance-day-contract.ps1
new file mode 100644
index 0000000..5e4d555
--- /dev/null
+++ b/scripts/test-attendance-day-contract.ps1
@@ -0,0 +1,23 @@
+param([string]$DatabaseRoot = (Split-Path -Parent $PSScriptRoot))
+$ErrorActionPreference = 'Stop'
+$migrationPath = Join-Path $DatabaseRoot 'changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml'
+[xml]$migration = Get-Content -LiteralPath $migrationPath -Raw
+[xml]$master = Get-Content -LiteralPath (Join-Path $DatabaseRoot 'changelog/tenant.changelog-master.xml') -Raw
+$ns = New-Object System.Xml.XmlNamespaceManager($migration.NameTable)
+$ns.AddNamespace('db', 'http://www.liquibase.org/xml/ns/dbchangelog')
+$tables = @($migration.SelectNodes('//db:createTable', $ns))
+foreach ($name in @('attendance_day_profile', 'attendance_day_policy_version', 'attendance_day_window')) {
+    $table = @($tables | Where-Object { $_.tableName -eq $name })
+    if ($table.Count -ne 1) { throw "Missing or duplicate table $name" }
+    if ($table[0].schemaName -ne '${schema}') { throw "Table $name must use tenant schema" }
+    if (-not $table[0].SelectSingleNode('db:column[@name="tenant_id"]/db:constraints[@nullable="false"]', $ns)) { throw "Tenant key absent from $name" }
+}
+$masterNs = New-Object System.Xml.XmlNamespaceManager($master.NameTable)
+$masterNs.AddNamespace('db', 'http://www.liquibase.org/xml/ns/dbchangelog')
+$included = @($master.SelectNodes('//db:include', $masterNs) | Where-Object { $_.file -eq 'migrations/0087_attendance_day_boundary/attendance_day_boundary.xml' })
+if ($included.Count -ne 1) { throw 'Migration must be included exactly once' }
+$constraints = @($migration.SelectNodes('//db:addUniqueConstraint | //db:addForeignKeyConstraint', $ns))
+foreach ($name in @('uq_attendance_day_window_tenant_date', 'uq_attendance_day_version_tenant_id', 'fk_attendance_day_window_version')) {
+    if (-not ($constraints | Where-Object { $_.constraintName -eq $name })) { throw "Missing constraint $name" }
+}
+Write-Output 'PASS: attendance-day XML tables, required tenant keys, composite references and master inclusion'


