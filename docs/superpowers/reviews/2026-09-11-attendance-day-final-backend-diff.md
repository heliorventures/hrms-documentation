# Final attendance backend/database source snapshot

Uncommitted feature changes only. Service base62092ac5b72f34e26844e2a392d7feb391936ee0; database basee4f6d4d4c1a8c7857a1e65c93eff1439ff070c51. Includes final Task1/2 fixes. No unrelated dirty files.

## D:/work/heliorventures/hrms-svc
warning: in the working copy of 'Cargo.lock', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/Cargo.toml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/lib.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/resolvers/mutation.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/resolvers/query.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/resolvers/types.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_regularization_service.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_service.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/src/services/mod.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-attendance/tests/attendance_management_postgres.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-outbox-worker/Cargo.toml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'crates/kabipay-outbox-worker/src/main.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/Cargo.lock b/Cargo.lock
index 4ee070d..b30c2e4 100644
--- a/Cargo.lock
+++ b/Cargo.lock
@@ -2095,20 +2095,21 @@ dependencies = [
 ]
 
 [[package]]
 name = "kabipay-outbox-worker"
 version = "0.1.0"
 dependencies = [
  "anyhow",
  "chrono",
  "hex",
  "hmac",
+ "kabipay-attendance",
  "kabipay-common",
  "kabipay-db-entities",
  "kabipay-notification",
  "kabipay-performance",
  "kabipay-survey",
  "reqwest",
  "sea-orm",
  "serde",
  "serde_json",
  "sha2",
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
index ace1fad..de7534d 100644
--- a/crates/kabipay-attendance/src/lib.rs
+++ b/crates/kabipay-attendance/src/lib.rs
@@ -1,16 +1,18 @@
 //! Attendance domain library used by the subgraph binary and integration tests.
 
 mod resolvers;
 mod services;
 
 pub use resolvers::{MutationRoot, QueryRoot};
+pub use services::attendance_day;
+pub use services::attendance_day_runtime::{sweep_expired_attendance, ExpirySweepResult};
 
 /// Public attendance-management types supported for integration consumers.
 ///
 /// Keep this facade intentionally narrow. Task 4B may add only the
 /// regularization-specific types or functions its integration tests require.
 pub mod attendance_management {
     pub use crate::services::attendance_management_service::AttendancePage;
     pub use crate::services::attendance_regularization_service::{
         create_managed_attendance_segment_in_transaction, ManagedCreateCommand, SegmentInstants,
         SegmentTimes,
diff --git a/crates/kabipay-attendance/src/resolvers/mutation.rs b/crates/kabipay-attendance/src/resolvers/mutation.rs
index 7f7a8aa..f0d1a6b 100644
--- a/crates/kabipay-attendance/src/resolvers/mutation.rs
+++ b/crates/kabipay-attendance/src/resolvers/mutation.rs
@@ -43,20 +43,28 @@ use crate::services::{
     },
     attendance_service, hrms_master_service, punch_policy, timesheet_batch_service,
     timesheet_project_assignment_service,
 };
 
 fn parse_uuid(id: &ID, field: &'static str) -> Result<Uuid> {
     Uuid::parse_str(id.as_str())
         .map_err(|e| KabiPayError::Validation(format!("invalid {field}: {e}")).into_graphql())
 }
 
+fn actual_attendance_dates(check_in: Option<chrono::NaiveDate>, check_out: Option<chrono::NaiveDate>) -> Result<Option<(chrono::NaiveDate, chrono::NaiveDate)>> {
+    match (check_in, check_out) {
+        (None, None) => Ok(None),
+        (Some(start), Some(end)) => Ok(Some((start, end))),
+        _ => Err(KabiPayError::Validation("provide both checkInDate and checkOutDate, or neither".into()).into_graphql()),
+    }
+}
+
 async fn managed_attendance_dto<C>(
     db: &C,
     row: attendance::Model,
 ) -> Result<ManagedAttendanceDto>
 where
     C: ConnectionTrait,
 {
     let target = employee::Entity::find_by_id(row.employee_id)
         .filter(employee::Column::TenantId.eq(row.tenant_id))
         .filter(employee::Column::IsDeleted.eq(false))
@@ -110,28 +118,46 @@ fn require_self_authority(ctx: &Context<'_>, permission: &'static str) -> Result
     require_mutation_authority(ctx, permission, &[ScopeType::Self_], true).map(|_| ())
 }
 
 fn require_team_or_all_authority(
     ctx: &Context<'_>,
     permission: &'static str,
 ) -> Result<ScopeType> {
     require_mutation_authority(ctx, permission, &[ScopeType::Team, ScopeType::All], false)
 }
 
-fn require_all_authority(ctx: &Context<'_>, permission: &'static str) -> Result<()> {
+pub(crate) fn require_all_authority(ctx: &Context<'_>, permission: &'static str) -> Result<()> {
     require_mutation_authority(ctx, permission, &[ScopeType::All], false).map(|_| ())
 }
 
 pub struct MutationRoot;
 
 #[Object]
 impl MutationRoot {
+    async fn schedule_attendance_day_policy(
+        &self, ctx: &Context<'_>, input: crate::resolvers::types::ScheduleAttendanceDayPolicyInput,
+    ) -> Result<crate::resolvers::types::AttendanceDayPolicyDto> {
+        let tenant_id = require_tenant_id(ctx)?;
+        require_all_authority(ctx, PERM_ATTENDANCE_PUNCH_POLICY)?;
+        let command = input.command().map_err(KabiPayError::into_graphql)?;
+        let claims = require_client_claims(ctx)?;
+        let db = tenant_db(ctx, tenant_id).await?;
+        let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        let txn = db.begin().await.map_err(KabiPayError::from).map_err(KabiPayError::into_graphql)?;
+        crate::services::attendance_day::lock_policy(&txn, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        let now = chrono::Utc::now();
+        let state = crate::services::attendance_day::schedule_policy(&txn, tenant_id, clock, claims, command, now)
+            .await.map_err(KabiPayError::into_graphql)?;
+        let dto = crate::resolvers::types::AttendanceDayPolicyDto::from_state(state, now).map_err(KabiPayError::into_graphql)?;
+        txn.commit().await.map_err(KabiPayError::from).map_err(KabiPayError::into_graphql)?;
+        Ok(dto)
+    }
     /// Record a punch: closes the **open** segment (punch in without out) if any, otherwise
     /// starts a **new** segment (new `attendance` row). Multiple in/out pairs per `work_date`
     /// are allowed; there is no “third punch” error.
     ///
     /// When `input` includes **both** `latitude` and `longitude` (WGS84), they are stored on
     /// `attendance` as punch-in coordinates for a new row, or punch-out coordinates when closing
     /// an open segment (`check_out_lat` / `check_out_lng` columns).
     async fn punch_today(
         &self,
         ctx: &Context<'_>,
@@ -206,20 +232,21 @@ impl MutationRoot {
             .await
             .map_err(KabiPayError::into_graphql)?;
         let m = attendance_service::add_manual_attendance_segment(
             &db,
             tenant_id,
             employee_id,
             clock,
             input.work_date,
             input.check_in_time,
             input.check_out_time,
+            actual_attendance_dates(input.check_in_date, input.check_out_date)?,
         )
         .await
         .map_err(KabiPayError::into_graphql)?;
         Ok(AttendanceDto::from(m))
     }
 
     /// Update an existing manual attendance segment with server-side overlap and daily-cap checks.
     async fn update_manual_attendance_segment(
         &self,
         ctx: &Context<'_>,
@@ -237,20 +264,21 @@ impl MutationRoot {
         let attendance_id = parse_uuid(&input.id, "id")?;
         let m = attendance_service::update_manual_attendance_segment(
             &db,
             tenant_id,
             attendance_id,
             employee_id,
             clock,
             input.work_date,
             input.check_in_time,
             input.check_out_time,
+            actual_attendance_dates(input.check_in_date, input.check_out_date)?,
         )
         .await
         .map_err(KabiPayError::into_graphql)?;
         Ok(AttendanceDto::from(m))
     }
 
     async fn add_managed_attendance_segment(
         &self,
         ctx: &Context<'_>,
         input: AddManagedAttendanceSegmentInput,
@@ -262,42 +290,41 @@ impl MutationRoot {
         let request_id = client_request_hints(ctx).request_id;
         let db = tenant_db(ctx, tenant_id).await?;
         let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id)
             .await
             .map_err(KabiPayError::into_graphql)?;
         let segment = SegmentTimes::for_manual_input(
             input.work_date,
             input.check_in_time,
             input.check_out_time,
         );
-        let instants = segment.to_instants(clock).map_err(KabiPayError::into_graphql)?;
+        let actual_dates = actual_attendance_dates(input.check_in_date, input.check_out_date)?;
         let mut txn = db
             .begin()
             .await
             .map_err(KabiPayError::from)
             .map_err(KabiPayError::into_graphql)?;
         attendance_management_auth::assert_target_in_scope_with_connection(
             ctx,
             &txn,
             tenant_id,
             target_employee_id,
         )
         .await?;
         let created = create_managed_attendance_segment_in_transaction(
             &mut txn,
             &ManagedCreateCommand {
                 tenant_id,
                 target_employee_id,
                 actor_user_id,
                 segment,
-                instants,
-                today: clock.now_date(),
+                clock, actual_dates,
                 reason: input.reason,
                 request_id,
             },
         )
         .await
         .map_err(KabiPayError::into_graphql)?;
         let result = managed_attendance_dto(&txn, created).await?;
         txn.commit()
             .await
             .map_err(KabiPayError::from)
@@ -317,21 +344,21 @@ impl MutationRoot {
         let request_id = client_request_hints(ctx).request_id;
         let db = tenant_db(ctx, tenant_id).await?;
         let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id)
             .await
             .map_err(KabiPayError::into_graphql)?;
         let segment = SegmentTimes::for_manual_input(
             input.work_date,
             input.check_in_time,
             input.check_out_time,
         );
-        let instants = segment.to_instants(clock).map_err(KabiPayError::into_graphql)?;
+        let actual_dates = actual_attendance_dates(input.check_in_date, input.check_out_date)?;
         let mut txn = db
             .begin()
             .await
             .map_err(KabiPayError::from)
             .map_err(KabiPayError::into_graphql)?;
         let initial = attendance_management_auth::attendance_target_in_scope_with_connection(
             ctx,
             &txn,
             tenant_id,
             attendance_id,
@@ -339,22 +366,21 @@ impl MutationRoot {
         .await?;
         let updated = update_managed_attendance_segment_in_transaction(
             &mut txn,
             &ManagedUpdateCommand {
                 tenant_id,
                 attendance_id,
                 target_employee_id: initial.employee_id,
                 actor_user_id,
                 initial_work_date: initial.work_date,
                 segment,
-                instants,
-                today: clock.now_date(),
+                clock, actual_dates,
                 reason: input.reason,
                 request_id,
                 expected_updated_at: input.expected_updated_at,
             },
         )
         .await
         .map_err(KabiPayError::into_graphql)?;
         let result = managed_attendance_dto(&txn, updated).await?;
         txn.commit()
             .await
@@ -779,20 +805,22 @@ mod authorization_tests {
             .data(claims)
             .finish()
             .execute(Request::new(mutation))
             .await
     }
 
     fn mutation_inventory() -> Vec<(&'static str, String)> {
         let id = Uuid::new_v4();
         let step_id = Uuid::new_v4();
         vec![
+            (PERM_ATTENDANCE_PUNCH_POLICY,
+                "mutation { scheduleAttendanceDayPolicy(input: { boundaryTime: \"05:00\", effectiveWorkDate: \"2026-09-15\", expectedRevision: 1 }) { revision } }".into()),
             (PERM_ATTENDANCE_PUNCH_SELF, "mutation { punchToday { id } }".into()),
             (
                 PERM_ATTENDANCE_PUNCH_POLICY,
                 "mutation { upsertAttendancePunchPolicy(input: { isEnforced: false }) { id } }"
                     .into(),
             ),
             (
                 PERM_ATTENDANCE_PUNCH_SELF,
                 "mutation { addManualAttendanceSegment(input: { workDate: \"2026-08-27\", checkInTime: \"09:00:00\", checkOutTime: \"17:00:00\" }) { id } }".into(),
             ),
@@ -943,21 +971,21 @@ mod authorization_tests {
                     &mutation,
                 )
                 .await;
                 assert_exact_permission_denied_before_db(&response, required_permission);
             }
         }
     }
 
     #[tokio::test]
     async fn suitable_exact_scopes_allow_every_mutation_to_reach_its_database_boundary() {
-        assert_eq!(mutation_inventory().len(), 21);
+        assert_eq!(mutation_inventory().len(), 22);
         for (required_permission, mutation) in mutation_inventory() {
             for scope in allowed_scopes(required_permission) {
                 let response = execute_mutation(
                     claims(
                         Some(required_permission),
                         Some(scope),
                         Some(Uuid::new_v4()),
                     ),
                     &mutation,
                 )
diff --git a/crates/kabipay-attendance/src/resolvers/query.rs b/crates/kabipay-attendance/src/resolvers/query.rs
index a3ad427..aaced34 100644
--- a/crates/kabipay-attendance/src/resolvers/query.rs
+++ b/crates/kabipay-attendance/src/resolvers/query.rs
@@ -79,20 +79,58 @@ fn timesheet_read_scope(ctx: &Context<'_>) -> Result<ScopeType> {
 
 fn timesheet_approval_scope(ctx: &Context<'_>) -> Result<ScopeType> {
     timesheet_approval_scope_from_claims(ctx.data_opt::<ClientClaims>())
         .map_err(KabiPayError::into_graphql)
 }
 
 pub struct QueryRoot;
 
 #[Object]
 impl QueryRoot {
+    /// Tenant configuration metadata; only explicit ALL configuration authority.
+    async fn attendance_day_policy(&self, ctx: &Context<'_>) -> Result<crate::resolvers::types::AttendanceDayPolicyDto> {
+        let tenant_id = require_tenant_id(ctx)?;
+        super::mutation::require_all_authority(ctx, kabipay_common::context::PERM_ATTENDANCE_PUNCH_POLICY)?;
+        let db = tenant_db(ctx, tenant_id).await?;
+        let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        let now = chrono::Utc::now();
+        let state = crate::services::attendance_day::policy(&db, tenant_id, clock, now).await.map_err(KabiPayError::into_graphql)?;
+        crate::resolvers::types::AttendanceDayPolicyDto::from_state(state, now).map_err(KabiPayError::into_graphql)
+    }
+
+    /// Read-only metadata for current or historical corrections; no employee data.
+    async fn attendance_day_window(&self, ctx: &Context<'_>, work_date: Option<NaiveDate>) -> Result<crate::resolvers::types::AttendanceDayWindowDto> {
+        let tenant_id = require_tenant_id(ctx)?;
+        attendance_read_scope(ctx)?;
+        let db = tenant_db(ctx, tenant_id).await?;
+        let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        let now = chrono::Utc::now();
+        let window = match work_date {
+            Some(date) => crate::services::attendance_day::window_for_date(&db, tenant_id, clock, date, now).await,
+            None => crate::services::attendance_day::current_window(&db, tenant_id, clock, now).await,
+        }.map_err(KabiPayError::into_graphql)?;
+        Ok(window.into())
+    }
+
+    async fn preview_attendance_day_policy(&self, ctx: &Context<'_>, input: crate::resolvers::types::ScheduleAttendanceDayPolicyInput) -> Result<crate::resolvers::types::AttendanceDayPolicyPreviewDto> {
+        let tenant_id = require_tenant_id(ctx)?;
+        super::mutation::require_all_authority(ctx, kabipay_common::context::PERM_ATTENDANCE_PUNCH_POLICY)?;
+        let command = input.command().map_err(KabiPayError::into_graphql)?;
+        let claims = kabipay_common::subgraph::require_client_claims(ctx)?;
+        let db = tenant_db(ctx, tenant_id).await?;
+        let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        let preview = crate::services::attendance_day::preview_policy(&db, tenant_id, clock, claims, command, chrono::Utc::now())
+            .await.map_err(KabiPayError::into_graphql)?;
+        Ok(crate::resolvers::types::AttendanceDayPolicyPreviewDto {
+            revision: preview.revision, transition: preview.transition.into(), following: preview.following.into(),
+        })
+    }
     async fn attendance_health(&self) -> &'static str {
         "ok"
     }
 
     /// Live punch policy (geofence + IP). Requires exact scoped `attendance:read`.
     async fn attendance_punch_policy(&self, ctx: &Context<'_>) -> Result<AttendancePunchPolicyDto> {
         let tenant_id = require_tenant_id(ctx)?;
         attendance_read_scope(ctx)?;
         let db = tenant_db(ctx, tenant_id).await?;
         let row = punch_policy::find_punch_policy(&db, tenant_id)
@@ -127,23 +165,26 @@ impl QueryRoot {
         from_date: Option<NaiveDate>,
         to_date: Option<NaiveDate>,
     ) -> Result<Vec<AttendanceDto>> {
         let tenant_id = require_tenant_id(ctx)?;
         let scope = attendance_read_scope(ctx)?;
         let db = tenant_db(ctx, tenant_id).await?;
         let viewer = resolve_viewer_employee(ctx, &db, tenant_id).await?;
         let filt = resolve_employee_scope_filter(&db, tenant_id, scope, viewer)
             .await
             .map_err(KabiPayError::into_graphql)?;
-        let rows = attendance_service::list_attendance(&db, tenant_id, limit, &filt, from_date, to_date)
+        let mut rows = attendance_service::list_attendance(&db, tenant_id, limit, &filt, from_date, to_date)
             .await
             .map_err(KabiPayError::into_graphql)?;
+        let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        crate::services::attendance_day_runtime::project_rows(&db, tenant_id, clock, &mut rows, chrono::Utc::now())
+            .await.map_err(KabiPayError::into_graphql)?;
         Ok(rows.into_iter().map(AttendanceDto::from).collect())
     }
 
     /// Complete-period totals for the JWT-linked employee; cursor pages never affect totals.
     async fn my_attendance_summary(
         &self,
         ctx: &Context<'_>,
         from_date: NaiveDate,
         to_date: NaiveDate,
     ) -> Result<AttendancePeriodSummaryDto> {
@@ -177,33 +218,37 @@ impl QueryRoot {
     ) -> Result<AttendanceConnectionDto> {
         let tenant_id = require_tenant_id(ctx)?;
         attendance_read_scope(ctx)?;
         let db = tenant_db(ctx, tenant_id).await?;
         let employee_id = resolve_client_employee_id(ctx, &db, tenant_id)
             .await
             .map_err(KabiPayError::into_graphql)?;
         let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id)
             .await
             .map_err(KabiPayError::into_graphql)?;
+        let current = crate::services::attendance_day::current_window(&db, tenant_id, clock, chrono::Utc::now())
+            .await.map_err(KabiPayError::into_graphql)?;
         let (from_date, to_date) =
-            self_attendance_date_range(from_date, to_date, clock.now_date())?;
-        let page = attendance_management_service::list_my_attendance(
+            self_attendance_date_range(from_date, to_date, current.work_date)?;
+        let mut page = attendance_management_service::list_my_attendance(
             &db,
             tenant_id,
             employee_id,
             from_date,
             to_date,
             first,
             after.as_deref(),
         )
         .await
         .map_err(KabiPayError::into_graphql)?;
+        crate::services::attendance_day_runtime::project_rows(&db, tenant_id, clock, &mut page.rows, chrono::Utc::now())
+            .await.map_err(KabiPayError::into_graphql)?;
         Ok(AttendanceConnectionDto {
             edges: page
                 .rows
                 .into_iter()
                 .map(|row| AttendanceEdgeDto {
                     cursor: attendance_management_service::AttendanceCursor::new(
                         row.work_date,
                         row.created_at,
                         row.id,
                     )
@@ -242,33 +287,39 @@ impl QueryRoot {
             .transpose()?;
         if let Some(employee_id) = employee_id {
             attendance_management_auth::assert_target_in_resolved_scope(
                 &db,
                 tenant_id,
                 &scope,
                 employee_id,
             )
             .await?;
         }
-        let page = attendance_management_service::list_managed_attendance(
+        let mut page = attendance_management_service::list_managed_attendance(
             &db,
             tenant_id,
             &scope,
             from_date,
             to_date,
             employee_search.as_deref(),
             employee_id,
             first,
             after.as_deref(),
         )
         .await
         .map_err(KabiPayError::into_graphql)?;
+        let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id).await.map_err(KabiPayError::into_graphql)?;
+        let now = chrono::Utc::now();
+        let mut projected: Vec<_> = page.rows.iter().map(|row| row.attendance.clone()).collect();
+        crate::services::attendance_day_runtime::project_rows(&db, tenant_id, clock, &mut projected, now)
+            .await.map_err(KabiPayError::into_graphql)?;
+        for (row, attendance) in page.rows.iter_mut().zip(projected) { row.attendance = attendance; }
         Ok(ManagedAttendanceConnectionDto {
             edges: page
                 .rows
                 .into_iter()
                 .map(|row| {
                     let cursor = attendance_management_service::AttendanceCursor::new(
                         row.attendance.work_date,
                         row.attendance.created_at,
                         row.attendance.id,
                     )
@@ -393,22 +444,26 @@ impl QueryRoot {
     ) -> Result<PunchDaySummaryDto> {
         let tenant_id = require_tenant_id(ctx)?;
         attendance_read_scope(ctx)?;
         let db = tenant_db(ctx, tenant_id).await?;
         let employee_id = resolve_client_employee_id(ctx, &db, tenant_id)
             .await
             .map_err(KabiPayError::into_graphql)?;
         let clock = TenantBusinessClock::load(ops_db(ctx)?, tenant_id)
             .await
             .map_err(KabiPayError::into_graphql)?;
-        let date = work_date.unwrap_or_else(|| clock.now_date());
-        let s = attendance_service::punch_day_summary(&db, tenant_id, employee_id, date)
+        let date = match work_date {
+            Some(date) => date,
+            None => crate::services::attendance_day::current_window(&db, tenant_id, clock, chrono::Utc::now())
+                .await.map_err(KabiPayError::into_graphql)?.work_date,
+        };
+        let s = attendance_service::punch_day_summary(&db, tenant_id, employee_id, date, clock)
             .await
             .map_err(KabiPayError::into_graphql)?;
         Ok(s.into())
     }
 
     /// Holidays on or after `fromDate` (defaults to today), all calendars in the tenant.
     async fn upcoming_holidays(
         &self,
         ctx: &Context<'_>,
         from_date: Option<NaiveDate>,
@@ -702,20 +757,38 @@ mod tests {
     async fn execute_query(claims: ClientClaims, query: &str) -> async_graphql::Response {
         let tenant_id = claims.tenant_id;
         Schema::build(QueryRoot, EmptyMutation, EmptySubscription)
             .data(TenantId(tenant_id))
             .data(claims)
             .finish()
             .execute(Request::new(query))
             .await
     }
 
+    #[tokio::test]
+    async fn attendance_day_settings_and_preview_require_all_but_window_accepts_scoped_read() {
+        let permission = kabipay_common::context::PERM_ATTENDANCE_PUNCH_POLICY;
+        for query in [
+            "{ attendanceDayPolicy { revision } }",
+            "{ previewAttendanceDayPolicy(input: { boundaryTime: \"06:00\", effectiveWorkDate: \"2026-09-15\", expectedRevision: 1 }) { revision transition { startsAt endsAt } } }",
+        ] {
+            for scope in [None, Some("SELF"), Some("TEAM"), Some("ALL")] {
+                let result = execute_query(claims(permission, scope), query).await;
+                assert_eq!(result.errors.len(), 1);
+                let code = result.errors[0].extensions.as_ref().and_then(|e| e.get("code")).cloned();
+                assert_eq!(code, Some(async_graphql::Value::from(if scope == Some("ALL") { "INTERNAL_ERROR" } else { "FORBIDDEN" })), "{result:?}");
+            }
+        }
+        let result = execute_query(claims(PERM_ATTENDANCE_READ, Some("SELF")), "{ attendanceDayWindow { workDate startsAt endsAt timezone boundaryMinutes } }").await;
+        assert_eq!(result.errors[0].extensions.as_ref().and_then(|e| e.get("code")).cloned(), Some(async_graphql::Value::from("INTERNAL_ERROR")));
+    }
+
     fn assert_permission_denied_before_db(
         response: &async_graphql::Response,
         permission: &str,
     ) {
         assert_eq!(response.errors.len(), 1, "unexpected response: {response:?}");
         let message = &response.errors[0].message;
         assert!(
             message.contains(&format!("{permission} permission required")),
             "unexpected denial: {message}"
         );
diff --git a/crates/kabipay-attendance/src/resolvers/types.rs b/crates/kabipay-attendance/src/resolvers/types.rs
index 9d9ef3f..41380f5 100644
--- a/crates/kabipay-attendance/src/resolvers/types.rs
+++ b/crates/kabipay-attendance/src/resolvers/types.rs
@@ -18,20 +18,93 @@ use std::future::Future;
 use std::sync::Arc;
 use tokio::sync::OnceCell;
 use uuid::Uuid;
 
 use crate::resolvers::query::parse_uuid;
 use crate::services::timesheet_batch_service::{self, TimesheetApprovalSnapshot};
 
 use crate::services::attendance_service::PunchDaySummary;
 use crate::services::attendance_summary_service::AttendancePeriodSummary;
 
+#[derive(SimpleObject, Clone, Debug)]
+#[graphql(name = "AttendanceDayWindow")]
+pub struct AttendanceDayWindowDto {
+    pub work_date: NaiveDate,
+    pub starts_at: DateTime<Utc>,
+    pub ends_at: DateTime<Utc>,
+    pub timezone: String,
+    pub boundary_minutes: i32,
+}
+impl From<crate::services::attendance_day::AttendanceDayWindow> for AttendanceDayWindowDto {
+    fn from(w: crate::services::attendance_day::AttendanceDayWindow) -> Self {
+        Self { work_date: w.work_date, starts_at: w.starts_at, ends_at: w.ends_at,
+            timezone: w.timezone, boundary_minutes: w.boundary_minutes }
+    }
+}
+#[derive(SimpleObject, Clone, Debug)]
+#[graphql(name = "AttendanceDayPolicyVersion")]
+pub struct AttendanceDayPolicyVersionDto {
+    pub effective_work_date: NaiveDate,
+    pub boundary_minutes: i32,
+    pub timezone: String,
+}
+impl From<crate::services::attendance_day::PolicyVersion> for AttendanceDayPolicyVersionDto {
+    fn from(v: crate::services::attendance_day::PolicyVersion) -> Self {
+        Self { effective_work_date: v.effective_work_date, boundary_minutes: v.boundary_minutes, timezone: v.timezone }
+    }
+}
+#[derive(SimpleObject, Clone, Debug)]
+#[graphql(name = "AttendanceDayPolicy")]
+pub struct AttendanceDayPolicyDto {
+    pub revision: i64,
+    pub initialized: bool,
+    pub legacy_activation_pending: bool,
+    pub legacy_activation_date: Option<NaiveDate>,
+    pub current_policy: AttendanceDayPolicyVersionDto,
+    pub pending_policy: Option<AttendanceDayPolicyVersionDto>,
+    pub current_window: AttendanceDayWindowDto,
+}
+impl AttendanceDayPolicyDto {
+    pub fn from_state(state: crate::services::attendance_day::AttendanceDayPolicy, now: DateTime<Utc>) -> kabipay_common::KabiPayResult<Self> {
+        let current = crate::services::attendance_day::resolve_current_window(&state.versions, now)?;
+        let current_policy = state.versions.iter().find(|v| v.id == current.policy_version_id).cloned()
+            .ok_or_else(|| KabiPayError::Internal("attendance active policy missing".into()))?;
+        let pending_policy = state.versions.iter().find(|v| v.effective_work_date > current.work_date).cloned();
+        Ok(Self { revision: state.revision, initialized: state.initialized,
+            legacy_activation_pending: state.legacy_activation_pending,
+            legacy_activation_date: state.legacy_activation_date,
+            current_policy: current_policy.into(), pending_policy: pending_policy.map(Into::into), current_window: current.into() })
+    }
+}
+#[derive(InputObject, Clone, Debug)]
+pub struct ScheduleAttendanceDayPolicyInput {
+    /// Tenant-local time in strict HH:mm format.
+    pub boundary_time: String,
+    pub effective_work_date: NaiveDate,
+    pub expected_revision: i64,
+}
+impl ScheduleAttendanceDayPolicyInput {
+    pub fn command(&self) -> kabipay_common::KabiPayResult<crate::services::attendance_day::SchedulePolicyCommand> {
+        Ok(crate::services::attendance_day::SchedulePolicyCommand {
+            expected_revision: self.expected_revision, effective_work_date: self.effective_work_date,
+            boundary_minutes: crate::services::attendance_day::parse_boundary_minutes(&self.boundary_time)?,
+        })
+    }
+}
+#[derive(SimpleObject, Clone, Debug)]
+#[graphql(name = "AttendanceDayPolicyPreview")]
+pub struct AttendanceDayPolicyPreviewDto {
+    pub revision: i64,
+    pub transition: AttendanceDayWindowDto,
+    pub following: AttendanceDayWindowDto,
+}
+
 #[derive(SimpleObject, Clone, Debug)]
 #[graphql(name = "AttendancePeriodSummary")]
 pub struct AttendancePeriodSummaryDto {
     pub completed_minutes: i32,
     pub worked_days: i32,
     pub average_minutes: Option<f64>,
     pub incomplete_segments: i32,
 }
 
 impl From<AttendancePeriodSummary> for AttendancePeriodSummaryDto {
@@ -270,62 +343,74 @@ impl From<AttendanceReportSummary> for AttendanceReportSummaryDto {
     }
 }
 
 /// Optional client GPS (browser / mobile) for the **current** punch (in or out).
 #[derive(InputObject, Clone, Debug)]
 pub struct PunchTodayInput {
     pub latitude: Option<f64>,
     pub longitude: Option<f64>,
 }
 
-/// Log a **completed** check-in and check-out for a **past or today** `workDate` when both
-/// live punches were missed. Same calendar day only: check-in time must be before check-out.
+/// Log a completed interval inside a historical/current attendance window.
+/// Supply both actual dates for after-midnight or otherwise ambiguous wall times.
 #[derive(InputObject, Clone, Debug)]
 pub struct AddManualAttendanceSegmentInput {
+    pub check_in_date: Option<NaiveDate>,
+    pub check_out_date: Option<NaiveDate>,
     pub work_date: NaiveDate,
     pub check_in_time: NaiveTime,
     pub check_out_time: NaiveTime,
 }
 
-/// Update an existing completed attendance segment after client-side review.
+/// Correct the original completed or incomplete segment after client-side review.
 #[derive(InputObject, Clone, Debug)]
 pub struct UpdateManualAttendanceSegmentInput {
+    pub check_in_date: Option<NaiveDate>,
+    pub check_out_date: Option<NaiveDate>,
     pub id: ID,
     pub work_date: NaiveDate,
     pub check_in_time: NaiveTime,
     pub check_out_time: NaiveTime,
 }
 
 #[derive(InputObject, Clone, Debug)]
 pub struct AddManagedAttendanceSegmentInput {
+    pub check_in_date: Option<NaiveDate>,
+    pub check_out_date: Option<NaiveDate>,
     pub employee_id: ID,
     pub work_date: NaiveDate,
     pub check_in_time: NaiveTime,
     pub check_out_time: NaiveTime,
     pub reason: String,
 }
 
 #[derive(InputObject, Clone, Debug)]
 pub struct UpdateManagedAttendanceSegmentInput {
+    pub check_in_date: Option<NaiveDate>,
+    pub check_out_date: Option<NaiveDate>,
     pub id: ID,
     pub work_date: NaiveDate,
     pub check_in_time: NaiveTime,
     pub check_out_time: NaiveTime,
     pub reason: String,
     pub expected_updated_at: DateTime<Utc>,
 }
 
 /// One work day: all punch segments + sum of completed segment lengths (minutes).
 #[derive(SimpleObject, Clone, Debug)]
 #[graphql(name = "PunchDaySummary")]
 pub struct PunchDaySummaryDto {
     pub work_date: NaiveDate,
+    pub starts_at: DateTime<Utc>,
+    pub ends_at: DateTime<Utc>,
+    pub timezone: String,
+    pub boundary_minutes: i32,
     /// Sum of (check out − check in) for every **completed** segment that day.
     pub total_worked_minutes: i32,
     /// Current in-progress row (punched in, not out), if any.
     pub open_segment: Option<AttendanceDto>,
     /// All segment rows for that day, oldest first.
     pub segments: Vec<AttendanceDto>,
 }
 
 /// A holiday in a location calendar, with the parent calendar’s display name.
 #[derive(SimpleObject, Clone, Debug)]
@@ -791,20 +876,24 @@ mod timesheet_approval_snapshot_tests {
             sdl.contains("pendingApprovalStepId: ID"),
             "TimesheetWeekBatch must expose its actionable workflow step: {sdl}"
         );
     }
 }
 
 impl From<PunchDaySummary> for PunchDaySummaryDto {
     fn from(s: PunchDaySummary) -> Self {
         Self {
             work_date: s.work_date,
+            starts_at: s.window.starts_at,
+            ends_at: s.window.ends_at,
+            timezone: s.window.timezone,
+            boundary_minutes: s.window.boundary_minutes,
             total_worked_minutes: s.total_worked_minutes,
             open_segment: s.open_segment.map(AttendanceDto::from),
             segments: s.segments.into_iter().map(AttendanceDto::from).collect(),
         }
     }
 }
 
 #[derive(SimpleObject, Clone, Debug)]
 #[graphql(name = "HolidayCalendar")]
 pub struct HolidayCalendarDto {
diff --git a/crates/kabipay-attendance/src/services/attendance_regularization_service.rs b/crates/kabipay-attendance/src/services/attendance_regularization_service.rs
index 1566459..ae03d18 100644
--- a/crates/kabipay-attendance/src/services/attendance_regularization_service.rs
+++ b/crates/kabipay-attendance/src/services/attendance_regularization_service.rs
@@ -31,20 +31,62 @@ pub struct SegmentTimes {
     pub check_out_time: NaiveTime,
 }
 
 #[derive(Clone, Copy, Debug, Eq, PartialEq)]
 pub struct SegmentInstants {
     pub check_in_at: DateTime<Utc>,
     pub check_out_at: DateTime<Utc>,
 }
 
 impl SegmentTimes {
+    pub fn to_window_instants(
+        self, window: &crate::services::attendance_day::AttendanceDayWindow,
+        actual_dates: Option<(NaiveDate, NaiveDate)>,
+    ) -> KabiPayResult<SegmentInstants> {
+        let clock = TenantBusinessClock::from_name(&window.timezone)?;
+        let contained = |instants: SegmentInstants| {
+            instants.check_in_at >= window.starts_at && instants.check_in_at < window.ends_at
+                && instants.check_out_at > instants.check_in_at && instants.check_out_at <= window.ends_at
+        };
+        if let Some((check_in_date, check_out_date)) = actual_dates {
+            let instants = SegmentInstants {
+                check_in_at: clock.to_utc(check_in_date, self.check_in_time)?,
+                check_out_at: clock.to_utc(check_out_date, self.check_out_time)?,
+            };
+            return if contained(instants) { Ok(instants) } else {
+                Err(KabiPayError::Validation("attendance interval must be contained in its attendance day window".into()))
+            };
+        }
+        // With no actual dates, retain only an unambiguous interval. Transition
+        // windows can contain the same wall time on two dates; never guess.
+        let start_date = clock.business_date(window.starts_at);
+        let end_date = clock.business_date(window.ends_at);
+        let mut dates = vec![start_date];
+        let mut date = start_date;
+        while date < end_date {
+            date = date.succ_opt().ok_or_else(|| KabiPayError::Validation("attendance date overflow".into()))?;
+            dates.push(date);
+        }
+        let mut candidates = Vec::new();
+        for start in &dates {
+            for end in &dates {
+                if let (Ok(check_in_at), Ok(check_out_at)) = (clock.to_utc(*start, self.check_in_time), clock.to_utc(*end, self.check_out_time)) {
+                    let instants = SegmentInstants { check_in_at, check_out_at };
+                    if contained(instants) { candidates.push(instants); }
+                }
+            }
+        }
+        if candidates.len() != 1 {
+            return Err(KabiPayError::Validation("provide actual check-in and checkout dates for an unambiguous interval inside the attendance window".into()));
+        }
+        Ok(candidates[0])
+    }
     /// Builds an employee-entered or HR-entered segment using the precision exposed by the UI.
     /// Live punch instants remain second-precise; manual boundaries are intentionally minute-precise.
     pub fn for_manual_input(
         work_date: NaiveDate,
         check_in_time: NaiveTime,
         check_out_time: NaiveTime,
     ) -> Self {
         Self {
             work_date,
             check_in_time: truncate_to_minute(check_in_time),
@@ -71,36 +113,36 @@ fn truncate_to_minute(time: NaiveTime) -> NaiveTime {
     NaiveTime::from_hms_opt(time.hour(), time.minute(), 0)
         .expect("hour and minute from NaiveTime are always valid")
 }
 
 #[derive(Clone, Debug)]
 pub struct ManagedCreateCommand {
     pub tenant_id: Uuid,
     pub target_employee_id: Uuid,
     pub actor_user_id: Uuid,
     pub segment: SegmentTimes,
-    pub instants: SegmentInstants,
-    pub today: NaiveDate,
+    pub clock: TenantBusinessClock,
+    pub actual_dates: Option<(NaiveDate, NaiveDate)>,
     pub reason: String,
     pub request_id: Option<String>,
 }
 
 #[derive(Clone, Debug)]
 pub(crate) struct ManagedUpdateCommand {
     pub tenant_id: Uuid,
     pub attendance_id: Uuid,
     pub target_employee_id: Uuid,
     pub actor_user_id: Uuid,
     pub initial_work_date: NaiveDate,
     pub segment: SegmentTimes,
-    pub instants: SegmentInstants,
-    pub today: NaiveDate,
+    pub clock: TenantBusinessClock,
+    pub actual_dates: Option<(NaiveDate, NaiveDate)>,
     pub reason: String,
     pub request_id: Option<String>,
     pub expected_updated_at: DateTime<Utc>,
 }
 
 #[derive(Clone, Debug, Eq, PartialEq)]
 enum AttendanceAuditOperation {
     Create,
     Update,
 }
@@ -125,39 +167,41 @@ struct AttendanceAuditInsert {
     before_values: Option<Value>,
     after_values: Value,
     request_id: Option<String>,
     created_at: DateTime<Utc>,
 }
 
 #[derive(Clone, Debug, Serialize)]
 pub struct AttendanceAuditSnapshot {
     pub work_date: NaiveDate,
     pub check_in_time: NaiveTime,
-    pub check_out_time: NaiveTime,
+    pub check_out_time: Option<NaiveTime>,
+    pub check_in_at: Option<DateTime<Utc>>,
+    pub check_out_at: Option<DateTime<Utc>>,
     pub status: String,
     pub source: String,
     pub regularization_status: Option<String>,
     pub updated_at: DateTime<Utc>,
 }
 
 impl TryFrom<&attendance::Model> for AttendanceAuditSnapshot {
     type Error = KabiPayError;
 
     fn try_from(row: &attendance::Model) -> Result<Self, Self::Error> {
         Ok(Self {
             work_date: row.work_date,
             check_in_time: row.check_in_time.ok_or_else(|| {
                 KabiPayError::Validation("attendance segment has no check-in time".into())
             })?,
-            check_out_time: row.check_out_time.ok_or_else(|| {
-                KabiPayError::Validation("attendance segment has no check-out time".into())
-            })?,
+            check_out_time: row.check_out_time,
+            check_in_at: row.check_in_at,
+            check_out_at: row.check_out_at,
             status: row.status.clone().ok_or_else(|| {
                 KabiPayError::Validation("attendance segment has no status".into())
             })?,
             source: row.source.clone().ok_or_else(|| {
                 KabiPayError::Validation("attendance segment has no source".into())
             })?,
             regularization_status: row.regularization_status.clone(),
             updated_at: row.updated_at,
         })
     }
@@ -187,151 +231,118 @@ pub(crate) fn assert_locked_attendance_identity(
     current_work_date: NaiveDate,
 ) -> KabiPayResult<()> {
     if current_employee_id != locked_employee_id || current_work_date != locked_work_date {
         return Err(KabiPayError::Conflict(
             "attendance segment changed while acquiring locks; refresh before retrying".into(),
         ));
     }
     Ok(())
 }
 
-fn segment_minutes(check_in_time: NaiveTime, check_out_time: NaiveTime) -> KabiPayResult<i32> {
-    if check_in_time >= check_out_time {
-        return Err(KabiPayError::Validation(
-            "checkInTime must be before checkOutTime (same-day segment only)".into(),
-        ));
-    }
-    let seconds = i64::from(check_out_time.num_seconds_from_midnight())
-        - i64::from(check_in_time.num_seconds_from_midnight());
-    i32::try_from(seconds / 60)
-        .map_err(|_| KabiPayError::Internal("attendance segment duration overflow".into()))
-}
-
 pub(crate) fn assert_total_attendance_minutes_under_daily_cap(
     total_minutes: i32,
 ) -> KabiPayResult<()> {
     if total_minutes >= MAX_DAY_MINUTES {
         return Err(KabiPayError::Validation(
             "total attendance for a day must be less than 24 hours".into(),
         ));
     }
     Ok(())
 }
 
-fn validate_segment_date_and_time(segment: SegmentTimes, today: NaiveDate) -> KabiPayResult<i32> {
-    if segment.work_date > today {
-        return Err(KabiPayError::Validation(
-            "workDate cannot be in the future".into(),
-        ));
-    }
-    segment_minutes(segment.check_in_time, segment.check_out_time)
-}
-
+#[cfg(test)]
 fn validate_segment_against_rows(
-    segment: SegmentTimes,
-    today: NaiveDate,
-    max_self_adjust_days: i64,
-    existing: &[attendance::Model],
-    excluded_attendance_id: Option<Uuid>,
+    segment: SegmentTimes, today: NaiveDate, max_self_adjust_days: i64,
+    existing: &[attendance::Model], excluded_attendance_id: Option<Uuid>,
     bypass_self_service_age_window: bool,
 ) -> KabiPayResult<()> {
-    let requested_minutes = validate_segment_date_and_time(segment, today)?;
-    let days_since = today.signed_duration_since(segment.work_date).num_days();
-    let window = max_self_adjust_days.max(0);
-    if days_since > window && !bypass_self_service_age_window {
-        return Err(KabiPayError::Forbidden(format!(
-            "manual attendance is limited to the last {} calendar days unless you hold attendance regularization permission",
-            window
-        )));
-    }
-
-    let mut total_minutes = requested_minutes;
-    for row in existing {
-        if excluded_attendance_id == Some(row.id) {
-            continue;
-        }
-        match (row.check_in_time, row.check_out_time) {
-            (Some(stored_in), Some(stored_out)) => {
-                let is_manual = row
-                    .source
-                    .as_deref()
-                    .is_some_and(|source| {
-                        source
-                            .trim()
-                            .eq_ignore_ascii_case(MANUAL_ATTENDANCE_SOURCE)
-                    });
-                let (existing_in, existing_out) = if is_manual {
-                    (truncate_to_minute(stored_in), truncate_to_minute(stored_out))
-                } else {
-                    (stored_in, stored_out)
-                };
-                if segment.check_in_time < existing_out && segment.check_out_time > existing_in {
-                    return Err(KabiPayError::Validation(
-                        "manual attendance overlaps with an existing segment for this day".into(),
-                    ));
-                }
-                total_minutes = total_minutes
-                    .checked_add(segment_minutes(existing_in, existing_out)?)
-                    .ok_or_else(|| {
-                        KabiPayError::Internal("attendance daily duration overflow".into())
-                    })?;
-            }
-            (Some(_), None) => {
-                return Err(KabiPayError::Validation(
-                    "complete the open punch before adjusting manual attendance for this day"
-                        .into(),
-                ));
-            }
-            _ => {}
-        }
-    }
-    assert_total_attendance_minutes_under_daily_cap(total_minutes)
+    let clock = TenantBusinessClock::from_name("UTC")?;
+    let instants = segment.to_instants(clock)?;
+    validate_resolved_segment_against_rows(segment, instants, clock, today,
+        max_self_adjust_days, existing, excluded_attendance_id, bypass_self_service_age_window)
 }
 
-pub(crate) async fn validate_segment_with_connection<C>(
-    db: &C,
+pub(crate) async fn validate_segment_with_connection(
+    db: &DatabaseTransaction,
     tenant_id: Uuid,
     employee_id: Uuid,
     segment: SegmentTimes,
     excluded_attendance_id: Option<Uuid>,
     bypass_self_service_age_window: bool,
-    today: NaiveDate,
-) -> KabiPayResult<()>
-where
-    C: ConnectionTrait,
-{
-    validate_segment_date_and_time(segment, today)?;
+    clock: TenantBusinessClock,
+    actual_dates: Option<(NaiveDate, NaiveDate)>,
+    now: DateTime<Utc>,
+) -> KabiPayResult<SegmentInstants> {
+    let window = super::attendance_day::ensure_window(db, tenant_id, clock, segment.work_date, now).await?;
+    if window.starts_at > now { return Err(KabiPayError::Validation("workDate cannot be in the future".into())); }
+    let instants = segment.to_window_instants(&window, actual_dates)?;
     let policy = hrms_master_service::load_attendance_adjustment_policy(db, tenant_id).await?;
     let existing = attendance::Entity::find()
         .filter(attendance::Column::TenantId.eq(tenant_id))
         .filter(attendance::Column::EmployeeId.eq(employee_id))
         .filter(attendance::Column::WorkDate.eq(segment.work_date))
         .order_by_asc(attendance::Column::CreatedAt)
         .all(db)
         .await?;
-    validate_segment_against_rows(
-        segment,
-        today,
+    validate_resolved_segment_against_rows(
+        segment, instants, TenantBusinessClock::from_name(&window.timezone)?,
+        clock.business_date(now),
         policy.max_self_adjust_days,
         &existing,
         excluded_attendance_id,
         bypass_self_service_age_window,
-    )
+    )?;
+    Ok(instants)
+}
+
+fn validate_resolved_segment_against_rows(
+    segment: SegmentTimes, instants: SegmentInstants, clock: TenantBusinessClock,
+    today: NaiveDate, max_self_adjust_days: i64, existing: &[attendance::Model],
+    excluded_attendance_id: Option<Uuid>, bypass_self_service_age_window: bool,
+) -> KabiPayResult<()> {
+    if segment.work_date > today { return Err(KabiPayError::Validation("workDate cannot be in the future".into())); }
+    if today.signed_duration_since(segment.work_date).num_days() > max_self_adjust_days.max(0)
+        && !bypass_self_service_age_window {
+        return Err(KabiPayError::Forbidden(format!("manual attendance is limited to the last {} calendar days unless you hold attendance regularization permission", max_self_adjust_days.max(0))));
+    }
+    let mut seconds = instants.check_out_at.signed_duration_since(instants.check_in_at).num_seconds();
+    if seconds <= 0 { return Err(KabiPayError::Validation("check-in must precede checkout".into())); }
+    for row in existing.iter().filter(|row| Some(row.id) != excluded_attendance_id) {
+        let mut normalized = row.clone();
+        if row.source.as_deref() == Some(MANUAL_ATTENDANCE_SOURCE) && row.check_in_at.is_none() && row.check_out_at.is_none() {
+            normalized.check_in_time = row.check_in_time.map(truncate_to_minute);
+            normalized.check_out_time = row.check_out_time.map(truncate_to_minute);
+        }
+        match super::attendance_duration::canonical_instants(&normalized, clock) {
+            (Some(start), Some(end)) if end > start => {
+                if instants.check_in_at < end && instants.check_out_at > start {
+                    return Err(KabiPayError::Validation("manual attendance overlaps with an existing segment for this day".into()));
+                }
+                seconds = seconds.checked_add(end.signed_duration_since(start).num_seconds())
+                    .ok_or_else(|| KabiPayError::Internal("attendance daily duration overflow".into()))?;
+            }
+            (Some(_), None) => return Err(KabiPayError::Validation("correct the original incomplete or open punch before adding attendance for this day".into())),
+            _ => {}
+        }
+    }
+    assert_total_attendance_minutes_under_daily_cap(i32::try_from(seconds / 60)
+        .map_err(|_| KabiPayError::Internal("attendance daily duration overflow".into()))?)
 }
 
 /// Acquires transaction-scoped locks for one employee's dates in stable order.
 pub async fn lock_employee_dates(
     txn: &DatabaseTransaction,
     tenant_id: Uuid,
     employee_id: Uuid,
     dates: &[NaiveDate],
 ) -> KabiPayResult<()> {
+    super::attendance_day::lock_policy(txn, tenant_id).await?;
     let mut ordered_dates = dates.to_vec();
     ordered_dates.sort_unstable();
     ordered_dates.dedup();
     for work_date in ordered_dates {
         let key = format!("attendance:{tenant_id}:{employee_id}:{work_date}");
         txn.execute(Statement::from_sql_and_values(
             DbBackend::Postgres,
             "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
             vec![key.into()],
         ))
@@ -422,22 +433,24 @@ trait AttendanceRegularizationStore {
         tenant_id: Uuid,
         attendance_id: Uuid,
     ) -> KabiPayResult<Option<attendance::Model>>;
     async fn validate_segment(
         &mut self,
         tenant_id: Uuid,
         employee_id: Uuid,
         segment: SegmentTimes,
         excluded_attendance_id: Option<Uuid>,
         bypass_self_service_age_window: bool,
-        today: NaiveDate,
-    ) -> KabiPayResult<()>;
+        clock: TenantBusinessClock,
+        actual_dates: Option<(NaiveDate, NaiveDate)>,
+        now: DateTime<Utc>,
+    ) -> KabiPayResult<SegmentInstants>;
     async fn insert_segment(
         &mut self,
         tenant_id: Uuid,
         employee_id: Uuid,
         segment: SegmentTimes,
         instants: SegmentInstants,
         regularization_status: &'static str,
         now: DateTime<Utc>,
     ) -> KabiPayResult<attendance::Model>;
     async fn update_segment(
@@ -473,30 +486,32 @@ impl AttendanceRegularizationStore for DatabaseTransaction {
             .map_err(KabiPayError::from)
     }
 
     async fn validate_segment(
         &mut self,
         tenant_id: Uuid,
         employee_id: Uuid,
         segment: SegmentTimes,
         excluded_attendance_id: Option<Uuid>,
         bypass_self_service_age_window: bool,
-        today: NaiveDate,
-    ) -> KabiPayResult<()> {
+        clock: TenantBusinessClock,
+        actual_dates: Option<(NaiveDate, NaiveDate)>,
+        now: DateTime<Utc>,
+    ) -> KabiPayResult<SegmentInstants> {
         validate_segment_with_connection(
             self,
             tenant_id,
             employee_id,
             segment,
             excluded_attendance_id,
             bypass_self_service_age_window,
-            today,
+            clock, actual_dates, now,
         )
         .await
     }
 
     async fn insert_segment(
         &mut self,
         tenant_id: Uuid,
         employee_id: Uuid,
         segment: SegmentTimes,
         instants: SegmentInstants,
@@ -555,36 +570,36 @@ where
     S: AttendanceRegularizationStore,
 {
     let reason = validate_reason(&command.reason)?;
     store
         .lock_employee_dates(
             command.tenant_id,
             command.target_employee_id,
             &[command.segment.work_date],
         )
         .await?;
-    store
+    let instants = store
         .validate_segment(
             command.tenant_id,
             command.target_employee_id,
             command.segment,
             None,
             true,
-            command.today,
+            command.clock, command.actual_dates, now,
         )
         .await?;
     let created = store
         .insert_segment(
             command.tenant_id,
             command.target_employee_id,
             command.segment,
-            command.instants,
+            instants,
             MANUAL_REGULARIZED,
             now,
         )
         .await?;
     let after_values = serde_json::to_value(AttendanceAuditSnapshot::try_from(&created)?)?;
     store
         .insert_audit(AttendanceAuditInsert {
             tenant_id: command.tenant_id,
             attendance_id: created.id,
             target_employee_id: command.target_employee_id,
@@ -624,36 +639,37 @@ where
     if before.employee_id != command.target_employee_id {
         return Err(KabiPayError::Forbidden(
             ATTENDANCE_MANAGEMENT_ACCESS_DENIED.into(),
         ));
     }
     if before.updated_at != command.expected_updated_at {
         return Err(KabiPayError::Conflict(
             "attendance segment changed; refresh before retrying".into(),
         ));
     }
+    assert_locked_attendance_identity(command.target_employee_id, command.initial_work_date, before.employee_id, before.work_date)?;
     let before_values = serde_json::to_value(AttendanceAuditSnapshot::try_from(&before)?)?;
-    store
+    let instants = store
         .validate_segment(
             command.tenant_id,
             command.target_employee_id,
             command.segment,
             Some(command.attendance_id),
             true,
-            command.today,
+            command.clock, command.actual_dates, now,
         )
         .await?;
     let updated = store
         .update_segment(
             before,
             command.segment,
-            command.instants,
+            instants,
             MANUAL_REGULARIZED,
             now,
         )
         .await?;
     let after_values = serde_json::to_value(AttendanceAuditSnapshot::try_from(&updated)?)?;
     store
         .insert_audit(AttendanceAuditInsert {
             tenant_id: command.tenant_id,
             attendance_id: updated.id,
             target_employee_id: command.target_employee_id,
@@ -667,43 +683,103 @@ where
         })
         .await?;
     Ok(updated)
 }
 
 /// Writes one managed segment and its immutable audit in the caller-owned transaction.
 pub async fn create_managed_attendance_segment_in_transaction(
     txn: &mut DatabaseTransaction,
     command: &ManagedCreateCommand,
 ) -> KabiPayResult<attendance::Model> {
+    lock_employee_dates(txn, command.tenant_id, command.target_employee_id, &[command.segment.work_date]).await?;
     orchestrate_managed_create(txn, command, Utc::now()).await
 }
 
 pub(crate) async fn update_managed_attendance_segment_in_transaction(
     txn: &mut DatabaseTransaction,
     command: &ManagedUpdateCommand,
 ) -> KabiPayResult<attendance::Model> {
+    lock_employee_dates(txn, command.tenant_id, command.target_employee_id, &[command.initial_work_date, command.segment.work_date]).await?;
     orchestrate_managed_update(txn, command, Utc::now()).await
 }
 
 #[cfg(test)]
 mod tests {
     use super::*;
     use chrono::{NaiveDate, NaiveTime, TimeZone, Utc};
     use kabipay_db_entities::tenant::d0010_time_shift_roster::attendance;
     use serde_json::json;
     use uuid::Uuid;
 
     const TENANT_ID: Uuid = Uuid::from_u128(1);
     const EMPLOYEE_ID: Uuid = Uuid::from_u128(2);
     const ACTOR_USER_ID: Uuid = Uuid::from_u128(3);
     const ATTENDANCE_ID: Uuid = Uuid::from_u128(4);
 
+    #[test]
+    fn attendance_day_actual_dates_allow_after_midnight_correction_in_original_window() {
+        let window = crate::services::attendance_day::resolve_window(&[
+            crate::services::attendance_day::PolicyVersion {
+                id: Uuid::from_u128(9), effective_work_date: date(2026, 1, 1),
+                boundary_minutes: 300, timezone: "Asia/Kolkata".into(),
+            }
+        ], date(2026, 9, 11)).unwrap();
+        let segment = SegmentTimes::for_manual_input(date(2026, 9, 11), time(2, 0), time(4, 0));
+        let actual = segment.to_window_instants(&window, Some((date(2026, 9, 12), date(2026, 9, 12)))).unwrap();
+        assert_eq!(actual.check_in_at, "2026-09-11T20:30:00Z".parse::<DateTime<Utc>>().unwrap());
+        assert_eq!(actual.check_out_at, "2026-09-11T22:30:00Z".parse::<DateTime<Utc>>().unwrap());
+        let past_end = SegmentTimes::for_manual_input(date(2026, 9, 11), time(2, 0), time(5, 1));
+        assert!(past_end.to_window_instants(&window, Some((date(2026, 9, 12), date(2026, 9, 12)))).is_err());
+        let at_end = SegmentTimes::for_manual_input(date(2026, 9, 11), time(2, 0), time(5, 0));
+        assert!(at_end.to_window_instants(&window, Some((date(2026, 9, 12), date(2026, 9, 12)))).is_ok());
+    }
+
+    #[test]
+    fn attendance_day_managed_snapshot_accepts_original_incomplete_without_inventing_checkout() {
+        let mut row = attendance_model(date(2026, 8, 24), timestamp(9));
+        row.check_out_time = None;
+        row.status = Some("INCOMPLETE".into());
+        let snapshot = AttendanceAuditSnapshot::try_from(&row).expect("incomplete must be correctable through original ID");
+        let json = serde_json::to_value(snapshot).unwrap();
+        assert!(json["check_out_time"].is_null());
+    }
+
+    #[test]
+    fn attendance_day_actual_intervals_reject_overnight_overlap_and_excess_hours_but_exclude_original_id() {
+        let clock = TenantBusinessClock::from_name("Asia/Kolkata").unwrap();
+        let segment = SegmentTimes::for_manual_input(date(2026, 9, 11), time(2, 0), time(4, 0));
+        let instants = SegmentInstants { check_in_at: "2026-09-11T20:30:00Z".parse().unwrap(), check_out_at: "2026-09-11T22:30:00Z".parse().unwrap() };
+        let mut existing = attendance_model(date(2026, 9, 11), timestamp(9));
+        existing.check_in_at = Some("2026-09-11T19:30:00Z".parse().unwrap());
+        existing.check_out_at = Some("2026-09-11T21:30:00Z".parse().unwrap());
+        assert!(validate_resolved_segment_against_rows(segment, instants, clock, date(2026, 9, 12), 5, &[existing.clone()], None, false).is_err());
+        assert!(validate_resolved_segment_against_rows(segment, instants, clock, date(2026, 9, 12), 5, &[existing], Some(ATTENDANCE_ID), false).is_ok());
+        assert!(matches!(validate_resolved_segment_against_rows(segment, instants, clock, date(2026, 9, 20), 5, &[], None, false), Err(KabiPayError::Forbidden(_))));
+        let too_long = SegmentInstants { check_in_at: "2026-09-10T23:30:00Z".parse().unwrap(), check_out_at: "2026-09-11T23:30:00Z".parse().unwrap() };
+        assert!(validate_resolved_segment_against_rows(segment, too_long, clock, date(2026, 9, 12), 5, &[], None, true).is_err());
+    }
+
+    #[test]
+    fn attendance_day_legacy_inputs_remain_unambiguous_and_long_transition_requires_actual_dates() {
+        let policy = |date, boundary| crate::services::attendance_day::PolicyVersion {
+            id: Uuid::new_v4(), effective_work_date: date, boundary_minutes: boundary, timezone: "Asia/Kolkata".into(),
+        };
+        let legacy = crate::services::attendance_day::resolve_window(&[policy(date(2026, 1, 1), 0)], date(2026, 9, 11)).unwrap();
+        let segment = SegmentTimes::for_manual_input(date(2026, 9, 11), time(2, 0), time(4, 0));
+        assert_eq!(segment.to_window_instants(&legacy, None).unwrap().check_in_at, "2026-09-10T20:30:00Z".parse::<DateTime<Utc>>().unwrap());
+        assert!(SegmentTimes::for_manual_input(date(2026, 9, 11), time(23, 0), time(4, 0)).to_window_instants(&legacy, None).is_err());
+        let transition = crate::services::attendance_day::resolve_window(&[policy(date(2026, 1, 1), 300), policy(date(2026, 9, 11), 360)], date(2026, 9, 11)).unwrap();
+        let ambiguous = SegmentTimes::for_manual_input(date(2026, 9, 11), time(5, 10), time(5, 20));
+        assert!(ambiguous.to_window_instants(&transition, None).is_err());
+        assert!(ambiguous.to_window_instants(&transition, Some((date(2026, 9, 12), date(2026, 9, 12)))).is_ok());
+    }
+
     fn date(year: i32, month: u32, day: u32) -> NaiveDate {
         NaiveDate::from_ymd_opt(year, month, day).expect("test date must be valid")
     }
 
     fn time(hour: u32, minute: u32) -> NaiveTime {
         NaiveTime::from_hms_opt(hour, minute, 0).expect("test time must be valid")
     }
 
     fn timestamp(hour: u32) -> chrono::DateTime<Utc> {
         Utc.with_ymd_and_hms(2026, 8, 24, hour, 0, 0)
@@ -758,20 +834,22 @@ mod tests {
 
         let snapshot = AttendanceAuditSnapshot::try_from(&row).expect("valid snapshot");
         let serialized = serde_json::to_value(snapshot).expect("snapshot must serialize");
 
         assert_eq!(
             serialized,
             json!({
                 "work_date": "2026-08-20",
                 "check_in_time": "09:00:00",
                 "check_out_time": "17:00:00",
+                "check_in_at": null,
+                "check_out_at": null,
                 "status": "COMPLETE",
                 "source": "WEB+MANUAL",
                 "regularization_status": "SELF_REPORTED",
                 "updated_at": "2026-08-24T12:00:00Z"
             })
         );
     }
 
     #[test]
     fn moved_segment_dates_are_sorted_and_deduplicated_before_locking() {
@@ -990,29 +1068,31 @@ mod tests {
             _attendance_id: Uuid,
         ) -> kabipay_common::KabiPayResult<Option<attendance::Model>> {
             self.operations.push(Operation::Load);
             Ok(self.row.clone())
         }
 
         async fn validate_segment(
             &mut self,
             _tenant_id: Uuid,
             _employee_id: Uuid,
-            _segment: SegmentTimes,
+            segment: SegmentTimes,
             _excluded_attendance_id: Option<Uuid>,
             bypass_self_service_age_window: bool,
-            _today: NaiveDate,
-        ) -> kabipay_common::KabiPayResult<()> {
+            clock: TenantBusinessClock,
+            _actual_dates: Option<(NaiveDate, NaiveDate)>,
+            _now: DateTime<Utc>,
+        ) -> kabipay_common::KabiPayResult<SegmentInstants> {
             self.operations.push(Operation::Validate {
                 bypass_self_service_age_window,
             });
-            Ok(())
+            segment.to_instants(clock)
         }
 
         async fn insert_segment(
             &mut self,
             tenant_id: Uuid,
             employee_id: Uuid,
             segment: SegmentTimes,
             instants: SegmentInstants,
             regularization_status: &'static str,
             now: chrono::DateTime<Utc>,
@@ -1065,24 +1145,22 @@ mod tests {
             check_in_time: time(10, 0),
             check_out_time: time(18, 0),
         };
         ManagedUpdateCommand {
             tenant_id: TENANT_ID,
             attendance_id: ATTENDANCE_ID,
             target_employee_id: EMPLOYEE_ID,
             actor_user_id: ACTOR_USER_ID,
             initial_work_date: date(2026, 8, 24),
             segment,
-            instants: segment
-                .to_instants(TenantBusinessClock::from_name("UTC").unwrap())
-                .unwrap(),
-            today: date(2026, 8, 24),
+            clock: TenantBusinessClock::from_name("UTC").unwrap(),
+            actual_dates: None,
             reason: "  approved payroll correction  ".into(),
             request_id: Some("request-123".into()),
             expected_updated_at,
         }
     }
 
     #[tokio::test]
     async fn stale_managed_update_returns_conflict_before_attendance_or_audit_write() {
         let current_updated_at = timestamp(12);
         let mut store = FakeStore::new(Some(attendance_model(
@@ -1113,24 +1191,22 @@ mod tests {
         let segment = SegmentTimes {
             work_date: date(2026, 8, 20),
             check_in_time: time(9, 30),
             check_out_time: time(17, 30),
         };
         let command = ManagedCreateCommand {
             tenant_id: TENANT_ID,
             target_employee_id: EMPLOYEE_ID,
             actor_user_id: ACTOR_USER_ID,
             segment,
-            instants: segment
-                .to_instants(TenantBusinessClock::from_name("UTC").unwrap())
-                .unwrap(),
-            today: date(2026, 8, 24),
+            clock: TenantBusinessClock::from_name("UTC").unwrap(),
+            actual_dates: None,
             reason: "  approved missed punch  ".into(),
             request_id: Some("request-123".into()),
         };
 
         let created = orchestrate_managed_create(&mut store, &command, timestamp(13))
             .await
             .expect("managed create must succeed");
 
         assert_eq!(created.regularization_status.as_deref(), Some("REGULARIZED"));
         assert!(matches!(
diff --git a/crates/kabipay-attendance/src/services/attendance_service.rs b/crates/kabipay-attendance/src/services/attendance_service.rs
index 80ddc79..4f95b5a 100644
--- a/crates/kabipay-attendance/src/services/attendance_service.rs
+++ b/crates/kabipay-attendance/src/services/attendance_service.rs
@@ -24,27 +24,20 @@ use uuid::Uuid;
 
 use crate::services::{
     attendance_regularization_service::{
         assert_locked_attendance_identity, insert_manual_segment, lock_employee_dates,
         update_manual_segment,
         validate_segment_with_connection, SegmentTimes,
         MANUAL_SELF_REPORTED,
     },
     timesheet_dates, timesheet_policy,
 };
-fn attendance_business_date_time(
-    now_utc: DateTime<Utc>,
-    clock: TenantBusinessClock,
-) -> (NaiveDate, NaiveTime) {
-    (clock.business_date(now_utc), clock.local_time(now_utc))
-}
-
 pub async fn list_shifts(
     db: &DatabaseConnection,
     tenant_id: Uuid,
     limit: u64,
 ) -> KabiPayResult<Vec<shift::Model>> {
     let limit = limit.clamp(1, 200);
     shift::Entity::find()
         .filter(shift::Column::TenantId.eq(tenant_id))
         .order_by_asc(shift::Column::Name)
         .limit(limit)
@@ -172,97 +165,97 @@ pub async fn list_employee_attendance_on_date(
         .order_by_asc(attendance::Column::CreatedAt)
         .all(db)
         .await
         .map_err(KabiPayError::from)
 }
 
 /// Aggregated stats for a day: sum of (check-out − check-in) for every completed
 /// segment, plus the current open segment (checked in, not out) if any.
 pub struct PunchDaySummary {
     pub work_date: NaiveDate,
+    pub window: super::attendance_day::AttendanceDayWindow,
     pub total_worked_minutes: i32,
     pub open_segment: Option<attendance::Model>,
     pub segments: Vec<attendance::Model>,
 }
 
 pub async fn punch_day_summary(
     db: &DatabaseConnection,
     tenant_id: Uuid,
     employee_id: Uuid,
     work_date: NaiveDate,
+    clock: TenantBusinessClock,
 ) -> KabiPayResult<PunchDaySummary> {
-    let segments = list_employee_attendance_on_date(db, tenant_id, employee_id, work_date).await?;
+    let now = Utc::now();
+    let window = super::attendance_day::window_for_date(db, tenant_id, clock, work_date, now).await?;
+    let mut segments = list_employee_attendance_on_date(db, tenant_id, employee_id, work_date).await?;
+    for row in &mut segments { super::attendance_day_runtime::derive_expiry(row, &window, now); }
     let total = segments.iter().map(attendance_segment_minutes).sum();
     let open_segment = segments
         .iter()
         .filter(|r| {
             r.status.as_deref() == Some("OPEN")
                 && (r.check_in_at.is_some() || r.check_in_time.is_some())
                 && r.check_out_at.is_none()
                 && r.check_out_time.is_none()
         })
         .max_by_key(|r| r.created_at)
         .cloned();
     Ok(PunchDaySummary {
         work_date,
+        window,
         total_worked_minutes: total,
         open_segment,
         segments,
     })
 }
 
 /// **Multi-segment punch:** each pair (punch in → punch out) is a separate `attendance` row
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
     clock: TenantBusinessClock,
     geo: Option<PunchGeo>,
     client_ip: Option<&str>,
+) -> KabiPayResult<attendance::Model> {
+    punch_today_with_clock(db, tenant_id, employee_id, clock, geo, client_ip, Utc::now).await
+}
+
+pub(crate) async fn punch_today_with_clock(
+    db: &DatabaseConnection, tenant_id: Uuid, employee_id: Uuid,
+    clock: TenantBusinessClock, geo: Option<PunchGeo>, client_ip: Option<&str>,
+    mut now: impl FnMut() -> DateTime<Utc>,
 ) -> KabiPayResult<attendance::Model> {
     let policy = crate::services::punch_policy::find_punch_policy(db, tenant_id).await?;
     let lat_lng = geo.as_ref().map(|g| (g.lat, g.lng));
     crate::services::punch_policy::validate_live_punch_for_policy(
         policy.as_ref(),
         lat_lng,
         client_ip,
     )?;
 
-    let now_ts = Utc::now();
-    let (today, now_t) = attendance_business_date_time(now_ts, clock);
     let source = if geo.is_some() { "WEB+GPS" } else { "WEB" };
     let txn = db.begin().await?;
-    // Retain missed punch-outs without inventing working time. The database permits
-    // one OPEN row per employee, so retire earlier days before opening today's row.
-    let stale = attendance::Entity::find()
-        .filter(attendance::Column::TenantId.eq(tenant_id))
-        .filter(attendance::Column::EmployeeId.eq(employee_id))
-        .filter(attendance::Column::WorkDate.lt(today))
-        .filter(attendance::Column::Status.eq("OPEN"))
-        .all(&txn).await?;
-    let mut dates: Vec<_> = stale.iter().map(|row| row.work_date).collect();
-    dates.push(today);
-    lock_employee_dates(&txn, tenant_id, employee_id, &dates).await?;
-    attendance::Entity::update_many()
-        .col_expr(attendance::Column::Status, sea_orm::sea_query::Expr::value("INCOMPLETE"))
-        .col_expr(attendance::Column::UpdatedAt, sea_orm::sea_query::Expr::value(now_ts))
-        .filter(attendance::Column::TenantId.eq(tenant_id))
-        .filter(attendance::Column::EmployeeId.eq(employee_id))
-        .filter(attendance::Column::WorkDate.lt(today))
-        .filter(attendance::Column::Status.eq("OPEN"))
-        .exec(&txn).await?;
+    let (window, now_ts) = super::attendance_day_runtime::lock_current_window(
+        &txn, tenant_id, employee_id, clock, &mut now,
+    ).await?;
+    let today = window.work_date;
+    let window_clock = TenantBusinessClock::from_name(&window.timezone)?;
+    let now_t = window_clock.local_time(now_ts);
+    super::attendance_day_runtime::expire_employee(&txn, tenant_id, employee_id, clock, now_ts).await?;
     let open = open_punch_on_date(tenant_id, employee_id, today)
         .one(&txn)
         .await?;
 
     if let Some(row) = open {
         let existing = attendance::Entity::find()
             .filter(attendance::Column::TenantId.eq(tenant_id))
             .filter(attendance::Column::EmployeeId.eq(employee_id))
             .filter(attendance::Column::WorkDate.eq(row.work_date))
             .all(&txn)
@@ -330,56 +323,56 @@ pub async fn punch_today(
         updated_at: Set(now_ts),
     };
     am.insert(&txn).await?;
     txn.commit().await?;
     attendance::Entity::find_by_id(id)
         .one(db)
         .await?
         .ok_or_else(|| KabiPayError::Internal("attendance row missing after insert".into()))
 }
 
-/// One completed in→out **segment** for a chosen `work_date` when the user missed live punches
-/// (e.g. forgot to open the app). **Same calendar day** only — night shifts that span midnight
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
+    actual_dates: Option<(NaiveDate, NaiveDate)>,
 ) -> KabiPayResult<attendance::Model> {
     let segment = SegmentTimes::for_manual_input(work_date, check_in_time, check_out_time);
-    let instants = segment.to_instants(clock)?;
-    let today = clock.now_date();
     let txn = db.begin().await?;
     lock_employee_dates(&txn, tenant_id, employee_id, &[work_date]).await?;
-    validate_segment_with_connection(
+    let now = Utc::now();
+    let instants = validate_segment_with_connection(
         &txn,
         tenant_id,
         employee_id,
         segment,
         None,
         false,
-        today,
+        clock, actual_dates, now,
     )
     .await?;
     let created = insert_manual_segment(
         &txn,
         tenant_id,
         employee_id,
         segment,
         instants,
         MANUAL_SELF_REPORTED,
-        Utc::now(),
+        now,
     )
     .await?;
     txn.commit().await?;
     Ok(created)
 }
 
 fn open_punch_on_date(tenant_id: Uuid, employee_id: Uuid, work_date: NaiveDate) -> sea_orm::Select<attendance::Entity> {
     attendance::Entity::find()
         .filter(attendance::Column::TenantId.eq(tenant_id))
         .filter(attendance::Column::EmployeeId.eq(employee_id))
@@ -392,40 +385,40 @@ fn open_punch_on_date(tenant_id: Uuid, employee_id: Uuid, work_date: NaiveDate)
 
 pub async fn update_manual_attendance_segment(
     db: &DatabaseConnection,
     tenant_id: Uuid,
     attendance_id: Uuid,
     requesting_employee_id: Uuid,
     clock: TenantBusinessClock,
     work_date: NaiveDate,
     check_in_time: NaiveTime,
     check_out_time: NaiveTime,
+    actual_dates: Option<(NaiveDate, NaiveDate)>,
 ) -> KabiPayResult<attendance::Model> {
     let txn = db.begin().await?;
+    super::attendance_day::lock_policy(&txn, tenant_id).await?;
     let row = attendance::Entity::find_by_id(attendance_id)
         .filter(attendance::Column::TenantId.eq(tenant_id))
         .one(&txn)
         .await?
         .ok_or_else(|| KabiPayError::NotFound {
             entity: "attendance",
             id: attendance_id.to_string(),
         })?;
 
     if row.employee_id != requesting_employee_id {
         return Err(KabiPayError::Forbidden(
             "attendance segment belongs to another employee".into(),
         ));
     }
 
     let segment = SegmentTimes::for_manual_input(work_date, check_in_time, check_out_time);
-    let instants = segment.to_instants(clock)?;
-    let today = clock.now_date();
     let locked_employee_id = row.employee_id;
     let locked_work_date = row.work_date;
     lock_employee_dates(
         &txn,
         tenant_id,
         locked_employee_id,
         &[locked_work_date, work_date],
     )
     .await?;
     let row = attendance::Entity::find_by_id(attendance_id)
@@ -435,37 +428,38 @@ pub async fn update_manual_attendance_segment(
         .ok_or_else(|| KabiPayError::NotFound {
             entity: "attendance",
             id: attendance_id.to_string(),
         })?;
     assert_locked_attendance_identity(
         locked_employee_id,
         locked_work_date,
         row.employee_id,
         row.work_date,
     )?;
-    validate_segment_with_connection(
+    let now = Utc::now();
+    let instants = validate_segment_with_connection(
         &txn,
         tenant_id,
         row.employee_id,
         segment,
         Some(attendance_id),
         false,
-        today,
+        clock, actual_dates, now,
     )
     .await?;
     let updated = update_manual_segment(
         &txn,
         row,
         segment,
         instants,
         MANUAL_SELF_REPORTED,
-        Utc::now(),
+        now,
     )
     .await?;
     txn.commit().await?;
     Ok(updated)
 }
 
 pub async fn list_timesheet_entries(
     db: &DatabaseConnection,
     tenant_id: Uuid,
     employee_id: Uuid,
@@ -962,40 +956,21 @@ mod tests {
     }
     use super::*;
 
     #[test]
     fn timesheet_hours_reject_more_than_two_decimal_places() {
         assert!(parse_hours("1").is_ok());
         assert!(parse_hours("1.2").is_ok());
         assert!(parse_hours("1.23").is_ok());
         assert!(parse_hours("1.234").is_err());
     }
-    use chrono::{NaiveDate, NaiveTime};
-
-    #[test]
-    fn live_punch_clock_uses_configured_business_timezone_not_utc_wall_time() {
-        let now_utc = "2026-08-22T20:00:00Z"
-            .parse::<DateTime<Utc>>()
-            .expect("valid UTC timestamp");
 
-        let clock = TenantBusinessClock::from_name("Asia/Kolkata").expect("valid timezone");
-        let (work_date, punch_time) = attendance_business_date_time(now_utc, clock);
-
-        assert_eq!(
-            work_date,
-            NaiveDate::from_ymd_opt(2026, 8, 23).expect("valid date")
-        );
-        assert_eq!(
-            punch_time,
-            NaiveTime::from_hms_opt(1, 30, 0).expect("valid time")
-        );
-    }
 
     #[test]
     fn attendance_daily_total_must_remain_below_twenty_four_hours() {
         assert!(
             crate::services::attendance_regularization_service::assert_total_attendance_minutes_under_daily_cap(
                 23 * 60 + 59,
             )
             .is_ok()
         );
         assert!(
diff --git a/crates/kabipay-attendance/src/services/mod.rs b/crates/kabipay-attendance/src/services/mod.rs
index e6a9c2b..15cfe88 100644
--- a/crates/kabipay-attendance/src/services/mod.rs
+++ b/crates/kabipay-attendance/src/services/mod.rs
@@ -4,10 +4,12 @@ pub mod attendance_management_service;
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
+pub mod attendance_day_runtime;
diff --git a/crates/kabipay-attendance/tests/attendance_management_postgres.rs b/crates/kabipay-attendance/tests/attendance_management_postgres.rs
index cd02343..b17eb72 100644
--- a/crates/kabipay-attendance/tests/attendance_management_postgres.rs
+++ b/crates/kabipay-attendance/tests/attendance_management_postgres.rs
@@ -102,20 +102,40 @@ impl Fixture {
                 attendance_id UUID NOT NULL REFERENCES attendance(id),
                 target_employee_id UUID NOT NULL REFERENCES employee(id),
                 actor_user_id UUID NOT NULL REFERENCES "user"(id),
                 operation VARCHAR(10) NOT NULL CHECK (operation IN ('CREATE', 'UPDATE')),
                 reason VARCHAR(500) NOT NULL,
                 before_values JSONB,
                 after_values JSONB NOT NULL,
                 request_id VARCHAR(128),
                 created_at TIMESTAMPTZ NOT NULL
             )"#,
+            // Required by the real transaction-owned attendance window resolver.
+            // These fixtures do not substitute for migration/trigger acceptance.
+            r#"CREATE TABLE attendance_day_profile (
+                tenant_id UUID PRIMARY KEY, revision BIGINT NOT NULL,
+                legacy_activation_date DATE, initialized_at TIMESTAMPTZ NOT NULL
+            )"#,
+            r#"CREATE TABLE attendance_day_policy_version (
+                id UUID PRIMARY KEY, tenant_id UUID NOT NULL,
+                effective_work_date DATE NOT NULL, boundary_minutes INTEGER NOT NULL,
+                timezone TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL,
+                superseded_at TIMESTAMPTZ, UNIQUE (tenant_id, id)
+            )"#,
+            r#"CREATE TABLE attendance_day_window (
+                id UUID PRIMARY KEY, tenant_id UUID NOT NULL, work_date DATE NOT NULL,
+                starts_at TIMESTAMPTZ NOT NULL, ends_at TIMESTAMPTZ NOT NULL,
+                timezone TEXT NOT NULL, boundary_minutes INTEGER NOT NULL,
+                policy_version_id UUID NOT NULL, created_at TIMESTAMPTZ NOT NULL,
+                UNIQUE (tenant_id, work_date), CHECK (ends_at > starts_at),
+                FOREIGN KEY (tenant_id, policy_version_id) REFERENCES attendance_day_policy_version(tenant_id, id)
+            )"#,
         ] {
             db.execute(Statement::from_string(DbBackend::Postgres, ddl))
                 .await?;
         }
 
         let tenant_id = Uuid::new_v4();
         let employee_id = Uuid::new_v4();
         let actor_user_id = Uuid::new_v4();
         db.execute(Statement::from_sql_and_values(
             DbBackend::Postgres,
@@ -150,25 +170,22 @@ impl Fixture {
             work_date: NaiveDate::from_ymd_opt(2026, 8, 20)
                 .expect("fixed harness date is valid"),
             check_in_time,
             check_out_time,
         };
         ManagedCreateCommand {
             tenant_id: self.tenant_id,
             target_employee_id: self.employee_id,
             actor_user_id,
             segment,
-            instants: segment
-                .to_instants(TenantBusinessClock::from_name("UTC").expect("valid timezone"))
-                .expect("valid segment instants"),
-            today: NaiveDate::from_ymd_opt(2026, 8, 24)
-                .expect("fixed harness date is valid"),
+            clock: TenantBusinessClock::from_name("UTC").expect("valid timezone"),
+            actual_dates: None,
             reason: "approved external harness adjustment".into(),
             request_id: Some(Uuid::new_v4().to_string()),
         }
     }
 
     async fn count(&self, table: &str) -> Result<i64> {
         ensure!(
             matches!(table, "attendance" | "attendance_adjustment_audit"),
             "unsupported harness table"
         );
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
diff --git a/crates/kabipay-outbox-worker/Cargo.toml b/crates/kabipay-outbox-worker/Cargo.toml
index 3300861..15a97b5 100644
--- a/crates/kabipay-outbox-worker/Cargo.toml
+++ b/crates/kabipay-outbox-worker/Cargo.toml
@@ -5,20 +5,21 @@ edition.workspace = true
 rust-version.workspace = true
 license.workspace = true
 authors.workspace = true
 
 [[bin]]
 name = "kabipay-outbox-worker"
 path = "src/main.rs"
 
 [dependencies]
 kabipay-common.workspace = true
+kabipay-attendance = { path = "../kabipay-attendance" }
 kabipay-db-entities.workspace = true
 kabipay-notification = { path = "../kabipay-notification" }
 kabipay-performance = { path = "../kabipay-performance" }
 kabipay-survey = { path = "../kabipay-survey" }
 tokio.workspace = true
 sea-orm.workspace = true
 serde.workspace = true
 serde_json.workspace = true
 uuid.workspace = true
 chrono.workspace = true
diff --git a/crates/kabipay-outbox-worker/src/main.rs b/crates/kabipay-outbox-worker/src/main.rs
index e57f115..9856ce3 100644
--- a/crates/kabipay-outbox-worker/src/main.rs
+++ b/crates/kabipay-outbox-worker/src/main.rs
@@ -548,27 +548,36 @@ async fn main() -> anyhow::Result<()> {
                                     let now = Utc::now();
                                     let business_date = clock.business_date(now);
                                     let business_time = clock.local_time(now);
                                     match process_due_separations(&tdb, tid, business_date).await {
                                         Ok(result) if result.processed > 0 => {
                                             tracing::info!(%tid, processed = result.processed, "due employee offboarding completed");
                                         }
                                         Ok(_) => {}
                                         Err(error) => tracing::error!(%tid, code = error.code(), "due employee offboarding sweep failed"),
                                     }
-                                    let employee_enabled = match Entitlements::load(&ops_db, tid).await {
-                                        Ok(state) => state.allows("EMPLOYEE"),
+                                    let (employee_enabled, attendance_enabled) = match Entitlements::load(&ops_db, tid).await {
+                                        Ok(state) => (state.allows("EMPLOYEE"), state.allows("ATTENDANCE")),
                                         Err(error) => {
                                             tracing::error!(%tid, code = error.code(), "scheduled domain work held: entitlements unavailable");
-                                            false
+                                            (false, false)
                                         }
                                     };
+                                    if attendance_enabled {
+                                        match kabipay_attendance::sweep_expired_attendance(&tdb, tid, clock, 50).await {
+                                            Ok(result) if result.expired > 0 || result.failed > 0 => tracing::info!(
+                                                %tid, expired = result.expired, failed = result.failed, "attendance expiry sweep completed"
+                                            ),
+                                            Ok(_) => {},
+                                            Err(error) => tracing::error!(%tid, code = error.code(), "attendance expiry sweep failed"),
+                                        }
+                                    }
                                     if employee_enabled {
                                     match process_due_surveys(&tdb, tid).await {
                                         Ok(result) if result.opened > 0 || result.closed > 0 || result.failed > 0 => tracing::info!(
                                             %tid, opened = result.opened, closed = result.closed, failed = result.failed,
                                             "scheduled survey sweep completed"
                                         ),
                                         Ok(_) => {},
                                         Err(error) => tracing::error!(%tid, code = error.code(), "scheduled survey sweep failed"),
                                     }
                                     match process_due_celebrations(

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
index 0000000..a8860d1
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/mod.rs
@@ -0,0 +1,9 @@
+//! Effective-dated attendance policy and immutable UTC windows.
+mod calendar;
+pub use calendar::*;
+mod repository;
+pub use repository::*;
+mod preview;
+pub use preview::*;
+#[cfg(test)]
+mod tests;

warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day/preview.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day/preview.rs b/crates/kabipay-attendance/src/services/attendance_day/preview.rs
new file mode 100644
index 0000000..eddf29a
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/preview.rs
@@ -0,0 +1,29 @@
+//! Read-only settings transition preview; scheduling revalidates under its lock.
+use super::*;
+use chrono::{DateTime, Utc};
+use kabipay_common::{context::ClientClaims, tenant_business_clock::TenantBusinessClock, KabiPayResult};
+use sea_orm::ConnectionTrait;
+use uuid::Uuid;
+
+#[derive(Clone, Debug)]
+pub struct AttendanceDayPolicyPreview {
+    pub revision: i64,
+    pub transition: AttendanceDayWindow,
+    pub following: AttendanceDayWindow,
+}
+
+pub async fn preview_policy<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, clock: TenantBusinessClock, claims: &ClientClaims,
+    command: SchedulePolicyCommand, now: DateTime<Utc>,
+) -> KabiPayResult<AttendanceDayPolicyPreview> {
+    super::repository::validate_schedule_request(tenant_id, claims, &command)?;
+    let state = policy(db, tenant_id, clock, now).await?;
+    let revision = state.revision;
+    let proposal = super::repository::propose_policy_change(db, tenant_id, clock, state, &command, now).await?;
+    let mut transition = proposal.transition;
+    let mut following = proposal.following;
+    // A preview does not persist or reserve these prospective policy versions.
+    transition.policy_version_id = Uuid::nil();
+    following.policy_version_id = Uuid::nil();
+    Ok(AttendanceDayPolicyPreview { revision, transition, following })
+}

warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day/repository.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day/repository.rs b/crates/kabipay-attendance/src/services/attendance_day/repository.rs
new file mode 100644
index 0000000..824ba85
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day/repository.rs
@@ -0,0 +1,335 @@
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
+    // Profile, live versions AND legacy attendance existence must share one MVCC
+    // snapshot: bootstrap can commit a fresh 05:00 profile and attendance together.
+    // The scalar existence row survives missing profiles. A profile without live
+    // versions still has a revision, so its null version fields fail closed below.
+    let rows = db.query_all(sql(
+        "SELECT p.revision, p.legacy_activation_date, v.id, v.effective_work_date, v.boundary_minutes, v.timezone, history.has_attendance FROM (SELECT EXISTS (SELECT 1 FROM attendance WHERE tenant_id = $1) AS has_attendance) history LEFT JOIN attendance_day_profile p ON p.tenant_id = $1 LEFT JOIN attendance_day_policy_version v ON v.tenant_id = p.tenant_id AND v.superseded_at IS NULL ORDER BY v.effective_work_date",
+        vec![tenant_id.into()],
+    )).await?;
+    let first = rows.first()
+        .ok_or_else(|| invalid("attendance policy snapshot returned no result"))?;
+    if let Some(revision) = first.try_get::<Option<i64>>("", "revision")? {
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
+    // Deleted historical rows still establish legacy interpretation, from the
+    // same snapshot that established the profile's absence.
+    let has_attendance: bool = first.try_get("", "has_attendance")?;
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
+/// Prepare the same bootstrap state for a read-only proposal and a later write.
+/// Generated IDs are prospective until the caller persists this state.
+fn prepare_initialization(
+    clock: TenantBusinessClock,
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
+    Ok(state)
+}
+
+async fn persist_initialization(
+    db: &DatabaseTransaction, tenant_id: Uuid, state: &AttendanceDayPolicy,
+    now: DateTime<Utc>,
+) -> KabiPayResult<()> {
+    db.execute(sql(
+        "INSERT INTO attendance_day_profile (tenant_id, revision, legacy_activation_date, initialized_at) VALUES ($1, 1, $2, $3)",
+        vec![tenant_id.into(), state.legacy_activation_date.into(), now.into()],
+    )).await?;
+    for version in &state.versions { insert_version(db, tenant_id, version, now).await?; }
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
+    Ok(state)
+}
+
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
+    validate_schedule_request(tenant_id, claims, &command)?;
+    lock_policy(db, tenant_id).await?;
+    let state = policy(db, tenant_id, clock, now).await?;
+    let before = audit_state(&state);
+    let needs_initialization = !state.initialized;
+    let proposal = propose_policy_change(db, tenant_id, clock, state, &command, now).await?;
+    if needs_initialization {
+        persist_initialization(db, tenant_id, &proposal.state, now).await?;
+    }
+    let PolicyChangeProposal {
+        mut state, pending, version, versions: proposed, next_revision: revision, ..
+    } = proposal;
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

warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day_runtime.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day_runtime.rs b/crates/kabipay-attendance/src/services/attendance_day_runtime.rs
new file mode 100644
index 0000000..4537055
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day_runtime.rs
@@ -0,0 +1,194 @@
+//! Attendance-only expiry and transaction locking; never manufacture a checkout.
+use chrono::{DateTime, NaiveDate, Utc};
+use kabipay_common::{tenant_business_clock::TenantBusinessClock, KabiPayError, KabiPayResult};
+use kabipay_db_entities::tenant::d0010_time_shift_roster::attendance;
+use sea_orm::{ColumnTrait, ConnectionTrait, DatabaseConnection, DatabaseTransaction, DbBackend, EntityTrait, QueryFilter, QueryOrder, QuerySelect, Statement, TransactionTrait};
+use uuid::Uuid;
+use super::{attendance_day::{self, AttendanceDayWindow}, attendance_regularization_service::lock_employee_dates};
+
+pub(crate) fn derive_expiry(
+    row: &mut attendance::Model, window: &AttendanceDayWindow, now: DateTime<Utc>,
+) -> bool {
+    if row.work_date != window.work_date || now < window.ends_at
+        || row.status.as_deref() != Some("OPEN")
+        || row.check_out_at.is_some() || row.check_out_time.is_some()
+    { return false; }
+    row.status = Some("INCOMPLETE".into());
+    row.regularization_status = Some("MISSED_PUNCH_OUT".into());
+    true
+}
+
+/// Project effective status without changing revision or persisting any row.
+pub(crate) async fn project_rows<C: ConnectionTrait>(
+    db: &C, tenant_id: Uuid, clock: TenantBusinessClock,
+    rows: &mut [attendance::Model], now: DateTime<Utc>,
+) -> KabiPayResult<()> {
+    let mut windows = std::collections::HashMap::new();
+    for row in rows.iter_mut().filter(|r| r.status.as_deref() == Some("OPEN")) {
+        if row.tenant_id != tenant_id { return Err(KabiPayError::Forbidden("attendance tenant mismatch".into())); }
+        if !windows.contains_key(&row.work_date) {
+            windows.insert(row.work_date, attendance_day::window_for_date(db, tenant_id, clock, row.work_date, now).await?);
+        }
+        if let Some(window) = windows.get(&row.work_date) { derive_expiry(row, window, now); }
+    }
+    Ok(())
+}
+
+/// Policy serialization precedes every employee lock. Resample after locks and
+/// add any newly current date before making a punch decision.
+pub(crate) async fn lock_current_window(
+    txn: &DatabaseTransaction, tenant_id: Uuid, employee_id: Uuid,
+    clock: TenantBusinessClock, now: &mut impl FnMut() -> DateTime<Utc>,
+) -> KabiPayResult<(AttendanceDayWindow, DateTime<Utc>)> {
+    attendance_day::lock_policy(txn, tenant_id).await?;
+    let open = open_rows(txn, tenant_id, Some(employee_id)).all(txn).await?;
+    let mut dates: Vec<NaiveDate> = open.iter().map(|r| r.work_date).collect();
+    for _ in 0..3 {
+        let candidate = attendance_day::current_window(txn, tenant_id, clock, now()).await?;
+        dates.push(candidate.work_date);
+        lock_employee_dates(txn, tenant_id, employee_id, &dates).await?;
+        let locked_now = now();
+        let current = attendance_day::current_window(txn, tenant_id, clock, locked_now).await?;
+        if dates.contains(&current.work_date) {
+            let frozen = attendance_day::ensure_window(txn, tenant_id, clock, current.work_date, locked_now).await?;
+            return Ok((frozen, locked_now));
+        }
+        // All writers need our policy lock, so taking the extended sorted set
+        // cannot invert ordering against another employee/day writer.
+        dates.push(current.work_date);
+    }
+    Err(KabiPayError::Conflict("attendance day changed while acquiring locks; retry".into()))
+}
+
+fn open_rows<C: ConnectionTrait>(
+    _db: &C, tenant_id: Uuid, employee_id: Option<Uuid>,
+) -> sea_orm::Select<attendance::Entity> {
+    let query = attendance::Entity::find()
+        .filter(attendance::Column::TenantId.eq(tenant_id))
+        .filter(attendance::Column::Status.eq("OPEN"))
+        .filter(attendance::Column::CheckOutAt.is_null())
+        .filter(attendance::Column::CheckOutTime.is_null());
+    match employee_id { Some(id) => query.filter(attendance::Column::EmployeeId.eq(id)), None => query }
+}
+
+/// Called only after policy and employee/day locks; re-read rows under those locks.
+pub(crate) async fn expire_employee(
+    txn: &DatabaseTransaction, tenant_id: Uuid, employee_id: Uuid,
+    clock: TenantBusinessClock, now: DateTime<Utc>,
+) -> KabiPayResult<u64> {
+    let rows = open_rows(txn, tenant_id, Some(employee_id)).all(txn).await?;
+    let mut expired = 0;
+    for mut row in rows {
+        let prior_reason = row.regularization_status.clone();
+        let window = attendance_day::window_for_date(txn, tenant_id, clock, row.work_date, now).await?;
+        if !derive_expiry(&mut row, &window, now) { continue; }
+        attendance_day::ensure_window(txn, tenant_id, clock, row.work_date, now).await?;
+        let result = txn.execute(Statement::from_sql_and_values(DbBackend::Postgres,
+            "UPDATE attendance SET status = 'INCOMPLETE', regularization_status = 'MISSED_PUNCH_OUT', updated_at = $4 WHERE tenant_id = $1 AND employee_id = $2 AND id = $3 AND status = 'OPEN' AND check_out_at IS NULL AND check_out_time IS NULL",
+            vec![tenant_id.into(), employee_id.into(), row.id.into(), now.into()],
+        )).await?;
+        if result.rows_affected() != 1 { continue; }
+        txn.execute(Statement::from_sql_and_values(DbBackend::Postgres,
+            "INSERT INTO audit_log (id, tenant_id, entity_type, entity_id, action, before_state, after_state, created_at) VALUES ($1, $2, 'ATTENDANCE', $3, 'EXPIRE', $4, $5, $6)",
+            vec![Uuid::new_v4().into(), tenant_id.into(), row.id.into(),
+                serde_json::json!({"status":"OPEN","regularization_status":prior_reason}).into(),
+                serde_json::json!({"status":"INCOMPLETE","reason":"MISSED_PUNCH_OUT","work_date":row.work_date,"ends_at":window.ends_at}).into(), now.into()],
+        )).await?;
+        expired += 1;
+    }
+    Ok(expired)
+}
+
+#[derive(Debug, Default)]
+pub struct ExpirySweepResult { pub expired: u64, pub failed: u64 }
+
+/// Bounded, retryable worker sweep. Caller must hold ATTENDANCE entitlement.
+pub async fn sweep_expired_attendance(
+    db: &DatabaseConnection, tenant_id: Uuid, clock: TenantBusinessClock, limit: u64,
+) -> KabiPayResult<ExpirySweepResult> {
+    sweep_with_clock(db, tenant_id, clock, limit, Utc::now).await
+}
+
+async fn sweep_with_clock(
+    db: &DatabaseConnection, tenant_id: Uuid, clock: TenantBusinessClock, limit: u64,
+    mut now: impl FnMut() -> DateTime<Utc>,
+) -> KabiPayResult<ExpirySweepResult> {
+    let candidates = open_rows(db, tenant_id, None)
+        .order_by_asc(attendance::Column::WorkDate).order_by_asc(attendance::Column::Id)
+        .limit(limit.clamp(1, 100)).all(db).await?;
+    let mut result = ExpirySweepResult::default();
+    for candidate in candidates {
+        let txn = db.begin().await?;
+        let attempt = async {
+            attendance_day::lock_policy(&txn, tenant_id).await?;
+            // Re-read all OPEN dates while serialized with punches/corrections.
+            let rows = open_rows(&txn, tenant_id, Some(candidate.employee_id)).all(&txn).await?;
+            let dates: Vec<_> = rows.iter().map(|r| r.work_date).collect();
+            lock_employee_dates(&txn, tenant_id, candidate.employee_id, &dates).await?;
+            expire_employee(&txn, tenant_id, candidate.employee_id, clock, now()).await
+        }.await;
+        match attempt {
+            Ok(count) => { txn.commit().await?; result.expired += count; }
+            Err(error) => {
+                txn.rollback().await?;
+                result.failed += 1;
+                tracing::warn!(code = error.code(), "attendance expiry will retry");
+            }
+        }
+    }
+    Ok(result)
+}
+
+#[cfg(test)]
+mod tests {
+    use super::*;
+    use uuid::Uuid;
+    pub(super) fn utc(value: &str) -> DateTime<Utc> { value.parse().unwrap() }
+    pub(super) fn window() -> AttendanceDayWindow {
+        AttendanceDayWindow {
+            work_date: "2026-09-11".parse().unwrap(),
+            starts_at: utc("2026-09-10T23:30:00Z"),
+            ends_at: utc("2026-09-11T23:30:00Z"),
+            timezone: "Asia/Kolkata".into(), boundary_minutes: 300,
+            policy_version_id: Uuid::from_u128(3),
+        }
+    }
+    pub(super) fn row() -> attendance::Model {
+        attendance::Model {
+            id: Uuid::from_u128(1), tenant_id: Uuid::from_u128(2), employee_id: Uuid::from_u128(4),
+            shift_id: None, work_date: "2026-09-11".parse().unwrap(),
+            check_in_time: Some("23:00:00".parse().unwrap()), check_out_time: None,
+            check_in_at: Some(utc("2026-09-11T17:30:00Z")), check_out_at: None,
+            check_in_lat: None, check_in_lng: None, check_out_lat: None, check_out_lng: None,
+            source: Some("WEB".into()), status: Some("OPEN".into()), regularization_status: None,
+            biometric_ref: None, overtime_hours: None, late_minutes: None, early_exit_minutes: None,
+            created_at: utc("2026-09-11T17:30:00Z"), updated_at: utc("2026-09-11T17:30:00Z"),
+        }
+    }
+    #[test]
+    fn attendance_day_expiry_at_exact_end_preserves_null_checkout_and_original_identity() {
+        let mut row = row();
+        assert!(!derive_expiry(&mut row, &window(), utc("2026-09-11T23:29:59Z")));
+        assert!(derive_expiry(&mut row, &window(), utc("2026-09-11T23:30:00Z")));
+        assert_eq!(row.status.as_deref(), Some("INCOMPLETE"));
+        assert_eq!(row.regularization_status.as_deref(), Some("MISSED_PUNCH_OUT"));
+        assert_eq!(row.id, Uuid::from_u128(1));
+        assert!(row.check_out_time.is_none() && row.check_out_at.is_none());
+        assert_eq!(row.updated_at, utc("2026-09-11T17:30:00Z"), "read projection must retain persisted revision");
+        assert!(!derive_expiry(&mut row, &window(), utc("2026-09-12T10:00:00Z")));
+    }
+    #[test]
+    fn attendance_day_expiry_never_overwrites_a_corrected_or_completed_record() {
+        let mut row = row();
+        row.status = Some("COMPLETE".into());
+        row.check_out_at = Some(utc("2026-09-11T22:30:00Z"));
+        row.check_out_time = Some("04:00:00".parse().unwrap());
+        let before = row.clone();
+        assert!(!derive_expiry(&mut row, &window(), utc("2026-09-12T10:00:00Z")));
+        assert_eq!(row, before);
+    }
+}
+
+#[cfg(test)]
+#[path = "attendance_day_runtime_tests.rs"]
+mod integration_tests;

warning: in the working copy of 'crates/kabipay-attendance/src/services/attendance_day_runtime_tests.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/src/services/attendance_day_runtime_tests.rs b/crates/kabipay-attendance/src/services/attendance_day_runtime_tests.rs
new file mode 100644
index 0000000..46d8102
--- /dev/null
+++ b/crates/kabipay-attendance/src/services/attendance_day_runtime_tests.rs
@@ -0,0 +1,197 @@
+//! SQL boundary tests execute the real punch/expiry services without PostgreSQL.
+use super::*;
+use super::tests::{row, utc, window};
+use sea_orm::{entity::prelude::async_trait, Database, DbErr, Iden, Iterable, ModelTrait, ProxyDatabaseTrait, ProxyExecResult, ProxyRow, Value};
+use std::{collections::BTreeMap, sync::{Arc, Mutex}};
+
+#[derive(Debug)]
+struct Fixture {
+    rows: Mutex<Vec<BTreeMap<String, Value>>>,
+    statements: Mutex<Vec<Statement>>,
+    now: Mutex<DateTime<Utc>>,
+    advance_on_lock: bool,
+    fail_audit: bool,
+    correct_on_lock: bool,
+}
+fn fields(model: attendance::Model) -> BTreeMap<String, Value> {
+    attendance::Column::iter().map(|c| (c.to_string(), model.get(c))).collect()
+}
+fn value_date(value: &Value) -> NaiveDate { match value { Value::ChronoDate(Some(v)) => **v, _ => panic!("expected date") } }
+fn value_uuid(value: &Value) -> Uuid { match value { Value::Uuid(Some(v)) => **v, _ => panic!("expected UUID") } }
+fn value_text(value: &Value) -> Option<&str> { match value { Value::String(Some(v)) => Some(v), _ => None } }
+impl Fixture {
+    fn new(advance_on_lock: bool) -> Self {
+        Self { rows: Mutex::new(vec![fields(row())]), statements: Mutex::new(vec![]),
+            now: Mutex::new(utc("2026-09-11T23:29:59Z")), advance_on_lock, fail_audit: false, correct_on_lock: false }
+    }
+}
+#[async_trait::async_trait]
+impl ProxyDatabaseTrait for Fixture {
+    async fn query(&self, statement: Statement) -> Result<Vec<ProxyRow>, DbErr> {
+        let sql = statement.to_string();
+        self.statements.lock().unwrap().push(statement.clone());
+        if sql.contains("attendance_punch_policy") { return Ok(vec![]); }
+        if sql.starts_with("SELECT work_date, starts_at") {
+            let date: NaiveDate = if sql.contains("2026-09-12") || sql.contains("2026-09-11 23:30:00") {
+                "2026-09-12".parse().unwrap()
+            } else { "2026-09-11".parse().unwrap() };
+            let w = window();
+            let offset = if date == w.work_date { chrono::Duration::zero() } else { chrono::Duration::days(1) };
+            return Ok(vec![ProxyRow::new(BTreeMap::from([
+                ("work_date".into(), date.into()), ("starts_at".into(), (w.starts_at+offset).into()),
+                ("ends_at".into(), (w.ends_at+offset).into()), ("timezone".into(), w.timezone.into()),
+                ("boundary_minutes".into(), 300.into()), ("policy_version_id".into(), w.policy_version_id.into()),
+            ]))]);
+        }
+        if sql.starts_with("INSERT INTO \"attendance\"") {
+            let columns = statement.sql.split_once('(').unwrap().1.split_once(')').unwrap().0;
+            let values = &statement.values.as_ref().unwrap().0;
+            let inserted: BTreeMap<_, _> = columns.split(',').map(|s| s.trim().trim_matches('"').to_owned())
+                .zip(values.iter().cloned()).collect();
+            self.rows.lock().unwrap().push(inserted.clone());
+            return Ok(vec![ProxyRow::new(inserted)]);
+        }
+        if sql.starts_with("UPDATE \"attendance\" SET") {
+            let values = &statement.values.as_ref().unwrap().0;
+            let mut rows = self.rows.lock().unwrap();
+            let target = rows.iter_mut().find(|row| sql.contains(&value_uuid(&row["id"]).to_string()))
+                .ok_or_else(|| DbErr::Custom("attendance update target missing".into()))?;
+            let assignments = statement.sql.split_once(" SET ").unwrap().1.split_once(" WHERE ").unwrap().0;
+            for assignment in assignments.split(',') {
+                let (column, parameter) = assignment.split_once('=').unwrap();
+                let index: usize = parameter.trim().trim_start_matches('$').parse().unwrap();
+                target.insert(column.trim().trim_matches('"').into(), values[index - 1].clone());
+            }
+            return Ok(vec![ProxyRow::new(target.clone())]);
+        }
+        if sql.contains("FROM \"attendance\"") {
+            let rows = self.rows.lock().unwrap();
+            return Ok(rows.iter().filter(|r| {
+                let date = value_date(&r["work_date"]);
+                let date_match = if sql.contains("\"work_date\" =") { sql.contains(&format!("\"work_date\" = '{date}'")) }
+                    else if sql.contains("\"work_date\" <") { date < "2026-09-12".parse().unwrap() } else { true };
+                let status_match = !sql.contains("\"status\" = 'OPEN'") || value_text(&r["status"]) == Some("OPEN");
+                let id_match = !sql.contains("\"id\" =") || sql.contains(&value_uuid(&r["id"]).to_string());
+                date_match && status_match && id_match
+            }).cloned().map(ProxyRow::new).collect());
+        }
+        Err(DbErr::Custom(format!("unexpected SQL: {sql}")))
+    }
+    async fn execute(&self, statement: Statement) -> Result<ProxyExecResult, DbErr> {
+        let sql = statement.to_string();
+        self.statements.lock().unwrap().push(statement.clone());
+        if sql.contains("pg_advisory_xact_lock") {
+            if self.advance_on_lock && sql.contains("attendance:") { *self.now.lock().unwrap() = utc("2026-09-11T23:30:00Z"); }
+            // A correction commits while expiry waits for the policy lock,
+            // after the worker's initial candidate snapshot but before its
+            // locked read. No compliant writer runs inside the held lock.
+            if self.correct_on_lock && sql.contains("attendance-day-policy:") {
+                let mut rows = self.rows.lock().unwrap();
+                rows[0].insert("status".into(), "COMPLETE".into());
+                rows[0].insert("check_out_at".into(), utc("2026-09-11T22:30:00Z").into());
+                rows[0].insert("check_out_time".into(), "04:00:00".parse::<chrono::NaiveTime>().unwrap().into());
+            }
+        } else if sql.starts_with("UPDATE attendance SET status") || sql.starts_with("UPDATE \"attendance\" SET \"status\"") {
+            for row in self.rows.lock().unwrap().iter_mut().filter(|r| value_text(&r["status"]) == Some("OPEN")) {
+                row.insert("status".into(), "INCOMPLETE".into());
+                row.insert("regularization_status".into(), "MISSED_PUNCH_OUT".into());
+            }
+        } else if sql.starts_with("INSERT INTO audit_log") {
+            if self.fail_audit { return Err(DbErr::Custom("audit unavailable".into())); }
+        } else { return Err(DbErr::Custom(format!("unexpected execution: {sql}"))); }
+        Ok(ProxyExecResult { last_insert_id: 0, rows_affected: 1 })
+    }
+}
+async fn fixture_db(fixture: Arc<Fixture>) -> DatabaseConnection {
+    Database::connect_proxy(DbBackend::Postgres, Arc::new(Box::new(SharedFixture(fixture)))).await.unwrap()
+}
+// Arc delegates only the external SQL boundary; all attendance logic is real.
+#[derive(Debug)]
+struct SharedFixture(Arc<Fixture>);
+#[async_trait::async_trait]
+impl ProxyDatabaseTrait for SharedFixture {
+    async fn query(&self, s: Statement) -> Result<Vec<ProxyRow>, DbErr> { self.0.query(s).await }
+    async fn execute(&self, s: Statement) -> Result<ProxyExecResult, DbErr> { self.0.execute(s).await }
+}
+#[tokio::test]
+async fn attendance_day_punch_resamples_after_locks_expires_original_and_opens_new_day() {
+    let fixture = Arc::new(Fixture::new(true));
+    let db = fixture_db(fixture.clone()).await;
+    let result = crate::services::attendance_service::punch_today_with_clock(
+        &db, Uuid::from_u128(2), Uuid::from_u128(4), TenantBusinessClock::from_name("Asia/Kolkata").unwrap(),
+        None, None, || *fixture.now.lock().unwrap(),
+    ).await.unwrap();
+    assert_eq!(result.check_in_at, Some(utc("2026-09-11T23:30:00Z")));
+    assert_eq!(result.work_date, "2026-09-12".parse::<NaiveDate>().unwrap());
+    assert_eq!(result.status.as_deref(), Some("OPEN"));
+    let rows = fixture.rows.lock().unwrap();
+    assert_eq!(rows.len(), 2);
+    assert_eq!(value_text(&rows[0]["status"]), Some("INCOMPLETE"));
+    assert!(matches!(&rows[0]["check_out_time"], Value::ChronoTime(None)));
+    assert!(matches!(&rows[0]["check_out_at"], Value::ChronoDateTimeUtc(None)));
+    assert_eq!(rows.iter().filter(|r| value_text(&r["status"]) == Some("OPEN")).count(), 1);
+    let statements = fixture.statements.lock().unwrap();
+    let locks: Vec<_> = statements.iter().filter(|s| s.sql.contains("pg_advisory_xact_lock")).collect();
+    assert!(locks[0].to_string().contains("attendance-day-policy:"));
+    assert!(statements.iter().any(|s| s.sql.contains("INSERT INTO audit_log")));
+}
+
+#[tokio::test]
+async fn attendance_day_worker_retires_once_and_preserves_a_correction_seen_after_lock() {
+    for corrected in [false, true] {
+        let mut state = Fixture::new(true);
+        state.correct_on_lock = corrected;
+        let fixture = Arc::new(state);
+        let db = fixture_db(fixture.clone()).await;
+        let clock = TenantBusinessClock::from_name("Asia/Kolkata").unwrap();
+        let first = sweep_with_clock(&db, Uuid::from_u128(2), clock, 25, || *fixture.now.lock().unwrap()).await.unwrap();
+        assert_eq!(first.expired, if corrected { 0 } else { 1 });
+        assert_eq!(first.failed, 0);
+        let second = sweep_with_clock(&db, Uuid::from_u128(2), clock, 25, || *fixture.now.lock().unwrap()).await.unwrap();
+        assert_eq!(second.expired, 0);
+        let rows = fixture.rows.lock().unwrap();
+        assert_eq!(value_text(&rows[0]["status"]), Some(if corrected { "COMPLETE" } else { "INCOMPLETE" }));
+        if corrected { assert_eq!(rows[0]["check_out_at"], utc("2026-09-11T22:30:00Z").into()); }
+        else { assert!(matches!(rows[0]["check_out_at"], Value::ChronoDateTimeUtc(None))); }
+        let statements = fixture.statements.lock().unwrap();
+        assert_eq!(statements.iter().filter(|s| s.sql.starts_with("INSERT INTO audit_log")).count(), if corrected { 0 } else { 1 });
+    }
+}
+
+#[tokio::test]
+async fn attendance_day_punch_before_cutoff_completes_the_existing_original_day() {
+    let fixture = Arc::new(Fixture::new(false));
+    let db = fixture_db(fixture.clone()).await;
+    let result = crate::services::attendance_service::punch_today_with_clock(
+        &db, Uuid::from_u128(2), Uuid::from_u128(4), TenantBusinessClock::from_name("Asia/Kolkata").unwrap(),
+        None, None, || *fixture.now.lock().unwrap(),
+    ).await.unwrap();
+    assert_eq!(result.id, Uuid::from_u128(1));
+    assert_eq!(result.work_date, "2026-09-11".parse::<NaiveDate>().unwrap());
+    assert_eq!(result.check_out_at, Some(utc("2026-09-11T23:29:59Z")));
+    assert_eq!(result.status.as_deref(), Some("COMPLETE"));
+    assert_eq!(fixture.rows.lock().unwrap().len(), 1);
+}
+
+#[tokio::test]
+async fn attendance_day_read_projection_expires_without_writes_or_revision_changes() {
+    let fixture = Arc::new(Fixture::new(false));
+    let db = fixture_db(fixture.clone()).await;
+    let mut rows = vec![row()];
+    project_rows(&db, Uuid::from_u128(2), TenantBusinessClock::from_name("Asia/Kolkata").unwrap(), &mut rows, utc("2026-09-11T23:30:00Z")).await.unwrap();
+    assert_eq!(rows[0].status.as_deref(), Some("INCOMPLETE"));
+    assert!(rows[0].check_out_at.is_none() && rows[0].check_out_time.is_none());
+    assert_eq!(rows[0].updated_at, utc("2026-09-11T17:30:00Z"));
+    assert!(fixture.statements.lock().unwrap().iter().all(|s| s.sql.starts_with("SELECT")));
+}
+
+#[tokio::test]
+async fn attendance_day_worker_reports_audit_failure_for_retry() {
+    let mut state = Fixture::new(true);
+    state.fail_audit = true;
+    let fixture = Arc::new(state);
+    let db = fixture_db(fixture.clone()).await;
+    let result = sweep_with_clock(&db, Uuid::from_u128(2), TenantBusinessClock::from_name("Asia/Kolkata").unwrap(), 25, || *fixture.now.lock().unwrap()).await.unwrap();
+    assert_eq!(result.failed, 1);
+    assert_eq!(result.expired, 0);
+}

warning: in the working copy of 'crates/kabipay-attendance/tests/attendance_day_policy.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/crates/kabipay-attendance/tests/attendance_day_policy.rs b/crates/kabipay-attendance/tests/attendance_day_policy.rs
new file mode 100644
index 0000000..274f7b8
--- /dev/null
+++ b/crates/kabipay-attendance/tests/attendance_day_policy.rs
@@ -0,0 +1,424 @@
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
+
+fn missing_profile_snapshot(has_attendance: bool) -> Vec<ProxyRow> {
+    vec![ProxyRow::new(BTreeMap::from([
+        ("revision".into(), Option::<i64>::None.into()),
+        ("legacy_activation_date".into(), Option::<NaiveDate>::None.into()),
+        ("id".into(), Option::<Uuid>::None.into()),
+        ("effective_work_date".into(), Option::<NaiveDate>::None.into()),
+        ("boundary_minutes".into(), Option::<i32>::None.into()),
+        ("timezone".into(), Option::<String>::None.into()),
+        ("has_attendance".into(), has_attendance.into()),
+    ]))]
+}
+
+/// The first statement reads its snapshot, then a fresh tenant's bootstrap commits
+/// a 05:00 profile and first attendance row before any subsequent statement.
+#[derive(Debug)]
+struct BootstrapInterleaving {
+    committed: Mutex<bool>,
+    statements: Arc<Mutex<Vec<Statement>>>,
+}
+
+#[async_trait::async_trait]
+impl ProxyDatabaseTrait for BootstrapInterleaving {
+    async fn query(&self, statement: Statement) -> Result<Vec<ProxyRow>, DbErr> {
+        let includes_policy = statement.sql.contains("attendance_day_profile");
+        let includes_attendance = statement.sql.contains("FROM attendance WHERE tenant_id");
+        self.statements.lock().unwrap().push(statement);
+        let mut committed = self.committed.lock().unwrap();
+        let snapshot_committed = *committed;
+        *committed = true;
+        match (includes_policy, includes_attendance, snapshot_committed) {
+            (true, _, true) => Ok(policy_rows(&[("0001-01-01", 300)], None)),
+            (true, true, false) => Ok(missing_profile_snapshot(false)),
+            (true, false, false) => Ok(vec![]),
+            (false, true, committed) => Ok(exists(committed)),
+            _ => Err(DbErr::Custom("unexpected bootstrap query".into())),
+        }
+    }
+
+    async fn execute(&self, _statement: Statement) -> Result<ProxyExecResult, DbErr> {
+        Err(DbErr::Custom("policy reads must not write during bootstrap".into()))
+    }
+}
+
+#[tokio::test]
+async fn attendance_day_bootstrap_interleaving_keeps_one_consistent_read_snapshot() {
+    // 03:00 local Sep12 belongs to Sep11 under BOTH consistent snapshots:
+    // missing profile/no attendance (fresh default) and committed 05:00 profile.
+    for initially_committed in [false, true] {
+        let tenant = Uuid::new_v4();
+        let statements = Arc::new(Mutex::new(Vec::new()));
+        let db = Database::connect_proxy(DbBackend::Postgres, Arc::new(Box::new(
+            BootstrapInterleaving {
+                committed: Mutex::new(initially_committed),
+                statements: statements.clone(),
+            },
+        ))).await.unwrap();
+        let now = utc("2026-09-11T21:30:00Z");
+        let state = policy(&db, tenant, clock(), now).await.unwrap();
+        let window = resolve_current_window(&state.versions, now).unwrap();
+        assert_eq!(window.work_date, date("2026-09-11"));
+        assert_eq!(window.starts_at, utc("2026-09-10T23:30:00Z"));
+        assert_eq!(window.ends_at, utc("2026-09-11T23:30:00Z"));
+        assert!(!state.legacy_activation_pending);
+        assert_eq!(state.initialized, initially_committed);
+        let statements = statements.lock().unwrap();
+        assert_eq!(statements.len(), 1, "policy and bootstrap existence need one SQL snapshot");
+        assert!(statements[0].to_string().contains(&tenant.to_string()));
+        assert!(statements[0].sql.starts_with("SELECT"));
+    }
+}
+#[tokio::test]
+async fn attendance_day_missing_profile_reads_are_write_free_and_legacy_aware() {
+    for (has_attendance, boundary, expected_start) in [(true, 0, "2026-09-10T18:30:00Z"), (false, 300, "2026-09-10T23:30:00Z")] {
+        let tenant = Uuid::new_v4();
+        let (db, statements) = db(vec![missing_profile_snapshot(has_attendance)]).await;
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
+
+#[tokio::test]
+async fn attendance_day_preview_validates_authority_revision_and_exact_transition_without_writes() {
+    let tenant = Uuid::new_v4();
+    let (denied_db, denied_statements) = db(vec![]).await;
+    let denied = preview_policy(&denied_db, tenant, clock(), &claims(tenant, "SELF"), command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await;
+    assert!(matches!(denied, Err(kabipay_common::KabiPayError::Forbidden(_))));
+    assert!(denied_statements.lock().unwrap().is_empty());
+    let (preview_db, statements) = db(vec![policy_rows(&[("0001-01-01", 300)], None), vec![]]).await;
+    let preview = preview_policy(&preview_db, tenant, clock(), &claims(tenant, "ALL"), command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap();
+    assert_eq!(preview.revision, 7);
+    assert_eq!(preview.transition.starts_at, utc("2026-09-11T23:30:00Z"));
+    assert_eq!(preview.transition.ends_at, utc("2026-09-13T00:30:00Z"));
+    assert_eq!(preview.following.starts_at, utc("2026-09-13T00:30:00Z"));
+    assert!(statements.lock().unwrap().iter().all(|s| s.sql.starts_with("SELECT")));
+    let (stale_db, _) = db(vec![policy_rows(&[("0001-01-01", 300)], None)]).await;
+    assert!(matches!(preview_policy(&stale_db, tenant, clock(), &claims(tenant, "ALL"), command(6, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await, Err(kabipay_common::KabiPayError::Conflict(_))));
+}
+fn policy_rows(versions: &[(&str, i32)], activation: Option<NaiveDate>) -> Vec<ProxyRow> {
+    policy_rows_at_revision(versions, activation, 7)
+}
+fn policy_rows_at_revision(versions: &[(&str, i32)], activation: Option<NaiveDate>, revision: i64) -> Vec<ProxyRow> {
+    versions.iter().map(|(effective, minutes)| ProxyRow::new(BTreeMap::from([
+        ("revision".into(), revision.into()),
+        ("legacy_activation_date".into(), activation.into()),
+        ("id".into(), Uuid::new_v4().into()),
+        ("effective_work_date".into(), date(effective).into()),
+        ("boundary_minutes".into(), (*minutes).into()),
+        ("timezone".into(), "Asia/Kolkata".into()),
+        ("has_attendance".into(), true.into()),
+    ]))).collect()
+}
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
+        let (db, statements) = db(vec![vec![], missing_profile_snapshot(true), vec![]]).await;
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
+    let (db, statements) = db(vec![vec![], missing_profile_snapshot(false), vec![]]).await;
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
index 0000000..80f5c5b
--- /dev/null
+++ b/scripts/test-attendance-day-contract.ps1
@@ -0,0 +1,31 @@
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
+$windowKey = $constraints | Where-Object { $_.constraintName -eq 'uq_attendance_day_window_tenant_date' }
+if ($windowKey.tableName -ne 'attendance_day_window' -or $windowKey.columnNames -ne 'tenant_id,work_date') { throw 'Window uniqueness must use tenant and work date' }
+$versionKey = $constraints | Where-Object { $_.constraintName -eq 'uq_attendance_day_version_tenant_id' }
+if ($versionKey.tableName -ne 'attendance_day_policy_version' -or $versionKey.columnNames -ne 'tenant_id,id') { throw 'Version reference key must include tenant' }
+$reference = $constraints | Where-Object { $_.constraintName -eq 'fk_attendance_day_window_version' }
+if ($reference.baseTableName -ne 'attendance_day_window' -or $reference.baseColumnNames -ne 'tenant_id,policy_version_id' -or $reference.referencedTableName -ne 'attendance_day_policy_version' -or $reference.referencedColumnNames -ne 'tenant_id,id' -or $reference.onDelete -ne 'RESTRICT') { throw 'Window version reference must enforce tenant ownership and preserve history' }
+$profileKey = $migration.SelectSingleNode('//db:addPrimaryKey[@tableName="attendance_day_profile"]', $ns)
+if (-not $profileKey -or $profileKey.columnNames -ne 'tenant_id') { throw 'Activation profile must be unique per tenant' }
+Write-Output 'PASS: attendance-day XML tables, required tenant keys, composite references and master inclusion'


