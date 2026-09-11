# Task3 UI uncommitted review package

UI base402309e81cc5405e01ed1912677d2c026860c31d, clean before task. Full tracked/untracked Task3 diff; no commits or live operations.
warning: in the working copy of 'scripts/generate-attendance-client.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/api/attendance/gql.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/api/attendance/graphql.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/api/documents/attendance.graphql', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/attendance/components/ManualAttendanceModal.test.tsx', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/attendance/components/ManualAttendanceModal.tsx', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/hr/HrAttendanceManagementPage.context.test.tsx', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/utils/attendanceValidation.test.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/utils/attendanceValidation.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/scripts/generate-attendance-client.mjs b/scripts/generate-attendance-client.mjs
index 0ecabe5..f5832eb 100644
--- a/scripts/generate-attendance-client.mjs
+++ b/scripts/generate-attendance-client.mjs
@@ -33,16 +33,24 @@ const document = parse(readFileSync(source, 'utf8'));
 const errors = validate(schema, document);
 if (errors.length) throw new Error(errors.map((error) => error.message).join('\n'));
 await generate(
   {
     schema: schemaText,
     documents: source,
     generates: {
       [destination]: {
         preset,
         presetConfig: { fragmentMasking: false, gqlTagName: 'attendanceGraphql' },
-        config: { onlyOperationTypes: true, useTypeImports: true },
+        config: {
+          onlyOperationTypes: true,
+          useTypeImports: true,
+          scalars: {
+            DateTime: 'string',
+            NaiveDate: 'string',
+            NaiveTime: 'string',
+          },
+        },
       },
     },
   },
   true
 );
diff --git a/src/api/attendance/gql.ts b/src/api/attendance/gql.ts
index 8f454ad..5ce581a 100644
--- a/src/api/attendance/gql.ts
+++ b/src/api/attendance/gql.ts
@@ -7,40 +7,40 @@ import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-
  *
  * This map has several performance disadvantages:
  * 1. It is not tree-shakeable, so it will include all operations in the project.
  * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
  * 3. It does not support dead code elimination, so it will add unused operations.
  *
  * Therefore it is highly recommended to use the babel or swc plugin for production.
  * Learn more about it here: https://the-guild.dev/graphql/codegen/plugins/presets/preset-client#reducing-bundle-size
  */
 type Documents = {
-    "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}": typeof types.MyAttendanceBoardDocument,
+    "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nquery AttendanceCurrentDayWindow {\n  attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendanceCorrectionWindows($workDate: NaiveDate!) {\n  currentWindow: attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n  selectedWindow: attendanceDayWindow(workDate: $workDate) {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendancePolicySettings($slim: Int! = 50) {\n  attendanceDayPolicy {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n  attendancePunchPolicy {\n    id\n    tenantId\n    isEnforced\n    siteLatitude\n    siteLongitude\n    maxDistanceMeters\n    ipAllowlist\n    updatedAt\n  }\n  shifts(limit: $slim) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n}\n\nquery PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  previewAttendanceDayPolicy(input: $input) {\n    revision\n    transition {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n    following {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nmutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  scheduleAttendanceDayPolicy(input: $input) {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nquery AttendancePunchDaySummary {\n  punchDaySummary {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n    totalWorkedMinutes\n    openSegment {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n    segments {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n  }\n}\n\nmutation AttendancePunchToday($input: PunchTodayInput) {\n  punchToday(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    checkInLat\n    checkInLng\n    checkOutLat\n    checkOutLng\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {\n  addManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {\n  updateManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {\n  addManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}\n\nmutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {\n  updateManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}": typeof types.MyAttendanceBoardDocument,
 };
 const documents: Documents = {
-    "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}": types.MyAttendanceBoardDocument,
+    "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nquery AttendanceCurrentDayWindow {\n  attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendanceCorrectionWindows($workDate: NaiveDate!) {\n  currentWindow: attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n  selectedWindow: attendanceDayWindow(workDate: $workDate) {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendancePolicySettings($slim: Int! = 50) {\n  attendanceDayPolicy {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n  attendancePunchPolicy {\n    id\n    tenantId\n    isEnforced\n    siteLatitude\n    siteLongitude\n    maxDistanceMeters\n    ipAllowlist\n    updatedAt\n  }\n  shifts(limit: $slim) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n}\n\nquery PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  previewAttendanceDayPolicy(input: $input) {\n    revision\n    transition {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n    following {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nmutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  scheduleAttendanceDayPolicy(input: $input) {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nquery AttendancePunchDaySummary {\n  punchDaySummary {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n    totalWorkedMinutes\n    openSegment {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n    segments {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n  }\n}\n\nmutation AttendancePunchToday($input: PunchTodayInput) {\n  punchToday(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    checkInLat\n    checkInLng\n    checkOutLat\n    checkOutLng\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {\n  addManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {\n  updateManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {\n  addManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}\n\nmutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {\n  updateManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}": types.MyAttendanceBoardDocument,
 };
 
 /**
  * The attendanceGraphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
  *
  *
  * @example
  * ```ts
  * const query = attendanceGraphql(`query GetUser($id: ID!) { user(id: $id) { name } }`);
  * ```
  *
  * The query argument is unknown!
  * Please regenerate the types.
  */
 export function attendanceGraphql(source: string): unknown;
 
 /**
  * The attendanceGraphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
  */
-export function attendanceGraphql(source: "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}"): (typeof documents)["query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}"];
+export function attendanceGraphql(source: "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nquery AttendanceCurrentDayWindow {\n  attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendanceCorrectionWindows($workDate: NaiveDate!) {\n  currentWindow: attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n  selectedWindow: attendanceDayWindow(workDate: $workDate) {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendancePolicySettings($slim: Int! = 50) {\n  attendanceDayPolicy {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n  attendancePunchPolicy {\n    id\n    tenantId\n    isEnforced\n    siteLatitude\n    siteLongitude\n    maxDistanceMeters\n    ipAllowlist\n    updatedAt\n  }\n  shifts(limit: $slim) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n}\n\nquery PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  previewAttendanceDayPolicy(input: $input) {\n    revision\n    transition {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n    following {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nmutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  scheduleAttendanceDayPolicy(input: $input) {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nquery AttendancePunchDaySummary {\n  punchDaySummary {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n    totalWorkedMinutes\n    openSegment {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n    segments {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n  }\n}\n\nmutation AttendancePunchToday($input: PunchTodayInput) {\n  punchToday(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    checkInLat\n    checkInLng\n    checkOutLat\n    checkOutLng\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {\n  addManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {\n  updateManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {\n  addManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}\n\nmutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {\n  updateManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}"): (typeof documents)["query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nquery AttendanceCurrentDayWindow {\n  attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendanceCorrectionWindows($workDate: NaiveDate!) {\n  currentWindow: attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n  selectedWindow: attendanceDayWindow(workDate: $workDate) {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendancePolicySettings($slim: Int! = 50) {\n  attendanceDayPolicy {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n  attendancePunchPolicy {\n    id\n    tenantId\n    isEnforced\n    siteLatitude\n    siteLongitude\n    maxDistanceMeters\n    ipAllowlist\n    updatedAt\n  }\n  shifts(limit: $slim) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n}\n\nquery PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  previewAttendanceDayPolicy(input: $input) {\n    revision\n    transition {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n    following {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nmutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  scheduleAttendanceDayPolicy(input: $input) {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nquery AttendancePunchDaySummary {\n  punchDaySummary {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n    totalWorkedMinutes\n    openSegment {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n    segments {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n  }\n}\n\nmutation AttendancePunchToday($input: PunchTodayInput) {\n  punchToday(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    checkInLat\n    checkInLng\n    checkOutLat\n    checkOutLng\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {\n  addManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {\n  updateManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {\n  addManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}\n\nmutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {\n  updateManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}"];
 
 export function attendanceGraphql(source: string) {
   return (documents as any)[source] ?? {};
 }
 
 export type DocumentType<TDocumentNode extends DocumentNode<any, any>> = TDocumentNode extends DocumentNode<  infer TType,  any>  ? TType  : never;
\ No newline at end of file

diff --git a/src/api/attendance/graphql.ts b/src/api/attendance/graphql.ts
index bc22a14..9c576d8 100644
--- a/src/api/attendance/graphql.ts
+++ b/src/api/attendance/graphql.ts
@@ -12,86 +12,101 @@ export type Scalars = {
   ID: { input: string; output: string; }
   String: { input: string; output: string; }
   Boolean: { input: boolean; output: boolean; }
   Int: { input: number; output: number; }
   Float: { input: number; output: number; }
   /**
    * Implement the DateTime<Utc> scalar
    *
    * The input/output is a string in RFC3339 format.
    */
-  DateTime: { input: any; output: any; }
+  DateTime: { input: string; output: string; }
   /**
    * ISO 8601 calendar date without timezone.
    * Format: %Y-%m-%d
    *
    * # Examples
    *
    * * `1994-11-13`
    * * `2000-02-24`
    */
-  NaiveDate: { input: any; output: any; }
+  NaiveDate: { input: string; output: string; }
   /**
    * ISO 8601 time without timezone.
    * Allows for the nanosecond precision and optional leap second representation.
    * Format: %H:%M:%S%.f
    *
    * # Examples
    *
    * * `08:59:60.123`
    */
-  NaiveTime: { input: any; output: any; }
+  NaiveTime: { input: string; output: string; }
 };
 
 export type AddManagedAttendanceSegmentInput = {
+  checkInDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkInTime: Scalars['NaiveTime']['input'];
+  checkOutDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkOutTime: Scalars['NaiveTime']['input'];
   employeeId: Scalars['ID']['input'];
   reason: Scalars['String']['input'];
   workDate: Scalars['NaiveDate']['input'];
 };
 
 /**
- * Log a **completed** check-in and check-out for a **past or today** `workDate` when both
- * live punches were missed. Same calendar day only: check-in time must be before check-out.
+ * Log a completed interval inside a historical/current attendance window.
+ * Supply both actual dates for after-midnight or otherwise ambiguous wall times.
  */
 export type AddManualAttendanceSegmentInput = {
+  checkInDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkInTime: Scalars['NaiveTime']['input'];
+  checkOutDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkOutTime: Scalars['NaiveTime']['input'];
   workDate: Scalars['NaiveDate']['input'];
 };
 
 export type CreateTimesheetEntryInput = {
   description?: InputMaybe<Scalars['String']['input']>;
   hoursWorked: Scalars['String']['input'];
   projectCode?: InputMaybe<Scalars['String']['input']>;
   workDate: Scalars['NaiveDate']['input'];
 };
 
 /** Optional client GPS (browser / mobile) for the **current** punch (in or out). */
 export type PunchTodayInput = {
   latitude?: InputMaybe<Scalars['Float']['input']>;
   longitude?: InputMaybe<Scalars['Float']['input']>;
 };
 
+export type ScheduleAttendanceDayPolicyInput = {
+  /** Tenant-local time in strict HH:mm format. */
+  boundaryTime: Scalars['String']['input'];
+  effectiveWorkDate: Scalars['NaiveDate']['input'];
+  expectedRevision: Scalars['Int']['input'];
+};
+
 export type UpdateManagedAttendanceSegmentInput = {
+  checkInDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkInTime: Scalars['NaiveTime']['input'];
+  checkOutDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkOutTime: Scalars['NaiveTime']['input'];
   expectedUpdatedAt: Scalars['DateTime']['input'];
   id: Scalars['ID']['input'];
   reason: Scalars['String']['input'];
   workDate: Scalars['NaiveDate']['input'];
 };
 
-/** Update an existing completed attendance segment after client-side review. */
+/** Correct the original completed or incomplete segment after client-side review. */
 export type UpdateManualAttendanceSegmentInput = {
+  checkInDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkInTime: Scalars['NaiveTime']['input'];
+  checkOutDate?: InputMaybe<Scalars['NaiveDate']['input']>;
   checkOutTime: Scalars['NaiveTime']['input'];
   id: Scalars['ID']['input'];
   workDate: Scalars['NaiveDate']['input'];
 };
 
 export type UpdateTimesheetEntryInput = {
   description?: InputMaybe<Scalars['String']['input']>;
   hoursWorked: Scalars['String']['input'];
   id: Scalars['ID']['input'];
   projectCode?: InputMaybe<Scalars['String']['input']>;
@@ -131,14 +146,98 @@ export type UpsertTimesheetLockPolicyInput = {
 };
 
 export type MyAttendanceBoardQueryVariables = Exact<{
   fromDate: Scalars['NaiveDate']['input'];
   toDate: Scalars['NaiveDate']['input'];
   first?: InputMaybe<Scalars['Int']['input']>;
   after?: InputMaybe<Scalars['String']['input']>;
 }>;
 
 
-export type MyAttendanceBoardQuery = { __typename?: 'QueryRoot', shifts: Array<{ __typename?: 'Shift', id: string, name: string, startTime?: any | null, endTime?: any | null, workHours?: number | null, isNightShift: boolean }>, myAttendanceSummary: { __typename?: 'AttendancePeriodSummary', completedMinutes: number, workedDays: number, averageMinutes?: number | null, incompleteSegments: number }, myAttendance: { __typename?: 'AttendanceConnection', edges: Array<{ __typename?: 'AttendanceEdge', cursor: string, node: { __typename?: 'Attendance', id: string, employeeId: string, workDate: any, checkInAt?: any | null, checkOutAt?: any | null, checkInTime?: any | null, checkOutTime?: any | null, checkInLat?: string | null, checkInLng?: string | null, checkOutLat?: string | null, checkOutLng?: string | null, status?: string | null, source?: string | null, lateMinutes?: number | null } }>, pageInfo: { __typename?: 'AttendancePageInfo', endCursor?: string | null, hasNextPage: boolean } } };
+export type MyAttendanceBoardQuery = { __typename?: 'QueryRoot', shifts: Array<{ __typename?: 'Shift', id: string, name: string, startTime?: string | null, endTime?: string | null, workHours?: number | null, isNightShift: boolean }>, myAttendanceSummary: { __typename?: 'AttendancePeriodSummary', completedMinutes: number, workedDays: number, averageMinutes?: number | null, incompleteSegments: number }, myAttendance: { __typename?: 'AttendanceConnection', edges: Array<{ __typename?: 'AttendanceEdge', cursor: string, node: { __typename?: 'Attendance', id: string, employeeId: string, workDate: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, checkInLat?: string | null, checkInLng?: string | null, checkOutLat?: string | null, checkOutLng?: string | null, status?: string | null, source?: string | null, lateMinutes?: number | null } }>, pageInfo: { __typename?: 'AttendancePageInfo', endCursor?: string | null, hasNextPage: boolean } } };
+
+export type AttendanceCurrentDayWindowQueryVariables = Exact<{ [key: string]: never; }>;
+
+
+export type AttendanceCurrentDayWindowQuery = { __typename?: 'QueryRoot', attendanceDayWindow: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number } };
+
+export type AttendanceCorrectionWindowsQueryVariables = Exact<{
+  workDate: Scalars['NaiveDate']['input'];
+}>;
+
+
+export type AttendanceCorrectionWindowsQuery = { __typename?: 'QueryRoot', currentWindow: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number }, selectedWindow: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number } };
+
+export type AttendancePolicySettingsQueryVariables = Exact<{
+  slim?: Scalars['Int']['input'];
+}>;
+
+
+export type AttendancePolicySettingsQuery = { __typename?: 'QueryRoot', attendanceDayPolicy: { __typename?: 'AttendanceDayPolicy', revision: number, initialized: boolean, legacyActivationPending: boolean, legacyActivationDate?: string | null, currentPolicy: { __typename?: 'AttendanceDayPolicyVersion', effectiveWorkDate: string, boundaryMinutes: number, timezone: string }, pendingPolicy?: { __typename?: 'AttendanceDayPolicyVersion', effectiveWorkDate: string, boundaryMinutes: number, timezone: string } | null, currentWindow: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number } }, attendancePunchPolicy: { __typename?: 'AttendancePunchPolicy', id?: string | null, tenantId: string, isEnforced: boolean, siteLatitude?: number | null, siteLongitude?: number | null, maxDistanceMeters?: number | null, ipAllowlist?: string | null, updatedAt?: string | null }, shifts: Array<{ __typename?: 'Shift', id: string, name: string, startTime?: string | null, endTime?: string | null, workHours?: number | null, isNightShift: boolean }> };
+
+export type PreviewAttendanceDayPolicyQueryVariables = Exact<{
+  input: ScheduleAttendanceDayPolicyInput;
+}>;
+
+
+export type PreviewAttendanceDayPolicyQuery = { __typename?: 'QueryRoot', previewAttendanceDayPolicy: { __typename?: 'AttendanceDayPolicyPreview', revision: number, transition: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number }, following: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number } } };
+
+export type ScheduleAttendanceDayPolicyMutationVariables = Exact<{
+  input: ScheduleAttendanceDayPolicyInput;
+}>;
+
+
+export type ScheduleAttendanceDayPolicyMutation = { __typename?: 'MutationRoot', scheduleAttendanceDayPolicy: { __typename?: 'AttendanceDayPolicy', revision: number, initialized: boolean, legacyActivationPending: boolean, legacyActivationDate?: string | null, currentPolicy: { __typename?: 'AttendanceDayPolicyVersion', effectiveWorkDate: string, boundaryMinutes: number, timezone: string }, pendingPolicy?: { __typename?: 'AttendanceDayPolicyVersion', effectiveWorkDate: string, boundaryMinutes: number, timezone: string } | null, currentWindow: { __typename?: 'AttendanceDayWindow', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number } } };
+
+export type AttendancePunchDaySummaryQueryVariables = Exact<{ [key: string]: never; }>;
+
+
+export type AttendancePunchDaySummaryQuery = { __typename?: 'QueryRoot', punchDaySummary: { __typename?: 'PunchDaySummary', workDate: string, startsAt: string, endsAt: string, timezone: string, boundaryMinutes: number, totalWorkedMinutes: number, openSegment?: { __typename?: 'Attendance', id: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, checkInLat?: string | null, checkInLng?: string | null, checkOutLat?: string | null, checkOutLng?: string | null, source?: string | null, status?: string | null } | null, segments: Array<{ __typename?: 'Attendance', id: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, checkInLat?: string | null, checkInLng?: string | null, checkOutLat?: string | null, checkOutLng?: string | null, source?: string | null, status?: string | null }> } };
+
+export type AttendancePunchTodayMutationVariables = Exact<{
+  input?: InputMaybe<PunchTodayInput>;
+}>;
+
+
+export type AttendancePunchTodayMutation = { __typename?: 'MutationRoot', punchToday: { __typename?: 'Attendance', id: string, workDate: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, checkInLat?: string | null, checkInLng?: string | null, checkOutLat?: string | null, checkOutLng?: string | null, source?: string | null, status?: string | null } };
+
+export type AttendanceAddManualSegmentMutationVariables = Exact<{
+  input: AddManualAttendanceSegmentInput;
+}>;
+
+
+export type AttendanceAddManualSegmentMutation = { __typename?: 'MutationRoot', addManualAttendanceSegment: { __typename?: 'Attendance', id: string, workDate: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, source?: string | null, status?: string | null } };
+
+export type AttendanceUpdateManualSegmentMutationVariables = Exact<{
+  input: UpdateManualAttendanceSegmentInput;
+}>;
+
+
+export type AttendanceUpdateManualSegmentMutation = { __typename?: 'MutationRoot', updateManualAttendanceSegment: { __typename?: 'Attendance', id: string, workDate: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, source?: string | null, status?: string | null } };
+
+export type AttendanceAddManagedSegmentMutationVariables = Exact<{
+  input: AddManagedAttendanceSegmentInput;
+}>;
+
+
+export type AttendanceAddManagedSegmentMutation = { __typename?: 'MutationRoot', addManagedAttendanceSegment: { __typename?: 'ManagedAttendance', id: string, employeeId: string, employeeName: string, employeeCode: string, workDate: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, status?: string | null, source?: string | null, regularizationStatus?: string | null, createdAt: string, updatedAt: string } };
+
+export type AttendanceUpdateManagedSegmentMutationVariables = Exact<{
+  input: UpdateManagedAttendanceSegmentInput;
+}>;
+
+
+export type AttendanceUpdateManagedSegmentMutation = { __typename?: 'MutationRoot', updateManagedAttendanceSegment: { __typename?: 'ManagedAttendance', id: string, employeeId: string, employeeName: string, employeeCode: string, workDate: string, checkInAt?: string | null, checkOutAt?: string | null, checkInTime?: string | null, checkOutTime?: string | null, status?: string | null, source?: string | null, regularizationStatus?: string | null, createdAt: string, updatedAt: string } };
 
 
-export const MyAttendanceBoardDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"MyAttendanceBoard"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"fromDate"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"NaiveDate"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"toDate"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"NaiveDate"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"first"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}},"defaultValue":{"kind":"IntValue","value":"50"}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"after"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"shifts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"IntValue","value":"100"}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"workHours"}},{"kind":"Field","name":{"kind":"Name","value":"isNightShift"}}]}},{"kind":"Field","name":{"kind":"Name","value":"myAttendanceSummary"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"fromDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"fromDate"}}},{"kind":"Argument","name":{"kind":"Name","value":"toDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"toDate"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"completedMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"workedDays"}},{"kind":"Field","name":{"kind":"Name","value":"averageMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"incompleteSegments"}}]}},{"kind":"Field","name":{"kind":"Name","value":"myAttendance"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"fromDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"fromDate"}}},{"kind":"Argument","name":{"kind":"Name","value":"toDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"toDate"}}},{"kind":"Argument","name":{"kind":"Name","value":"first"},"value":{"kind":"Variable","name":{"kind":"Name","value":"first"}}},{"kind":"Argument","name":{"kind":"Name","value":"after"},"value":{"kind":"Variable","name":{"kind":"Name","value":"after"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"edges"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"cursor"}},{"kind":"Field","name":{"kind":"Name","value":"node"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"employeeId"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLng"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLng"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"lateMinutes"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"pageInfo"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"endCursor"}},{"kind":"Field","name":{"kind":"Name","value":"hasNextPage"}}]}}]}}]}}]} as unknown as DocumentNode<MyAttendanceBoardQuery, MyAttendanceBoardQueryVariables>;
\ No newline at end of file
+export const MyAttendanceBoardDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"MyAttendanceBoard"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"fromDate"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"NaiveDate"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"toDate"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"NaiveDate"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"first"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}},"defaultValue":{"kind":"IntValue","value":"50"}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"after"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"shifts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"IntValue","value":"100"}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"workHours"}},{"kind":"Field","name":{"kind":"Name","value":"isNightShift"}}]}},{"kind":"Field","name":{"kind":"Name","value":"myAttendanceSummary"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"fromDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"fromDate"}}},{"kind":"Argument","name":{"kind":"Name","value":"toDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"toDate"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"completedMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"workedDays"}},{"kind":"Field","name":{"kind":"Name","value":"averageMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"incompleteSegments"}}]}},{"kind":"Field","name":{"kind":"Name","value":"myAttendance"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"fromDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"fromDate"}}},{"kind":"Argument","name":{"kind":"Name","value":"toDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"toDate"}}},{"kind":"Argument","name":{"kind":"Name","value":"first"},"value":{"kind":"Variable","name":{"kind":"Name","value":"first"}}},{"kind":"Argument","name":{"kind":"Name","value":"after"},"value":{"kind":"Variable","name":{"kind":"Name","value":"after"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"edges"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"cursor"}},{"kind":"Field","name":{"kind":"Name","value":"node"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"employeeId"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLng"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLng"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"lateMinutes"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"pageInfo"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"endCursor"}},{"kind":"Field","name":{"kind":"Name","value":"hasNextPage"}}]}}]}}]}}]} as unknown as DocumentNode<MyAttendanceBoardQuery, MyAttendanceBoardQueryVariables>;
+export const AttendanceCurrentDayWindowDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"AttendanceCurrentDayWindow"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"attendanceDayWindow"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}}]}}]} as unknown as DocumentNode<AttendanceCurrentDayWindowQuery, AttendanceCurrentDayWindowQueryVariables>;
+export const AttendanceCorrectionWindowsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"AttendanceCorrectionWindows"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"workDate"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"NaiveDate"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","alias":{"kind":"Name","value":"currentWindow"},"name":{"kind":"Name","value":"attendanceDayWindow"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}},{"kind":"Field","alias":{"kind":"Name","value":"selectedWindow"},"name":{"kind":"Name","value":"attendanceDayWindow"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"workDate"},"value":{"kind":"Variable","name":{"kind":"Name","value":"workDate"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}}]}}]} as unknown as DocumentNode<AttendanceCorrectionWindowsQuery, AttendanceCorrectionWindowsQueryVariables>;
+export const AttendancePolicySettingsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"AttendancePolicySettings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"slim"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},"defaultValue":{"kind":"IntValue","value":"50"}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"attendanceDayPolicy"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"revision"}},{"kind":"Field","name":{"kind":"Name","value":"initialized"}},{"kind":"Field","name":{"kind":"Name","value":"legacyActivationPending"}},{"kind":"Field","name":{"kind":"Name","value":"legacyActivationDate"}},{"kind":"Field","name":{"kind":"Name","value":"currentPolicy"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"effectiveWorkDate"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}}]}},{"kind":"Field","name":{"kind":"Name","value":"pendingPolicy"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"effectiveWorkDate"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}}]}},{"kind":"Field","name":{"kind":"Name","value":"currentWindow"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"attendancePunchPolicy"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"tenantId"}},{"kind":"Field","name":{"kind":"Name","value":"isEnforced"}},{"kind":"Field","name":{"kind":"Name","value":"siteLatitude"}},{"kind":"Field","name":{"kind":"Name","value":"siteLongitude"}},{"kind":"Field","name":{"kind":"Name","value":"maxDistanceMeters"}},{"kind":"Field","name":{"kind":"Name","value":"ipAllowlist"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"shifts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"slim"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"workHours"}},{"kind":"Field","name":{"kind":"Name","value":"isNightShift"}}]}}]}}]} as unknown as DocumentNode<AttendancePolicySettingsQuery, AttendancePolicySettingsQueryVariables>;
+export const PreviewAttendanceDayPolicyDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"PreviewAttendanceDayPolicy"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ScheduleAttendanceDayPolicyInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"previewAttendanceDayPolicy"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"revision"}},{"kind":"Field","name":{"kind":"Name","value":"transition"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}},{"kind":"Field","name":{"kind":"Name","value":"following"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}}]}}]}}]} as unknown as DocumentNode<PreviewAttendanceDayPolicyQuery, PreviewAttendanceDayPolicyQueryVariables>;
+export const ScheduleAttendanceDayPolicyDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"ScheduleAttendanceDayPolicy"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ScheduleAttendanceDayPolicyInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"scheduleAttendanceDayPolicy"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"revision"}},{"kind":"Field","name":{"kind":"Name","value":"initialized"}},{"kind":"Field","name":{"kind":"Name","value":"legacyActivationPending"}},{"kind":"Field","name":{"kind":"Name","value":"legacyActivationDate"}},{"kind":"Field","name":{"kind":"Name","value":"currentPolicy"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"effectiveWorkDate"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}}]}},{"kind":"Field","name":{"kind":"Name","value":"pendingPolicy"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"effectiveWorkDate"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}}]}},{"kind":"Field","name":{"kind":"Name","value":"currentWindow"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}}]}}]}}]}}]} as unknown as DocumentNode<ScheduleAttendanceDayPolicyMutation, ScheduleAttendanceDayPolicyMutationVariables>;
+export const AttendancePunchDaySummaryDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"AttendancePunchDaySummary"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"punchDaySummary"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"startsAt"}},{"kind":"Field","name":{"kind":"Name","value":"endsAt"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"boundaryMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"totalWorkedMinutes"}},{"kind":"Field","name":{"kind":"Name","value":"openSegment"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLng"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLng"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"status"}}]}},{"kind":"Field","name":{"kind":"Name","value":"segments"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLng"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLng"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"status"}}]}}]}}]}}]} as unknown as DocumentNode<AttendancePunchDaySummaryQuery, AttendancePunchDaySummaryQueryVariables>;
+export const AttendancePunchTodayDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"AttendancePunchToday"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"PunchTodayInput"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"punchToday"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkInLng"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLat"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutLng"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"status"}}]}}]}}]} as unknown as DocumentNode<AttendancePunchTodayMutation, AttendancePunchTodayMutationVariables>;
+export const AttendanceAddManualSegmentDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"AttendanceAddManualSegment"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"AddManualAttendanceSegmentInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"addManualAttendanceSegment"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"status"}}]}}]}}]} as unknown as DocumentNode<AttendanceAddManualSegmentMutation, AttendanceAddManualSegmentMutationVariables>;
+export const AttendanceUpdateManualSegmentDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"AttendanceUpdateManualSegment"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateManualAttendanceSegmentInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateManualAttendanceSegment"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"status"}}]}}]}}]} as unknown as DocumentNode<AttendanceUpdateManualSegmentMutation, AttendanceUpdateManualSegmentMutationVariables>;
+export const AttendanceAddManagedSegmentDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"AttendanceAddManagedSegment"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"AddManagedAttendanceSegmentInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"addManagedAttendanceSegment"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"employeeId"}},{"kind":"Field","name":{"kind":"Name","value":"employeeName"}},{"kind":"Field","name":{"kind":"Name","value":"employeeCode"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"regularizationStatus"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<AttendanceAddManagedSegmentMutation, AttendanceAddManagedSegmentMutationVariables>;
+export const AttendanceUpdateManagedSegmentDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"AttendanceUpdateManagedSegment"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateManagedAttendanceSegmentInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateManagedAttendanceSegment"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"employeeId"}},{"kind":"Field","name":{"kind":"Name","value":"employeeName"}},{"kind":"Field","name":{"kind":"Name","value":"employeeCode"}},{"kind":"Field","name":{"kind":"Name","value":"workDate"}},{"kind":"Field","name":{"kind":"Name","value":"checkInAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutAt"}},{"kind":"Field","name":{"kind":"Name","value":"checkInTime"}},{"kind":"Field","name":{"kind":"Name","value":"checkOutTime"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"regularizationStatus"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<AttendanceUpdateManagedSegmentMutation, AttendanceUpdateManagedSegmentMutationVariables>;
\ No newline at end of file

diff --git a/src/api/documents/attendance.graphql b/src/api/documents/attendance.graphql
index cf33188..e7b17f5 100644
--- a/src/api/documents/attendance.graphql
+++ b/src/api/documents/attendance.graphql
@@ -1,11 +1,16 @@
-query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {
+query MyAttendanceBoard(
+  $fromDate: NaiveDate!
+  $toDate: NaiveDate!
+  $first: Int = 50
+  $after: String
+) {
   shifts(limit: 100) {
     id
     name
     startTime
     endTime
     workHours
     isNightShift
   }
   myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {
     completedMinutes
@@ -32,10 +37,245 @@ query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int
         source
         lateMinutes
       }
     }
     pageInfo {
       endCursor
       hasNextPage
     }
   }
 }
+
+query AttendanceCurrentDayWindow {
+  attendanceDayWindow {
+    workDate
+    startsAt
+    endsAt
+    timezone
+    boundaryMinutes
+  }
+}
+
+query AttendanceCorrectionWindows($workDate: NaiveDate!) {
+  currentWindow: attendanceDayWindow {
+    workDate
+    startsAt
+    endsAt
+    timezone
+    boundaryMinutes
+  }
+  selectedWindow: attendanceDayWindow(workDate: $workDate) {
+    workDate
+    startsAt
+    endsAt
+    timezone
+    boundaryMinutes
+  }
+}
+
+query AttendancePolicySettings($slim: Int! = 50) {
+  attendanceDayPolicy {
+    revision
+    initialized
+    legacyActivationPending
+    legacyActivationDate
+    currentPolicy {
+      effectiveWorkDate
+      boundaryMinutes
+      timezone
+    }
+    pendingPolicy {
+      effectiveWorkDate
+      boundaryMinutes
+      timezone
+    }
+    currentWindow {
+      workDate
+      startsAt
+      endsAt
+      timezone
+      boundaryMinutes
+    }
+  }
+  attendancePunchPolicy {
+    id
+    tenantId
+    isEnforced
+    siteLatitude
+    siteLongitude
+    maxDistanceMeters
+    ipAllowlist
+    updatedAt
+  }
+  shifts(limit: $slim) {
+    id
+    name
+    startTime
+    endTime
+    workHours
+    isNightShift
+  }
+}
+
+query PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {
+  previewAttendanceDayPolicy(input: $input) {
+    revision
+    transition {
+      workDate
+      startsAt
+      endsAt
+      timezone
+      boundaryMinutes
+    }
+    following {
+      workDate
+      startsAt
+      endsAt
+      timezone
+      boundaryMinutes
+    }
+  }
+}
+
+mutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {
+  scheduleAttendanceDayPolicy(input: $input) {
+    revision
+    initialized
+    legacyActivationPending
+    legacyActivationDate
+    currentPolicy {
+      effectiveWorkDate
+      boundaryMinutes
+      timezone
+    }
+    pendingPolicy {
+      effectiveWorkDate
+      boundaryMinutes
+      timezone
+    }
+    currentWindow {
+      workDate
+      startsAt
+      endsAt
+      timezone
+      boundaryMinutes
+    }
+  }
+}
+
+query AttendancePunchDaySummary {
+  punchDaySummary {
+    workDate
+    startsAt
+    endsAt
+    timezone
+    boundaryMinutes
+    totalWorkedMinutes
+    openSegment {
+      id
+      checkInAt
+      checkOutAt
+      checkInTime
+      checkOutTime
+      checkInLat
+      checkInLng
+      checkOutLat
+      checkOutLng
+      source
+      status
+    }
+    segments {
+      id
+      checkInAt
+      checkOutAt
+      checkInTime
+      checkOutTime
+      checkInLat
+      checkInLng
+      checkOutLat
+      checkOutLng
+      source
+      status
+    }
+  }
+}
+
+mutation AttendancePunchToday($input: PunchTodayInput) {
+  punchToday(input: $input) {
+    id
+    workDate
+    checkInAt
+    checkOutAt
+    checkInTime
+    checkOutTime
+    checkInLat
+    checkInLng
+    checkOutLat
+    checkOutLng
+    source
+    status
+  }
+}
+
+mutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {
+  addManualAttendanceSegment(input: $input) {
+    id
+    workDate
+    checkInAt
+    checkOutAt
+    checkInTime
+    checkOutTime
+    source
+    status
+  }
+}
+
+mutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {
+  updateManualAttendanceSegment(input: $input) {
+    id
+    workDate
+    checkInAt
+    checkOutAt
+    checkInTime
+    checkOutTime
+    source
+    status
+  }
+}
+
+mutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {
+  addManagedAttendanceSegment(input: $input) {
+    id
+    employeeId
+    employeeName
+    employeeCode
+    workDate
+    checkInAt
+    checkOutAt
+    checkInTime
+    checkOutTime
+    status
+    source
+    regularizationStatus
+    createdAt
+    updatedAt
+  }
+}
+
+mutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {
+  updateManagedAttendanceSegment(input: $input) {
+    id
+    employeeId
+    employeeName
+    employeeCode
+    workDate
+    checkInAt
+    checkOutAt
+    checkInTime
+    checkOutTime
+    status
+    source
+    regularizationStatus
+    createdAt
+    updatedAt
+  }
+}
diff --git a/src/modules/admin/AdminAttendancePolicyPage.tsx b/src/modules/admin/AdminAttendancePolicyPage.tsx
index 92aa158..40a4fcb 100644
--- a/src/modules/admin/AdminAttendancePolicyPage.tsx
+++ b/src/modules/admin/AdminAttendancePolicyPage.tsx
@@ -1,23 +1,28 @@
-import { FormEvent, useCallback, useEffect, useState } from 'react';
+import { useCallback, useEffect, useState, type FormEvent } from 'react';
 
 import {
-  ClientOpsAdminAttendancePolicyDocument,
-  ClientOpsUpsertAttendancePunchPolicyDocument,
-} from '../../api/graphql/graphql';
+  AttendancePolicySettingsDocument,
+  type AttendancePolicySettingsQuery,
+} from '../../api/attendance/graphql';
+import { ClientOpsUpsertAttendancePunchPolicyDocument } from '../../api/graphql/graphql';
+import { createPermissionService } from '../../auth/permissionService';
 import Button from '../../components/common/Button';
 import Card from '../../components/common/Card';
 import Input from '../../components/common/Input';
 import PageInformation from '../../components/common/PageInformation';
