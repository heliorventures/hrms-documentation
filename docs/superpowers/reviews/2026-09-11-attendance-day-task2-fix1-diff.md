# Task2 fix round1 scoped diff

Exact pre-review source vs shared-validation fix. No commits; only listed fix files.
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_day__repository.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_day__repository.rs b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs
index 5b7cac3..824ba85 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_day__repository.rs
+++ b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs
@@ -124,46 +124,130 @@ async fn insert_version(
     db: &DatabaseTransaction, tenant_id: Uuid, version: &PolicyVersion, now: DateTime<Utc>,
 ) -> KabiPayResult<()> {
     db.execute(sql(
         "INSERT INTO attendance_day_policy_version (id, tenant_id, effective_work_date, boundary_minutes, timezone, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
         vec![version.id.into(), tenant_id.into(), version.effective_work_date.into(),
             version.boundary_minutes.into(), version.timezone.clone().into(), now.into()],
     )).await?;
     Ok(())
 }
 
-async fn initialize(
-    db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
+/// Prepare the same bootstrap state for a read-only proposal and a later write.
+/// Generated IDs are prospective until the caller persists this state.
+fn prepare_initialization(
+    clock: TenantBusinessClock,
     mut state: AttendanceDayPolicy, now: DateTime<Utc>,
 ) -> KabiPayResult<AttendanceDayPolicy> {
     if state.initialized { return Ok(state); }
     if state.legacy_activation_pending {
         let activation = clock.business_date(now).succ_opt()
             .ok_or_else(|| invalid("attendance activation date overflows"))?;
         state.legacy_activation_date = Some(activation);
         state.versions.push(PolicyVersion {
             id: Uuid::new_v4(), effective_work_date: activation,
             boundary_minutes: 300, timezone: clock.timezone_name().into(),
         });
     }
     state.versions.first_mut()
         .ok_or_else(|| invalid("attendance baseline policy is missing"))?.id = Uuid::new_v4();
     state.revision = 1;
     state.initialized = true;
+    Ok(state)
+}
+
+async fn persist_initialization(
+    db: &DatabaseTransaction, tenant_id: Uuid, state: &AttendanceDayPolicy,
+    now: DateTime<Utc>,
+) -> KabiPayResult<()> {
     db.execute(sql(
         "INSERT INTO attendance_day_profile (tenant_id, revision, legacy_activation_date, initialized_at) VALUES ($1, 1, $2, $3)",
         vec![tenant_id.into(), state.legacy_activation_date.into(), now.into()],
     )).await?;
     for version in &state.versions { insert_version(db, tenant_id, version, now).await?; }
+    Ok(())
+}
+
+async fn initialize(
+    db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
+    state: AttendanceDayPolicy, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayPolicy> {
+    if state.initialized { return Ok(state); }
+    let state = prepare_initialization(clock, state, now)?;
+    persist_initialization(db, tenant_id, &state, now).await?;
     Ok(state)
 }
 
+pub(super) fn validate_schedule_request(
+    tenant_id: Uuid, claims: &ClientClaims, command: &SchedulePolicyCommand,
+) -> KabiPayResult<()> {
+    if claims.tenant_id != tenant_id
+        || !claims.has_any_permission(&[PERM_ATTENDANCE_PUNCH_POLICY])
+        || claims.explicit_scope_for_permission(PERM_ATTENDANCE_PUNCH_POLICY) != Some(ScopeType::All)
+    {
+        return Err(KabiPayError::Forbidden("attendance day policy requires tenant-wide configuration authority".into()));
+    }
+    validate_minutes(command.boundary_minutes)
+}
+
+/// A validated proposal has no durable side effects. Scheduling builds it anew
+/// from its locked snapshot; a previously returned preview is never trusted.
+pub(super) struct PolicyChangeProposal {
+    pub state: AttendanceDayPolicy,
+    pub pending: Vec<PolicyVersion>,
+    pub version: PolicyVersion,
+    pub versions: Vec<PolicyVersion>,
+    pub transition: AttendanceDayWindow,
+    pub following: AttendanceDayWindow,
+    pub next_revision: i64,
+}
+
+pub(super) async fn propose_policy_change<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, clock: TenantBusinessClock,
+    state: AttendanceDayPolicy, command: &SchedulePolicyCommand, now: DateTime<Utc>,
+) -> KabiPayResult<PolicyChangeProposal> {
+    if command.expected_revision != state.revision {
+        return Err(KabiPayError::Conflict("attendance day policy changed; refresh before retrying".into()));
+    }
+    let active = resolve_current_window(&state.versions, now)?;
+    if command.effective_work_date <= active.work_date {
+        return Err(invalid("attendance day policy must take effect after the active work date"));
+    }
+    let state = prepare_initialization(clock, state, now)?;
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
+    let mut versions: Vec<_> = state.versions.iter()
+        .filter(|v| v.effective_work_date <= active.work_date).cloned().collect();
+    versions.push(version.clone());
+    let transition = resolve_window(&versions, command.effective_work_date)?;
+    let next_date = command.effective_work_date.succ_opt()
+        .ok_or_else(|| invalid("attendance effective date overflows"))?;
+    let following = resolve_window(&versions, next_date)?;
+    if transition.starts_at <= now || transition.ends_at != following.starts_at {
+        return Err(invalid("attendance policy transition must be future and continuous"));
+    }
+    let next_revision = state.revision.checked_add(1)
+        .ok_or_else(|| invalid("attendance policy revision overflows"))?;
+    Ok(PolicyChangeProposal { state, pending, version, versions, transition, following, next_revision })
+}
+
 /// Freeze within the caller's transaction; on error the caller must roll back.
 pub async fn ensure_window(
     db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
     work_date: NaiveDate, now: DateTime<Utc>,
 ) -> KabiPayResult<AttendanceDayWindow> {
     lock_policy(db, tenant_id).await?;
     if let Some(window) = frozen_for_date(db, tenant_id, work_date).await? {
         return Ok(window);
     }
     let state = policy(db, tenant_id, clock, now).await?;
@@ -204,64 +288,32 @@ fn audit_state(state: &AttendanceDayPolicy) -> serde_json::Value {
         })).collect::<Vec<_>>()
     })
 }
 
 /// Schedule one future replacement, preserving superseded rows and auditing the actor.
 /// Caller owns commit/rollback and must pass a timestamp sampled after locks.
 pub async fn schedule_policy(
     db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock,
     claims: &ClientClaims, command: SchedulePolicyCommand, now: DateTime<Utc>,
 ) -> KabiPayResult<AttendanceDayPolicy> {
-    if claims.tenant_id != tenant_id
-        || !claims.has_any_permission(&[PERM_ATTENDANCE_PUNCH_POLICY])
-        || claims.explicit_scope_for_permission(PERM_ATTENDANCE_PUNCH_POLICY) != Some(ScopeType::All)
-    {
-        return Err(KabiPayError::Forbidden("attendance day policy requires tenant-wide configuration authority".into()));
-    }
-    validate_minutes(command.boundary_minutes)?;
+    validate_schedule_request(tenant_id, claims, &command)?;
     lock_policy(db, tenant_id).await?;
     let state = policy(db, tenant_id, clock, now).await?;
-    if command.expected_revision != state.revision {
-        return Err(KabiPayError::Conflict("attendance day policy changed; refresh before retrying".into()));
-    }
-    let active = resolve_current_window(&state.versions, now)?;
-    if command.effective_work_date <= active.work_date {
-        return Err(invalid("attendance day policy must take effect after the active work date"));
-    }
     let before = audit_state(&state);
-    let mut state = initialize(db, tenant_id, clock, state, now).await?;
-    let pending: Vec<_> = state.versions.iter()
-        .filter(|v| v.effective_work_date > active.work_date).cloned().collect();
-    let affected_date = pending.iter().map(|v| v.effective_work_date)
-        .fold(command.effective_work_date, NaiveDate::min);
-    if db.query_one(sql(
-        "SELECT work_date FROM attendance_day_window WHERE tenant_id = $1 AND work_date >= $2 LIMIT 1",
-        vec![tenant_id.into(), affected_date.into()],
-    )).await?.is_some() {
-        return Err(KabiPayError::Conflict("attendance day policy would alter a frozen window".into()));
-    }
-    let version = PolicyVersion {
-        id: Uuid::new_v4(), effective_work_date: command.effective_work_date,
-        boundary_minutes: command.boundary_minutes, timezone: clock.timezone_name().into(),
-    };
-    let mut proposed: Vec<_> = state.versions.iter()
-        .filter(|v| v.effective_work_date <= active.work_date).cloned().collect();
-    proposed.push(version.clone());
-    let transition = resolve_window(&proposed, command.effective_work_date)?;
-    let following = command.effective_work_date.succ_opt()
-        .ok_or_else(|| invalid("attendance effective date overflows"))?;
-    let next = resolve_window(&proposed, following)?;
-    if transition.starts_at <= now || transition.ends_at != next.starts_at {
-        return Err(invalid("attendance policy transition must be future and continuous"));
+    let needs_initialization = !state.initialized;
+    let proposal = propose_policy_change(db, tenant_id, clock, state, &command, now).await?;
+    if needs_initialization {
+        persist_initialization(db, tenant_id, &proposal.state, now).await?;
     }
-    let revision = state.revision.checked_add(1)
-        .ok_or_else(|| invalid("attendance policy revision overflows"))?;
+    let PolicyChangeProposal {
+        mut state, pending, version, versions: proposed, next_revision: revision, ..
+    } = proposal;
     let update = db.execute(sql(
         "UPDATE attendance_day_profile SET revision = $2 WHERE tenant_id = $1 AND revision = $3",
         vec![tenant_id.into(), revision.into(), state.revision.into()],
     )).await?;
     if update.rows_affected() != 1 {
         return Err(KabiPayError::Conflict("attendance day policy changed; refresh before retrying".into()));
     }
     for prior in pending {
         let update = db.execute(sql(
             "UPDATE attendance_day_policy_version SET superseded_at = $3 WHERE tenant_id = $1 AND id = $2 AND superseded_at IS NULL",

warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_day__preview.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/preview.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_day__preview.rs b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/preview.rs
index a854c73..eddf29a 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_day__preview.rs
+++ b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/preview.rs
@@ -1,55 +1,29 @@
 //! Read-only settings transition preview; scheduling revalidates under its lock.
 use super::*;
 use chrono::{DateTime, Utc};
-use kabipay_common::{context::{ClientClaims, ScopeType, PERM_ATTENDANCE_PUNCH_POLICY}, tenant_business_clock::TenantBusinessClock, KabiPayError, KabiPayResult};
-use sea_orm::{ConnectionTrait, DbBackend, Statement};
+use kabipay_common::{context::ClientClaims, tenant_business_clock::TenantBusinessClock, KabiPayResult};
+use sea_orm::ConnectionTrait;
 use uuid::Uuid;
 
 #[derive(Clone, Debug)]
 pub struct AttendanceDayPolicyPreview {
     pub revision: i64,
     pub transition: AttendanceDayWindow,
     pub following: AttendanceDayWindow,
 }
 
 pub async fn preview_policy<C: ConnectionTrait>(
     db: &C, tenant_id: Uuid, clock: TenantBusinessClock, claims: &ClientClaims,
     command: SchedulePolicyCommand, now: DateTime<Utc>,
 ) -> KabiPayResult<AttendanceDayPolicyPreview> {
-    if claims.tenant_id != tenant_id || !claims.has_any_permission(&[PERM_ATTENDANCE_PUNCH_POLICY])
-        || claims.explicit_scope_for_permission(PERM_ATTENDANCE_PUNCH_POLICY) != Some(ScopeType::All) {
-        return Err(KabiPayError::Forbidden("attendance day policy requires tenant-wide configuration authority".into()));
-    }
-    super::calendar::validate_minutes(command.boundary_minutes)?;
+    super::repository::validate_schedule_request(tenant_id, claims, &command)?;
     let state = policy(db, tenant_id, clock, now).await?;
-    if state.revision != command.expected_revision {
-        return Err(KabiPayError::Conflict("attendance day policy changed; refresh before retrying".into()));
-    }
-    let active = resolve_current_window(&state.versions, now)?;
-    if command.effective_work_date <= active.work_date {
-        return Err(KabiPayError::Validation("attendance day policy must take effect after the active work date".into()));
-    }
-    let mut affected = state.versions.iter().filter(|v| v.effective_work_date > active.work_date)
-        .map(|v| v.effective_work_date).fold(command.effective_work_date, chrono::NaiveDate::min);
-    if !state.initialized && state.legacy_activation_pending {
-        let activation = clock.business_date(now).succ_opt()
-            .ok_or_else(|| KabiPayError::Validation("attendance activation date overflows".into()))?;
-        affected = affected.min(activation);
-    }
-    if db.query_one(Statement::from_sql_and_values(DbBackend::Postgres,
-        "SELECT work_date FROM attendance_day_window WHERE tenant_id = $1 AND work_date >= $2 LIMIT 1",
-        vec![tenant_id.into(), affected.into()],
-    )).await?.is_some() {
-        return Err(KabiPayError::Conflict("attendance day policy would alter a frozen window".into()));
-    }
-    let mut proposed: Vec<_> = state.versions.into_iter().filter(|v| v.effective_work_date <= active.work_date).collect();
-    proposed.push(PolicyVersion { id: Uuid::nil(), effective_work_date: command.effective_work_date,
-        boundary_minutes: command.boundary_minutes, timezone: clock.timezone_name().into() });
-    let transition = resolve_window(&proposed, command.effective_work_date)?;
-    let following = resolve_window(&proposed, command.effective_work_date.succ_opt()
-        .ok_or_else(|| KabiPayError::Validation("attendance effective date overflows".into()))?)?;
-    if transition.starts_at <= now || transition.ends_at != following.starts_at {
-        return Err(KabiPayError::Validation("attendance policy transition must be future and continuous".into()));
-    }
-    Ok(AttendanceDayPolicyPreview { revision: state.revision, transition, following })
+    let revision = state.revision;
+    let proposal = super::repository::propose_policy_change(db, tenant_id, clock, state, &command, now).await?;
+    let mut transition = proposal.transition;
+    let mut following = proposal.following;
+    // A preview does not persist or reserve these prospective policy versions.
+    transition.policy_version_id = Uuid::nil();
+    following.policy_version_id = Uuid::nil();
+    Ok(AttendanceDayPolicyPreview { revision, transition, following })
 }

warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__tests__attendance_day_policy.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/tests/attendance_day_policy.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__tests__attendance_day_policy.rs b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/tests/attendance_day_policy.rs
index c788304..274f7b8 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__tests__attendance_day_policy.rs
+++ b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/tests/attendance_day_policy.rs
@@ -171,30 +171,138 @@ async fn attendance_day_preview_validates_authority_revision_and_exact_transitio
     let preview = preview_policy(&preview_db, tenant, clock(), &claims(tenant, "ALL"), command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap();
     assert_eq!(preview.revision, 7);
     assert_eq!(preview.transition.starts_at, utc("2026-09-11T23:30:00Z"));
     assert_eq!(preview.transition.ends_at, utc("2026-09-13T00:30:00Z"));
     assert_eq!(preview.following.starts_at, utc("2026-09-13T00:30:00Z"));
     assert!(statements.lock().unwrap().iter().all(|s| s.sql.starts_with("SELECT")));
     let (stale_db, _) = db(vec![policy_rows(&[("0001-01-01", 300)], None)]).await;
     assert!(matches!(preview_policy(&stale_db, tenant, clock(), &claims(tenant, "ALL"), command(6, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await, Err(kabipay_common::KabiPayError::Conflict(_))));
 }
 fn policy_rows(versions: &[(&str, i32)], activation: Option<NaiveDate>) -> Vec<ProxyRow> {
+    policy_rows_at_revision(versions, activation, 7)
+}
+fn policy_rows_at_revision(versions: &[(&str, i32)], activation: Option<NaiveDate>, revision: i64) -> Vec<ProxyRow> {
     versions.iter().map(|(effective, minutes)| ProxyRow::new(BTreeMap::from([
-        ("revision".into(), 7_i64.into()),
+        ("revision".into(), revision.into()),
         ("legacy_activation_date".into(), activation.into()),
         ("id".into(), Uuid::new_v4().into()),
         ("effective_work_date".into(), date(effective).into()),
         ("boundary_minutes".into(), (*minutes).into()),
         ("timezone".into(), "Asia/Kolkata".into()),
         ("has_attendance".into(), true.into()),
     ]))).collect()
 }
+
+#[derive(Clone, Copy, Debug)]
+enum AgreementFixture { Fresh, Legacy, PendingLegacy, PendingCustom }
+impl AgreementFixture {
+    fn snapshot(self) -> Vec<ProxyRow> {
+        match self {
+            Self::Fresh => missing_profile_snapshot(false),
+            Self::Legacy => missing_profile_snapshot(true),
+            Self::PendingLegacy => policy_rows(&[("0001-01-01", 0), ("2026-09-12", 300)], Some(date("2026-09-12"))),
+            Self::PendingCustom => policy_rows(&[("0001-01-01", 300), ("2026-09-13", 240)], None),
+        }
+    }
+    fn revision(self) -> i64 {
+        match self { Self::Fresh | Self::Legacy => 0, _ => 7 }
+    }
+}
+
+#[tokio::test]
+async fn attendance_day_preview_schedule_agreement_preserves_bootstrap_and_replacement_intervals() {
+    for (fixture, effective, expected_start, expected_end, expected_anchor) in [
+        (AgreementFixture::Fresh, "2026-09-12", "2026-09-11T23:30:00Z", "2026-09-13T00:30:00Z", None),
+        (AgreementFixture::Legacy, "2026-09-13", "2026-09-12T18:30:00Z", "2026-09-14T00:30:00Z", Some("2026-09-12")),
+        (AgreementFixture::PendingLegacy, "2026-09-13", "2026-09-12T18:30:00Z", "2026-09-14T00:30:00Z", Some("2026-09-12")),
+        (AgreementFixture::PendingCustom, "2026-09-14", "2026-09-13T23:30:00Z", "2026-09-15T00:30:00Z", None),
+    ] {
+        let tenant = Uuid::new_v4();
+        let now = utc("2026-09-11T10:00:00Z");
+        let cmd = command(fixture.revision(), effective);
+        let (preview_db, read_statements) = db(vec![fixture.snapshot(), vec![]]).await;
+        let preview = preview_policy(&preview_db, tenant, clock(), &claims(tenant, "ALL"), cmd.clone(), now).await.unwrap();
+        let (schedule_db, write_statements) = db(vec![fixture.snapshot(), vec![]]).await;
+        let txn = schedule_db.begin().await.unwrap();
+        let scheduled = schedule_policy(&txn, tenant, clock(), &claims(tenant, "ALL"), cmd, now).await.unwrap();
+        let actual = resolve_window(&scheduled.versions, date(effective)).unwrap();
+        assert_eq!(preview.transition.starts_at, utc(expected_start), "{fixture:?}");
+        assert_eq!(preview.transition.ends_at, utc(expected_end), "{fixture:?}");
+        assert_eq!(actual.starts_at, utc(expected_start), "{fixture:?}");
+        assert_eq!(actual.ends_at, utc(expected_end), "{fixture:?}");
+        assert_eq!(preview.following.starts_at, utc(expected_end));
+        assert_eq!(scheduled.legacy_activation_date, expected_anchor.map(date));
+        assert_eq!(preview.revision, fixture.revision());
+        assert_eq!(scheduled.revision, if fixture.revision() == 0 { 2 } else { 8 });
+        assert_eq!(scheduled.versions.len(), 2);
+        assert!(read_statements.lock().unwrap().iter().all(|s| s.sql.starts_with("SELECT")));
+        let statements = write_statements.lock().unwrap();
+        assert!(statements[0].sql.contains("pg_advisory_xact_lock"));
+        assert!(statements.iter().any(|s| s.sql.starts_with("INSERT INTO audit_log")));
+    }
+}
+
+#[tokio::test]
+async fn attendance_day_preview_schedule_agreement_rejects_stale_active_and_affected_frozen_dates() {
+    for (fixture, effective, affected) in [
+        (AgreementFixture::Fresh, "2026-09-13", "2026-09-13"),
+        (AgreementFixture::Legacy, "2026-09-13", "2026-09-12"),
+        (AgreementFixture::PendingLegacy, "2026-09-13", "2026-09-12"),
+        (AgreementFixture::PendingCustom, "2026-09-14", "2026-09-13"),
+    ] {
+        for rejection in ["revision", "active", "frozen"] {
+            let tenant = Uuid::new_v4();
+            let mut cmd = command(fixture.revision(), effective);
+            if rejection == "revision" { cmd.expected_revision -= 1; }
+            if rejection == "active" { cmd.effective_work_date = date("2026-09-11"); }
+            let expected_code = if rejection == "active" { "VALIDATION_ERROR" } else { "CONFLICT" };
+            for schedule in [false, true] {
+                let mut replies = vec![fixture.snapshot()];
+                if rejection == "frozen" { replies.push(vec![ProxyRow::new(BTreeMap::from([("work_date".into(), date(affected).into())]))]); }
+                let (db, statements) = db(replies).await;
+                let now = utc("2026-09-11T10:00:00Z");
+                let error = if schedule {
+                    let txn = db.begin().await.unwrap();
+                    let error = schedule_policy(&txn, tenant, clock(), &claims(tenant, "ALL"), cmd.clone(), now).await.unwrap_err();
+                    txn.rollback().await.unwrap();
+                    error
+                } else {
+                    preview_policy(&db, tenant, clock(), &claims(tenant, "ALL"), cmd.clone(), now).await.unwrap_err()
+                };
+                assert_eq!(error.code(), expected_code, "{fixture:?} {rejection} schedule={schedule}");
+                let statements = statements.lock().unwrap();
+                if !schedule { assert!(statements.iter().all(|s| s.sql.starts_with("SELECT"))); }
+                if rejection == "frozen" {
+                    let frozen = statements.iter().find(|s| s.sql.contains("work_date >= $2")).unwrap();
+                    assert!(frozen.to_string().contains(&format!("'{affected}'")), "{fixture:?}: {frozen}");
+                }
+            }
+        }
+    }
+}
+
+#[tokio::test]
+async fn attendance_day_preview_schedule_agreement_rejects_exhausted_revision() {
+    let tenant = Uuid::new_v4();
+    for schedule in [false, true] {
+        let (db, _) = db(vec![policy_rows_at_revision(&[("0001-01-01", 300)], None, i64::MAX), vec![]]).await;
+        let now = utc("2026-09-11T10:00:00Z");
+        let cmd = command(i64::MAX, "2026-09-12");
+        let rejected = if schedule {
+            let txn = db.begin().await.unwrap();
+            schedule_policy(&txn, tenant, clock(), &claims(tenant, "ALL"), cmd, now).await.is_err()
+        } else {
+            preview_policy(&db, tenant, clock(), &claims(tenant, "ALL"), cmd, now).await.is_err()
+        };
+        assert!(rejected, "preview and save must reject an exhausted revision; schedule={schedule}");
+    }
+}
 #[tokio::test]
 async fn attendance_day_policy_rejects_unauthorized_and_foreign_tenants_before_sql() {
     let tenant = Uuid::new_v4();
     for claimant in [claims(tenant, "TEAM"), claims(Uuid::new_v4(), "ALL")] {
         let (db, statements) = db(vec![]).await;
         let tx = db.begin().await.unwrap();
         let err = schedule_policy(&tx, tenant, clock(), &claimant, command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap_err();
         assert!(matches!(err, kabipay_common::KabiPayError::Forbidden(_)));
         assert!(statements.lock().unwrap().is_empty());
     }

warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_service.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_service.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_service.rs b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_service.rs
index 6e748ed..4f95b5a 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task2-fix1-base/crates__kabipay-attendance__src__services__attendance_service.rs
+++ b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_service.rs
@@ -102,21 +102,21 @@ pub async fn list_upcoming_holidays(
         .limit(limit)
         .all(db)
         .await?;
     let out: Vec<(holiday::Model, String)> = rows
         .into_iter()
         .filter_map(|h| names.get(&h.calendar_id).cloned().map(|n| (h, n)))
         .collect();
     Ok(out)
 }
 
-/// Minutes in a single completed inâ†’out pair (same calendar work_date).
+/// Minutes in a single completed in→out pair (same calendar work_date).
 fn segment_minutes(t_in: chrono::NaiveTime, t_out: chrono::NaiveTime) -> i32 {
     use chrono::Timelike;
     let s_in = t_in.num_seconds_from_midnight() as i64;
     let s_out = t_out.num_seconds_from_midnight() as i64;
     let d = s_out - s_in;
     if d <= 0 {
         return 0;
     }
     (d / 60) as i32
 }
@@ -161,21 +161,21 @@ pub async fn list_employee_attendance_on_date(
     attendance::Entity::find()
         .filter(attendance::Column::TenantId.eq(tenant_id))
         .filter(attendance::Column::EmployeeId.eq(employee_id))
         .filter(attendance::Column::WorkDate.eq(work_date))
         .order_by_asc(attendance::Column::CreatedAt)
         .all(db)
         .await
         .map_err(KabiPayError::from)
 }
 
-/// Aggregated stats for a day: sum of (check-out âˆ’ check-in) for every completed
+/// Aggregated stats for a day: sum of (check-out − check-in) for every completed
 /// segment, plus the current open segment (checked in, not out) if any.
 pub struct PunchDaySummary {
     pub work_date: NaiveDate,
     pub window: super::attendance_day::AttendanceDayWindow,
     pub total_worked_minutes: i32,
     pub open_segment: Option<attendance::Model>,
     pub segments: Vec<attendance::Model>,
 }
 
 pub async fn punch_day_summary(
@@ -202,21 +202,21 @@ pub async fn punch_day_summary(
         .cloned();
     Ok(PunchDaySummary {
         work_date,
         window,
         total_worked_minutes: total,
         open_segment,
         segments,
     })
 }
 
-/// **Multi-segment punch:** each pair (punch in â†’ punch out) is a separate `attendance` row
+/// **Multi-segment punch:** each pair (punch in → punch out) is a separate `attendance` row
 /// for the same `work_date`. The next call after a completed segment starts a new segment
 /// (new check-in row). `total` worked time for the day is the sum of all completed segments.
 ///
 /// `geo` applies to **this** event: on punch-in (new row) it fills `check_in_*`;
 /// on punch-out (update open row) it fills `check_out_*`. Columns in Liquibase: `attendance`
 /// already has `check_in_lat` / `check_in_lng` / `check_out_lat` / `check_out_lng`.
 pub async fn punch_today(
     db: &DatabaseConnection,
     tenant_id: Uuid,
     employee_id: Uuid,
@@ -323,23 +323,23 @@ pub(crate) async fn punch_today_with_clock(
         updated_at: Set(now_ts),
     };
     am.insert(&txn).await?;
     txn.commit().await?;
     attendance::Entity::find_by_id(id)
         .one(db)
         .await?
         .ok_or_else(|| KabiPayError::Internal("attendance row missing after insert".into()))
 }
 
-/// One completed inâ†’out **segment** for a chosen `work_date` when the user missed live punches
-/// (e.g. forgot to open the app). **Same calendar day** only â€” night shifts that span midnight
-/// are not represented as a single row here. Stored with `source` `WEB+MANUAL` and
+/// One completed interval inside the retained attendance window for `work_date`.
+/// Paired actual dates support intervals across midnight; omitted dates must
+/// identify an unambiguous interval. Stored with `source` `WEB+MANUAL` and
 /// `regularization_status` `SELF_REPORTED` for audit.
 pub async fn add_manual_attendance_segment(
     db: &DatabaseConnection,
     tenant_id: Uuid,
     employee_id: Uuid,
     clock: TenantBusinessClock,
     work_date: NaiveDate,
     check_in_time: NaiveTime,
     check_out_time: NaiveTime,
     actual_dates: Option<(NaiveDate, NaiveDate)>,

