# Task1 fix round1 diff

Compared against exact source snapshot seen by first reviewer. No commits. Files only repository.rs and attendance_day_policy.rs.
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task1-review-base-repository.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task1-review-base-repository.rs b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs
index 0513298..5b7cac3 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task1-review-base-repository.rs
+++ b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs
@@ -40,49 +40,49 @@ async fn frozen_for_date<C: ConnectionTrait>(
     db.query_one(sql(
         "SELECT work_date, starts_at, ends_at, timezone, boundary_minutes, policy_version_id FROM attendance_day_window WHERE tenant_id = $1 AND work_date = $2",
         vec![tenant_id.into(), work_date.into()],
     )).await?.map(frozen_row).transpose()
 }
 
 /// Read-only snapshot; a missing profile never creates a moving activation anchor.
 pub async fn policy<C: ConnectionTrait>(
     db: &C, tenant_id: Uuid, clock: TenantBusinessClock, now: DateTime<Utc>,
 ) -> KabiPayResult<AttendanceDayPolicy> {
-    // One statement observes revision and live versions from one MVCC snapshot.
-    // LEFT JOIN makes a corrupt profile without versions fail closed.
+    // Profile, live versions AND legacy attendance existence must share one MVCC
+    // snapshot: bootstrap can commit a fresh 05:00 profile and attendance together.
+    // The scalar existence row survives missing profiles. A profile without live
+    // versions still has a revision, so its null version fields fail closed below.
     let rows = db.query_all(sql(
-        "SELECT p.revision, p.legacy_activation_date, v.id, v.effective_work_date, v.boundary_minutes, v.timezone FROM attendance_day_profile p LEFT JOIN attendance_day_policy_version v ON v.tenant_id = p.tenant_id AND v.superseded_at IS NULL WHERE p.tenant_id = $1 ORDER BY v.effective_work_date",
+        "SELECT p.revision, p.legacy_activation_date, v.id, v.effective_work_date, v.boundary_minutes, v.timezone, history.has_attendance FROM (SELECT EXISTS (SELECT 1 FROM attendance WHERE tenant_id = $1) AS has_attendance) history LEFT JOIN attendance_day_profile p ON p.tenant_id = $1 LEFT JOIN attendance_day_policy_version v ON v.tenant_id = p.tenant_id AND v.superseded_at IS NULL ORDER BY v.effective_work_date",
         vec![tenant_id.into()],
     )).await?;
-    if let Some(first) = rows.first() {
-        let revision = first.try_get("", "revision")?;
+    let first = rows.first()
+        .ok_or_else(|| invalid("attendance policy snapshot returned no result"))?;
+    if let Some(revision) = first.try_get::<Option<i64>>("", "revision")? {
         let legacy_activation_date: Option<NaiveDate> = first.try_get("", "legacy_activation_date")?;
         let versions = rows.iter().map(|row| Ok(PolicyVersion {
             id: row.try_get("", "id")?,
             effective_work_date: row.try_get("", "effective_work_date")?,
             boundary_minutes: row.try_get("", "boundary_minutes")?,
             timezone: row.try_get("", "timezone")?,
         })).collect::<KabiPayResult<Vec<_>>>()?;
         let active = resolve_current_window(&versions, now)?;
         let legacy_activation_pending = legacy_activation_date.is_some()
             && versions.first().is_some_and(|v| v.id == active.policy_version_id);
         return Ok(AttendanceDayPolicy {
             revision, initialized: true, legacy_activation_pending,
             legacy_activation_date, versions,
         });
     }
-    // Deleted historical rows still establish legacy interpretation.
-    let has_attendance: bool = db.query_one(sql(
-        "SELECT EXISTS (SELECT 1 FROM attendance WHERE tenant_id = $1) AS has_attendance",
-        vec![tenant_id.into()],
-    )).await?.ok_or_else(|| invalid("attendance existence query returned no result"))?
-        .try_get("", "has_attendance")?;
+    // Deleted historical rows still establish legacy interpretation, from the
+    // same snapshot that established the profile's absence.
+    let has_attendance: bool = first.try_get("", "has_attendance")?;
     Ok(AttendanceDayPolicy {
         revision: 0, initialized: false,
         legacy_activation_pending: has_attendance, legacy_activation_date: None,
         versions: vec![PolicyVersion {
             id: Uuid::nil(),
             effective_work_date: NaiveDate::from_ymd_opt(1, 1, 1)
                 .ok_or_else(|| invalid("attendance baseline date is invalid"))?,
             boundary_minutes: if has_attendance { 0 } else { 300 },
             timezone: clock.timezone_name().into(),
         }],

warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task1-review-base-attendance_day_policy.rs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/tests/attendance_day_policy.rs', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task1-review-base-attendance_day_policy.rs b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/tests/attendance_day_policy.rs
index e3e3167..6ab02a2 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task1-review-base-attendance_day_policy.rs
+++ b/D:/work/heliorventures/hrms-svc/crates/kabipay-attendance/tests/attendance_day_policy.rs
@@ -24,25 +24,96 @@ impl ProxyDatabaseTrait for Fixture {
 }
 async fn db(rows: Vec<Vec<ProxyRow>>) -> (sea_orm::DatabaseConnection, Arc<Mutex<Vec<Statement>>>) {
     db_with_audit_failure(rows, false).await
 }
 async fn db_with_audit_failure(rows: Vec<Vec<ProxyRow>>, fail_audit: bool) -> (sea_orm::DatabaseConnection, Arc<Mutex<Vec<Statement>>>) {
     let statements = Arc::new(Mutex::new(Vec::new()));
     let db = Database::connect_proxy(DbBackend::Postgres, Arc::new(Box::new(Fixture { rows: Mutex::new(rows.into()), statements: statements.clone(), fail_audit }))).await.unwrap();
     (db, statements)
 }
 fn exists(value: bool) -> Vec<ProxyRow> { vec![ProxyRow::new(BTreeMap::from([("has_attendance".into(), value.into())]))] }
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
 #[tokio::test]
 async fn attendance_day_missing_profile_reads_are_write_free_and_legacy_aware() {
     for (has_attendance, boundary, expected_start) in [(true, 0, "2026-09-10T18:30:00Z"), (false, 300, "2026-09-10T23:30:00Z")] {
         let tenant = Uuid::new_v4();
-        let (db, statements) = db(vec![vec![], exists(has_attendance)]).await;
+        let (db, statements) = db(vec![missing_profile_snapshot(has_attendance)]).await;
         let policy = policy(&db, tenant, clock(), utc("2026-09-11T10:00:00Z")).await.unwrap();
         assert!(!policy.initialized);
         assert_eq!(policy.legacy_activation_pending, has_attendance);
         assert_eq!(policy.revision, 0);
         let w = resolve_window(&policy.versions, date("2026-09-11")).unwrap();
         assert_eq!(w.boundary_minutes, boundary);
         assert_eq!(w.starts_at, utc(expected_start));
         for statement in statements.lock().unwrap().iter() {
             assert!(statement.sql.trim_start().starts_with("SELECT"));
             assert!(statement.to_string().contains(&tenant.to_string()), "tenant must qualify every read");
@@ -89,20 +160,21 @@ fn command(revision: i64, effective: &str) -> SchedulePolicyCommand {
     SchedulePolicyCommand { expected_revision: revision, effective_work_date: date(effective), boundary_minutes: 360 }
 }
 fn policy_rows(versions: &[(&str, i32)], activation: Option<NaiveDate>) -> Vec<ProxyRow> {
     versions.iter().map(|(effective, minutes)| ProxyRow::new(BTreeMap::from([
         ("revision".into(), 7_i64.into()),
         ("legacy_activation_date".into(), activation.into()),
         ("id".into(), Uuid::new_v4().into()),
         ("effective_work_date".into(), date(effective).into()),
         ("boundary_minutes".into(), (*minutes).into()),
         ("timezone".into(), "Asia/Kolkata".into()),
+        ("has_attendance".into(), true.into()),
     ]))).collect()
 }
 #[tokio::test]
 async fn attendance_day_policy_rejects_unauthorized_and_foreign_tenants_before_sql() {
     let tenant = Uuid::new_v4();
     for claimant in [claims(tenant, "TEAM"), claims(Uuid::new_v4(), "ALL")] {
         let (db, statements) = db(vec![]).await;
         let tx = db.begin().await.unwrap();
         let err = schedule_policy(&tx, tenant, clock(), &claimant, command(7, "2026-09-12"), utc("2026-09-11T10:00:00Z")).await.unwrap_err();
         assert!(matches!(err, kabipay_common::KabiPayError::Forbidden(_)));
@@ -149,36 +221,36 @@ async fn attendance_day_policy_replacement_audits_and_preserves_history() {
     assert!(audit.to_string().contains(&claimant.sub.to_string()));
     assert!(audit.to_string().contains("before_state") && audit.to_string().contains("after_state"));
 }
 #[tokio::test]
 async fn attendance_day_initialization_preserves_legacy_active_day_and_freezes_explicit_transition() {
     for (work_date, start, end) in [
         ("2026-09-11", "2026-09-10T18:30:00Z", "2026-09-11T18:30:00Z"),
         ("2026-09-12", "2026-09-11T18:30:00Z", "2026-09-12T23:30:00Z")
     ] {
         let tenant = Uuid::new_v4();
-        let (db, statements) = db(vec![vec![], vec![], exists(true), vec![]]).await;
+        let (db, statements) = db(vec![vec![], missing_profile_snapshot(true), vec![]]).await;
         let tx = db.begin().await.unwrap();
         let result = ensure_window(&tx, tenant, clock(), date(work_date), utc("2026-09-11T10:00:00Z")).await.unwrap();
         assert_eq!(result.starts_at, utc(start)); assert_eq!(result.ends_at, utc(end));
         let sql = statements.lock().unwrap();
         assert!(sql.iter().all(|s| s.to_string().contains(&tenant.to_string())));
         let profile = sql.iter().find(|s| s.sql.starts_with("INSERT INTO attendance_day_profile")).unwrap();
         assert!(profile.to_string().contains("2026-09-12"));
         assert_eq!(sql.iter().filter(|s| s.sql.starts_with("INSERT INTO attendance_day_policy_version")).count(), 2);
         assert!(sql.iter().any(|s| s.sql.starts_with("INSERT INTO attendance_day_window")));
     }
 }
 #[tokio::test]
 async fn attendance_day_initialization_fresh_tenant_uses_five_without_conversion() {
     let tenant = Uuid::new_v4();
-    let (db, statements) = db(vec![vec![], vec![], exists(false), vec![]]).await;
+    let (db, statements) = db(vec![vec![], missing_profile_snapshot(false), vec![]]).await;
     let tx = db.begin().await.unwrap();
     let result = ensure_window(&tx, tenant, clock(), date("2026-09-11"), utc("2026-09-11T10:00:00Z")).await.unwrap();
     assert_eq!(result.starts_at, utc("2026-09-10T23:30:00Z"));
     assert_eq!(result.ends_at, utc("2026-09-11T23:30:00Z"));
     assert_eq!(statements.lock().unwrap().iter().filter(|s| s.sql.starts_with("INSERT INTO attendance_day_policy_version")).count(), 1);
 }
 #[tokio::test]
 async fn attendance_day_current_read_uses_frozen_interval_and_exclusive_end_query() {
     let tenant = Uuid::new_v4();
     let (db, statements) = db(vec![frozen(tenant)]).await;