+import { useAuth } from '../../contexts/AuthContext';
 import { useGraphClient } from '../../hooks/useGraphClient';
 import { graphQlUserMessage } from '../../utils/graphqlUserMessage';
 
+import AttendanceDayPolicySettings from './AttendanceDayPolicySettings';
+
 const DECIMAL_PATTERN = /^-?(?:\d+|\d+\.\d+|\.\d+)$/;
 
 const parseOptionalDecimal = (raw: string) => {
   const trimmed = raw.trim();
   if (!trimmed) return null;
   if (!DECIMAL_PATTERN.test(trimmed)) return NaN;
   return Number(trimmed);
 };
 
 const isValidIpv4CidrToken = (token: string) => {
@@ -30,31 +35,34 @@ const isValidIpv4CidrToken = (token: string) => {
     const value = Number(part);
     return value >= 0 && value <= 255;
   });
   if (!hasValidOctets) return false;
   if (cidr == null) return true;
   if (!/^\d{1,2}$/.test(cidr)) return false;
   const mask = Number(cidr);
   return mask >= 0 && mask <= 32;
 };
 
-const AdminAttendancePolicyPage = () => {
+const AuthorizedAttendancePolicyPage = () => {
   const client = useGraphClient('client');
   const [policy, setPolicy] = useState<{
     id?: string | null;
     isEnforced: boolean;
     siteLatitude?: number | null;
     siteLongitude?: number | null;
     maxDistanceMeters?: number | null;
     ipAllowlist?: string | null;
     updatedAt?: string | null;
   } | null>(null);
+  const [dayPolicy, setDayPolicy] = useState<
+    AttendancePolicySettingsQuery['attendanceDayPolicy'] | null
+  >(null);
   const [shifts, setShifts] = useState<
     {
       id: string;
       name: string;
       startTime?: string | null;
       endTime?: string | null;
       workHours?: number | null;
       isNightShift: boolean;
     }[]
   >([]);
@@ -63,61 +71,58 @@ const AdminAttendancePolicyPage = () => {
   const [saving, setSaving] = useState(false);
   const [formError, setFormError] = useState<string | null>(null);
 
   const [isEnforced, setIsEnforced] = useState(false);
   const [siteLatitude, setSiteLatitude] = useState('');
   const [siteLongitude, setSiteLongitude] = useState('');
   const [maxDistanceMeters, setMaxDistanceMeters] = useState('');
   const [ipAllowlist, setIpAllowlist] = useState('');
 
   const load = useCallback(async () => {
-    return client.request<{
-      attendancePunchPolicy: {
-        id?: string | null;
-        isEnforced: boolean;
-        siteLatitude?: number | null;
-        siteLongitude?: number | null;
-        maxDistanceMeters?: number | null;
-        ipAllowlist?: string | null;
-        updatedAt?: string | null;
-      };
-      shifts: typeof shifts;
-    }>(ClientOpsAdminAttendancePolicyDocument, { slim: 50 });
+    return client.request<AttendancePolicySettingsQuery>(AttendancePolicySettingsDocument);
   }, [client]);
 
   useEffect(() => {
     let c = false;
     void (async () => {
       try {
         setLoading(true);
         setError(null);
         const r = await load();
         if (c) return;
         setPolicy(r.attendancePunchPolicy);
+        setDayPolicy(r.attendanceDayPolicy);
         setShifts(r.shifts);
         const p = r.attendancePunchPolicy;
         setIsEnforced(p.isEnforced);
         setSiteLatitude(p.siteLatitude != null ? String(p.siteLatitude) : '');
         setSiteLongitude(p.siteLongitude != null ? String(p.siteLongitude) : '');
         setMaxDistanceMeters(p.maxDistanceMeters != null ? String(p.maxDistanceMeters) : '');
         setIpAllowlist(p.ipAllowlist ?? '');
       } catch (e) {
         if (!c) setError(graphQlUserMessage(e));
       } finally {
         if (!c) setLoading(false);
       }
     })();
     return () => {
       c = true;
     };
   }, [load]);
 
+  const reloadPolicy = useCallback(async () => {
+    const result = await load();
+    setPolicy(result.attendancePunchPolicy);
+    setDayPolicy(result.attendanceDayPolicy);
+    setShifts(result.shifts);
+  }, [load]);
+
   const onSave = async (e: FormEvent) => {
     e.preventDefault();
     setFormError(null);
     const lat = parseOptionalDecimal(siteLatitude);
     const lng = parseOptionalDecimal(siteLongitude);
     const maxM = parseOptionalDecimal(maxDistanceMeters);
     const allowlistTokens = ipAllowlist
       .split(',')
       .map((part) => part.trim())
       .filter(Boolean);
@@ -133,25 +138,29 @@ const AdminAttendancePolicyPage = () => {
       setFormError('Max distance must be a whole number greater than 0 meters.');
       return;
     }
     if (allowlistTokens.some((token) => !isValidIpv4CidrToken(token))) {
       setFormError('IP allowlist must contain comma-separated IPv4 addresses or IPv4 CIDR ranges.');
       return;
     }
     const hasCompleteGeoRule = lat != null && lng != null && maxM != null;
     const hasPartialGeoRule = lat != null || lng != null || maxM != null;
     if (hasPartialGeoRule && !hasCompleteGeoRule) {
-      setFormError('Latitude, longitude, and max distance are required together for geofence enforcement.');
+      setFormError(
+        'Latitude, longitude, and max distance are required together for geofence enforcement.'
+      );
       return;
     }
     if (isEnforced && !hasCompleteGeoRule && !allowlistTokens.length) {
-      setFormError('Enable enforcement only after adding a complete geofence or at least one IP rule.');
+      setFormError(
+        'Enable enforcement only after adding a complete geofence or at least one IP rule.'
+      );
       return;
     }
     setSaving(true);
     try {
       await client.request(ClientOpsUpsertAttendancePunchPolicyDocument, {
         input: {
           isEnforced,
           siteLatitude: lat,
           siteLongitude: lng,
           maxDistanceMeters: maxM,
@@ -168,20 +177,27 @@ const AdminAttendancePolicyPage = () => {
   };
 
   return (
     <div className="space-y-4">
       <h1 className="sr-only">Attendance punch policy</h1>
       {error && (
         <Card>
           <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
         </Card>
       )}
+      {dayPolicy ? (
+        <AttendanceDayPolicySettings
+          policy={dayPolicy}
+          onPolicyChanged={setDayPolicy}
+          reloadPolicy={reloadPolicy}
+        />
+      ) : null}
       <Card title="Live Punch Policy">
         {loading ? (
           <p className="text-sm text-gray-500">Loading...</p>
         ) : (
           <form onSubmit={(e) => void onSave(e)} className="space-y-4">
             {formError && <p className="text-sm text-red-600 dark:text-red-400">{formError}</p>}
             <label className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
               <input
                 type="checkbox"
                 checked={isEnforced}
@@ -250,11 +266,24 @@ const AdminAttendancePolicyPage = () => {
             </ul>
           ) : (
             <p className="text-sm text-gray-500">No Shift Templates.</p>
           )}
         </Card>
       </PageInformation>
     </div>
   );
 };
 
+const AdminAttendancePolicyPage = () => {
+  const { clientSession } = useAuth();
+  const permissions = createPermissionService(clientSession);
+  if (!permissions.canRoute('/admin/attendance-policy')) {
+    return (
+      <p role="status" className="text-sm text-content-secondary">
+        You do not have access to manage attendance policy.
+      </p>
+    );
+  }
+  return <AuthorizedAttendancePolicyPage />;
+};
+
 export default AdminAttendancePolicyPage;
diff --git a/src/modules/attendance/AttendancePage.editorOwnership.test.tsx b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
index 697ec01..c1080f2 100644
--- a/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
+++ b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
@@ -1,49 +1,78 @@
 // @vitest-environment jsdom
 import { fireEvent, screen, waitFor } from '@testing-library/react';
 import { expect, it, vi } from 'vitest';
 
+import { AttendanceCurrentDayWindowDocument } from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 
 import {
   authState,
   boardResponse,
+  currentWindowResponse,
   graphClient,
   graphClientState,
   policyResponse,
   renderPage,
   rerenderPage,
 } from './attendancePageTestSupport';
 
 it('discards an open attendance edit when the client or employee changes, including returning to the previous identity', async () => {
   authState.clientSession.permissions = new Set(['attendance:punch_self']);
   const view = renderPage();
   fireEvent.click(await screen.findByRole('button', { name: 'Adjust day' }));
   expect(screen.getByRole('dialog', { name: 'Update Attendance Segment' })).toBeTruthy();
   expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-08-24');
 
   authState.clientSession.employeeId = 'employee-replacement';
   graphClientState.current = {
-    request: vi.fn((document: unknown) =>
-      Promise.resolve(
-        document === AttendanceAdjustmentPolicyDocument ? policyResponse : boardResponse()
-      )
-    ),
+    request: vi.fn((document: unknown) => {
+      if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+      if (document === AttendanceCurrentDayWindowDocument) {
+        return Promise.resolve(currentWindowResponse);
+      }
+      return Promise.resolve(boardResponse());
+    }),
   };
   rerenderPage(view);
   await waitFor(() =>
     expect(
       screen.getByRole<HTMLButtonElement>('button', { name: 'Add Missed Punches' }).disabled
     ).toBe(false)
   );
   expect(screen.queryByRole('dialog')).toBeNull();
 
   authState.clientSession.employeeId = 'employee-self';
   graphClientState.current = graphClient;
   rerenderPage(view);
   await waitFor(() =>
     expect(
       screen.getByRole<HTMLButtonElement>('button', { name: 'Add Missed Punches' }).disabled
     ).toBe(false)
   );
   expect(screen.queryByRole('dialog')).toBeNull();
 });
+
+it('uses the server current work date for the initial month and missed-punch default', async () => {
+  vi.setSystemTime(new Date('2026-09-01T00:30:00Z'));
+  authState.clientSession.permissions = new Set(['attendance:punch_self']);
+  graphClient.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument) {
+      return Promise.resolve({
+        attendanceDayWindow: {
+          ...currentWindowResponse.attendanceDayWindow,
+          workDate: '2026-08-31',
+          startsAt: '2026-08-30T23:30:00Z',
+          endsAt: '2026-08-31T23:30:00Z',
+        },
+      });
+    }
+    return Promise.resolve(boardResponse());
+  });
+
+  renderPage();
+
+  await waitFor(() => expect(screen.getByLabelText<HTMLSelectElement>('Month').value).toBe('7'));
+  fireEvent.click(screen.getByRole('button', { name: 'Add Missed Punches' }));
+  expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-08-31');
+});
diff --git a/src/modules/attendance/AttendancePage.ownership.test.tsx b/src/modules/attendance/AttendancePage.ownership.test.tsx
index 2ac64bc..38b191b 100644
--- a/src/modules/attendance/AttendancePage.ownership.test.tsx
+++ b/src/modules/attendance/AttendancePage.ownership.test.tsx
@@ -1,34 +1,40 @@
 // @vitest-environment jsdom
 import { act, fireEvent, screen, waitFor } from '@testing-library/react';
 import { expect, it, vi } from 'vitest';
 
-import { MyAttendanceBoardDocument } from '../../api/attendance/graphql';
+import {
+  AttendanceCurrentDayWindowDocument,
+  MyAttendanceBoardDocument,
+} from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 
 import {
   graphClientState,
   graphClient,
   authState,
   policyResponse,
+  currentWindowResponse,
   deferred,
   boardResponse,
   renderPage,
   rerenderPage,
   advanceToNextPage,
 } from './attendancePageTestSupport';
 
 it('does not let a deferred refresh overwrite a newer month request', async () => {
   const refresh = deferred<ReturnType<typeof boardResponse>>();
   let boardCalls = 0;
   graphClient.request.mockImplementation((document: unknown, variables?: { fromDate?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     boardCalls += 1;
     if (boardCalls === 2) return refresh.promise;
     return Promise.resolve(
       boardResponse({
         rows: [
           {
             id: `page-${boardCalls}`,
             employeeId: 'employee-self',
             workDate: variables?.fromDate ?? '2026-08-24',
             checkInTime: '09:00:00',
@@ -80,20 +86,22 @@ it('does not let a deferred refresh overwrite a newer month request', async () =
 
   await waitFor(() => expect(screen.queryByText('Stale refresh')).toBeNull());
   expect(screen.getByText('Newer month')).toBeTruthy();
 });
 
 it('hides stale paging controls and rows during a deferred month transition', async () => {
   const nextMonth = deferred<ReturnType<typeof boardResponse>>();
   let boardCalls = 0;
   graphClient.request.mockImplementation((document: unknown, variables?: { fromDate?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     boardCalls += 1;
     if (boardCalls === 2) return nextMonth.promise;
     return Promise.resolve(
       boardResponse({
         endCursor: 'next-page',
         hasNextPage: true,
         rows: [
           {
             id: `page-${boardCalls}`,
             employeeId: 'employee-self',
@@ -153,20 +161,22 @@ it('hides stale paging controls and rows during a deferred month transition', as
       false
     )
   );
 });
 
 it('hides stale board rows and paging during a deferred client/session transition', async () => {
   const replacement = deferred<ReturnType<typeof boardResponse>>();
   const replacementClient = { request: vi.fn() };
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(
       boardResponse({
         endCursor: 'client-a-next',
         hasNextPage: true,
         rows: [
           {
             id: 'client-a-row',
             employeeId: 'employee-self',
             workDate: '2026-08-24',
             checkInTime: '09:00:00',
@@ -178,20 +188,22 @@ it('hides stale board rows and paging during a deferred client/session transitio
             status: 'Client A',
             source: 'SELF_REPORTED',
             lateMinutes: null,
           },
         ],
       })
     );
   });
   replacementClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return replacement.promise;
   });
 
   const view = renderPage();
 
   await screen.findByText('Client A');
   await waitFor(() =>
     expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Next page' }).disabled).toBe(
       false
     )
@@ -236,20 +248,22 @@ it('hides stale board rows and paging during a deferred client/session transitio
       false
     )
   );
 });
 
 it('resets a page-two cursor before requesting a deferred client/session transition', async () => {
   const replacement = deferred<ReturnType<typeof boardResponse>>();
   const replacementClient = { request: vi.fn() };
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     if (variables?.after === 'client-a-page-two') {
       return Promise.resolve(
         boardResponse({
           endCursor: 'client-a-page-three',
           hasNextPage: true,
           rows: [
             {
               id: 'client-a-page-two-row',
               employeeId: 'employee-self',
               workDate: '2026-08-23',
@@ -285,20 +299,22 @@ it('resets a page-two cursor before requesting a deferred client/session transit
             status: 'Client A page 1',
             source: 'SELF_REPORTED',
             lateMinutes: null,
           },
         ],
       })
     );
   });
   replacementClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return replacement.promise;
   });
 
   const view = renderPage();
 
   await screen.findByText('Client A page 1');
   await advanceToNextPage();
   await screen.findByText('Client A page 2');
   expect(screen.getByText(/Page 2/)).toBeTruthy();
 
diff --git a/src/modules/attendance/AttendancePage.paging.test.tsx b/src/modules/attendance/AttendancePage.paging.test.tsx
index 642faff..1a5d613 100644
--- a/src/modules/attendance/AttendancePage.paging.test.tsx
+++ b/src/modules/attendance/AttendancePage.paging.test.tsx
@@ -1,19 +1,23 @@
 // @vitest-environment jsdom
 import { fireEvent, screen, waitFor, within } from '@testing-library/react';
 import { expect, it } from 'vitest';
 
-import { MyAttendanceBoardDocument } from '../../api/attendance/graphql';
+import {
+  AttendanceCurrentDayWindowDocument,
+  MyAttendanceBoardDocument,
+} from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 
 import {
   graphClient,
+  currentWindowResponse,
   policyResponse,
   boardResponse,
   renderPage,
   advanceToNextPage,
   requestCalls,
 } from './attendancePageTestSupport';
 
 it('refreshes the active cursor page instead of returning to the first page', async () => {
   renderPage();
 
@@ -70,20 +74,22 @@ it('keeps complete monthly totals unchanged when navigating attendance pages', a
         checkOutLat: null,
         checkOutLng: null,
         status: 'Present',
         source: 'SELF_REPORTED',
         lateMinutes: null,
       },
     ],
   });
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(variables?.after === 'page-two' ? secondPage : firstPage);
   });
 
   renderPage();
 
   const summary = screen.getByLabelText('Monthly attendance summary');
   await waitFor(() => expect(within(summary).getByText('12h 00m')).toBeTruthy());
   expect(within(summary).getByText('6h 00m')).toBeTruthy();
   expect(screen.queryByText(/on This Page/)).toBeNull();
 
@@ -95,20 +101,22 @@ it('keeps complete monthly totals unchanged when navigating attendance pages', a
       expect.objectContaining({ after: 'page-two' })
     )
   );
   await waitFor(() => expect(within(summary).getByText('12h 00m')).toBeTruthy());
   expect(within(summary).getByText('6h 00m')).toBeTruthy();
 });
 
 it('shows no average for an open-only month while identifying incomplete punches', async () => {
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(
       boardResponse({
         summary: {
           completedMinutes: 0,
           workedDays: 0,
           averageMinutes: null,
           incompleteSegments: 3,
         },
       })
     );
@@ -116,20 +124,22 @@ it('shows no average for an open-only month while identifying incomplete punches
   renderPage();
   const summary = screen.getByLabelText('Monthly attendance summary');
   await waitFor(() => expect(within(summary).getByText('0h 00m')).toBeTruthy());
   expect(within(summary).getByText('—')).toBeTruthy();
   expect(within(summary).getByText('3')).toBeTruthy();
 });
 
 it('uses the local cursor stack when returning to a prior page', async () => {
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     if (variables?.after === 'cursor-one') {
       return Promise.resolve(boardResponse({ endCursor: 'cursor-two', hasNextPage: true }));
     }
     if (variables?.after === 'cursor-two') return Promise.resolve(boardResponse());
     return Promise.resolve(boardResponse({ endCursor: 'cursor-one', hasNextPage: true }));
   });
   renderPage();
 
   await screen.findByRole('button', { name: 'Next page' });
   await advanceToNextPage();
diff --git a/src/modules/attendance/AttendancePage.refresh.test.tsx b/src/modules/attendance/AttendancePage.refresh.test.tsx
index 5b6790b..4ecd3e8 100644
--- a/src/modules/attendance/AttendancePage.refresh.test.tsx
+++ b/src/modules/attendance/AttendancePage.refresh.test.tsx
@@ -1,31 +1,35 @@
 // @vitest-environment jsdom
 import { act, fireEvent, screen, waitFor } from '@testing-library/react';
 import { expect, it } from 'vitest';
 
+import { AttendanceCurrentDayWindowDocument } from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 
 import {
   graphClient,
   authState,
   policyResponse,
   deferred,
   boardResponse,
+  currentWindowResponse,
   renderPage,
   advanceToNextPage,
 } from './attendancePageTestSupport';
 
 it('does not show refresh success after refresh A is superseded by B and return to A', async () => {
   const pendingRefresh = deferred<ReturnType<typeof boardResponse>>();
   let boardCalls = 0;
   graphClient.request.mockImplementation((document: unknown, variables?: { fromDate?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     boardCalls += 1;
     if (boardCalls === 2) return pendingRefresh.promise;
     return Promise.resolve(
       boardResponse({
         rows: [
           {
             id: `page-${boardCalls}`,
             employeeId: 'employee-self',
             workDate: variables?.fromDate ?? '2026-08-24',
             checkInTime: '09:00:00',
@@ -58,34 +62,36 @@ it('does not show refresh success after refresh A is superseded by B and return
   await screen.findByText('Return A');
 
   expect(screen.queryByText('Attendance refreshed.')).toBeNull();
 });
 
 it('keeps adjustment controls unavailable until the policy is resolved without refetching it on paging', async () => {
   const policy = deferred<typeof policyResponse>();
   authState.clientSession.permissions = new Set(['attendance:punch_self']);
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return policy.promise;
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(
       boardResponse({
         endCursor: variables?.after ? null : 'page-two',
         hasNextPage: !variables?.after,
       })
     );
   });
   renderPage();
 
   const addButton = await screen.findByRole('button', { name: 'Loading adjustment policy…' });
   expect((addButton as HTMLButtonElement).disabled).toBe(true);
   expect(screen.queryByRole('button', { name: 'Adjust day' })).toBeNull();
   await advanceToNextPage();
-  await waitFor(() => expect(graphClient.request).toHaveBeenCalledTimes(3));
+  await waitFor(() => expect(graphClient.request).toHaveBeenCalledTimes(4));
 
   await act(async () => {
     await Promise.resolve();
     policy.resolve(policyResponse);
   });
 
   await waitFor(() =>
     expect(
       screen.getByRole<HTMLButtonElement>('button', { name: 'Add Missed Punches' }).disabled
     ).toBe(false)
diff --git a/src/modules/attendance/attendancePageTestSupport.tsx b/src/modules/attendance/attendancePageTestSupport.tsx
index 895dd02..fb951d8 100644
--- a/src/modules/attendance/attendancePageTestSupport.tsx
+++ b/src/modules/attendance/attendancePageTestSupport.tsx
@@ -1,16 +1,17 @@
 // @vitest-environment jsdom
 
 import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
 import { MemoryRouter } from 'react-router-dom';
 import { afterEach, beforeEach, expect, vi } from 'vitest';
 
+import { AttendanceCurrentDayWindowDocument } from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 import type { ParsedClientSession } from '../../auth/clientSession';
 
 import AttendancePage from './AttendancePage';
 
 const graphClientState = vi.hoisted(() => {
   const defaultClient = { request: vi.fn() };
   return { current: defaultClient, defaultClient };
 });
 export const graphClient = graphClientState.defaultClient;
@@ -28,20 +29,29 @@ const authState = vi.hoisted(() => ({
 
 vi.mock('../../hooks/useGraphClient', () => ({
   useGraphClient: () => graphClientState.current,
 }));
 
 vi.mock('../../contexts/AuthContext', () => ({
   useAuth: () => authState,
 }));
 
 export const policyResponse = { attendanceAdjustmentPolicy: { maxSelfAdjustDays: 14 } };
+export const currentWindowResponse = {
+  attendanceDayWindow: {
+    workDate: '2026-08-25',
+    startsAt: '2026-08-24T23:30:00Z',
+    endsAt: '2026-08-25T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
+  },
+};
 
 export function deferred<T>() {
   let resolve!: (value: T) => void;
   const promise = new Promise<T>((resolvePromise) => {
     resolve = resolvePromise;
   });
   return { promise, resolve };
 }
 
 export function boardResponse({
@@ -120,20 +130,23 @@ export async function advanceToNextPage() {
 
 beforeEach(() => {
   vi.useFakeTimers({ shouldAdvanceTime: true });
   vi.setSystemTime(new Date('2026-08-25T12:00:00Z'));
   graphClientState.current = graphClient;
   authState.clientSession.employeeId = 'employee-self';
   authState.clientSession.permissions = new Set();
   graphClient.request.mockReset();
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument) {
+      return Promise.resolve(currentWindowResponse);
+    }
     return Promise.resolve(boardResponse({ endCursor: 'opaque-next', hasNextPage: true }));
   });
 });
 
 afterEach(() => {
   cleanup();
   vi.useRealTimers();
 });
 
 export const requestCalls = () =>
diff --git a/src/modules/attendance/components/AttendancePageFeedback.tsx b/src/modules/attendance/components/AttendancePageFeedback.tsx
index 3af9b50..57161b5 100644
--- a/src/modules/attendance/components/AttendancePageFeedback.tsx
+++ b/src/modules/attendance/components/AttendancePageFeedback.tsx
@@ -1,39 +1,46 @@
 import Button from '../../../components/common/Button';
 import PageActions from '../../../components/common/PageActions';
 import PageNotice from '../../../components/common/PageNotice';
-import { toIsoDate } from '../../../utils/calendarRange';
 import type { AttendancePageModel } from '../hooks/useAttendancePageModel';
 
 import ManualAttendanceModal from './ManualAttendanceModal';
 
 export const AttendancePageToolbar = ({ model }: { model: AttendancePageModel }) => {
-  const { canPunchAttendance, policyReady, openAdjust } = model;
+  const { canPunchAttendance, policyReady, openAdjust, currentWorkDate } = model;
   return (
     <PageActions>
       <h1 className="sr-only">Attendance</h1>
       {canPunchAttendance ? (
         <Button
           variant="primary"
           type="button"
           disabled={!policyReady}
           title={policyReady ? undefined : 'Loading adjustment policy'}
-          onClick={() => openAdjust(toIsoDate(new Date()))}
+          onClick={() => currentWorkDate && openAdjust(currentWorkDate)}
         >
           {policyReady ? 'Add Missed Punches' : 'Loading adjustment policy…'}
         </Button>
       ) : null}
     </PageActions>
   );
 };
 export const AttendancePageNotices = ({ model }: { model: AttendancePageModel }) => {
-  const { error, success, setSuccess, refreshing, refreshBoard } = model;
+  const {
+    error,
+    success,
+    setSuccess,
+    refreshing,
+    refreshBoard,
+    attendanceWindowError,
+    refreshAttendanceWindow,
+  } = model;
   return (
     <>
       {' '}
       {error && (
         <PageNotice
           variant="error"
           title="Attendance could not be refreshed"
           focusOnMount
           action={
             <Button
@@ -43,20 +50,38 @@ export const AttendancePageNotices = ({ model }: { model: AttendancePageModel })
               disabled={refreshing}
               onClick={() => void refreshBoard()}
             >
               {refreshing ? 'Trying again…' : 'Try again'}
             </Button>
           }
         >
           {error}
         </PageNotice>
       )}
+      {attendanceWindowError ? (
+        <PageNotice
+          variant="error"
+          title="Current attendance day could not be loaded"
+          action={
+            <Button
+              type="button"
+              variant="outline"
+              size="sm"
+              onClick={() => void refreshAttendanceWindow()}
+            >
+              Try again
+            </Button>
+          }
+        >
+          {attendanceWindowError}
+        </PageNotice>
+      ) : null}
       {success && (
         <PageNotice variant="success" onDismiss={() => setSuccess(null)}>
           {success}
         </PageNotice>
       )}
     </>
   );
 };
 export const AttendancePageEditor = ({ model }: { model: AttendancePageModel }) => {
   const {
@@ -79,20 +104,22 @@ export const AttendancePageEditor = ({ model }: { model: AttendancePageModel })
     <>
       {' '}
       {canPunchAttendance && policyReady ? (
         <ManualAttendanceModal
           isOpen={adjustOpen}
           onClose={closeAdjust}
           defaultWorkDate={adjustDefaultDate}
           editingSegmentId={adjustDefaultSegment?.id}
           defaultCheckIn={adjustDefaultSegment?.checkInTime}
           defaultCheckOut={adjustDefaultSegment?.checkOutTime}
+          defaultCheckInAt={adjustDefaultSegment?.checkInAt}
+          defaultCheckOutAt={adjustDefaultSegment?.checkOutAt}
           existingSegments={currentBoard?.attendance ?? []}
           existingSegmentsComplete={existingSegmentsComplete}
           existingSegmentsCoverage={{ fromDate: monthBounds.start, toDate: monthBounds.end }}
           selfServiceDays={adjustPolicyDays}
           canRegularize={canRegularize}
           onSaved={() => {
             if (isEditorCurrent()) refreshBoard();
           }}
         />
       ) : null}
diff --git a/src/modules/attendance/components/ManualAttendanceModal.test.tsx b/src/modules/attendance/components/ManualAttendanceModal.test.tsx
index eded690..281d22f 100644
--- a/src/modules/attendance/components/ManualAttendanceModal.test.tsx
+++ b/src/modules/attendance/components/ManualAttendanceModal.test.tsx
@@ -1,25 +1,58 @@
 // @vitest-environment jsdom
 
 import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
 import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
 
+import {
+  AttendanceAddManualSegmentDocument,
+  AttendanceCorrectionWindowsDocument,
+} from '../../../api/attendance/graphql';
+
 import ManualAttendanceModal from './ManualAttendanceModal';
 
-const request = vi.hoisted(() => vi.fn());
+const graphState = vi.hoisted(() => ({ client: { request: vi.fn() } }));
+const { request } = graphState.client;
+
+function correctionWindows(workDate: string) {
+  const start = new Date(`${workDate}T23:30:00Z`);
+  start.setUTCDate(start.getUTCDate() - 1);
+  return {
+    currentWindow: {
+      workDate: '2026-09-12',
+      startsAt: '2026-09-11T23:30:00Z',
+      endsAt: '2026-09-12T23:30:00Z',
+      timezone: 'Asia/Kolkata',
+      boundaryMinutes: 300,
+    },
+    selectedWindow: {
+      workDate,
+      startsAt: start.toISOString(),
+      endsAt: `${workDate}T23:30:00.000Z`,
+      timezone: 'Asia/Kolkata',
+      boundaryMinutes: 300,
+    },
+  };
+}
 
 vi.mock('../../../hooks/useGraphClient', () => ({
-  useGraphClient: () => ({ request }),
+  useGraphClient: () => graphState.client,
 }));
 
 beforeEach(() => {
   request.mockReset();
+  request.mockImplementation((document: unknown, variables?: { workDate?: string }) => {
+    if (document === AttendanceCorrectionWindowsDocument) {
+      return Promise.resolve(correctionWindows(variables?.workDate ?? '2025-01-15'));
+    }
+    return Promise.resolve({});
+  });
 });
 
 afterEach(() => {
   cleanup();
   document.body.style.overflow = '';
 });
 
 function renderModal(overrides: Partial<React.ComponentProps<typeof ManualAttendanceModal>> = {}) {
   const onClose = vi.fn();
   const onSaved = vi.fn();
@@ -36,126 +69,189 @@ function renderModal(overrides: Partial<React.ComponentProps<typeof ManualAttend
     />
   );
   return { onClose, onSaved };
 }
 
 describe('ManualAttendanceModal', () => {
   it('associates invalid punch order with Punch Out and focuses that field', async () => {
     renderModal();
     const punchIn = screen.getByLabelText('Punch In');
     const punchOut = screen.getByLabelText('Punch Out');
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.change(punchIn, { target: { value: '18:00' } });
     fireEvent.change(punchOut, { target: { value: '09:00' } });
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     await waitFor(() => {
       expect(punchOut.getAttribute('aria-invalid')).toBe('true');
       expect(document.activeElement).toBe(punchOut);
     });
+    expect(screen.getByText('Punch In must be before Punch Out.')).toBeTruthy();
     expect(
-      screen.getByText('Punch In must be before Punch Out for the same calendar day.')
-    ).toBeTruthy();
-    expect(request).not.toHaveBeenCalled();
+      request.mock.calls.some(([document]) => document === AttendanceAddManualSegmentDocument)
+    ).toBe(false);
   });
 
   it('keeps entered values and focuses a persistent alert when saving fails', async () => {
-    request.mockRejectedValueOnce(new Error('request rejected by upstream API'));
+    request.mockImplementation((document: unknown, variables?: { workDate?: string }) => {
+      if (document === AttendanceCorrectionWindowsDocument) {
+        return Promise.resolve(correctionWindows(variables?.workDate ?? '2025-01-15'));
+      }
+      return Promise.reject(new Error('request rejected by upstream API'));
+    });
     renderModal();
     const workDate = screen.getByLabelText<HTMLInputElement>('Work Date');
     const punchIn = screen.getByLabelText<HTMLInputElement>('Punch In');
     const punchOut = screen.getByLabelText<HTMLInputElement>('Punch Out');
 
     fireEvent.change(workDate, { target: { value: '2025-01-16' } });
+    await screen.findByText(/16 Jan 2025/);
     fireEvent.change(punchIn, { target: { value: '08:30' } });
     fireEvent.change(punchOut, { target: { value: '17:15' } });
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     const alert = await screen.findByRole('alert');
     await waitFor(() => expect(document.activeElement).toBe(alert));
     expect(screen.getByText('Attendance was not saved')).toBeTruthy();
     expect(workDate.value).toBe('2025-01-16');
     expect(punchIn.value).toBe('08:30');
     expect(punchOut.value).toBe('17:15');
   });
 
   it('closes only after the attendance segment is saved', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal();
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
     expect(onClose).toHaveBeenCalledOnce();
   });
 
+  it('updates the original incomplete segment with explicit overnight calendar dates', async () => {
+    request.mockImplementation((document: unknown) => {
+      if (document === AttendanceCorrectionWindowsDocument) {
+        return Promise.resolve({
+          currentWindow: {
+            workDate: '2026-09-12',
+            startsAt: '2026-09-11T23:30:00Z',
+            endsAt: '2026-09-12T23:30:00Z',
+            timezone: 'Asia/Kolkata',
+            boundaryMinutes: 300,
+          },
+          selectedWindow: {
+            workDate: '2026-09-11',
+            startsAt: '2026-09-10T23:30:00Z',
+            endsAt: '2026-09-11T23:30:00Z',
+            timezone: 'Asia/Kolkata',
+            boundaryMinutes: 300,
+          },
+        });
+      }
+      return Promise.resolve({});
+    });
+    renderModal({
+      defaultWorkDate: '2026-09-11',
+      editingSegmentId: 'incomplete-1',
+      defaultCheckIn: '02:00:00',
+      defaultCheckOut: null,
+      defaultCheckInAt: '2026-09-11T20:30:00Z',
+      defaultCheckOutAt: null,
+    });
+    await screen.findByText(/Attendance window:/);
+    fireEvent.change(await screen.findByLabelText('Punch In date'), {
+      target: { value: '2026-09-12' },
+    });
+    fireEvent.change(screen.getByLabelText('Punch Out date'), {
+      target: { value: '2026-09-12' },
+    });
+    fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '04:00' } });
+    fireEvent.click(screen.getByRole('button', { name: 'Update Segment' }));
+
+    await waitFor(() =>
+      expect(request).toHaveBeenCalledWith(expect.anything(), {
+        input: {
+          id: 'incomplete-1',
+          workDate: '2026-09-11',
+          checkInDate: '2026-09-12',
+          checkOutDate: '2026-09-12',
+          checkInTime: '02:00:00',
+          checkOutTime: '04:00:00',
+        },
+      })
+    );
+  });
+});
+
+describe('ManualAttendanceModal loaded-coverage safeguards', () => {
   it('submits an overlapping range when the supplied segments are explicitly incomplete', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal({
       defaultCheckIn: '10:00:00',
       defaultCheckOut: '12:00:00',
       existingSegmentsComplete: false,
       existingSegments: [
         {
           id: 'other-segment',
           workDate: '2025-01-15',
           checkInTime: '08:00:00',
           checkOutTime: '11:00:00',
         },
       ],
     });
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
     expect(onClose).toHaveBeenCalledOnce();
   });
 
   it('defers overlap checks when Add defaults outside a historical loaded range', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal({
       defaultWorkDate: '2026-08-24',
       defaultCheckIn: '10:00:00',
       defaultCheckOut: '12:00:00',
       existingSegmentsComplete: true,
       existingSegmentsCoverage: { fromDate: '2025-01-01', toDate: '2025-01-31' },
       existingSegments: [
         {
           id: 'outside-range',
           workDate: '2026-08-24',
           checkInTime: '08:00:00',
           checkOutTime: '11:00:00',
         },
       ],
     });
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
     expect(onClose).toHaveBeenCalledOnce();
   });
 
   it('defers overlap checks after the user changes the date outside loaded coverage', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal({
       defaultWorkDate: '2025-01-15',
       defaultCheckIn: '10:00:00',
       defaultCheckOut: '12:00:00',
       existingSegmentsComplete: true,
       existingSegmentsCoverage: { fromDate: '2025-01-01', toDate: '2025-01-31' },
       existingSegments: [
         {
           id: 'outside-range',
           workDate: '2026-08-24',
           checkInTime: '08:00:00',
           checkOutTime: '11:00:00',
         },
       ],
     });
 
     fireEvent.change(screen.getByLabelText('Work Date'), { target: { value: '2026-08-24' } });
+    await screen.findByText(/24 Aug 2026/);
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
     expect(onClose).toHaveBeenCalledOnce();
   });
 });
diff --git a/src/modules/attendance/components/ManualAttendanceModal.tsx b/src/modules/attendance/components/ManualAttendanceModal.tsx
index f23577a..fbb40da 100644
--- a/src/modules/attendance/components/ManualAttendanceModal.tsx
+++ b/src/modules/attendance/components/ManualAttendanceModal.tsx
@@ -1,115 +1,155 @@
 import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
 
 import {
-  AddManualAttendanceSegmentDocument,
-  UpdateManualAttendanceSegmentDocument,
-} from '../../../api/graphql/graphql';
+  AttendanceAddManualSegmentDocument,
+  AttendanceUpdateManualSegmentDocument,
+} from '../../../api/attendance/graphql';
 import Button from '../../../components/common/Button';
 import Input from '../../../components/common/Input';
 import Modal from '../../../components/common/Modal';
 import PageNotice from '../../../components/common/PageNotice';
 import { useGraphClient } from '../../../hooks/useGraphClient';
+import { formatAttendanceWindow, localDateAt } from '../../../utils/attendanceDay';
 import { attendancePolicyMessage } from '../../../utils/attendancePolicyMessage';
 import {
   type AttendanceSegmentInterval,
   type ExistingSegmentsCoverage,
   type ManualAttendanceField,
   validateManualAttendanceSegment,
 } from '../../../utils/attendanceValidation';
 import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
 import { formatBackendTime } from '../../../utils/timeFormat';
+import { useAttendanceCorrectionWindows } from '../hooks/useAttendanceDayWindows';
 
 const DEFAULT_CHECK_IN = '09:00';
 const DEFAULT_CHECK_OUT = '18:00';
 
 type FieldErrors = Partial<Record<Exclude<ManualAttendanceField, 'form'>, string>>;
 
 interface FormError {
   title: string;
   message: string;
 }
 
 export interface ManualAttendanceModalProps {
   isOpen: boolean;
   onClose: () => void;
   defaultWorkDate: string;
   editingSegmentId?: string | null;
   defaultCheckIn?: string | null;
   defaultCheckOut?: string | null;
+  defaultCheckInAt?: string | null;
+  defaultCheckOutAt?: string | null;
   existingSegments: AttendanceSegmentInterval[];
   /** Defaults to true for callers that supply a complete list. */
   existingSegmentsComplete?: boolean;
   /** Loaded date range when the supplied list is only complete within that range. */
   existingSegmentsCoverage?: ExistingSegmentsCoverage;
   selfServiceDays: number;
   canRegularize: boolean;
   onSaved: () => void;
 }
 
 const ManualAttendanceModal = ({
   isOpen,
   onClose,
   defaultWorkDate,
   editingSegmentId,
   defaultCheckIn,
   defaultCheckOut,
+  defaultCheckInAt,
+  defaultCheckOutAt,
   existingSegments,
   existingSegmentsComplete = true,
   existingSegmentsCoverage,
   selfServiceDays,
   canRegularize,
   onSaved,
 }: ManualAttendanceModalProps) => {
   const client = useGraphClient('client');
   const workDateRef = useRef<HTMLInputElement>(null);
   const checkInRef = useRef<HTMLInputElement>(null);
   const checkOutRef = useRef<HTMLInputElement>(null);
+  const checkInDateRef = useRef<HTMLInputElement>(null);
+  const checkOutDateRef = useRef<HTMLInputElement>(null);
+  const datesTouched = useRef(false);
   const [workDate, setWorkDate] = useState(defaultWorkDate);
+  const [checkInDate, setCheckInDate] = useState(defaultWorkDate);
+  const [checkOutDate, setCheckOutDate] = useState(defaultWorkDate);
   const [checkIn, setCheckIn] = useState(DEFAULT_CHECK_IN);
   const [checkOut, setCheckOut] = useState(DEFAULT_CHECK_OUT);
   const [busy, setBusy] = useState(false);
   const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
   const [formError, setFormError] = useState<FormError | null>(null);
   const isEditing = Boolean(editingSegmentId);
+  const windows = useAttendanceCorrectionWindows(client, isOpen, workDate);
   const policyMessage = useMemo(
     () => attendancePolicyMessage(selfServiceDays, canRegularize),
     [canRegularize, selfServiceDays]
   );
 
   useEffect(() => {
     if (!isOpen) return;
     setWorkDate(defaultWorkDate);
+    setCheckInDate(defaultWorkDate);
+    setCheckOutDate(defaultWorkDate);
+    datesTouched.current = false;
     setCheckIn(formatBackendTime(defaultCheckIn ?? DEFAULT_CHECK_IN).slice(0, 5));
     setCheckOut(formatBackendTime(defaultCheckOut ?? DEFAULT_CHECK_OUT).slice(0, 5));
     setFieldErrors({});
     setFormError(null);
   }, [isOpen, defaultWorkDate, defaultCheckIn, defaultCheckOut]);
 
+  useEffect(() => {
+    const selected = windows.data?.selectedWindow;
+    if (!isOpen || !selected || datesTouched.current) return;
+    setCheckInDate(localDateAt(defaultCheckInAt, selected.timezone) ?? workDate);
+    setCheckOutDate(
+      localDateAt(defaultCheckOutAt, selected.timezone) ??
+        localDateAt(defaultCheckInAt, selected.timezone) ??
+        workDate
+    );
+  }, [defaultCheckInAt, defaultCheckOutAt, isOpen, windows.data, workDate]);
+
   const focusField = (field: Exclude<ManualAttendanceField, 'form'>) => {
     const refs = {
       workDate: workDateRef,
+      checkInDate: checkInDateRef,
+      checkOutDate: checkOutDateRef,
       checkIn: checkInRef,
       checkOut: checkOutRef,
     };
     refs[field].current?.focus();
   };
 
   const submit = async (event: FormEvent) => {
     event.preventDefault();
     setFieldErrors({});
     setFormError(null);
 
+    if (!windows.data || windows.loading || windows.error) {
+      setFormError({
+        title: 'Attendance day window is not ready',
+        message: windows.error ?? 'Wait for the attendance day window to load and try again.',
+      });
+      return;
+    }
+
     const validationError = validateManualAttendanceSegment({
       workDate,
+      checkInDate,
+      checkOutDate,
       checkIn,
       checkOut,
+      currentWorkDate: windows.data.currentWindow.workDate,
+      window: windows.data.selectedWindow,
       existingSegments,
       existingSegmentsComplete,
       existingSegmentsCoverage,
       excludedSegmentId: editingSegmentId,
     });
     if (validationError) {
       if (validationError.field === 'form') {
         setFormError({
           title: 'Review the attendance details',
           message: validationError.message,
@@ -117,30 +157,32 @@ const ManualAttendanceModal = ({
       } else {
         setFieldErrors({ [validationError.field]: validationError.message });
         focusField(validationError.field);
       }
       return;
     }
 
     setBusy(true);
     const input = {
       workDate,
+      checkInDate,
+      checkOutDate,
       checkInTime: `${checkIn}:00`,
       checkOutTime: `${checkOut}:00`,
     };
     try {
       if (editingSegmentId) {
-        await client.request(UpdateManualAttendanceSegmentDocument, {
+        await client.request(AttendanceUpdateManualSegmentDocument, {
           input: { id: editingSegmentId, ...input },
         });
       } else {
-        await client.request(AddManualAttendanceSegmentDocument, { input });
+        await client.request(AttendanceAddManualSegmentDocument, { input });
       }
       onSaved();
       onClose();
     } catch (error) {
       setFormError({
         title: 'Attendance was not saved',
         message: graphQlUserMessage(error),
       });
     } finally {
       setBusy(false);
@@ -182,40 +224,100 @@ const ManualAttendanceModal = ({
           </PageNotice>
         ) : null}
 
         <Input
           ref={workDateRef}
           type="date"
           label="Work Date"
           value={workDate}
           onChange={(event) => {
             setWorkDate(event.target.value);
+            setCheckInDate(event.target.value);
+            setCheckOutDate(event.target.value);
+            datesTouched.current = false;
             setFieldErrors((current) => ({ ...current, workDate: undefined }));
           }}
           error={fieldErrors.workDate}
           fullWidth
           required
+          readOnly={isEditing}
         />
+        {windows.loading ? (
+          <p role="status" className="text-xs text-content-secondary">
+            Loading attendance day window…
+          </p>
+        ) : null}
+        {windows.error ? (
+          <PageNotice
+            variant="error"
+            title="Attendance day window could not be loaded"
+            action={
+              <Button
+                type="button"
+                variant="outline"
+                size="sm"
+                onClick={() => void windows.refresh()}
+              >
+                Try again
+              </Button>
+            }
+          >
+            {windows.error}
+          </PageNotice>
+        ) : null}
+        {windows.data ? (
+          <p className="rounded-lg bg-canvas px-3 py-2 text-xs text-content-secondary">
+            Attendance window: {formatAttendanceWindow(windows.data.selectedWindow)}
+          </p>
+        ) : null}
         <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
+          <Input
+            ref={checkInDateRef}
+            type="date"
+            label="Punch In date"
+            value={checkInDate}
+            onChange={(event) => {
+              datesTouched.current = true;
+              setCheckInDate(event.target.value);
+              setFieldErrors((current) => ({ ...current, checkInDate: undefined }));
+            }}
+            error={fieldErrors.checkInDate}
+            fullWidth
+            required
+          />
           <Input
             ref={checkInRef}
             type="time"
             label="Punch In"
             value={checkIn}
             onChange={(event) => {
               setCheckIn(event.target.value);
               setFieldErrors((current) => ({ ...current, checkIn: undefined }));
             }}
             error={fieldErrors.checkIn}
             fullWidth
             required
           />
+          <Input
+            ref={checkOutDateRef}
+            type="date"
+            label="Punch Out date"
+            value={checkOutDate}
+            onChange={(event) => {
+              datesTouched.current = true;
+              setCheckOutDate(event.target.value);
+              setFieldErrors((current) => ({ ...current, checkOutDate: undefined }));
+            }}
+            error={fieldErrors.checkOutDate}
+            fullWidth
+            required
+          />
           <Input
             ref={checkOutRef}
             type="time"
             label="Punch Out"
             value={checkOut}
             onChange={(event) => {
               setCheckOut(event.target.value);
               setFieldErrors((current) => ({ ...current, checkOut: undefined }));
             }}
             error={fieldErrors.checkOut}
diff --git a/src/modules/attendance/hooks/useAttendanceEditor.ts b/src/modules/attendance/hooks/useAttendanceEditor.ts
index 4c588e5..c91ae21 100644
--- a/src/modules/attendance/hooks/useAttendanceEditor.ts
+++ b/src/modules/attendance/hooks/useAttendanceEditor.ts
@@ -1,24 +1,27 @@
 import { useLayoutEffect, useMemo, useRef, useState } from 'react';
 
-import { parseIsoDate, toIsoDate } from '../../../utils/calendarRange';
 import type { FlatSegmentRow } from '../types';
 
-function calendarDaysBetweenWorkAndToday(workIso: string): number {
-  const a = parseIsoDate(workIso);
-  a.setHours(0, 0, 0, 0);
-  const b = new Date();
-  b.setHours(0, 0, 0, 0);
-  return Math.round((b.getTime() - a.getTime()) / 86400000);
+function dateOrdinal(iso: string): number | null {
+  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
+  if (!match) return null;
+  const value = Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
+  return Number.isFinite(value) ? value / 86_400_000 : null;
 }
 
-export function useAttendanceEditor(adjustPolicyDays: number, client: object, identity: string) {
+export function useAttendanceEditor(
+  adjustPolicyDays: number,
+  client: object,
+  identity: string,
+  currentWorkDate: string | null
+) {
   const owner = useMemo(() => ({ client, identity }), [client, identity]);
   const currentOwner = useRef<typeof owner | null>(owner);
   const [selection, setSelection] = useState<{
     owner: typeof owner;
     date: string;
     segment: FlatSegmentRow | null;
   } | null>(null);
   useLayoutEffect(() => {
     currentOwner.current = owner;
     return () => {
@@ -28,24 +31,27 @@ export function useAttendanceEditor(adjustPolicyDays: number, client: object, id
   const isEditorCurrent = () => currentOwner.current === owner;
   const visible = selection?.owner === owner ? selection : null;
   const openAdjust = (iso: string, segment: FlatSegmentRow | null = null) => {
     if (isEditorCurrent()) setSelection({ owner, date: iso, segment });
   };
   const closeAdjust = () => {
     if (isEditorCurrent()) setSelection(null);
   };
 
   const selfAdjustAllowedForDate = (workIso: string) => {
-    const delta = calendarDaysBetweenWorkAndToday(workIso);
+    const work = dateOrdinal(workIso);
+    const current = currentWorkDate ? dateOrdinal(currentWorkDate) : null;
+    if (work === null || current === null) return false;
+    const delta = current - work;
     if (delta < 0) return false;
     return delta <= adjustPolicyDays;
   };
   return {
     adjustOpen: visible !== null,
-    adjustDefaultDate: visible?.date ?? toIsoDate(new Date()),
+    adjustDefaultDate: visible?.date ?? currentWorkDate ?? '',
     adjustDefaultSegment: visible?.segment ?? null,
     closeAdjust,
     isEditorCurrent,
     openAdjust,
     selfAdjustAllowedForDate,
   };
 }
diff --git a/src/modules/attendance/hooks/useAttendancePageModel.ts b/src/modules/attendance/hooks/useAttendancePageModel.ts
index ff2f525..703a880 100644
--- a/src/modules/attendance/hooks/useAttendancePageModel.ts
+++ b/src/modules/attendance/hooks/useAttendancePageModel.ts
@@ -1,36 +1,62 @@
-import { useMemo } from 'react';
+import { useEffect, useMemo, useRef } from 'react';
 
 import { authorizationStateKey, createPermissionService } from '../../../auth/permissionService';
 import { useAuth } from '../../../contexts/AuthContext';
 import { useGraphClient } from '../../../hooks/useGraphClient';
 import { attendancePolicyMessage } from '../../../utils/attendancePolicyMessage';
 import { monthBoundsIso } from '../../../utils/calendarRange';
 
 import { attendanceSegmentRows } from './attendanceSegmentRows';
 import { useAttendanceAdjustmentPolicy } from './useAttendanceAdjustmentPolicy';
 import { useAttendanceCursor } from './useAttendanceCursor';
+import { useCurrentAttendanceDayWindow } from './useAttendanceDayWindows';
 import { useAttendanceEditor } from './useAttendanceEditor';
 import { useAttendancePeriod } from './useAttendancePeriod';
 import { usePersonalAttendanceBoard } from './usePersonalAttendanceBoard';
 
 export function useAttendancePageModel() {
   const client = useGraphClient('client');
   const auth = useAuth();
   const { clientSession } = auth;
   const permissions = createPermissionService(clientSession);
   const canPunchAttendance = permissions.canCapability('action.attendance.punch');
   const canRegularize = permissions.canCapability('action.attendance.regularize');
+  const employeeId = clientSession?.employeeId;
+  const identity = `${auth.tenantId ?? ''}:${auth.user?.id ?? ''}:${employeeId ?? ''}:${authorizationStateKey(clientSession)}`;
+  const currentWindow = useCurrentAttendanceDayWindow(client, identity);
+  const currentWorkDate = currentWindow.data?.workDate ?? null;
 
   const now = new Date();
+  const browserDefaultYear = now.getFullYear();
+  const browserDefaultMonth = now.getMonth();
   const { year, monthIndex, updateView } = useAttendancePeriod(client, auth, now);
-  const employeeId = clientSession?.employeeId;
+  const defaultMonthApplied = useRef(false);
+  const defaultMonthOwner = useRef(identity);
+  if (defaultMonthOwner.current !== identity) {
+    defaultMonthOwner.current = identity;
+    defaultMonthApplied.current = false;
+  }
+  useEffect(() => {
+    if (!currentWorkDate || defaultMonthApplied.current) return;
+    defaultMonthApplied.current = true;
+    const [serverYear, serverMonth] = currentWorkDate.split('-').map(Number);
+    if (
+      Number.isInteger(serverYear) &&
+      Number.isInteger(serverMonth) &&
+      year === browserDefaultYear &&
+      monthIndex === browserDefaultMonth &&
+      (serverYear !== year || serverMonth - 1 !== monthIndex)
+    ) {
+      updateView({ year: String(serverYear), month: String(serverMonth) });
+    }
+  }, [browserDefaultMonth, browserDefaultYear, currentWorkDate, monthIndex, updateView, year]);
   const monthBounds = useMemo(() => monthBoundsIso(year, monthIndex), [year, monthIndex]);
   const {
     effectiveCursorStack,
     activeCursor,
     queryKey,
     requestIdentity,
     changeCursor,
     resetCursorStack,
   } = useAttendanceCursor(client, employeeId, monthBounds);
   const {
@@ -43,27 +69,25 @@ export function useAttendancePageModel() {
     setSuccess,
     refreshBoard,
   } = usePersonalAttendanceBoard(
     client,
     employeeId,
     monthBounds,
     activeCursor,
     queryKey,
     requestIdentity
   );
-  const { adjustPolicyDays, policyReady } = useAttendanceAdjustmentPolicy(client);
+  const { adjustPolicyDays, policyReady: adjustmentPolicyReady } =
+    useAttendanceAdjustmentPolicy(client);
+  const policyReady = adjustmentPolicyReady && currentWindow.phase === 'ready';
   const policyMessage = attendancePolicyMessage(adjustPolicyDays, canRegularize);
-  const editor = useAttendanceEditor(
-    adjustPolicyDays,
-    client,
-    `${auth.tenantId ?? ''}:${auth.user?.id ?? ''}:${employeeId ?? ''}:${authorizationStateKey(clientSession)}`
-  );
+  const editor = useAttendanceEditor(adjustPolicyDays, client, identity, currentWorkDate);
   const filteredSegments = useMemo(
     () => attendanceSegmentRows(currentBoard?.attendance ?? [], monthBounds),
     [currentBoard?.attendance, monthBounds]
   );
 
   const existingSegmentsComplete =
     boardIsCurrent &&
     currentBoard !== null &&
     effectiveCursorStack.length === 0 &&
     !currentBoard.pageInfo.hasNextPage;
@@ -85,13 +109,16 @@ export function useAttendancePageModel() {
     setSuccess,
     refreshBoard,
     resetCursorStack,
     changeCursor,
     adjustPolicyDays,
     policyReady,
     policyMessage,
     filteredSegments,
     existingSegmentsComplete,
     monthBounds,
+    currentWorkDate,
+    attendanceWindowError: currentWindow.error,
+    refreshAttendanceWindow: currentWindow.refresh,
   };
 }
 export type AttendancePageModel = ReturnType<typeof useAttendancePageModel>;
diff --git a/src/modules/dashboard/components/AttendanceSummaryDetails.tsx b/src/modules/dashboard/components/AttendanceSummaryDetails.tsx
index f99c122..2d8aa33 100644
--- a/src/modules/dashboard/components/AttendanceSummaryDetails.tsx
+++ b/src/modules/dashboard/components/AttendanceSummaryDetails.tsx
@@ -13,33 +13,41 @@ interface AttendanceSegmentsProps {
 }
 
 const AttendanceSegments = ({ segments, startIndex = 0 }: AttendanceSegmentsProps) => (
   <ol
     aria-label="Recorded attendance sessions"
     className="ml-1 space-y-3 border-l-2 border-accent/25 pl-4 text-content-secondary"
   >
     {segments.map((segment, index) => {
       const checkInCoords = formatCoord(segment.checkInLat, segment.checkInLng);
       const checkOutCoords = formatCoord(segment.checkOutLat, segment.checkOutLng);
-      const checkOutTime = segment.checkOutTime ? formatBackendTime(segment.checkOutTime) : 'open';
+      const incomplete = segment.status?.trim().toUpperCase() === 'INCOMPLETE';
+      let checkOutTime = 'open';
+      if (incomplete) checkOutTime = 'missed punch out';
+      if (segment.checkOutTime) checkOutTime = formatBackendTime(segment.checkOutTime);
       return (
         <li key={segment.id} className="relative text-xs">
           <span
             aria-hidden="true"
             className="absolute -left-[1.4375rem] top-1 h-3 w-3 rounded-full border-2 border-surface bg-accent"
           />
           <div className="flex justify-between">
             <span>Session {index + startIndex + 1}</span>
             <span>
               {formatBackendTime(segment.checkInTime ?? null)} → {checkOutTime}
             </span>
           </div>
+          {incomplete ? (
+            <p className="mt-1 text-amber-800 dark:text-amber-200">
+              Missed punch out — correction required. No checkout time was recorded.
+            </p>
+          ) : null}
           {checkInCoords || checkOutCoords ? (
             <details className="mt-1">
               <summary className="cursor-pointer rounded text-xs text-content-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus">
                 Location details
               </summary>
               <p className="mt-1 break-words text-xs text-content-secondary">
                 In: {checkInCoords ?? '—'} · Out: {checkOutCoords ?? '—'}
               </p>
             </details>
           ) : null}
diff --git a/src/modules/dashboard/components/PunchInOut.test.tsx b/src/modules/dashboard/components/PunchInOut.test.tsx
index 41cb213..917b5e4 100644
--- a/src/modules/dashboard/components/PunchInOut.test.tsx
+++ b/src/modules/dashboard/components/PunchInOut.test.tsx
@@ -1,31 +1,39 @@
 // @vitest-environment jsdom
 
-import { act, cleanup, render, screen } from '@testing-library/react';
+import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
 import { userEvent } from '@testing-library/user-event';
+import { StrictMode } from 'react';
 import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
 
-import { PunchDaySummaryDocument, PunchTodayDocument } from '../../../api/graphql/graphql';
+import {
+  AttendancePunchDaySummaryDocument,
+  AttendancePunchTodayDocument,
+} from '../../../api/attendance/graphql';
 
 import PunchInOut from './PunchInOut';
 
 const graphState = vi.hoisted(() => ({
   client: { request: vi.fn() },
   permissions: new Set<string>(),
+  tenantId: 'tenant-1',
+  userId: 'user-1',
 }));
 
 vi.mock('../../../hooks/useGraphClient', () => ({
   useGraphClient: () => graphState.client,
 }));
 
 vi.mock('../../../contexts/AuthContext', () => ({
   useAuth: () => ({
+    tenantId: graphState.tenantId,
+    user: { id: graphState.userId },
     clientSession: {
       employeeId: 'employee-1',
       permissions: graphState.permissions,
       permissionScopes: { 'attendance:read': 'SELF', 'attendance:punch_self': 'SELF' },
       resourceScopes: {},
     },
   }),
 }));
 
 vi.mock('../../../contexts/TenantContext', () => ({
@@ -50,42 +58,49 @@ const segment = (index: number) => ({
   checkInLng: null,
   checkOutLat: null,
   checkOutLng: null,
   source: 'web',
   status: 'completed',
 });
 
 const summary = (segmentCount = 1) => ({
   punchDaySummary: {
     workDate: '2026-08-21',
+    startsAt: '2026-08-20T23:30:00Z',
+    endsAt: '2026-08-21T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
     totalWorkedMinutes: segmentCount * 60,
     openSegment: null,
     segments: Array.from({ length: segmentCount }, (_, index) => segment(index)),
   },
 });
 
 const openSummary = () => ({
   punchDaySummary: {
     ...summary(0).punchDaySummary,
     openSegment: { ...segment(3), checkOutTime: null },
   },
 });
 
 function renderCard() {
   return render(<PunchInOut />);
 }
 
 beforeEach(() => {
+  vi.useFakeTimers({ shouldAdvanceTime: true });
   vi.setSystemTime(new Date('2026-08-21T12:00:00Z'));
   graphState.permissions = new Set(['attendance:read', 'attendance:punch_self']);
+  graphState.tenantId = 'tenant-1';
+  graphState.userId = 'user-1';
   graphState.client.request = vi.fn((document) => {
-    if (document === PunchDaySummaryDocument) return Promise.resolve(summary());
+    if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary());
     return Promise.resolve({ punchToday: segment(2) });
   });
 });
 
 afterEach(() => {
   cleanup();
   vi.clearAllMocks();
   vi.useRealTimers();
 });
 
@@ -98,21 +113,21 @@ describe('PunchInOut truthful states', () => {
     expect(view.container.innerHTML).toBe('');
     expect(graphState.client.request).not.toHaveBeenCalled();
   });
 
   it('loads attendance read-only without rendering punch controls', async () => {
     graphState.permissions = new Set(['attendance:read']);
     renderCard();
 
     expect(await screen.findByText('Session 1')).toBeTruthy();
     expect(screen.queryByRole('button', { name: 'Punch In' })).toBeNull();
-    expect(graphState.client.request).toHaveBeenCalledWith(PunchDaySummaryDocument);
+    expect(graphState.client.request).toHaveBeenCalledWith(AttendancePunchDaySummaryDocument);
   });
 
   it('renders an actionable summary failure and disables punching until summary data is ready', async () => {
     graphState.client.request.mockRejectedValue(new Error('Failed to fetch'));
     renderCard();
 
     const alert = await screen.findByRole('alert');
     expect(alert.textContent).toContain('Attendance Summary Could Not Be Loaded');
     expect(screen.getByRole('button', { name: 'Retry' })).toBeTruthy();
     expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Punch In' }).disabled).toBe(true);
@@ -123,20 +138,127 @@ describe('PunchInOut truthful states', () => {
     graphState.client.request.mockResolvedValue(summary(0));
     renderCard();
 
     expect(await screen.findByText('No Attendance Recorded Today.')).toBeTruthy();
     expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Punch In' }).disabled).toBe(
       false
     );
     expect(screen.queryByRole('alert')).toBeNull();
   });
 
+  it('accepts the server-owned prior work date before the tenant boundary', async () => {
+    vi.setSystemTime(new Date('2026-08-21T20:00:00Z'));
+    renderCard();
+
+    expect(await screen.findByText('Attendance work date: 2026-08-21')).toBeTruthy();
+    expect(screen.getByText(/05:00.*05:00.*Asia\/Kolkata/)).toBeTruthy();
+    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Punch In' }).disabled).toBe(
+      false
+    );
+  });
+
+  it('invalidates at the exact exclusive end and loads the replacement summary', async () => {
+    vi.setSystemTime(new Date('2026-08-21T23:29:59Z'));
+    const next = summary(0);
+    next.punchDaySummary.workDate = '2026-08-22';
+    next.punchDaySummary.startsAt = '2026-08-21T23:30:00Z';
+    next.punchDaySummary.endsAt = '2026-08-22T23:30:00Z';
+    graphState.client.request.mockResolvedValueOnce(summary()).mockResolvedValueOnce(next);
+    renderCard();
+    await screen.findByText('Session 1');
+
+    await act(async () => {
+      vi.advanceTimersByTime(1000);
+      await Promise.resolve();
+      await Promise.resolve();
+    });
+
+    expect(screen.getByText('Attendance work date: 2026-08-22')).toBeTruthy();
+    expect(graphState.client.request).toHaveBeenCalledTimes(2);
+  });
+
+  it('refreshes stale attendance once when the window regains focus', async () => {
+    renderCard();
+    await screen.findByText('Session 1');
+    window.dispatchEvent(new Event('focus'));
+    await waitFor(() => expect(graphState.client.request).toHaveBeenCalledTimes(2));
+  });
+});
+
+describe('PunchInOut lifecycle ownership', () => {
+  it('keeps one focus listener after a StrictMode remount', async () => {
+    render(
+      <StrictMode>
+        <PunchInOut />
+      </StrictMode>
+    );
+    await screen.findByText('Session 1');
+    const initialSummaryRequests = graphState.client.request.mock.calls.filter(
+      ([document]) => document === AttendancePunchDaySummaryDocument
+    ).length;
+
+    window.dispatchEvent(new Event('focus'));
+
+    await waitFor(() =>
+      expect(
+        graphState.client.request.mock.calls.filter(
+          ([document]) => document === AttendancePunchDaySummaryDocument
+        )
+      ).toHaveLength(initialSummaryRequests + 1)
+    );
+  });
+
+  it('does not publish a late focus refresh after the tenant and client change', async () => {
+    const stale = deferred<ReturnType<typeof summary>>();
+    const oldClient = graphState.client;
+    oldClient.request.mockResolvedValueOnce(summary()).mockImplementationOnce(() => stale.promise);
+    const view = renderCard();
+    await screen.findByText('Attendance work date: 2026-08-21');
+
+    window.dispatchEvent(new Event('focus'));
+    await waitFor(() => expect(oldClient.request).toHaveBeenCalledTimes(2));
+
+    const replacement = summary(0);
+    replacement.punchDaySummary.workDate = '2026-08-22';
+    replacement.punchDaySummary.startsAt = '2026-08-21T00:00:00Z';
+    replacement.punchDaySummary.endsAt = '2026-08-22T23:30:00Z';
+    graphState.tenantId = 'tenant-2';
+    graphState.client = { request: vi.fn().mockResolvedValue(replacement) };
+    view.rerender(<PunchInOut />);
+    await screen.findByText('Attendance work date: 2026-08-22');
+
+    const late = summary(0);
+    late.punchDaySummary.workDate = '2026-08-20';
+    await act(async () => {
+      stale.resolve(late);
+      await Promise.resolve();
+    });
+
+    expect(screen.queryByText('Attendance work date: 2026-08-20')).toBeNull();
+    expect(screen.getByText('Attendance work date: 2026-08-22')).toBeTruthy();
+  });
+});
+
+describe('PunchInOut truthful refresh states', () => {
+  it('shows an expired incomplete segment as correction-required without a fake checkout', async () => {
+    graphState.client.request.mockResolvedValueOnce({
+      punchDaySummary: {
+        ...summary(0).punchDaySummary,
+        segments: [{ ...segment(1), checkOutAt: null, checkOutTime: null, status: 'INCOMPLETE' }],
+      },
+    });
+    renderCard();
+
+    expect(await screen.findByText(/Missed punch out.*correction required/i)).toBeTruthy();
+    expect(screen.queryByText(/Select.*Punch Out.*close this block/i)).toBeNull();
+  });
+
   it('shows loading while retrying an initial summary failure and then renders ready data', async () => {
     const retry = deferred<ReturnType<typeof summary>>();
     graphState.client.request
       .mockRejectedValueOnce(new Error('Failed to fetch'))
       .mockImplementationOnce(() => retry.promise);
     const user = userEvent.setup();
     renderCard();
 
     await user.click(await screen.findByRole('button', { name: 'Retry' }));
     expect(screen.getByText('Loading Attendance Summary…')).toBeTruthy();
@@ -166,27 +288,28 @@ describe('PunchInOut truthful states', () => {
     await screen.findByText('Session 1');
     expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Punch In' }).disabled).toBe(
       false
     );
   });
 
   it('keeps punching disabled when mutation success is followed by a failed summary refresh', async () => {
     const retry = deferred<ReturnType<typeof openSummary>>();
     let summaryRequestCount = 0;
     graphState.client.request = vi.fn((document) => {
-      if (document === PunchDaySummaryDocument) {
+      if (document === AttendancePunchDaySummaryDocument) {
         summaryRequestCount += 1;
         if (summaryRequestCount === 1) return Promise.resolve(summary());
         if (summaryRequestCount === 2) return Promise.reject(new Error('Failed to fetch'));
         return retry.promise;
       }
-      if (document === PunchTodayDocument) return Promise.resolve({ punchToday: segment(2) });
+      if (document === AttendancePunchTodayDocument)
+        return Promise.resolve({ punchToday: segment(2) });
       throw new Error('Unexpected document');
     });
     const user = userEvent.setup();
     renderCard();
     await screen.findByText('Session 1');
     await user.click(screen.getByRole('checkbox', { name: /Record GPS location/i }));
 
     await user.click(screen.getByRole('button', { name: 'Punch In' }));
 
     expect(await screen.findByText('Attendance Summary May Be Out of Date')).toBeTruthy();
@@ -197,43 +320,44 @@ describe('PunchInOut truthful states', () => {
     expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Punch In' }).disabled).toBe(true);
     act(() => retry.resolve(openSummary()));
     expect(await screen.findByRole('button', { name: 'Punch Out' })).toBeTruthy();
     expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Punch Out' }).disabled).toBe(
       false
     );
   });
 
   it('keeps mutation errors separate from the loaded summary', async () => {
     graphState.client.request = vi.fn((document) => {
-      if (document === PunchDaySummaryDocument) return Promise.resolve(summary());
-      if (document === PunchTodayDocument) return Promise.reject(new Error('Failed to fetch'));
+      if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary());
+      if (document === AttendancePunchTodayDocument)
+        return Promise.reject(new Error('Failed to fetch'));
       throw new Error('Unexpected document');
     });
     const user = userEvent.setup();
     renderCard();
     await screen.findByText('Session 1');
     await user.click(screen.getByRole('checkbox', { name: /Record GPS location/i }));
 
     await user.click(screen.getByRole('button', { name: 'Punch In' }));
 
     expect(await screen.findByText('Punch Could Not Be Recorded')).toBeTruthy();
     expect(screen.getByText('Session 1')).toBeTruthy();
     expect(screen.queryByText('Attendance Summary May Be Out of Date')).toBeNull();
   });
 });
 
 describe('PunchInOut submission and display safeguards', () => {
   it('prevents duplicate punch submissions while a mutation is busy', async () => {
     const mutation = deferred<{ punchToday: ReturnType<typeof segment> }>();
     graphState.client.request = vi.fn((document) => {
-      if (document === PunchDaySummaryDocument) return Promise.resolve(summary());
-      if (document === PunchTodayDocument) return mutation.promise;
+      if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary());
+      if (document === AttendancePunchTodayDocument) return mutation.promise;
       throw new Error('Unexpected document');
     });
     const user = userEvent.setup();
     renderCard();
     await screen.findByText('Session 1');
     await user.click(screen.getByRole('checkbox', { name: /Record GPS location/i }));
 
     const punchButton = screen.getByRole('button', { name: 'Punch In' });
     await user.dblClick(punchButton);
 
diff --git a/src/modules/dashboard/components/PunchInOut.tsx b/src/modules/dashboard/components/PunchInOut.tsx
index 65c8424..cde4aee 100644
--- a/src/modules/dashboard/components/PunchInOut.tsx
+++ b/src/modules/dashboard/components/PunchInOut.tsx
@@ -1,60 +1,61 @@
-import { useCallback, useEffect, useRef, useState } from 'react';
+import { useEffect, useLayoutEffect, useRef, useState, type MutableRefObject } from 'react';
 
-import { PunchDaySummaryDocument, PunchTodayDocument } from '../../../api/graphql/graphql';
+import { AttendancePunchTodayDocument } from '../../../api/attendance/graphql';
 import { authorizationStateKey, createPermissionService } from '../../../auth/permissionService';
 import Badge from '../../../components/common/Badge';
 import Button from '../../../components/common/Button';
 import Card from '../../../components/common/Card';
 import PageInformation from '../../../components/common/PageInformation';
 import PageNotice from '../../../components/common/PageNotice';
 import { useAuth } from '../../../contexts/AuthContext';
 import { useTenant } from '../../../contexts/TenantContext';
 import { useGraphClient } from '../../../hooks/useGraphClient';
-import { useRetainedQuery, type RetainedQueryPhase } from '../../../hooks/useRetainedQuery';
+import type { RetainedQueryPhase } from '../../../hooks/useRetainedQuery';
+import { formatAttendanceWindow } from '../../../utils/attendanceDay';
 import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
-import { formatTenantTime, tenantDateKey } from '../../../utils/tenantTime';
 import { formatBackendTime } from '../../../utils/timeFormat';
 
 import AttendanceSummaryDetails from './AttendanceSummaryDetails';
 import type { AttendanceRow, Summary } from './attendanceSummaryTypes';
 import { DashboardCardInitialState, DashboardCardRefreshNotice } from './DashboardCardQueryState';
-
-function displayRow(row: AttendanceRow, timezone: string): AttendanceRow {
-  return {
-    ...row,
-    checkInTime: row.checkInAt ? formatTenantTime(row.checkInAt, timezone) : row.checkInTime,
-    checkOutTime: row.checkOutAt ? formatTenantTime(row.checkOutAt, timezone) : row.checkOutTime,
-  };
-}
+import {
+  displayAttendanceRow,
+  usePunchDaySummary,
+  type PunchGraphClient,
+} from './usePunchDaySummary';
 
 function getCurrentPosition(): Promise<GeolocationPosition> {
   return new Promise((resolve, reject) => {
     if (!('geolocation' in navigator)) {
       reject(new Error('Geolocation is not supported in this browser'));
       return;
     }
     navigator.geolocation.getCurrentPosition(resolve, reject, {
       enableHighAccuracy: true,
       timeout: 20000,
       maximumAge: 0,
     });
   });
 }
 
+async function punchInput(trackLocation: boolean) {
+  if (!trackLocation) return null;
+  const position = await getCurrentPosition();
+  return { latitude: position.coords.latitude, longitude: position.coords.longitude };
+}
+
 function formatCoord(lat?: string | null, lng?: string | null) {
   if (lat === null || lat === undefined || lng === null || lng === undefined) return null;
   return `${lat}, ${lng}`;
 }
 
-type GraphClient = ReturnType<typeof useGraphClient>;
-
 const formatTime = (date: Date, timezone: string) =>
   date.toLocaleTimeString('en-IN', {
     timeZone: timezone,
     hour: '2-digit',
     minute: '2-digit',
     second: '2-digit',
   });
 
 const formatDate = (date: Date, timezone: string) =>
   date.toLocaleDateString('en-IN', {
@@ -71,60 +72,103 @@ const useDashboardCardClock = () => {
   useEffect(() => {
     const timer = setInterval(() => setCurrentTime(new Date()), 1000);
     return () => clearInterval(timer);
   }, []);
 
   return currentTime;
 };
 
 interface UsePunchMutationOptions {
   timezone: string;
-  client: GraphClient;
+  client: PunchGraphClient;
   refreshSummary: () => Promise<void>;
   summary: Summary | null;
   summaryPhase: RetainedQueryPhase;
+  summaryOwner: string;
+}
+
+function summaryReady(summary: Summary | null, phase: RetainedQueryPhase): summary is Summary {
+  return summary !== null && phase === 'ready';
+}
+
+function summaryExpired(summary: Summary): boolean {
+  return Date.now() >= Date.parse(summary.endsAt);
+}
+
+function submissionIsOwned(
+  mounted: MutableRefObject<boolean>,
+  generationRef: MutableRefObject<number>,
+  generation: number
+): boolean {
+  return mounted.current && generationRef.current === generation;
 }
 
 const usePunchMutation = ({
   timezone,
   client,
   refreshSummary,
   summary,
   summaryPhase,
+  summaryOwner,
 }: UsePunchMutationOptions) => {
   const [lastPunch, setLastPunch] = useState<AttendanceRow | null>(null);
   const [mutationError, setMutationError] = useState<string | null>(null);
   const [submitting, setSubmitting] = useState(false);
   const [trackLocation, setTrackLocation] = useState(true);
   const submittingRef = useRef(false);
+  const generationRef = useRef(0);
+  const mountedRef = useRef(false);
+
+  useLayoutEffect(() => {
+    mountedRef.current = true;
+    generationRef.current += 1;
+    return () => {
+      mountedRef.current = false;
+      generationRef.current += 1;
+    };
+  }, [client, summaryOwner]);
 
   const handlePunch = async () => {
-    if (submittingRef.current || !summary || summaryPhase !== 'ready') return;
+    if (submittingRef.current) return;
+    if (!summaryReady(summary, summaryPhase)) return;
+    if (summaryExpired(summary)) {
+      await refreshSummary();
+      return;
+    }
+    const generation = generationRef.current;
+    const ownsSubmission = () => submissionIsOwned(mountedRef, generationRef, generation);
     submittingRef.current = true;
     setMutationError(null);
     setSubmitting(true);
     try {
-      let input: { latitude: number; longitude: number } | null = null;
-      if (trackLocation) {
-        const position = await getCurrentPosition();
-        input = { latitude: position.coords.latitude, longitude: position.coords.longitude };
+      const input = await punchInput(trackLocation);
+      if (!ownsSubmission()) return;
+      if (summaryExpired(summary)) {
+        await refreshSummary();
+        return;
       }
-      const result = await client.request<{ punchToday: AttendanceRow }>(PunchTodayDocument, {
-        input,
-      });
-      setLastPunch(displayRow(result.punchToday, timezone));
+      const result = await client.request<{ punchToday: AttendanceRow }>(
+        AttendancePunchTodayDocument,
+        {
+          input,
+        }
+      );
+      if (!ownsSubmission()) return;
+      setLastPunch(displayAttendanceRow(result.punchToday, timezone));
       await refreshSummary();
     } catch (error) {
-      setMutationError(graphQlUserMessage(error));
+      if (ownsSubmission()) setMutationError(graphQlUserMessage(error));
     } finally {
-      submittingRef.current = false;
-      setSubmitting(false);
+      if (ownsSubmission()) {
+        submittingRef.current = false;
+        setSubmitting(false);
+      }
     }
   };
 
   return {
     handlePunch,
     lastPunch,
     mutationError,
     setTrackLocation,
     submitting,
     trackLocation,
@@ -258,68 +302,75 @@ const PunchActionArea = ({
       disabled={disabled}
       onClick={() => void onPunch()}
     >
       {buttonLabel}
     </Button>
   </>
 );
 
 interface AuthorizedPunchInOutProps {
   canPunch: boolean;
+  identity: string;
 }
 
-const AuthorizedPunchInOut = ({ canPunch }: AuthorizedPunchInOutProps) => {
+const AuthorizedPunchInOut = ({ canPunch, identity }: AuthorizedPunchInOutProps) => {
   const client = useGraphClient('client');
   const currentTime = useDashboardCardClock();
   const { currentTenant } = useTenant();
   const { timezone } = currentTenant;
-  const today = tenantDateKey(currentTime, timezone);
-  const loadSummary = useCallback(async () => {
-    const result = await client.request<{ punchDaySummary: Summary }>(PunchDaySummaryDocument);
-    const summary = result.punchDaySummary;
-    if (summary.workDate !== today)
-      throw new Error('Attendance summary is for another day. Refresh to load today’s attendance.');
-    return {
-      ...summary,
-      segments: summary.segments.map((row) => displayRow(row, timezone)),
-      openSegment: summary.openSegment ? displayRow(summary.openSegment, timezone) : null,
-    };
-  }, [client, timezone, today]);
   const {
     data: summary,
     error: summaryError,
     phase: summaryPhase,
     refresh: refreshSummary,
-  } = useRetainedQuery(loadSummary);
+  } = usePunchDaySummary(client, identity);
   const onRefresh = () => void refreshSummary();
+
+  const summaryIsWithinWindow = Boolean(
+    summary &&
+    currentTime.getTime() >= Date.parse(summary.startsAt) &&
+    currentTime.getTime() < Date.parse(summary.endsAt)
+  );
+  const summaryTimezone = summary?.timezone ?? timezone;
   const { handlePunch, lastPunch, mutationError, setTrackLocation, submitting, trackLocation } =
     usePunchMutation({
-      timezone,
+      timezone: summaryTimezone,
       client,
       refreshSummary,
-      summary: summary?.workDate === today ? summary : null,
+      summary: summaryIsWithinWindow ? summary : null,
       summaryPhase,
+      summaryOwner: identity,
     });
   const nextIsCheckIn = !summary?.openSegment;
   const buttonLabel = getButtonLabel(submitting, nextIsCheckIn);
-  const summaryIsReady = summaryPhase === 'ready' && summary?.workDate === today;
+  const summaryIsReady = summaryPhase === 'ready' && summaryIsWithinWindow;
   const lastEventCoords = getLastEventCoords(lastPunch);
 
   return (
     <Card title="Today’s attendance">
       <div className="space-y-4">
         <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-3">
           <div className="text-xl font-semibold tabular-nums text-content-primary">
-            {formatTime(currentTime, timezone)}
+            {formatTime(currentTime, summaryTimezone)}
+          </div>
+          <div className="text-xs text-content-secondary">
+            Calendar date: {formatDate(currentTime, summaryTimezone)}
           </div>
-          <div className="text-xs text-content-secondary">{formatDate(currentTime, timezone)}</div>
         </div>
+        {summary ? (
+          <div className="rounded-lg bg-canvas px-3 py-2 text-xs text-content-secondary">
+            <p className="font-medium text-content-primary">
+              Attendance work date: {summary.workDate}
+            </p>
+            <p>{formatAttendanceWindow(summary)}</p>
+          </div>
+        ) : null}
         <PunchSummaryContent
           error={summaryError}
           phase={summaryPhase}
           summary={summary}
           onRefresh={onRefresh}
         />
         {summary ? (
           <Button
             variant="quiet"
             size="sm"
@@ -348,23 +399,24 @@ const AuthorizedPunchInOut = ({ canPunch }: AuthorizedPunchInOutProps) => {
             submitting={submitting}
             trackLocation={trackLocation}
           />
         ) : null}
       </div>
     </Card>
   );
 };
 
 const PunchInOut = () => {
-  const { clientSession } = useAuth();
+  const { clientSession, tenantId, user } = useAuth();
   const permissions = createPermissionService(clientSession);
   if (!permissions.canCapability('dashboard.attendance')) return null;
 
   return (
     <AuthorizedPunchInOut
-      key={authorizationStateKey(clientSession)}
+      key={`${tenantId ?? ''}:${user?.id ?? ''}:${authorizationStateKey(clientSession)}`}
       canPunch={permissions.canCapability('action.attendance.punch')}
+      identity={`${tenantId ?? ''}:${user?.id ?? ''}:${authorizationStateKey(clientSession)}`}
     />
   );
 };
 
 export default PunchInOut;
diff --git a/src/modules/dashboard/components/attendanceSummaryTypes.ts b/src/modules/dashboard/components/attendanceSummaryTypes.ts
index 473627b..3940ab6 100644
--- a/src/modules/dashboard/components/attendanceSummaryTypes.ts
+++ b/src/modules/dashboard/components/attendanceSummaryTypes.ts
@@ -7,14 +7,18 @@ export type AttendanceRow = {
   checkInLat?: string | null;
   checkInLng?: string | null;
   checkOutLat?: string | null;
   checkOutLng?: string | null;
   source?: string | null;
   status?: string | null;
 };
 
 export type Summary = {
   workDate: string;
+  startsAt: string;
+  endsAt: string;
+  timezone: string;
+  boundaryMinutes: number;
   totalWorkedMinutes: number;
   openSegment: AttendanceRow | null;
   segments: AttendanceRow[];
 };
diff --git a/src/modules/hr/HrAttendanceManagementPage.context.test.tsx b/src/modules/hr/HrAttendanceManagementPage.context.test.tsx
index 38a44c8..d9490c4 100644
--- a/src/modules/hr/HrAttendanceManagementPage.context.test.tsx
+++ b/src/modules/hr/HrAttendanceManagementPage.context.test.tsx
@@ -1,22 +1,23 @@
 // @vitest-environment jsdom
 
 import { act, cleanup, fireEvent, render as renderUi, screen } from '@testing-library/react';
 import type { ReactElement } from 'react';
 import { Link, MemoryRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
 import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
 
 import {
-  AddManagedAttendanceSegmentDocument,
-  ManagedAttendancePageDocument,
-  UpdateManagedAttendanceSegmentDocument,
-} from '../../api/graphql/graphql';
+  AttendanceAddManagedSegmentDocument,
+  AttendanceCorrectionWindowsDocument,
+  AttendanceUpdateManagedSegmentDocument,
+} from '../../api/attendance/graphql';
+import { ManagedAttendancePageDocument } from '../../api/graphql/graphql';
 
 import HrAttendanceManagementPage from './HrAttendanceManagementPage';
 
 const graphState = vi.hoisted(() => ({ client: { request: vi.fn() } }));
 const authState = vi.hoisted(() => ({
   identity: 'employee-a',
   userId: 'user-a',
   tenantId: 'tenant-a',
 }));
 vi.mock('../../contexts/AuthContext', () => ({
@@ -57,20 +58,22 @@ const RouteHarness = () => {
     </>
   );
 };
 
 const ashaRow = {
   id: 'attendance-42',
   employeeId: 'employee-42',
   employeeName: 'Asha Rao',
   employeeCode: 'EMP-0042',
   workDate: '2026-08-24',
+  checkInAt: '2026-08-24T03:30:00Z',
+  checkOutAt: '2026-08-24T12:00:00Z',
   checkInTime: '09:00:00',
   checkOutTime: '17:30:00',
   status: 'PRESENT',
   source: 'BIOMETRIC',
   regularizationStatus: 'REGULARIZED',
   createdAt: '2026-08-24T09:00:00Z',
   updatedAt: '2026-08-24T17:30:00Z',
 };
 
 const managedPage = (
@@ -86,60 +89,85 @@ const managedPage = (
   },
 });
 
 const settle = async () => {
   await act(async () => {
     await Promise.resolve();
     await Promise.resolve();
   });
 };
 
+const correctionWindows = {
+  currentWindow: {
+    workDate: '2026-08-25',
+    startsAt: '2026-08-24T23:30:00Z',
+    endsAt: '2026-08-25T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
+  },
+  selectedWindow: {
+    workDate: '2026-08-24',
+    startsAt: '2026-08-23T23:30:00Z',
+    endsAt: '2026-08-24T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
+  },
+};
+
 beforeEach(() => {
   authState.identity = 'employee-a';
   authState.userId = 'user-a';
   authState.tenantId = 'tenant-a';
   vi.useFakeTimers();
   vi.setSystemTime(new Date(2026, 7, 25, 12));
   graphState.client = { request: vi.fn() };
-  graphState.client.request.mockResolvedValue(managedPage());
+  graphState.client.request.mockImplementation((document: unknown) =>
+    Promise.resolve(
+      document === AttendanceCorrectionWindowsDocument ? correctionWindows : managedPage()
+    )
+  );
 });
 
 afterEach(() => {
   cleanup();
   vi.useRealTimers();
 });
 
 describe('HR attendance context', () => {
   it('creates from a historical row with its employee and date without reusing its edit id', async () => {
     render(<HrAttendanceManagementPage />);
     await settle();
     fireEvent.click(screen.getAllByRole('button', { name: 'Add segment for Asha Rao' })[0]);
+    await settle();
+    expect(screen.getByText(/Attendance window:/)).toBeTruthy();
     expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-08-24');
     fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '18:00' } });
     fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '19:00' } });
     fireEvent.change(screen.getByLabelText('Reason'), {
       target: { value: 'Approved evening work' },
     });
     fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
     await settle();
-    expect(graphState.client.request).toHaveBeenCalledWith(AddManagedAttendanceSegmentDocument, {
+    expect(graphState.client.request).toHaveBeenCalledWith(AttendanceAddManagedSegmentDocument, {
       input: {
         employeeId: 'employee-42',
         workDate: '2026-08-24',
+        checkInDate: '2026-08-24',
+        checkOutDate: '2026-08-24',
         checkInTime: '18:00:00',
         checkOutTime: '19:00:00',
         reason: 'Approved evening work',
       },
     });
     expect(
       graphState.client.request.mock.calls.some(
-        ([document]) => document === UpdateManagedAttendanceSegmentDocument
+        ([document]) => document === AttendanceUpdateManagedSegmentDocument
       )
     ).toBe(false);
     expect(screen.queryByRole('dialog')).toBeNull();
   });
 
   it('restores dates and private search on return, supports Back, and resets opaque pagination', async () => {
     render(<RouteHarness />);
     await settle();
     fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '2026-08-02' } });
     await settle();
diff --git a/src/modules/hr/HrAttendanceManagementPage.test.tsx b/src/modules/hr/HrAttendanceManagementPage.test.tsx
index 7bb424a..af1fe91 100644
--- a/src/modules/hr/HrAttendanceManagementPage.test.tsx
+++ b/src/modules/hr/HrAttendanceManagementPage.test.tsx
@@ -1,21 +1,22 @@
 // @vitest-environment jsdom
 
 import { act, cleanup, fireEvent, render as renderUi, screen } from '@testing-library/react';
 import type { ReactElement } from 'react';
 import { MemoryRouter } from 'react-router-dom';
 import { afterEach, beforeEach, expect, it, vi } from 'vitest';
 
 import {
-  ManagedAttendancePageDocument,
-  UpdateManagedAttendanceSegmentDocument,
-} from '../../api/graphql/graphql';
+  AttendanceCorrectionWindowsDocument,
+  AttendanceUpdateManagedSegmentDocument,
+} from '../../api/attendance/graphql';
+import { ManagedAttendancePageDocument } from '../../api/graphql/graphql';
 
 import HrAttendanceManagementPage from './HrAttendanceManagementPage';
 
 const graphState = vi.hoisted(() => ({ client: { request: vi.fn() } }));
 vi.mock('../../contexts/AuthContext', () => ({
   useAuth: () => ({
     clientSession: 'employee-a',
     user: { id: 'user-a' },
     tenantId: 'tenant-a',
   }),
@@ -27,20 +28,22 @@ vi.mock('../../auth/permissionService', () => ({
 vi.mock('../../hooks/useGraphClient', () => ({ useGraphClient: () => graphState.client }));
 
 const render = (ui: ReactElement) => renderUi(ui, { wrapper: MemoryRouter });
 
 const ashaRow = {
   id: 'attendance-42',
   employeeId: 'employee-42',
   employeeName: 'Asha Rao',
   employeeCode: 'EMP-0042',
   workDate: '2026-08-24',
+  checkInAt: '2026-08-24T03:30:00Z',
+  checkOutAt: '2026-08-24T12:00:00Z',
   checkInTime: '09:00:00',
   checkOutTime: '17:30:00',
   status: 'PRESENT',
   source: 'BIOMETRIC',
   regularizationStatus: 'REGULARIZED',
   createdAt: '2026-08-24T09:00:00Z',
   updatedAt: '2026-08-24T17:30:00Z',
 };
 
 const managedPage = (
@@ -66,20 +69,37 @@ const deferred = <T,>() => {
   };
 };
 
 const settle = async () => {
   await act(async () => {
     await Promise.resolve();
     await Promise.resolve();
   });
 };
 
+const correctionWindows = {
+  currentWindow: {
+    workDate: '2026-08-25',
+    startsAt: '2026-08-24T23:30:00Z',
+    endsAt: '2026-08-25T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
+  },
+  selectedWindow: {
+    workDate: '2026-08-24',
+    startsAt: '2026-08-23T23:30:00Z',
+    endsAt: '2026-08-24T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
+  },
+};
+
 beforeEach(() => {
   vi.useFakeTimers();
   vi.setSystemTime(new Date(2026, 7, 25, 12));
   graphState.client = { request: vi.fn() };
   graphState.client.request.mockResolvedValue(managedPage());
 });
 
 afterEach(() => {
   cleanup();
   vi.useRealTimers();
@@ -253,21 +273,24 @@ it('returns to the prior page and refreshes the current opaque page', async () =
   expect(graphState.client.request).toHaveBeenLastCalledWith(ManagedAttendancePageDocument, {
     fromDate: '2026-08-01',
     toDate: '2026-08-31',
     first: 50,
   });
 });
 
 it('resets to page one, refetches, and identifies the employee after a successful adjustment', async () => {
   graphState.client.request.mockImplementation(
     (document: unknown, variables?: { after?: string }) => {
-      if (document === UpdateManagedAttendanceSegmentDocument) return Promise.resolve({});
+      if (document === AttendanceUpdateManagedSegmentDocument) return Promise.resolve({});
+      if (document === AttendanceCorrectionWindowsDocument) {
+        return Promise.resolve(correctionWindows);
+      }
       return Promise.resolve(
         variables?.after === 'opaque-next'
           ? managedPage(
               [
                 {
                   ...ashaRow,
                   id: 'attendance-43',
                   employeeName: 'Bina Shah',
                   employeeCode: 'EMP-0043',
                 },
@@ -276,28 +299,30 @@ it('resets to page one, refetches, and identifies the employee after a successfu
             )
           : managedPage()
       );
     }
   );
   render(<HrAttendanceManagementPage />);
   await settle();
   fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
   await settle();
   fireEvent.click(screen.getAllByRole('button', { name: 'Adjust Bina Shah on 2026-08-24' })[0]);
+  await settle();
+  expect(screen.getByText(/Attendance window:/)).toBeTruthy();
   fireEvent.change(screen.getByLabelText('Reason'), {
     target: { value: 'Approved biometric correction' },
   });
   fireEvent.click(screen.getByRole('button', { name: 'Update segment' }));
   await settle();
 
   expect(graphState.client.request).toHaveBeenCalledWith(
-    UpdateManagedAttendanceSegmentDocument,
+    AttendanceUpdateManagedSegmentDocument,
     expect.anything()
   );
   expect(graphState.client.request).toHaveBeenLastCalledWith(ManagedAttendancePageDocument, {
     fromDate: '2026-08-01',
     toDate: '2026-08-31',
     first: 50,
   });
   expect(screen.getAllByText('Attendance updated for Bina Shah on 2026-08-24.')[0]).toBeTruthy();
   expect(screen.queryByRole('dialog')).toBeNull();
 });
@@ -366,21 +391,21 @@ it('fails closed across a client replacement and ignores the old page request',
   );
   expect((replacementClient.request.mock.calls as unknown[][])[0][1]).not.toHaveProperty('after');
 
   await act(async () => {
     replacementPage.resolve(
       managedPage([{ ...ashaRow, id: 'attendance-new', employeeName: 'Replacement Client Row' }])
     );
     await Promise.resolve();
   });
   expect(screen.getAllByText('Replacement Client Row')[0]).toBeTruthy();
-  expect(oldClient.request).toHaveBeenCalledTimes(4);
+  expect(oldClient.request).toHaveBeenCalledTimes(5);
 });
 
 it('does not publish a late query completion from a replaced client', async () => {
   const oldPage = deferred<ReturnType<typeof managedPage>>();
   graphState.client.request.mockReturnValueOnce(oldPage.promise);
   const { rerender } = render(<HrAttendanceManagementPage />);
 
   const replacementClient = {
     request: vi
       .fn()
diff --git a/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx b/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
index cb5d6c0..0f35414 100644
--- a/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
+++ b/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
@@ -1,19 +1,20 @@
 // @vitest-environment jsdom
 
 import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
 import { afterEach, beforeEach, expect, it, vi } from 'vitest';
 
 import {
-  AddManagedAttendanceSegmentDocument,
-  UpdateManagedAttendanceSegmentDocument,
-} from '../../../api/graphql/graphql';
+  AttendanceAddManagedSegmentDocument,
+  AttendanceCorrectionWindowsDocument,
+  AttendanceUpdateManagedSegmentDocument,
+} from '../../../api/attendance/graphql';
 
 import AttendanceRegularizationModal from './AttendanceRegularizationModal';
 import type { ManagedAttendanceEmployee, ManagedAttendanceRow } from './managedAttendanceTypes';
 
 const graphState = vi.hoisted(() => ({ client: { request: vi.fn() } }));
 
 vi.mock('../../../hooks/useGraphClient', () => ({ useGraphClient: () => graphState.client }));
 
 const employee: ManagedAttendanceEmployee = {
   employeeId: 'employee-42',
@@ -22,196 +23,331 @@ const employee: ManagedAttendanceEmployee = {
 };
 
 const row: ManagedAttendanceRow = {
   id: 'attendance-42',
   employeeId: employee.employeeId,
   employeeName: employee.employeeName,
   employeeCode: employee.employeeCode,
   workDate: '2026-08-24',
   checkInTime: '09:00:00',
   checkOutTime: '17:30:00',
+  checkInAt: '2026-08-24T03:30:00Z',
+  checkOutAt: '2026-08-24T12:00:00Z',
   status: 'PRESENT',
   source: 'BIOMETRIC',
   regularizationStatus: 'REGULARIZED',
   createdAt: '2026-08-24T09:00:00Z',
   updatedAt: '2026-08-24T17:30:00Z',
 };
 
 const baseProps = {
   isOpen: true,
   onClose: vi.fn(),
   employee,
+  initialWorkDate: '2026-08-24',
   existingSegments: [row],
   existingSegmentsComplete: false,
   existingSegmentsCoverage: { fromDate: '2026-08-01', toDate: '2026-08-31' },
   onSaved: vi.fn(),
 };
 
 const deferred = <T,>() => {
   let resolve!: (value: T) => void;
   return {
     promise: new Promise<T>((done) => {
       resolve = done;
     }),
     resolve,
   };
 };
 
-function fillValidForm(reason = 'Correct biometric outage') {
+async function fillValidForm(reason = 'Correct biometric outage') {
+  await screen.findByText(/Attendance window:/);
   fireEvent.change(screen.getByLabelText('Work Date'), { target: { value: '2026-08-24' } });
   fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '09:00' } });
   fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '17:30' } });
   fireEvent.change(screen.getByLabelText('Reason'), { target: { value: reason } });
 }
 
 beforeEach(() => {
   graphState.client = { request: vi.fn() };
-  graphState.client.request.mockResolvedValue({});
+  graphState.client.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceCorrectionWindowsDocument) {
+      return Promise.resolve({
+        currentWindow: {
+          workDate: '2026-08-25',
+          startsAt: '2026-08-24T23:30:00Z',
+          endsAt: '2026-08-25T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+        selectedWindow: {
+          workDate: '2026-08-24',
+          startsAt: '2026-08-23T23:30:00Z',
+          endsAt: '2026-08-24T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+      });
+    }
+    return Promise.resolve({});
+  });
   baseProps.onClose.mockReset();
   baseProps.onSaved.mockReset();
 });
 
 afterEach(cleanup);
 
 it('adds for an immutable employee using the generated managed mutation and trimmed reason', async () => {
   render(<AttendanceRegularizationModal {...baseProps} />);
 
   expect(screen.getByText('Asha Rao (EMP-0042)')).toBeTruthy();
   expect(screen.queryByRole('textbox', { name: /employee/i })).toBeNull();
-  fillValidForm('  Correct biometric outage  ');
+  await fillValidForm('  Correct biometric outage  ');
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
 
   await waitFor(() =>
-    expect(graphState.client.request).toHaveBeenCalledWith(AddManagedAttendanceSegmentDocument, {
+    expect(graphState.client.request).toHaveBeenCalledWith(AttendanceAddManagedSegmentDocument, {
       input: {
         employeeId: 'employee-42',
         workDate: '2026-08-24',
+        checkInDate: '2026-08-24',
+        checkOutDate: '2026-08-24',
         checkInTime: '09:00:00',
         checkOutTime: '17:30:00',
         reason: 'Correct biometric outage',
       },
     })
   );
   expect(baseProps.onSaved).toHaveBeenCalledWith('Asha Rao', '2026-08-24');
   expect(baseProps.onClose).toHaveBeenCalledTimes(1);
 });
 
 it('edits with optimistic concurrency and never sends an employee id', async () => {
   render(<AttendanceRegularizationModal {...baseProps} editingRow={row} />);
+  await screen.findByText(/Attendance window:/);
   fireEvent.change(screen.getByLabelText('Reason'), {
     target: { value: 'Manager approved correction' },
   });
   fireEvent.click(screen.getByRole('button', { name: 'Update segment' }));
 
   await waitFor(() =>
-    expect(graphState.client.request).toHaveBeenCalledWith(UpdateManagedAttendanceSegmentDocument, {
+    expect(graphState.client.request).toHaveBeenCalledWith(AttendanceUpdateManagedSegmentDocument, {
       input: {
         id: 'attendance-42',
         expectedUpdatedAt: '2026-08-24T17:30:00Z',
         workDate: '2026-08-24',
+        checkInDate: '2026-08-24',
+        checkOutDate: '2026-08-24',
         checkInTime: '09:00:00',
         checkOutTime: '17:30:00',
         reason: 'Manager approved correction',
       },
     })
   );
-  expect((graphState.client.request.mock.calls as unknown[][])[0][1]).not.toHaveProperty(
-    'employeeId'
+  const updateCall = (graphState.client.request.mock.calls as unknown[][]).find(
+    ([document]) => document === AttendanceUpdateManagedSegmentDocument
+  );
+  expect(updateCall?.[1]).not.toHaveProperty('employeeId');
+});
+
+it('corrects the original incomplete id with explicit after-midnight dates', async () => {
+  const incomplete = {
+    ...row,
+    id: 'incomplete-42',
+    workDate: '2026-08-24',
+    checkInAt: '2026-08-24T20:30:00Z',
+    checkOutAt: null,
+    checkInTime: '02:00:00',
+    checkOutTime: null,
+    status: 'INCOMPLETE',
+  };
+  render(<AttendanceRegularizationModal {...baseProps} editingRow={incomplete} />);
+  await screen.findByText(/Attendance window:/);
+  fireEvent.change(await screen.findByLabelText('Punch In date'), {
+    target: { value: '2026-08-25' },
+  });
+  fireEvent.change(screen.getByLabelText('Punch Out date'), { target: { value: '2026-08-25' } });
+  fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '04:00' } });
+  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Missed punch out' } });
+  fireEvent.click(screen.getByRole('button', { name: 'Update segment' }));
+
+  await waitFor(() =>
+    expect(graphState.client.request).toHaveBeenCalledWith(AttendanceUpdateManagedSegmentDocument, {
+      input: {
+        id: 'incomplete-42',
+        expectedUpdatedAt: '2026-08-24T17:30:00Z',
+        workDate: '2026-08-24',
+        checkInDate: '2026-08-25',
+        checkOutDate: '2026-08-25',
+        checkInTime: '02:00:00',
+        checkOutTime: '04:00:00',
+        reason: 'Missed punch out',
+      },
+    })
   );
 });
 
 it.each([
   ['four characters', '🙂🙂🙂🙂'],
   ['501 characters', '界'.repeat(501)],
 ])('rejects a %s reason by Unicode character count and focuses Reason', async (_, reason) => {
   render(<AttendanceRegularizationModal {...baseProps} />);
-  fillValidForm(reason);
+  await fillValidForm(reason);
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
 
   const reasonField = screen.getByLabelText('Reason');
   await waitFor(() => expect(document.activeElement).toBe(reasonField));
   expect(reasonField.getAttribute('aria-invalid')).toBe('true');
-  expect(graphState.client.request).not.toHaveBeenCalled();
+  expect(
+    graphState.client.request.mock.calls.some(
+      ([document]) => document === AttendanceAddManagedSegmentDocument
+    )
+  ).toBe(false);
 });
 
 it.each([
   ['5', `  ${'\u{1F642}'.repeat(5)}  `, '\u{1F642}'.repeat(5)],
   ['500', `  ${'\u754C'.repeat(500)}  `, '\u754C'.repeat(500)],
 ])('accepts exactly %s trimmed Unicode code points', async (_, reason, normalizedReason) => {
   render(<AttendanceRegularizationModal {...baseProps} />);
-  fillValidForm(reason);
+  await fillValidForm(reason);
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
 
-  await waitFor(() => expect(graphState.client.request).toHaveBeenCalledTimes(1));
-  expect((graphState.client.request.mock.calls as unknown[][])[0][1]).toEqual({
+  await waitFor(() =>
+    expect(
+      graphState.client.request.mock.calls.some(
+        ([document]) => document === AttendanceAddManagedSegmentDocument
+      )
+    ).toBe(true)
+  );
+  expect(graphState.client.request).toHaveBeenCalledWith(AttendanceAddManagedSegmentDocument, {
     input: expect.objectContaining({ reason: normalizedReason }) as unknown,
   });
 });
 
 it('keeps intrinsic time validation while deferring incomplete-page overlap checks to the server', async () => {
   render(<AttendanceRegularizationModal {...baseProps} />);
-  fillValidForm();
+  await fillValidForm();
   fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '18:00' } });
   fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '09:00' } });
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
+  expect(await screen.findByText('Punch In must be before Punch Out.')).toBeTruthy();
   expect(
-    await screen.findByText('Punch In must be before Punch Out for the same calendar day.')
-  ).toBeTruthy();
-  expect(graphState.client.request).not.toHaveBeenCalled();
+    graphState.client.request.mock.calls.some(
+      ([document]) => document === AttendanceAddManagedSegmentDocument
+    )
+  ).toBe(false);
 
   fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '09:30' } });
   fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '10:30' } });
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
-  await waitFor(() => expect(graphState.client.request).toHaveBeenCalledTimes(1));
+  await waitFor(() =>
+    expect(
+      graphState.client.request.mock.calls.some(
+        ([document]) => document === AttendanceAddManagedSegmentDocument
+      )
+    ).toBe(true)
+  );
 });
 
 it('blocks a known overlap when the loaded attendance page is complete', async () => {
   render(<AttendanceRegularizationModal {...baseProps} existingSegmentsComplete />);
-  fillValidForm();
+  await fillValidForm();
   fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '09:30' } });
   fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '10:30' } });
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
 
   expect(
     await screen.findByText('This punch range overlaps an existing attendance segment for the day.')
   ).toBeTruthy();
-  expect(graphState.client.request).not.toHaveBeenCalled();
+  expect(
+    graphState.client.request.mock.calls.some(
+      ([document]) => document === AttendanceAddManagedSegmentDocument
+    )
+  ).toBe(false);
 });
 
 it('keeps every entered value and the modal open after a save error', async () => {
-  graphState.client.request.mockRejectedValueOnce(new Error('database internals'));
+  graphState.client.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceCorrectionWindowsDocument) {
+      return Promise.resolve({
+        currentWindow: {
+          workDate: '2026-08-25',
+          startsAt: '2026-08-24T23:30:00Z',
+          endsAt: '2026-08-25T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+        selectedWindow: {
+          workDate: '2026-08-24',
+          startsAt: '2026-08-23T23:30:00Z',
+          endsAt: '2026-08-24T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+      });
+    }
+    return Promise.reject(new Error('database internals'));
+  });
   render(<AttendanceRegularizationModal {...baseProps} />);
-  fillValidForm('Payroll correction reason');
+  await fillValidForm('Payroll correction reason');
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
 
   const failureNotice = (await screen.findByText('Attendance was not saved')).closest(
     '[role="alert"]'
   );
   expect(failureNotice).toBeTruthy();
   await waitFor(() => expect(document.activeElement).toBe(failureNotice));
   expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-08-24');
   expect(screen.getByLabelText<HTMLInputElement>('Punch In').value).toBe('09:00');
   expect(screen.getByLabelText<HTMLInputElement>('Punch Out').value).toBe('17:30');
   expect(screen.getByLabelText<HTMLTextAreaElement>('Reason').value).toBe(
     'Payroll correction reason'
   );
   expect(screen.getByRole('dialog')).toBeTruthy();
   expect(baseProps.onClose).not.toHaveBeenCalled();
 });
 
 it('does not publish a late old-client mutation completion after client replacement', async () => {
   const oldMutation = deferred<Record<string, never>>();
-  graphState.client.request.mockReturnValueOnce(oldMutation.promise);
+  graphState.client.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceCorrectionWindowsDocument) {
+      return Promise.resolve({
+        currentWindow: {
+          workDate: '2026-08-25',
+          startsAt: '2026-08-24T23:30:00Z',
+          endsAt: '2026-08-25T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+        selectedWindow: {
+          workDate: '2026-08-24',
+          startsAt: '2026-08-23T23:30:00Z',
+          endsAt: '2026-08-24T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+      });
+    }
+    return oldMutation.promise;
+  });
   const { rerender } = render(<AttendanceRegularizationModal {...baseProps} />);
-  fillValidForm();
+  await fillValidForm();
   fireEvent.click(screen.getByRole('button', { name: 'Save segment' }));
-  await waitFor(() => expect(graphState.client.request).toHaveBeenCalledTimes(1));
+  await waitFor(() =>
+    expect(
+      graphState.client.request.mock.calls.some(
+        ([document]) => document === AttendanceAddManagedSegmentDocument
+      )
+    ).toBe(true)
+  );
 
   graphState.client = { request: vi.fn().mockResolvedValue({}) };
   rerender(<AttendanceRegularizationModal {...baseProps} />);
   await act(async () => {
     oldMutation.resolve({});
     await Promise.resolve();
   });
 
   expect(baseProps.onSaved).not.toHaveBeenCalled();
   expect(baseProps.onClose).not.toHaveBeenCalled();
diff --git a/src/modules/hr/attendance/AttendanceRegularizationModal.tsx b/src/modules/hr/attendance/AttendanceRegularizationModal.tsx
index 1b893b2..603a238 100644
--- a/src/modules/hr/attendance/AttendanceRegularizationModal.tsx
+++ b/src/modules/hr/attendance/AttendanceRegularizationModal.tsx
@@ -1,45 +1,171 @@
 import Button from '../../../components/common/Button';
 import Input from '../../../components/common/Input';
 import Modal from '../../../components/common/Modal';
 import PageNotice from '../../../components/common/PageNotice';
 import Textarea from '../../../components/common/Textarea';
+import { formatAttendanceWindow } from '../../../utils/attendanceDay';
 
 import {
   useAttendanceRegularization,
   type AttendanceRegularizationModalProps,
 } from './useAttendanceRegularization';
 
 export type { AttendanceRegularizationModalProps } from './useAttendanceRegularization';
 
-const AttendanceRegularizationModal = (props: AttendanceRegularizationModalProps) => {
-  const { isOpen, onClose, employee } = props;
+type RegularizationState = ReturnType<typeof useAttendanceRegularization>;
+
+const AttendanceWindowStatus = ({ windows }: { windows: RegularizationState['windows'] }) => (
+  <>
+    {windows.loading ? (
+      <p role="status" className="text-xs text-content-secondary">
+        Loading attendance day window…
+      </p>
+    ) : null}
+    {windows.error ? (
+      <PageNotice
+        variant="error"
+        title="Attendance day window could not be loaded"
+        action={
+          <Button type="button" variant="outline" size="sm" onClick={() => void windows.refresh()}>
+            Try again
+          </Button>
+        }
+      >
+        {windows.error}
+      </PageNotice>
+    ) : null}
+    {windows.data ? (
+      <p className="rounded-lg bg-canvas px-3 py-2 text-xs text-content-secondary">
+        Attendance window: {formatAttendanceWindow(windows.data.selectedWindow)}
+      </p>
+    ) : null}
+  </>
+);
+
+const AttendanceWindowFields = ({ state }: { state: RegularizationState }) => {
   const {
     workDateRef,
     checkInRef,
     checkOutRef,
-    reasonRef,
+    checkInDateRef,
+    checkOutDateRef,
     workDate,
     setWorkDate,
+    checkInDate,
+    setCheckInDate,
+    checkOutDate,
+    setCheckOutDate,
+    datesTouched,
     checkIn,
     setCheckIn,
     checkOut,
     setCheckOut,
+    fieldErrors,
+    setFieldErrors,
+    isEditing,
+    windows,
+  } = state;
+  return (
+    <>
+      <Input
+        ref={workDateRef}
+        type="date"
+        label="Work Date"
+        value={workDate}
+        onChange={(event) => {
+          setWorkDate(event.target.value);
+          setCheckInDate(event.target.value);
+          setCheckOutDate(event.target.value);
+          datesTouched.current = false;
+          setFieldErrors((current) => ({ ...current, workDate: undefined }));
+        }}
+        error={fieldErrors.workDate}
+        fullWidth
+        required
+        readOnly={isEditing}
+      />
+      <AttendanceWindowStatus windows={windows} />
+      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
+        <Input
+          ref={checkInDateRef}
+          type="date"
+          label="Punch In date"
+          value={checkInDate}
+          onChange={(event) => {
+            datesTouched.current = true;
+            setCheckInDate(event.target.value);
+            setFieldErrors((current) => ({ ...current, checkInDate: undefined }));
+          }}
+          error={fieldErrors.checkInDate}
+          fullWidth
+          required
+        />
+        <Input
+          ref={checkInRef}
+          type="time"
+          label="Punch In"
+          value={checkIn}
+          onChange={(event) => {
+            setCheckIn(event.target.value);
+            setFieldErrors((current) => ({ ...current, checkIn: undefined }));
+          }}
+          error={fieldErrors.checkIn}
+          fullWidth
+          required
+        />
+        <Input
+          ref={checkOutDateRef}
+          type="date"
+          label="Punch Out date"
+          value={checkOutDate}
+          onChange={(event) => {
+            datesTouched.current = true;
+            setCheckOutDate(event.target.value);
+            setFieldErrors((current) => ({ ...current, checkOutDate: undefined }));
+          }}
+          error={fieldErrors.checkOutDate}
+          fullWidth
+          required
+        />
+        <Input
+          ref={checkOutRef}
+          type="time"
+          label="Punch Out"
+          value={checkOut}
+          onChange={(event) => {
+            setCheckOut(event.target.value);
+            setFieldErrors((current) => ({ ...current, checkOut: undefined }));
+          }}
+          error={fieldErrors.checkOut}
+          fullWidth
+          required
+        />
+      </div>
+    </>
+  );
+};
+
+const AttendanceRegularizationModal = (props: AttendanceRegularizationModalProps) => {
+  const { isOpen, onClose, employee } = props;
+  const state = useAttendanceRegularization(props);
+  const {
+    reasonRef,
     reason,
     setReason,
     busy,
     fieldErrors,
     setFieldErrors,
     formError,
     isEditing,
     submit,
-  } = useAttendanceRegularization(props);
+  } = state;
 
   const submitLabel = isEditing ? 'Update segment' : 'Save segment';
   return (
     <Modal
       isOpen={isOpen}
       onClose={onClose}
       title={isEditing ? 'Adjust attendance segment' : 'Add attendance segment'}
       description="The employee is fixed from the attendance records in your approved scope."
       isDismissible={!busy}
     >
@@ -49,61 +175,21 @@ const AttendanceRegularizationModal = (props: AttendanceRegularizationModalProps
             {formError}
           </PageNotice>
         ) : null}
 
         <div>
           <p className="text-sm font-medium text-content-primary">Employee</p>
           <p className="mt-1 rounded-lg bg-canvas px-3 py-2 text-sm text-content-secondary">
             {employee.employeeName} ({employee.employeeCode})
           </p>
         </div>
-        <Input
-          ref={workDateRef}
-          type="date"
-          label="Work Date"
-          value={workDate}
-          onChange={(event) => {
-            setWorkDate(event.target.value);
-            setFieldErrors((current) => ({ ...current, workDate: undefined }));
-          }}
-          error={fieldErrors.workDate}
-          fullWidth
-          required
-        />
-        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
-          <Input
-            ref={checkInRef}
-            type="time"
-            label="Punch In"
-            value={checkIn}
-            onChange={(event) => {
-              setCheckIn(event.target.value);
-              setFieldErrors((current) => ({ ...current, checkIn: undefined }));
-            }}
-            error={fieldErrors.checkIn}
-            fullWidth
-            required
-          />
-          <Input
-            ref={checkOutRef}
-            type="time"
-            label="Punch Out"
-            value={checkOut}
-            onChange={(event) => {
-              setCheckOut(event.target.value);
-              setFieldErrors((current) => ({ ...current, checkOut: undefined }));
-            }}
-            error={fieldErrors.checkOut}
-            fullWidth
-            required
-          />
-        </div>
+        <AttendanceWindowFields state={state} />
         <Textarea
           ref={reasonRef}
           label="Reason"
           value={reason}
           onChange={(event) => {
             setReason(event.target.value);
             setFieldErrors((current) => ({ ...current, reason: undefined }));
           }}
           description="Required for the immutable attendance adjustment audit. 5 to 500 characters."
           error={fieldErrors.reason}
diff --git a/src/modules/hr/attendance/useAttendanceRegularization.ts b/src/modules/hr/attendance/useAttendanceRegularization.ts
index 77e6423..0f6f161 100644
--- a/src/modules/hr/attendance/useAttendanceRegularization.ts
+++ b/src/modules/hr/attendance/useAttendanceRegularization.ts
@@ -1,25 +1,34 @@
-import { useEffect, useLayoutEffect, useRef, useState, type FormEvent } from 'react';
+import {
+  useEffect,
+  useLayoutEffect,
+  useRef,
+  useState,
+  type FormEvent,
+  type MutableRefObject,
+} from 'react';
 
 import {
-  AddManagedAttendanceSegmentDocument,
-  UpdateManagedAttendanceSegmentDocument,
-} from '../../../api/graphql/graphql';
+  AttendanceAddManagedSegmentDocument,
+  AttendanceUpdateManagedSegmentDocument,
+} from '../../../api/attendance/graphql';
 import { useGraphClient } from '../../../hooks/useGraphClient';
+import { localDateAt } from '../../../utils/attendanceDay';
 import {
   type AttendanceSegmentInterval,
   type ExistingSegmentsCoverage,
   type ManualAttendanceField,
   validateManualAttendanceSegment,
 } from '../../../utils/attendanceValidation';
 import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
 import { formatBackendTime } from '../../../utils/timeFormat';
+import { useAttendanceCorrectionWindows } from '../../attendance/hooks/useAttendanceDayWindows';
 
 import type { ManagedAttendanceEmployee, ManagedAttendanceRow } from './managedAttendanceTypes';
 
 const DEFAULT_CHECK_IN = '09:00';
 const DEFAULT_CHECK_OUT = '18:00';
 const MIN_REASON_CHARACTERS = 5;
 const MAX_REASON_CHARACTERS = 500;
 
 type FieldErrors = Partial<Record<Exclude<ManualAttendanceField, 'form'> | 'reason', string>>;
 
@@ -28,150 +37,245 @@ export interface AttendanceRegularizationModalProps {
   onClose: () => void;
   employee: ManagedAttendanceEmployee;
   initialWorkDate?: string;
   editingRow?: ManagedAttendanceRow | null;
   existingSegments: AttendanceSegmentInterval[];
   existingSegmentsComplete: boolean;
   existingSegmentsCoverage: ExistingSegmentsCoverage;
   onSaved: (employeeName: string, workDate: string) => void;
 }
 
-function todayIso(): string {
-  const today = new Date();
-  const year = today.getFullYear();
-  const month = String(today.getMonth() + 1).padStart(2, '0');
-  const day = String(today.getDate()).padStart(2, '0');
-  return `${year}-${month}-${day}`;
-}
-
 function reasonError(value: string): string | null {
   const { length } = [...value.trim()];
   if (length < MIN_REASON_CHARACTERS) return 'Reason must be at least 5 characters.';
   if (length > MAX_REASON_CHARACTERS) return 'Reason must be 500 characters or fewer.';
   return null;
 }
 
+function optionalScalarString(value: unknown): string | null {
+  return typeof value === 'string' ? value : null;
+}
+
 const useAttendanceFields = ({
   isOpen,
   editingRow,
   initialWorkDate,
 }: Pick<AttendanceRegularizationModalProps, 'isOpen' | 'editingRow' | 'initialWorkDate'>) => {
   const client = useGraphClient('client');
   const workDateRef = useRef<HTMLInputElement>(null);
   const checkInRef = useRef<HTMLInputElement>(null);
   const checkOutRef = useRef<HTMLInputElement>(null);
+  const checkInDateRef = useRef<HTMLInputElement>(null);
+  const checkOutDateRef = useRef<HTMLInputElement>(null);
+  const datesTouched = useRef(false);
   const reasonRef = useRef<HTMLTextAreaElement>(null);
   const mountedRef = useRef(false);
   const mutationGeneration = useRef(0);
-  const [workDate, setWorkDate] = useState(todayIso);
+  const [workDate, setWorkDate] = useState('');
+  const [checkInDate, setCheckInDate] = useState('');
+  const [checkOutDate, setCheckOutDate] = useState('');
   const [checkIn, setCheckIn] = useState(DEFAULT_CHECK_IN);
   const [checkOut, setCheckOut] = useState(DEFAULT_CHECK_OUT);
   const [reason, setReason] = useState('');
   const [busy, setBusy] = useState(false);
   const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
   const [formError, setFormError] = useState<string | null>(null);
   const isEditing = editingRow !== null && editingRow !== undefined;
+  const windows = useAttendanceCorrectionWindows(client, isOpen, workDate);
 
   useEffect(() => {
     mountedRef.current = true;
     return () => {
       mountedRef.current = false;
     };
   }, []);
 
   useLayoutEffect(() => {
     mutationGeneration.current += 1;
     return () => {
       mutationGeneration.current += 1;
     };
   }, [client]);
 
   useEffect(() => {
     if (!isOpen) return;
-    setWorkDate(editingRow?.workDate ?? initialWorkDate ?? todayIso());
+    const nextWorkDate = editingRow?.workDate ?? initialWorkDate ?? '';
+    setWorkDate(nextWorkDate);
+    setCheckInDate(nextWorkDate);
+    setCheckOutDate(nextWorkDate);
+    datesTouched.current = false;
     setCheckIn(formatBackendTime(editingRow?.checkInTime ?? DEFAULT_CHECK_IN).slice(0, 5));
     setCheckOut(formatBackendTime(editingRow?.checkOutTime ?? DEFAULT_CHECK_OUT).slice(0, 5));
     setReason('');
     setBusy(false);
     setFieldErrors({});
     setFormError(null);
   }, [client, editingRow, initialWorkDate, isOpen]);
 
+  useEffect(() => {
+    const selected = windows.data?.selectedWindow;
+    if (!isOpen || !selected || datesTouched.current) return;
+    const checkInAt = optionalScalarString(editingRow?.checkInAt);
+    const checkOutAt = optionalScalarString(editingRow?.checkOutAt);
+    setCheckInDate(localDateAt(checkInAt, selected.timezone) ?? workDate);
+    setCheckOutDate(
+      localDateAt(checkOutAt, selected.timezone) ??
+        localDateAt(checkInAt, selected.timezone) ??
+        workDate
+    );
+  }, [editingRow?.checkInAt, editingRow?.checkOutAt, isOpen, windows.data, workDate]);
+
   return {
     client,
     workDateRef,
     checkInRef,
     checkOutRef,
+    checkInDateRef,
+    checkOutDateRef,
     reasonRef,
     mountedRef,
     mutationGeneration,
     workDate,
     setWorkDate,
+    checkInDate,
+    setCheckInDate,
+    checkOutDate,
+    setCheckOutDate,
+    datesTouched,
     checkIn,
     setCheckIn,
     checkOut,
     setCheckOut,
     reason,
     setReason,
     busy,
     setBusy,
     fieldErrors,
     setFieldErrors,
     formError,
     setFormError,
     isEditing,
+    windows,
   };
 };
 
+type GraphClient = ReturnType<typeof useGraphClient>;
+
+interface ManagedAttendanceInput {
+  checkInDate: string;
+  checkInTime: string;
+  checkOutDate: string;
+  checkOutTime: string;
+  reason: string;
+  workDate: string;
+}
+
+async function saveRegularization(
+  client: GraphClient,
+  editingRow: ManagedAttendanceRow | null | undefined,
+  employeeId: string,
+  input: ManagedAttendanceInput
+): Promise<void> {
+  if (editingRow) {
+    await client.request(AttendanceUpdateManagedSegmentDocument, {
+      input: {
+        id: editingRow.id,
+        expectedUpdatedAt: optionalScalarString(editingRow.updatedAt) ?? '',
+        ...input,
+      },
+    });
+    return;
+  }
+  await client.request(AttendanceAddManagedSegmentDocument, {
+    input: { employeeId, ...input },
+  });
+}
+
+function submissionIsCurrent(
+  mounted: MutableRefObject<boolean>,
+  generationRef: MutableRefObject<number>,
+  generation: number
+): boolean {
+  return mounted.current && generationRef.current === generation;
+}
+
+function correctionWindowsReady<T>(
+  data: T | null,
+  loading: boolean,
+  error: string | null
+): data is T {
+  return data !== null && !loading && error === null;
+}
+
 export const useAttendanceRegularization = ({
   isOpen,
   onClose,
   employee,
   initialWorkDate,
   editingRow,
   existingSegments,
   existingSegmentsComplete,
   existingSegmentsCoverage,
   onSaved,
 }: AttendanceRegularizationModalProps) => {
   const fields = useAttendanceFields({ isOpen, editingRow, initialWorkDate });
   const {
     client,
     workDateRef,
     checkInRef,
     checkOutRef,
+    checkInDateRef,
+    checkOutDateRef,
     reasonRef,
     mountedRef,
     mutationGeneration,
     workDate,
+    checkInDate,
+    checkOutDate,
     checkIn,
     checkOut,
     reason,
     setBusy,
     setFieldErrors,
     setFormError,
+    windows,
   } = fields;
 
   const focusAttendanceField = (field: Exclude<ManualAttendanceField, 'form'>) => {
-    const refs = { workDate: workDateRef, checkIn: checkInRef, checkOut: checkOutRef };
+    const refs = {
+      workDate: workDateRef,
+      checkInDate: checkInDateRef,
+      checkOutDate: checkOutDateRef,
+      checkIn: checkInRef,
+      checkOut: checkOutRef,
+    };
     refs[field].current?.focus();
   };
 
   const submit = async (event: FormEvent) => {
     event.preventDefault();
     setFieldErrors({});
     setFormError(null);
 
+    if (!correctionWindowsReady(windows.data, windows.loading, windows.error)) {
+      setFormError(windows.error ?? 'Wait for the attendance day window to load and try again.');
+      return;
+    }
+
     const attendanceError = validateManualAttendanceSegment({
       workDate,
+      checkInDate,
+      checkOutDate,
       checkIn,
       checkOut,
+      currentWorkDate: windows.data.currentWindow.workDate,
+      window: windows.data.selectedWindow,
       existingSegments,
       existingSegmentsComplete,
       existingSegmentsCoverage,
       excludedSegmentId: editingRow?.id,
     });
     if (attendanceError) {
       if (attendanceError.field === 'form') setFormError(attendanceError.message);
       else {
         setFieldErrors({ [attendanceError.field]: attendanceError.message });
         focusAttendanceField(attendanceError.field);
@@ -182,43 +286,32 @@ export const useAttendanceRegularization = ({
     const normalizedReason = reason.trim();
     const invalidReason = reasonError(reason);
     if (invalidReason) {
       setFieldErrors({ reason: invalidReason });
       reasonRef.current?.focus();
       return;
     }
 
     const attendanceInput = {
       workDate,
+      checkInDate,
+      checkOutDate,
       checkInTime: `${checkIn}:00`,
       checkOutTime: `${checkOut}:00`,
       reason: normalizedReason,
     };
-    const submissionClient = client;
     const generation = mutationGeneration.current;
     const isCurrentSubmission = () =>
-      mountedRef.current && mutationGeneration.current === generation;
+      submissionIsCurrent(mountedRef, mutationGeneration, generation);
     setBusy(true);
     try {
-      if (editingRow) {
-        await submissionClient.request(UpdateManagedAttendanceSegmentDocument, {
-          input: {
-            id: editingRow.id,
-            expectedUpdatedAt: editingRow.updatedAt,
-            ...attendanceInput,
-          },
-        });
-      } else {
-        await submissionClient.request(AddManagedAttendanceSegmentDocument, {
-          input: { employeeId: employee.employeeId, ...attendanceInput },
-        });
-      }
+      await saveRegularization(client, editingRow, employee.employeeId, attendanceInput);
       if (!isCurrentSubmission()) return;
       onSaved(employee.employeeName, workDate);
       onClose();
     } catch (error) {
       if (!isCurrentSubmission()) return;
       setFormError(graphQlUserMessage(error, 'attendance-management'));
     } finally {
       if (isCurrentSubmission()) setBusy(false);
     }
   };
diff --git a/src/utils/attendanceValidation.test.ts b/src/utils/attendanceValidation.test.ts
index 37fa22e..511e7ae 100644
--- a/src/utils/attendanceValidation.test.ts
+++ b/src/utils/attendanceValidation.test.ts
@@ -1,18 +1,28 @@
 import { describe, expect, it } from 'vitest';
 
 import { validateManualAttendanceSegment } from './attendanceValidation';
 
 const validInput = {
   workDate: '2025-01-15',
+  checkInDate: '2025-01-15',
+  checkOutDate: '2025-01-15',
   checkIn: '09:00',
   checkOut: '18:00',
+  currentWorkDate: '2025-01-20',
+  window: {
+    workDate: '2025-01-15',
+    startsAt: '2025-01-14T23:30:00Z',
+    endsAt: '2025-01-15T23:30:00Z',
+    timezone: 'Asia/Kolkata',
+    boundaryMinutes: 300,
+  },
   existingSegments: [],
 };
 
 describe('validateManualAttendanceSegment', () => {
   it('associates a missing date with the date field', () => {
     expect(validateManualAttendanceSegment({ ...validInput, workDate: '' })).toEqual({
       field: 'workDate',
       message: 'Enter work date, punch in, and punch out.',
     });
   });
@@ -33,21 +43,21 @@ describe('validateManualAttendanceSegment', () => {
 
   it('associates a missing or earlier punch out with the punch-out field', () => {
     expect(validateManualAttendanceSegment({ ...validInput, checkOut: '' })).toEqual({
       field: 'checkOut',
       message: 'Enter work date, punch in, and punch out.',
     });
     expect(
       validateManualAttendanceSegment({ ...validInput, checkIn: '18:00', checkOut: '09:00' })
     ).toEqual({
       field: 'checkOut',
-      message: 'Punch In must be before Punch Out for the same calendar day.',
+      message: 'Punch In must be before Punch Out.',
     });
   });
 
   it('returns form-level overlap and total-duration errors', () => {
     expect(
       validateManualAttendanceSegment({
         ...validInput,
         checkIn: '10:00',
         checkOut: '12:00',
         existingSegments: [
@@ -112,20 +122,54 @@ describe('validateManualAttendanceSegment', () => {
     ).toEqual({
       field: 'form',
       message: 'Total attendance for a day must be less than 24 hours.',
     });
   });
 
   it('accepts a valid non-overlapping interval', () => {
     expect(validateManualAttendanceSegment(validInput)).toBeNull();
   });
 
+  it('accepts a valid after-midnight interval using actual dates and canonical window bounds', () => {
+    expect(
+      validateManualAttendanceSegment({
+        ...validInput,
+        workDate: '2026-09-11',
+        checkInDate: '2026-09-12',
+        checkOutDate: '2026-09-12',
+        checkIn: '02:00',
+        checkOut: '04:00',
+        currentWorkDate: '2026-09-12',
+        window: {
+          workDate: '2026-09-11',
+          startsAt: '2026-09-10T23:30:00Z',
+          endsAt: '2026-09-11T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
+      })
+    ).toBeNull();
+  });
+
+  it('rejects actual dates outside the retained historical window', () => {
+    expect(
+      validateManualAttendanceSegment({
+        ...validInput,
+        checkInDate: '2025-01-14',
+        checkOutDate: '2025-01-15',
+      })
+    ).toEqual({
+      field: 'checkInDate',
+      message: 'Punch In must be inside the attendance day window.',
+    });
+  });
+
   it('normalizes hidden seconds only for legacy manual segments', () => {
     const existingSegment = {
       id: 'legacy-segment',
       workDate: validInput.workDate,
       checkInTime: '08:00:45',
       checkOutTime: '09:00:45',
     };
     const request = {
       ...validInput,
       checkIn: '09:00',
@@ -166,29 +210,39 @@ describe('validateManualAttendanceSegment', () => {
     expect(
       validateManualAttendanceSegment({ ...partialInput, checkIn: '10:00', checkOut: '12:00' })
     ).toBeNull();
     expect(
       validateManualAttendanceSegment({ ...partialInput, checkIn: '23:00', checkOut: '23:30' })
     ).toBeNull();
     expect(
       validateManualAttendanceSegment({ ...partialInput, checkIn: '18:00', checkOut: '09:00' })
     ).toEqual({
       field: 'checkOut',
-      message: 'Punch In must be before Punch Out for the same calendar day.',
+      message: 'Punch In must be before Punch Out.',
     });
   });
 
   it('defers cross-segment checks outside the loaded coverage range', () => {
     expect(
       validateManualAttendanceSegment({
         ...validInput,
         workDate: '2026-08-24',
+        checkInDate: '2026-08-24',
+        checkOutDate: '2026-08-24',
+        currentWorkDate: '2026-08-24',
+        window: {
+          workDate: '2026-08-24',
+          startsAt: '2026-08-23T23:30:00Z',
+          endsAt: '2026-08-24T23:30:00Z',
+          timezone: 'Asia/Kolkata',
+          boundaryMinutes: 300,
+        },
         checkIn: '10:00',
         checkOut: '12:00',
         existingSegmentsComplete: true,
         existingSegmentsCoverage: { fromDate: '2025-01-01', toDate: '2025-01-31' },
         existingSegments: [
           {
             id: 'outside-coverage',
             workDate: '2026-08-24',
             checkInTime: '08:00:00',
             checkOutTime: '11:00:00',
diff --git a/src/utils/attendanceValidation.ts b/src/utils/attendanceValidation.ts
index d06f77f..7e3fdd3 100644
--- a/src/utils/attendanceValidation.ts
+++ b/src/utils/attendanceValidation.ts
@@ -1,128 +1,259 @@
+import type { AttendanceDayWindowMetadata } from './attendanceDay';
+import { tenantLocalDateTimeToInstant } from './attendanceDay';
 import { naiveTimeToMinutes } from './attendanceDuration';
-import { toIsoDate } from './calendarRange';
 
 export const MAX_ATTENDANCE_MINUTES_PER_DAY = 24 * 60;
 
 export interface AttendanceSegmentInterval {
   id?: string;
   workDate: string;
   checkInTime?: string | null;
   checkOutTime?: string | null;
+  checkInAt?: string | null;
+  checkOutAt?: string | null;
   source?: string | null;
 }
 
 export interface ExistingSegmentsCoverage {
   fromDate: string;
   toDate: string;
 }
 
 export interface ManualAttendanceValidationInput {
   workDate: string;
+  checkInDate: string;
+  checkOutDate: string;
   checkIn: string;
   checkOut: string;
+  currentWorkDate: string;
+  window: AttendanceDayWindowMetadata;
   existingSegments: AttendanceSegmentInterval[];
   /** False when cursor paging means this is not the complete day/month list. */
   existingSegmentsComplete?: boolean;
   /** Omit only when existingSegments is complete for every date the caller can submit. */
   existingSegmentsCoverage?: ExistingSegmentsCoverage;
   excludedSegmentId?: string | null;
 }
 
-export type ManualAttendanceField = 'workDate' | 'checkIn' | 'checkOut' | 'form';
+export type ManualAttendanceField =
+  | 'workDate'
+  | 'checkInDate'
+  | 'checkOutDate'
+  | 'checkIn'
+  | 'checkOut'
+  | 'form';
 
 export interface ManualAttendanceValidationError {
   field: ManualAttendanceField;
   message: string;
 }
 
 function normalizeTime(value: string): string {
   return value.length === 5 ? `${value}:00` : value;
 }
 
 function intervalsOverlap(
   firstStart: number,
   firstEnd: number,
   secondStart: number,
   secondEnd: number
 ) {
   return firstStart < secondEnd && firstEnd > secondStart;
 }
 
-function existingTimeToMinutes(value: string | null | undefined, source: string | null | undefined) {
+function existingTimeToMinutes(
+  value: string | null | undefined,
+  source: string | null | undefined
+) {
   const minutes = naiveTimeToMinutes(value);
   return source?.trim().toUpperCase() === 'WEB+MANUAL' ? Math.floor(minutes) : minutes;
 }
 
-export function validateManualAttendanceSegment({
-  workDate,
-  checkIn,
-  checkOut,
-  existingSegments,
-  existingSegmentsComplete = true,
-  existingSegmentsCoverage,
-  excludedSegmentId,
-}: ManualAttendanceValidationInput): ManualAttendanceValidationError | null {
+interface ValidatedInterval {
+  end: number;
+  start: number;
+  wallEnd: number;
+  wallStart: number;
+}
+
+interface IntervalResult {
+  error: ManualAttendanceValidationError | null;
+  interval: ValidatedInterval | null;
+}
+
+function requiredInputError(
+  input: ManualAttendanceValidationInput
+): ManualAttendanceValidationError | null {
   const requiredMessage = 'Enter work date, punch in, and punch out.';
-  if (!workDate) return { field: 'workDate', message: requiredMessage };
-  if (workDate > toIsoDate(new Date())) {
+  if (!input.workDate) return { field: 'workDate', message: requiredMessage };
+  if (input.workDate > input.currentWorkDate) {
     return { field: 'workDate', message: 'Future attendance cannot be regularized.' };
   }
-  if (!checkIn) return { field: 'checkIn', message: requiredMessage };
-  if (!checkOut) return { field: 'checkOut', message: requiredMessage };
-
-  const start = naiveTimeToMinutes(normalizeTime(checkIn));
-  const end = naiveTimeToMinutes(normalizeTime(checkOut));
-  if (Number.isNaN(start)) return { field: 'checkIn', message: 'Enter valid punch times.' };
-  if (Number.isNaN(end)) return { field: 'checkOut', message: 'Enter valid punch times.' };
-  if (start >= end) {
+  if (!input.checkIn) return { field: 'checkIn', message: requiredMessage };
+  if (!input.checkOut) return { field: 'checkOut', message: requiredMessage };
+  if (!input.checkInDate) {
+    return { field: 'checkInDate', message: 'Enter the actual punch in and punch out dates.' };
+  }
+  if (!input.checkOutDate) {
+    return { field: 'checkOutDate', message: 'Enter the actual punch in and punch out dates.' };
+  }
+  return input.window.workDate === input.workDate
+    ? null
+    : { field: 'form', message: 'Reload the attendance day window before saving.' };
+}
+
+function canonicalRangeError(
+  start: number,
+  end: number,
+  window: AttendanceDayWindowMetadata
+): ManualAttendanceValidationError | null {
+  const windowStart = Date.parse(window.startsAt);
+  const windowEnd = Date.parse(window.endsAt);
+  if (start < windowStart || start >= windowEnd) {
+    return { field: 'checkInDate', message: 'Punch In must be inside the attendance day window.' };
+  }
+  if (end <= windowStart || end > windowEnd) {
     return {
-      field: 'checkOut',
-      message: 'Punch In must be before Punch Out for the same calendar day.',
+      field: 'checkOutDate',
+      message: 'Punch Out must be inside the attendance day window.',
     };
   }
+  return start < end ? null : { field: 'checkOut', message: 'Punch In must be before Punch Out.' };
+}
 
-  const newMinutes = end - start;
-  const isWithinLoadedCoverage =
-    existingSegmentsCoverage === undefined ||
-    (workDate >= existingSegmentsCoverage.fromDate && workDate <= existingSegmentsCoverage.toDate);
-  if (!existingSegmentsComplete || !isWithinLoadedCoverage) return null;
-
-  const sameDaySegments = existingSegments.filter(
-    (segment) => segment.workDate === workDate && segment.id !== excludedSegmentId
+function requestedInterval(input: ManualAttendanceValidationInput): IntervalResult {
+  const wallStart = naiveTimeToMinutes(normalizeTime(input.checkIn));
+  const wallEnd = naiveTimeToMinutes(normalizeTime(input.checkOut));
+  if (Number.isNaN(wallStart)) {
+    return { error: { field: 'checkIn', message: 'Enter valid punch times.' }, interval: null };
+  }
+  if (Number.isNaN(wallEnd)) {
+    return { error: { field: 'checkOut', message: 'Enter valid punch times.' }, interval: null };
+  }
+  const start = tenantLocalDateTimeToInstant(
+    input.checkInDate,
+    normalizeTime(input.checkIn),
+    input.window.timezone
   );
-  let existingMinutes = 0;
+  const end = tenantLocalDateTimeToInstant(
+    input.checkOutDate,
+    normalizeTime(input.checkOut),
+    input.window.timezone
+  );
+  if (start.ambiguous || end.ambiguous) {
+    return {
+      error: {
+        field: 'form',
+        message:
+          'These local times are ambiguous in the attendance timezone. Choose unambiguous times.',
+      },
+      interval: null,
+    };
+  }
+  if (start.instant === null) {
+    return {
+      error: { field: 'checkIn', message: 'Enter a valid punch date and time.' },
+      interval: null,
+    };
+  }
+  if (end.instant === null) {
+    return {
+      error: { field: 'checkOut', message: 'Enter a valid punch date and time.' },
+      interval: null,
+    };
+  }
+  const error = canonicalRangeError(start.instant, end.instant, input.window);
+  return {
+    error,
+    interval: error ? null : { start: start.instant, end: end.instant, wallStart, wallEnd },
+  };
+}
 
-  for (const segment of sameDaySegments) {
-    const existingStart = existingTimeToMinutes(segment.checkInTime, segment.source);
-    const existingEnd = existingTimeToMinutes(segment.checkOutTime, segment.source);
-    const hasValidInterval = !Number.isNaN(existingStart) && !Number.isNaN(existingEnd);
-    const worked =
-      hasValidInterval && existingStart !== existingEnd
-        ? existingEnd > existingStart
-          ? existingEnd - existingStart
-          : existingEnd + MAX_ATTENDANCE_MINUTES_PER_DAY - existingStart
-        : 0;
-    existingMinutes += worked;
-
-    const existingInterval =
-      hasValidInterval
-        ? { start: existingStart, end: existingEnd }
-        : null;
-
-    if (
-      existingInterval &&
-      intervalsOverlap(start, end, existingInterval.start, existingInterval.end)
-    ) {
-      return {
+interface ExistingSegmentResult {
+  error: ManualAttendanceValidationError | null;
+  minutes: number;
+}
+
+const overlapError = (): ManualAttendanceValidationError => ({
+  field: 'form',
+  message: 'This punch range overlaps an existing attendance segment for the day.',
+});
+
+function canonicalExistingSegment(
+  segment: AttendanceSegmentInterval,
+  requested: ValidatedInterval
+): ExistingSegmentResult | null {
+  const start = segment.checkInAt ? Date.parse(segment.checkInAt) : NaN;
+  const end = segment.checkOutAt ? Date.parse(segment.checkOutAt) : NaN;
+  if (Number.isFinite(start) && !segment.checkOutAt) {
+    return {
+      error: {
         field: 'form',
-        message: 'This punch range overlaps an existing attendance segment for the day.',
-      };
-    }
+        message: 'Complete or correct the existing incomplete segment before adding another.',
+      },
+      minutes: 0,
+    };
   }
+  if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
+  return {
+    error: intervalsOverlap(requested.start, requested.end, start, end) ? overlapError() : null,
+    minutes: (end - start) / 60_000,
+  };
+}
+
+function legacyExistingSegment(
+  segment: AttendanceSegmentInterval,
+  input: ManualAttendanceValidationInput,
+  requested: ValidatedInterval
+): ExistingSegmentResult {
+  const start = existingTimeToMinutes(segment.checkInTime, segment.source);
+  const end = existingTimeToMinutes(segment.checkOutTime, segment.source);
+  const valid = !Number.isNaN(start) && !Number.isNaN(end);
+  let minutes = 0;
+  if (valid && start !== end) {
+    minutes = end > start ? end - start : end + MAX_ATTENDANCE_MINUTES_PER_DAY - start;
+  }
+  const comparableDates =
+    input.checkInDate === input.workDate && input.checkOutDate === input.workDate;
+  const overlaps =
+    valid &&
+    comparableDates &&
+    intervalsOverlap(requested.wallStart, requested.wallEnd, start, end);
+  return { error: overlaps ? overlapError() : null, minutes };
+}
 
-  if (existingMinutes + newMinutes >= MAX_ATTENDANCE_MINUTES_PER_DAY) {
-    return { field: 'form', message: 'Total attendance for a day must be less than 24 hours.' };
+function validateExistingSegments(
+  input: ManualAttendanceValidationInput,
+  requested: ValidatedInterval
+): ManualAttendanceValidationError | null {
+  const sameDaySegments = input.existingSegments.filter(
+    (segment) => segment.workDate === input.workDate && segment.id !== input.excludedSegmentId
+  );
+  let existingMinutes = 0;
+  for (const segment of sameDaySegments) {
+    const result =
+      canonicalExistingSegment(segment, requested) ??
+      legacyExistingSegment(segment, input, requested);
+    if (result.error) return result.error;
+    existingMinutes += result.minutes;
   }
+  const requestedMinutes = (requested.end - requested.start) / 60_000;
+  return existingMinutes + requestedMinutes < MAX_ATTENDANCE_MINUTES_PER_DAY
+    ? null
+    : { field: 'form', message: 'Total attendance for a day must be less than 24 hours.' };
+}
 
-  return null;
+export function validateManualAttendanceSegment(
+  input: ManualAttendanceValidationInput
+): ManualAttendanceValidationError | null {
+  const requiredError = requiredInputError(input);
+  if (requiredError) return requiredError;
+  const { error, interval } = requestedInterval(input);
+  if (error || !interval) return error;
+  const isWithinLoadedCoverage =
+    input.existingSegmentsCoverage === undefined ||
+    (input.workDate >= input.existingSegmentsCoverage.fromDate &&
+      input.workDate <= input.existingSegmentsCoverage.toDate);
+  if (input.existingSegmentsComplete === false || !isWithinLoadedCoverage) return null;
+  return validateExistingSegments(input, interval);
 }

warning: in the working copy of 'src/modules/admin/AdminAttendancePolicyPage.test.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/modules/admin/AdminAttendancePolicyPage.test.tsx b/src/modules/admin/AdminAttendancePolicyPage.test.tsx
new file mode 100644
index 0000000..aa47d90
--- /dev/null
+++ b/src/modules/admin/AdminAttendancePolicyPage.test.tsx
@@ -0,0 +1,176 @@
+// @vitest-environment jsdom
+
+import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
+import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
+
+import {
+  AttendancePolicySettingsDocument,
+  PreviewAttendanceDayPolicyDocument,
+  ScheduleAttendanceDayPolicyDocument,
+} from '../../api/attendance/graphql';
+import type { ParsedClientSession } from '../../auth/clientSession';
+
+import AdminAttendancePolicyPage from './AdminAttendancePolicyPage';
+
+const state = vi.hoisted(() => ({
+  client: { request: vi.fn() },
+  session: {
+    employeeId: 'admin-1',
+    jwtRoles: [],
+    mustChangePassword: false,
+    persona: 'ADMIN',
+    permissions: new Set(['attendance:punch_policy']),
+    permissionScopes: { 'attendance:punch_policy': 'ALL' },
+    resourceScopes: {},
+  } as ParsedClientSession,
+}));
+
+vi.mock('../../hooks/useGraphClient', () => ({ useGraphClient: () => state.client }));
+vi.mock('../../contexts/AuthContext', () => ({
+  useAuth: () => ({ clientSession: state.session }),
+}));
+
+const policy = (revision = 7) => ({
+  attendanceDayPolicy: {
+    revision,
+    initialized: true,
+    legacyActivationPending: false,
+    legacyActivationDate: '2026-09-12',
+    currentPolicy: {
+      effectiveWorkDate: '2026-09-12',
+      boundaryMinutes: 300,
+      timezone: 'Asia/Kolkata',
+    },
+    pendingPolicy: {
+      effectiveWorkDate: '2026-09-20',
+      boundaryMinutes: 360,
+      timezone: 'Asia/Kolkata',
+    },
+    currentWindow: {
+      workDate: '2026-09-11',
+      startsAt: '2026-09-10T23:30:00Z',
+      endsAt: '2026-09-11T23:30:00Z',
+      timezone: 'Asia/Kolkata',
+      boundaryMinutes: 300,
+    },
+  },
+  attendancePunchPolicy: {
+    id: 'policy-1',
+    isEnforced: false,
+    siteLatitude: null,
+    siteLongitude: null,
+    maxDistanceMeters: null,
+    ipAllowlist: null,
+    updatedAt: null,
+  },
+  shifts: [],
+});
+
+const preview = {
+  previewAttendanceDayPolicy: {
+    revision: 8,
+    transition: {
+      workDate: '2026-09-20',
+      startsAt: '2026-09-19T23:30:00Z',
+      endsAt: '2026-09-21T00:30:00Z',
+      timezone: 'Asia/Kolkata',
+      boundaryMinutes: 360,
+    },
+    following: {
+      workDate: '2026-09-21',
+      startsAt: '2026-09-21T00:30:00Z',
+      endsAt: '2026-09-22T00:30:00Z',
+      timezone: 'Asia/Kolkata',
+      boundaryMinutes: 360,
+    },
+  },
+};
+
+beforeEach(() => {
+  state.session.permissions = new Set(['attendance:punch_policy']);
+  state.session.permissionScopes = { 'attendance:punch_policy': 'ALL' };
+  state.client = { request: vi.fn() };
+  state.client.request.mockImplementation((document: unknown) => {
+    if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy());
+    if (document === PreviewAttendanceDayPolicyDocument) return Promise.resolve(preview);
+    if (document === ScheduleAttendanceDayPolicyDocument)
+      return Promise.resolve({ scheduleAttendanceDayPolicy: policy(8).attendanceDayPolicy });
+    throw new Error('Unexpected operation');
+  });
+});
+
+afterEach(cleanup);
+
+describe('attendance day policy settings', () => {
+  it('does not issue policy operations without exact ALL authority', async () => {
+    state.session.permissionScopes = { 'attendance:punch_policy': 'TEAM' };
+    render(<AdminAttendancePolicyPage />);
+    expect(screen.getByRole('status').textContent).toContain('do not have access');
+    await Promise.resolve();
+    expect(state.client.request).not.toHaveBeenCalled();
+  });
+
+  it('shows current and pending policy and schedules only after exact interval confirmation', async () => {
+    render(<AdminAttendancePolicyPage />);
+    expect(await screen.findByText('Current start: 05:00')).toBeTruthy();
+    expect(screen.getByText('Scheduled start: 06:00 from 2026-09-20')).toBeTruthy();
+
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+
+    expect(await screen.findByText(/20 Sept 2026, 05:00.*21 Sept 2026, 06:00/)).toBeTruthy();
+    expect(screen.getAllByText(/Asia\/Kolkata/).length).toBeGreaterThan(0);
+    expect(
+      screen.getByRole<HTMLButtonElement>('button', { name: 'Schedule change' }).disabled
+    ).toBe(true);
+    fireEvent.click(screen.getByRole('checkbox', { name: /confirm this exact transition/i }));
+    fireEvent.click(screen.getByRole('button', { name: 'Schedule change' }));
+
+    await waitFor(() =>
+      expect(state.client.request).toHaveBeenCalledWith(ScheduleAttendanceDayPolicyDocument, {
+        input: {
+          boundaryTime: '06:00',
+          effectiveWorkDate: '2026-09-20',
+          expectedRevision: 7,
+        },
+      })
+    );
+  });
+
+  it('reloads a revision conflict without discarding the administrator draft', async () => {
+    state.client.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument)
+        return Promise.resolve(
+          state.client.request.mock.calls.filter(([operation]) => operation === document).length > 1
+            ? policy(8)
+            : policy(7)
+        );
+      if (document === PreviewAttendanceDayPolicyDocument) return Promise.resolve(preview);
+      if (document === ScheduleAttendanceDayPolicyDocument)
+        return Promise.reject({ code: 'CONFLICT' });
+      throw new Error('Unexpected operation');
+    });
+    render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:30' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-22' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    await screen.findByText(/20 Sept 2026, 05:00/);
+    fireEvent.click(screen.getByRole('checkbox', { name: /confirm this exact transition/i }));
+    fireEvent.click(screen.getByRole('button', { name: 'Schedule change' }));
+
+    expect(await screen.findByText(/changed while you were reviewing/i)).toBeTruthy();
+    expect(screen.getByLabelText<HTMLInputElement>('Attendance day starts at').value).toBe('06:30');
+    expect(screen.getByLabelText<HTMLInputElement>('Effective work date').value).toBe('2026-09-22');
+    expect(state.client.request).toHaveBeenCalledWith(AttendancePolicySettingsDocument);
+  });
+});

warning: in the working copy of 'src/modules/admin/AttendanceDayPolicySettings.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/modules/admin/AttendanceDayPolicySettings.tsx b/src/modules/admin/AttendanceDayPolicySettings.tsx
new file mode 100644
index 0000000..e0c9536
--- /dev/null
+++ b/src/modules/admin/AttendanceDayPolicySettings.tsx
@@ -0,0 +1,159 @@
+import Button from '../../components/common/Button';
+import Card from '../../components/common/Card';
+import Input from '../../components/common/Input';
+import PageNotice from '../../components/common/PageNotice';
+import { boundaryTime, formatAttendanceWindow } from '../../utils/attendanceDay';
+
+import {
+  useAttendanceDayPolicyDraft,
+  type AttendanceDayPolicyDraftOptions,
+} from './useAttendanceDayPolicyDraft';
+
+type Props = AttendanceDayPolicyDraftOptions;
+
+const PolicyNotices = ({
+  error,
+  legacyActivationPending,
+  success,
+}: {
+  error: string | null;
+  legacyActivationPending: boolean;
+  success: string | null;
+}) => (
+  <>
+    {legacyActivationPending ? (
+      <PageNotice variant="warning" title="Initial activation pending">
+        Choose a future work date to activate the default boundary without reinterpreting existing
+        attendance.
+      </PageNotice>
+    ) : null}
+    {error ? (
+      <PageNotice variant="error" title="Attendance day change was not saved">
+        {error}
+      </PageNotice>
+    ) : null}
+    {success ? <PageNotice variant="success">{success}</PageNotice> : null}
+  </>
+);
+
+const AttendanceDayPolicySettings = (props: Props) => {
+  const { policy } = props;
+  const {
+    boundary,
+    busy,
+    changeDraft,
+    confirmed,
+    effectiveDate,
+    error,
+    preview,
+    requestPreview,
+    schedule,
+    setBoundary,
+    setConfirmed,
+    setEffectiveDate,
+    success,
+  } = useAttendanceDayPolicyDraft(props);
+
+  return (
+    <Card title="Attendance Day Boundary">
+      <div className="space-y-4">
+        <div className="grid gap-3 text-sm sm:grid-cols-2">
+          <div className="rounded-lg bg-canvas p-3">
+            <p className="font-medium text-content-primary">
+              Current start: {boundaryTime(policy.currentPolicy.boundaryMinutes)}
+            </p>
+            <p className="mt-1 text-content-secondary">
+              Effective {policy.currentPolicy.effectiveWorkDate} · {policy.currentPolicy.timezone}
+            </p>
+          </div>
+          <div className="rounded-lg bg-canvas p-3">
+            {policy.pendingPolicy ? (
+              <>
+                <p className="font-medium text-content-primary">
+                  Scheduled start: {boundaryTime(policy.pendingPolicy.boundaryMinutes)} from{' '}
+                  {policy.pendingPolicy.effectiveWorkDate}
+                </p>
+                <p className="mt-1 text-content-secondary">{policy.pendingPolicy.timezone}</p>
+              </>
+            ) : (
+              <p className="text-content-secondary">No future boundary change is scheduled.</p>
+            )}
+          </div>
+        </div>
+
+        <p className="text-xs text-content-secondary">
+          Active work date {policy.currentWindow.workDate}:{' '}
+          {formatAttendanceWindow(policy.currentWindow)}
+        </p>
+        <PolicyNotices
+          error={error}
+          legacyActivationPending={policy.legacyActivationPending}
+          success={success}
+        />
+
+        <form className="space-y-3" onSubmit={(event) => void requestPreview(event)}>
+          <div className="grid gap-3 sm:grid-cols-2">
+            <Input
+              type="time"
+              label="Attendance day starts at"
+              value={boundary}
+              onChange={(event) => changeDraft(() => setBoundary(event.target.value))}
+              fullWidth
+              required
+            />
+            <Input
+              type="date"
+              label="Effective work date"
+              value={effectiveDate}
+              onChange={(event) => changeDraft(() => setEffectiveDate(event.target.value))}
+              fullWidth
+              required
+            />
+          </div>
+          <Button
+            type="submit"
+            variant="outline"
+            disabled={busy !== null || !boundary || !effectiveDate}
+          >
+            {busy === 'preview' ? 'Loading preview…' : 'Preview change'}
+          </Button>
+        </form>
+
+        {preview ? (
+          <div className="space-y-3 rounded-lg border border-line p-3">
+            <div>
+              <p className="text-sm font-medium text-content-primary">Transition work date</p>
+              <p className="text-sm text-content-secondary">
+                {formatAttendanceWindow(preview.transition)}
+              </p>
+            </div>
+            <div>
+              <p className="text-sm font-medium text-content-primary">Following work date</p>
+              <p className="text-sm text-content-secondary">
+                {formatAttendanceWindow(preview.following)}
+              </p>
+            </div>
+            <label className="flex items-start gap-2 text-sm text-content-secondary">
+              <input
+                type="checkbox"
+                className="mt-0.5"
+                checked={confirmed}
+                onChange={(event) => setConfirmed(event.target.checked)}
+              />
+              I confirm this exact transition interval and timezone.
+            </label>
+            <Button
+              type="button"
+              disabled={!confirmed || busy !== null}
+              onClick={() => void schedule()}
+            >
+              {busy === 'schedule' ? 'Scheduling…' : 'Schedule change'}
+            </Button>
+          </div>
+        ) : null}
+      </div>
+    </Card>
+  );
+};
+
+export default AttendanceDayPolicySettings;

warning: in the working copy of 'src/modules/admin/useAttendanceDayPolicyDraft.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/modules/admin/useAttendanceDayPolicyDraft.ts b/src/modules/admin/useAttendanceDayPolicyDraft.ts
new file mode 100644
index 0000000..235c183
--- /dev/null
+++ b/src/modules/admin/useAttendanceDayPolicyDraft.ts
@@ -0,0 +1,141 @@
+import { ClientError } from 'graphql-request';
+import { useEffect, useRef, useState, type FormEvent } from 'react';
+
+import {
+  PreviewAttendanceDayPolicyDocument,
+  ScheduleAttendanceDayPolicyDocument,
+  type AttendancePolicySettingsQuery,
+  type PreviewAttendanceDayPolicyQuery,
+} from '../../api/attendance/graphql';
+import { useGraphClient } from '../../hooks/useGraphClient';
+import { boundaryTime } from '../../utils/attendanceDay';
+import { graphQlUserMessage } from '../../utils/graphqlUserMessage';
+
+export type AttendanceDayPolicy = AttendancePolicySettingsQuery['attendanceDayPolicy'];
+type Preview = PreviewAttendanceDayPolicyQuery['previewAttendanceDayPolicy'];
+
+export interface AttendanceDayPolicyDraftOptions {
+  policy: AttendanceDayPolicy;
+  onPolicyChanged: (policy: AttendanceDayPolicy) => void;
+  reloadPolicy: () => Promise<void>;
+}
+
+function isConflict(error: unknown) {
+  if (error instanceof ClientError) {
+    return error.response.errors?.some(
+      ({ extensions }) => String(extensions.code).toUpperCase() === 'CONFLICT'
+    );
+  }
+  return Boolean(
+    error &&
+    typeof error === 'object' &&
+    'code' in error &&
+    String((error as { code?: unknown }).code).toUpperCase() === 'CONFLICT'
+  );
+}
+
+export function useAttendanceDayPolicyDraft({
+  policy,
+  onPolicyChanged,
+  reloadPolicy,
+}: AttendanceDayPolicyDraftOptions) {
+  const client = useGraphClient('client');
+  const initialized = useRef(false);
+  const [boundary, setBoundary] = useState('');
+  const [effectiveDate, setEffectiveDate] = useState('');
+  const [preview, setPreview] = useState<Preview | null>(null);
+  const [confirmed, setConfirmed] = useState(false);
+  const [busy, setBusy] = useState<'preview' | 'schedule' | null>(null);
+  const [error, setError] = useState<string | null>(null);
+  const [success, setSuccess] = useState<string | null>(null);
+
+  useEffect(() => {
+    if (initialized.current) return;
+    initialized.current = true;
+    const draft = policy.pendingPolicy ?? policy.currentPolicy;
+    setBoundary(boundaryTime(draft.boundaryMinutes));
+    setEffectiveDate(policy.pendingPolicy?.effectiveWorkDate ?? '');
+  }, [policy]);
+
+  const changeDraft = (change: () => void) => {
+    change();
+    setPreview(null);
+    setConfirmed(false);
+    setError(null);
+    setSuccess(null);
+  };
+  const input = {
+    boundaryTime: boundary,
+    effectiveWorkDate: effectiveDate,
+    expectedRevision: policy.revision,
+  };
+  const requestPreview = async (event: FormEvent) => {
+    event.preventDefault();
+    setBusy('preview');
+    setError(null);
+    setSuccess(null);
+    setConfirmed(false);
+    try {
+      const result = await client.request<PreviewAttendanceDayPolicyQuery>(
+        PreviewAttendanceDayPolicyDocument,
+        { input }
+      );
+      setPreview(result.previewAttendanceDayPolicy);
+    } catch (reason) {
+      setPreview(null);
+      setError(graphQlUserMessage(reason));
+    } finally {
+      setBusy(null);
+    }
+  };
+  const schedule = async () => {
+    if (!preview || !confirmed || busy) return;
+    setBusy('schedule');
+    setError(null);
+    setSuccess(null);
+    try {
+      const result = await client.request<{ scheduleAttendanceDayPolicy: AttendanceDayPolicy }>(
+        ScheduleAttendanceDayPolicyDocument,
+        { input }
+      );
+      onPolicyChanged(result.scheduleAttendanceDayPolicy);
+      setPreview(null);
+      setConfirmed(false);
+      setSuccess('Attendance day change scheduled.');
+    } catch (reason) {
+      setPreview(null);
+      setConfirmed(false);
+      if (!isConflict(reason)) {
+        setError(graphQlUserMessage(reason));
+      } else {
+        setError(
+          'The attendance day policy changed while you were reviewing it. The latest policy was reloaded; preview your retained draft again.'
+        );
+        try {
+          await reloadPolicy();
+        } catch {
+          setError(
+            'The attendance day policy changed while you were reviewing it. Your draft was retained, but the latest policy could not be reloaded. Reload the page before previewing again.'
+          );
+        }
+      }
+    } finally {
+      setBusy(null);
+    }
+  };
+  return {
+    boundary,
+    busy,
+    changeDraft,
+    confirmed,
+    effectiveDate,
+    error,
+    preview,
+    requestPreview,
+    schedule,
+    setBoundary,
+    setConfirmed,
+    setEffectiveDate,
+    success,
+  };
+}

warning: in the working copy of 'src/modules/attendance/hooks/useAttendanceDayWindows.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/modules/attendance/hooks/useAttendanceDayWindows.ts b/src/modules/attendance/hooks/useAttendanceDayWindows.ts
new file mode 100644
index 0000000..7db6756
--- /dev/null
+++ b/src/modules/attendance/hooks/useAttendanceDayWindows.ts
@@ -0,0 +1,105 @@
+import { useCallback, useEffect, useRef, useState } from 'react';
+
+import {
+  AttendanceCorrectionWindowsDocument,
+  AttendanceCurrentDayWindowDocument,
+  type AttendanceCorrectionWindowsQuery,
+  type AttendanceCurrentDayWindowQuery,
+} from '../../../api/attendance/graphql';
+import type { useGraphClient } from '../../../hooks/useGraphClient';
+import { useRetainedQuery } from '../../../hooks/useRetainedQuery';
+import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
+
+type GraphClient = ReturnType<typeof useGraphClient>;
+
+export function useCurrentAttendanceDayWindow(client: GraphClient, identity: string) {
+  const load = useCallback(async () => {
+    void identity;
+    const result = (await client.request<AttendanceCurrentDayWindowQuery>(
+      AttendanceCurrentDayWindowDocument
+    )) as Partial<AttendanceCurrentDayWindowQuery>;
+    if (!result.attendanceDayWindow) {
+      throw new Error('Attendance day window response was incomplete.');
+    }
+    return result.attendanceDayWindow;
+  }, [client, identity]);
+  return useRetainedQuery(load);
+}
+
+interface CorrectionWindowsState {
+  client: GraphClient;
+  workDate: string;
+  data: AttendanceCorrectionWindowsQuery | null;
+  error: string | null;
+  loading: boolean;
+}
+
+export function useAttendanceCorrectionWindows(
+  client: GraphClient,
+  isOpen: boolean,
+  workDate: string
+) {
+  const generation = useRef(0);
+  const mounted = useRef(false);
+  const [state, setState] = useState<CorrectionWindowsState>({
+    client,
+    workDate,
+    data: null,
+    error: null,
+    loading: isOpen,
+  });
+  const refresh = useCallback(async () => {
+    if (!isOpen || !workDate) return;
+    const request = ++generation.current;
+    setState({ client, workDate, data: null, error: null, loading: true });
+    try {
+      const data = (await client.request<AttendanceCorrectionWindowsQuery>(
+        AttendanceCorrectionWindowsDocument,
+        { workDate }
+      )) as Partial<AttendanceCorrectionWindowsQuery>;
+      if (!data.currentWindow || !data.selectedWindow) {
+        throw new Error('Attendance day window response was incomplete.');
+      }
+      if (mounted.current && generation.current === request) {
+        setState({
+          client,
+          workDate,
+          data: data as AttendanceCorrectionWindowsQuery,
+          error: null,
+          loading: false,
+        });
+      }
+    } catch (error) {
+      if (mounted.current && generation.current === request) {
+        setState({
+          client,
+          workDate,
+          data: null,
+          error: graphQlUserMessage(error),
+          loading: false,
+        });
+      }
+    }
+  }, [client, isOpen, workDate]);
+
+  useEffect(() => {
+    mounted.current = true;
+    return () => {
+      mounted.current = false;
+      generation.current += 1;
+    };
+  }, []);
+
+  useEffect(() => {
+    void refresh();
+    return () => {
+      generation.current += 1;
+    };
+  }, [refresh]);
+
+  const visible =
+    state.client === client && state.workDate === workDate
+      ? state
+      : { client, workDate, data: null, error: null, loading: isOpen };
+  return { ...visible, refresh };
+}

warning: in the working copy of 'src/modules/dashboard/components/usePunchDaySummary.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/modules/dashboard/components/usePunchDaySummary.ts b/src/modules/dashboard/components/usePunchDaySummary.ts
new file mode 100644
index 0000000..5a7e5f6
--- /dev/null
+++ b/src/modules/dashboard/components/usePunchDaySummary.ts
@@ -0,0 +1,91 @@
+import { useCallback, useEffect, useRef } from 'react';
+
+import { AttendancePunchDaySummaryDocument } from '../../../api/attendance/graphql';
+import type { useGraphClient } from '../../../hooks/useGraphClient';
+import { useRetainedQuery } from '../../../hooks/useRetainedQuery';
+import { formatTenantTime } from '../../../utils/tenantTime';
+
+import type { AttendanceRow, Summary } from './attendanceSummaryTypes';
+
+export type PunchGraphClient = ReturnType<typeof useGraphClient>;
+
+export function displayAttendanceRow(row: AttendanceRow, timezone: string): AttendanceRow {
+  return {
+    ...row,
+    checkInTime: row.checkInAt ? formatTenantTime(row.checkInAt, timezone) : row.checkInTime,
+    checkOutTime: row.checkOutAt ? formatTenantTime(row.checkOutAt, timezone) : row.checkOutTime,
+  };
+}
+
+function validateCurrentSummary(summary: Summary): void {
+  const startsAt = Date.parse(summary.startsAt);
+  const endsAt = Date.parse(summary.endsAt);
+  if (!Number.isFinite(startsAt) || !Number.isFinite(endsAt) || startsAt >= endsAt) {
+    throw new Error('Attendance summary returned an invalid attendance day window.');
+  }
+  if (Date.now() < startsAt || Date.now() >= endsAt) {
+    throw new Error('Attendance summary is outside the current attendance day. Refresh it.');
+  }
+}
+
+export function usePunchDaySummary(client: PunchGraphClient, identity: string) {
+  const loadSummary = useCallback(async () => {
+    void identity;
+    const result = await client.request<{ punchDaySummary: Summary }>(
+      AttendancePunchDaySummaryDocument
+    );
+    validateCurrentSummary(result.punchDaySummary);
+    const { punchDaySummary } = result;
+    return {
+      ...punchDaySummary,
+      segments: punchDaySummary.segments.map((row) =>
+        displayAttendanceRow(row, punchDaySummary.timezone)
+      ),
+      openSegment: punchDaySummary.openSegment
+        ? displayAttendanceRow(punchDaySummary.openSegment, punchDaySummary.timezone)
+        : null,
+    };
+  }, [client, identity]);
+  const { data, error, phase, refresh } = useRetainedQuery(loadSummary);
+  const refreshedBoundary = useRef<string | null>(null);
+  const resumeInFlight = useRef<Promise<void> | null>(null);
+
+  useEffect(() => {
+    const endsAt = data?.endsAt;
+    if (!endsAt) return;
+    const refreshBoundary = () => {
+      if (refreshedBoundary.current === endsAt) return;
+      refreshedBoundary.current = endsAt;
+      void refresh();
+    };
+    const delay = Date.parse(endsAt) - Date.now();
+    if (delay <= 0) {
+      refreshBoundary();
+      return;
+    }
+    const timer = window.setTimeout(refreshBoundary, Math.min(delay, 2_147_483_647));
+    return () => window.clearTimeout(timer);
+  }, [data?.endsAt, refresh]);
+
+  useEffect(() => {
+    const resume = () => {
+      if (resumeInFlight.current) return;
+      const request = refresh();
+      resumeInFlight.current = request;
+      void request.finally(() => {
+        if (resumeInFlight.current === request) resumeInFlight.current = null;
+      });
+    };
+    const visible = () => {
+      if (document.visibilityState === 'visible') resume();
+    };
+    window.addEventListener('focus', resume);
+    document.addEventListener('visibilitychange', visible);
+    return () => {
+      window.removeEventListener('focus', resume);
+      document.removeEventListener('visibilitychange', visible);
+    };
+  }, [refresh]);
+
+  return { data, error, phase, refresh };
+}

warning: in the working copy of 'src/utils/attendanceDay.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/utils/attendanceDay.ts b/src/utils/attendanceDay.ts
new file mode 100644
index 0000000..7f617da
--- /dev/null
+++ b/src/utils/attendanceDay.ts
@@ -0,0 +1,137 @@
+export interface AttendanceDayWindowMetadata {
+  workDate: string;
+  startsAt: string;
+  endsAt: string;
+  timezone: string;
+  boundaryMinutes: number;
+}
+
+const localPartsFormatter = new Map<string, Intl.DateTimeFormat>();
+
+function formatter(timezone: string) {
+  const cached = localPartsFormatter.get(timezone);
+  if (cached) return cached;
+  const value = new Intl.DateTimeFormat('en-GB', {
+    timeZone: timezone,
+    year: 'numeric',
+    month: '2-digit',
+    day: '2-digit',
+    hour: '2-digit',
+    minute: '2-digit',
+    second: '2-digit',
+    hourCycle: 'h23',
+  });
+  localPartsFormatter.set(timezone, value);
+  return value;
+}
+
+function partsAt(instant: Date, timezone: string) {
+  const parts = formatter(timezone).formatToParts(instant);
+  const get = (type: Intl.DateTimeFormatPartTypes) =>
+    Number(parts.find((part) => part.type === type)?.value);
+  return {
+    year: get('year'),
+    month: get('month'),
+    day: get('day'),
+    hour: get('hour'),
+    minute: get('minute'),
+    second: get('second'),
+  };
+}
+
+export function boundaryTime(boundaryMinutes: number): string {
+  const hours = Math.floor(boundaryMinutes / 60);
+  const minutes = boundaryMinutes % 60;
+  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
+}
+
+export function localDateAt(value: string | null | undefined, timezone: string): string | null {
+  if (!value) return null;
+  const instant = new Date(value);
+  if (!Number.isFinite(instant.getTime())) return null;
+  const parts = partsAt(instant, timezone);
+  return `${String(parts.year).padStart(4, '0')}-${String(parts.month).padStart(2, '0')}-${String(
+    parts.day
+  ).padStart(2, '0')}`;
+}
+
+export function formatAttendanceWindow(window: AttendanceDayWindowMetadata): string {
+  const format = new Intl.DateTimeFormat('en-GB', {
+    timeZone: window.timezone,
+    day: '2-digit',
+    month: 'short',
+    year: 'numeric',
+    hour: '2-digit',
+    minute: '2-digit',
+    hourCycle: 'h23',
+  });
+  return `${format.format(new Date(window.startsAt))} – ${format.format(new Date(window.endsAt))} (${window.timezone})`;
+}
+
+interface LocalDateTimeResult {
+  instant: number | null;
+  ambiguous: boolean;
+}
+
+type LocalDateTimeParts = ReturnType<typeof partsAt>;
+
+function validLocalParts(parts: LocalDateTimeParts): boolean {
+  return (
+    parts.month >= 1 &&
+    parts.month <= 12 &&
+    parts.day >= 1 &&
+    parts.day <= 31 &&
+    parts.hour <= 23 &&
+    parts.minute <= 59 &&
+    parts.second <= 59
+  );
+}
+
+function parseLocalDateTime(date: string, time: string): LocalDateTimeParts | null {
+  const dateMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
+  const timeMatch = /^(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(time);
+  if (!dateMatch || !timeMatch) return null;
+  const parts = {
+    year: Number(dateMatch[1]),
+    month: Number(dateMatch[2]),
+    day: Number(dateMatch[3]),
+    hour: Number(timeMatch[1]),
+    minute: Number(timeMatch[2]),
+    second: Number(timeMatch[3] || 0),
+  };
+  return validLocalParts(parts) ? parts : null;
+}
+
+function partsKey(parts: LocalDateTimeParts): string {
+  return [parts.year, parts.month, parts.day, parts.hour, parts.minute, parts.second].join(':');
+}
+
+function matchingInstants(wanted: LocalDateTimeParts, timezone: string): number[] {
+  const localAsUtc = Date.UTC(
+    wanted.year,
+    wanted.month - 1,
+    wanted.day,
+    wanted.hour,
+    wanted.minute,
+    wanted.second
+  );
+  const wantedKey = partsKey(wanted);
+  return Array.from({ length: 113 }, (_, index) => {
+    const offsetMinutes = -14 * 60 + index * 15;
+    return localAsUtc - offsetMinutes * 60_000;
+  }).filter((candidate) => partsKey(partsAt(new Date(candidate), timezone)) === wantedKey);
+}
+
+export function tenantLocalDateTimeToInstant(
+  date: string,
+  time: string,
+  timezone: string
+): LocalDateTimeResult {
+  const wanted = parseLocalDateTime(date, time);
+  if (!wanted) return { instant: null, ambiguous: false };
+  const candidates = matchingInstants(wanted, timezone);
+  return {
+    instant: candidates.length === 1 ? candidates[0] : null,
+    ambiguous: candidates.length > 1,
+  };
+}
