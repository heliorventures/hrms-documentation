# Final Task 3 UI source diff

Base 402309e81cc5405e01ed1912677d2c026860c31d, initially clean. All current uncommitted tracked/untracked UI changes. Generated code retained verbatim.

diff --git a/scripts/generate-attendance-client.mjs b/scripts/generate-attendance-client.mjs
index 0ecabe5..f5832eb 100644
--- a/scripts/generate-attendance-client.mjs
+++ b/scripts/generate-attendance-client.mjs
@@ -40,7 +40,15 @@ await generate(
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
diff --git a/src/api/attendance/gql.ts b/src/api/attendance/gql.ts
index 8f454ad..5ce581a 100644
--- a/src/api/attendance/gql.ts
+++ b/src/api/attendance/gql.ts
@@ -14,10 +14,10 @@ import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-
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
@@ -37,7 +37,7 @@ export function attendanceGraphql(source: string): unknown;
 /**
  * The attendanceGraphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
  */
-export function attendanceGraphql(source: "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}"): (typeof documents)["query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}"];
+export function attendanceGraphql(source: "query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nquery AttendanceCurrentDayWindow {\n  attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendanceCorrectionWindows($workDate: NaiveDate!) {\n  currentWindow: attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n  selectedWindow: attendanceDayWindow(workDate: $workDate) {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendancePolicySettings($slim: Int! = 50) {\n  attendanceDayPolicy {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n  attendancePunchPolicy {\n    id\n    tenantId\n    isEnforced\n    siteLatitude\n    siteLongitude\n    maxDistanceMeters\n    ipAllowlist\n    updatedAt\n  }\n  shifts(limit: $slim) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n}\n\nquery PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  previewAttendanceDayPolicy(input: $input) {\n    revision\n    transition {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n    following {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nmutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  scheduleAttendanceDayPolicy(input: $input) {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nquery AttendancePunchDaySummary {\n  punchDaySummary {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n    totalWorkedMinutes\n    openSegment {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n    segments {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n  }\n}\n\nmutation AttendancePunchToday($input: PunchTodayInput) {\n  punchToday(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    checkInLat\n    checkInLng\n    checkOutLat\n    checkOutLng\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {\n  addManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {\n  updateManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {\n  addManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}\n\nmutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {\n  updateManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}"): (typeof documents)["query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int = 50, $after: String) {\n  shifts(limit: 100) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n  myAttendanceSummary(fromDate: $fromDate, toDate: $toDate) {\n    completedMinutes\n    workedDays\n    averageMinutes\n    incompleteSegments\n  }\n  myAttendance(fromDate: $fromDate, toDate: $toDate, first: $first, after: $after) {\n    edges {\n      cursor\n      node {\n        id\n        employeeId\n        workDate\n        checkInAt\n        checkOutAt\n        checkInTime\n        checkOutTime\n        checkInLat\n        checkInLng\n        checkOutLat\n        checkOutLng\n        status\n        source\n        lateMinutes\n      }\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nquery AttendanceCurrentDayWindow {\n  attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendanceCorrectionWindows($workDate: NaiveDate!) {\n  currentWindow: attendanceDayWindow {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n  selectedWindow: attendanceDayWindow(workDate: $workDate) {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n  }\n}\n\nquery AttendancePolicySettings($slim: Int! = 50) {\n  attendanceDayPolicy {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n  attendancePunchPolicy {\n    id\n    tenantId\n    isEnforced\n    siteLatitude\n    siteLongitude\n    maxDistanceMeters\n    ipAllowlist\n    updatedAt\n  }\n  shifts(limit: $slim) {\n    id\n    name\n    startTime\n    endTime\n    workHours\n    isNightShift\n  }\n}\n\nquery PreviewAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  previewAttendanceDayPolicy(input: $input) {\n    revision\n    transition {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n    following {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nmutation ScheduleAttendanceDayPolicy($input: ScheduleAttendanceDayPolicyInput!) {\n  scheduleAttendanceDayPolicy(input: $input) {\n    revision\n    initialized\n    legacyActivationPending\n    legacyActivationDate\n    currentPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    pendingPolicy {\n      effectiveWorkDate\n      boundaryMinutes\n      timezone\n    }\n    currentWindow {\n      workDate\n      startsAt\n      endsAt\n      timezone\n      boundaryMinutes\n    }\n  }\n}\n\nquery AttendancePunchDaySummary {\n  punchDaySummary {\n    workDate\n    startsAt\n    endsAt\n    timezone\n    boundaryMinutes\n    totalWorkedMinutes\n    openSegment {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n    segments {\n      id\n      checkInAt\n      checkOutAt\n      checkInTime\n      checkOutTime\n      checkInLat\n      checkInLng\n      checkOutLat\n      checkOutLng\n      source\n      status\n    }\n  }\n}\n\nmutation AttendancePunchToday($input: PunchTodayInput) {\n  punchToday(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    checkInLat\n    checkInLng\n    checkOutLat\n    checkOutLng\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManualSegment($input: AddManualAttendanceSegmentInput!) {\n  addManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceUpdateManualSegment($input: UpdateManualAttendanceSegmentInput!) {\n  updateManualAttendanceSegment(input: $input) {\n    id\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    source\n    status\n  }\n}\n\nmutation AttendanceAddManagedSegment($input: AddManagedAttendanceSegmentInput!) {\n  addManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}\n\nmutation AttendanceUpdateManagedSegment($input: UpdateManagedAttendanceSegmentInput!) {\n  updateManagedAttendanceSegment(input: $input) {\n    id\n    employeeId\n    employeeName\n    employeeCode\n    workDate\n    checkInAt\n    checkOutAt\n    checkInTime\n    checkOutTime\n    status\n    source\n    regularizationStatus\n    createdAt\n    updatedAt\n  }\n}"];
 
 export function attendanceGraphql(source: string) {
   return (documents as any)[source] ?? {};
diff --git a/src/api/attendance/graphql.ts b/src/api/attendance/graphql.ts
index bc22a14..9c576d8 100644
--- a/src/api/attendance/graphql.ts
+++ b/src/api/attendance/graphql.ts
@@ -19,7 +19,7 @@ export type Scalars = {
    *
    * The input/output is a string in RFC3339 format.
    */
-  DateTime: { input: any; output: any; }
+  DateTime: { input: string; output: string; }
   /**
    * ISO 8601 calendar date without timezone.
    * Format: %Y-%m-%d
@@ -29,7 +29,7 @@ export type Scalars = {
    * * `1994-11-13`
    * * `2000-02-24`
    */
-  NaiveDate: { input: any; output: any; }
+  NaiveDate: { input: string; output: string; }
   /**
    * ISO 8601 time without timezone.
    * Allows for the nanosecond precision and optional leap second representation.
@@ -39,11 +39,13 @@ export type Scalars = {
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
@@ -51,11 +53,13 @@ export type AddManagedAttendanceSegmentInput = {
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
@@ -73,8 +77,17 @@ export type PunchTodayInput = {
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
@@ -82,9 +95,11 @@ export type UpdateManagedAttendanceSegmentInput = {
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
@@ -138,7 +153,91 @@ export type MyAttendanceBoardQueryVariables = Exact<{
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
@@ -1,4 +1,9 @@
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
@@ -39,3 +44,238 @@ query MyAttendanceBoard($fromDate: NaiveDate!, $toDate: NaiveDate!, $first: Int
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
index 92aa158..9f9bf72 100644
--- a/src/modules/admin/AdminAttendancePolicyPage.tsx
+++ b/src/modules/admin/AdminAttendancePolicyPage.tsx
@@ -1,16 +1,29 @@
-import { FormEvent, useCallback, useEffect, useState } from 'react';
+import {
+  useCallback,
+  useEffect,
+  useLayoutEffect,
+  useMemo,
+  useRef,
+  useState,
+  type FormEvent,
+} from 'react';
 
 import {
-  ClientOpsAdminAttendancePolicyDocument,
-  ClientOpsUpsertAttendancePunchPolicyDocument,
-} from '../../api/graphql/graphql';
+  AttendancePolicySettingsDocument,
+  type AttendancePolicySettingsQuery,
+} from '../../api/attendance/graphql';
+import { ClientOpsUpsertAttendancePunchPolicyDocument } from '../../api/graphql/graphql';
+import { authorizationStateKey, createPermissionService } from '../../auth/permissionService';
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
@@ -37,8 +50,12 @@ const isValidIpv4CidrToken = (token: string) => {
   return mask >= 0 && mask <= 32;
 };
 
-const AdminAttendancePolicyPage = () => {
+const AuthorizedAttendancePolicyPage = ({ identity }: { identity: string }) => {
   const client = useGraphClient('client');
+  const owner = useMemo(() => ({ client, identity }), [client, identity]);
+  const mounted = useRef(false);
+  const generation = useRef(0);
+  const [loadedOwner, setLoadedOwner] = useState<typeof owner | null>(null);
   const [policy, setPolicy] = useState<{
     id?: string | null;
     isEnforced: boolean;
@@ -48,6 +65,9 @@ const AdminAttendancePolicyPage = () => {
     ipAllowlist?: string | null;
     updatedAt?: string | null;
   } | null>(null);
+  const [dayPolicy, setDayPolicy] = useState<
+    AttendancePolicySettingsQuery['attendanceDayPolicy'] | null
+  >(null);
   const [shifts, setShifts] = useState<
     {
       id: string;
@@ -70,46 +90,67 @@ const AdminAttendancePolicyPage = () => {
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
-  }, [client]);
+    void identity;
+    return client.request<AttendancePolicySettingsQuery>(AttendancePolicySettingsDocument);
+  }, [client, identity]);
+
+  const ownsRequest = useCallback(
+    (request: number) => mounted.current && generation.current === request,
+    []
+  );
+
+  const applySettings = useCallback(
+    (result: AttendancePolicySettingsQuery) => {
+      setPolicy(result.attendancePunchPolicy);
+      setDayPolicy(result.attendanceDayPolicy);
+      setShifts(result.shifts);
+      const punchPolicy = result.attendancePunchPolicy;
+      setIsEnforced(punchPolicy.isEnforced);
+      setSiteLatitude(punchPolicy.siteLatitude != null ? String(punchPolicy.siteLatitude) : '');
+      setSiteLongitude(punchPolicy.siteLongitude != null ? String(punchPolicy.siteLongitude) : '');
+      setMaxDistanceMeters(
+        punchPolicy.maxDistanceMeters != null ? String(punchPolicy.maxDistanceMeters) : ''
+      );
+      setIpAllowlist(punchPolicy.ipAllowlist ?? '');
+      setLoadedOwner(owner);
+    },
+    [owner]
+  );
+
+  useLayoutEffect(() => {
+    mounted.current = true;
+    generation.current += 1;
+    setLoadedOwner(null);
+    setLoading(true);
+    setError(null);
+    setSaving(false);
+    setFormError(null);
+    return () => {
+      mounted.current = false;
+      generation.current += 1;
+    };
+  }, [owner]);
 
   useEffect(() => {
-    let c = false;
+    const request = generation.current;
     void (async () => {
       try {
-        setLoading(true);
-        setError(null);
-        const r = await load();
-        if (c) return;
-        setPolicy(r.attendancePunchPolicy);
-        setShifts(r.shifts);
-        const p = r.attendancePunchPolicy;
-        setIsEnforced(p.isEnforced);
-        setSiteLatitude(p.siteLatitude != null ? String(p.siteLatitude) : '');
-        setSiteLongitude(p.siteLongitude != null ? String(p.siteLongitude) : '');
-        setMaxDistanceMeters(p.maxDistanceMeters != null ? String(p.maxDistanceMeters) : '');
-        setIpAllowlist(p.ipAllowlist ?? '');
+        const result = await load();
+        if (!ownsRequest(request)) return;
+        applySettings(result);
       } catch (e) {
-        if (!c) setError(graphQlUserMessage(e));
+        if (ownsRequest(request)) setError(graphQlUserMessage(e));
       } finally {
-        if (!c) setLoading(false);
+        if (ownsRequest(request)) setLoading(false);
       }
     })();
-    return () => {
-      c = true;
-    };
-  }, [load]);
+  }, [applySettings, load, ownsRequest]);
+
+  const reloadPolicy = useCallback(async () => {
+    const request = generation.current;
+    const result = await load();
+    if (ownsRequest(request)) applySettings(result);
+  }, [applySettings, load, ownsRequest]);
 
   const onSave = async (e: FormEvent) => {
     e.preventDefault();
@@ -140,13 +181,18 @@ const AdminAttendancePolicyPage = () => {
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
+    const request = generation.current;
     setSaving(true);
     try {
       await client.request(ClientOpsUpsertAttendancePunchPolicyDocument, {
@@ -158,15 +204,18 @@ const AdminAttendancePolicyPage = () => {
           ipAllowlist: ipAllowlist.trim() || null,
         },
       });
+      if (!ownsRequest(request)) return;
       const r = await load();
-      if (r.attendancePunchPolicy) setPolicy(r.attendancePunchPolicy);
+      if (ownsRequest(request)) applySettings(r);
     } catch (err) {
-      setFormError(graphQlUserMessage(err));
+      if (ownsRequest(request)) setFormError(graphQlUserMessage(err));
     } finally {
-      setSaving(false);
+      if (ownsRequest(request)) setSaving(false);
     }
   };
 
+  const ownerIsCurrent = loadedOwner === owner;
+
   return (
     <div className="space-y-4">
       <h1 className="sr-only">Attendance punch policy</h1>
@@ -175,8 +224,18 @@ const AdminAttendancePolicyPage = () => {
           <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
         </Card>
       )}
+      {ownerIsCurrent && dayPolicy ? (
+        <AttendanceDayPolicySettings
+          ownerKey={identity}
+          policy={dayPolicy}
+          onPolicyChanged={(nextPolicy) => {
+            if (loadedOwner === owner) setDayPolicy(nextPolicy);
+          }}
+          reloadPolicy={reloadPolicy}
+        />
+      ) : null}
       <Card title="Live Punch Policy">
-        {loading ? (
+        {loading || !ownerIsCurrent ? (
           <p className="text-sm text-gray-500">Loading...</p>
         ) : (
           <form onSubmit={(e) => void onSave(e)} className="space-y-4">
@@ -236,7 +295,7 @@ const AdminAttendancePolicyPage = () => {
         <Card title="Shifts">
           {loading ? (
             <p className="text-sm text-gray-500">Loading...</p>
-          ) : shifts.length ? (
+          ) : ownerIsCurrent && shifts.length ? (
             <ul className="divide-y divide-gray-200 dark:divide-gray-700">
               {shifts.map((s) => (
                 <li key={s.id} className="py-3">
@@ -257,4 +316,18 @@ const AdminAttendancePolicyPage = () => {
   );
 };
 
+const AdminAttendancePolicyPage = () => {
+  const { clientSession, tenantId, user } = useAuth();
+  const permissions = createPermissionService(clientSession);
+  if (!permissions.canRoute('/admin/attendance-policy')) {
+    return (
+      <p role="status" className="text-sm text-content-secondary">
+        You do not have access to manage attendance policy.
+      </p>
+    );
+  }
+  const identity = `${tenantId ?? ''}:${user?.id ?? ''}:${authorizationStateKey(clientSession)}`;
+  return <AuthorizedAttendancePolicyPage key={identity} identity={identity} />;
+};
+
 export default AdminAttendancePolicyPage;
diff --git a/src/modules/attendance/AttendancePage.editorOwnership.test.tsx b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
index 697ec01..57899e1 100644
--- a/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
+++ b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
@@ -1,12 +1,14 @@
 // @vitest-environment jsdom
-import { fireEvent, screen, waitFor } from '@testing-library/react';
+import { act, fireEvent, screen, waitFor } from '@testing-library/react';
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
@@ -23,11 +25,13 @@ it('discards an open attendance edit when the client or employee changes, includ
 
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
@@ -47,3 +51,59 @@ it('discards an open attendance edit when the client or employee changes, includ
   );
   expect(screen.queryByRole('dialog')).toBeNull();
 });
+
+it('uses the server current work date for the initial month and missed-punch default', async () => {
+  vi.setSystemTime(new Date('2026-08-31T20:00:00Z'));
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
+
+it('preserves a selected historical month while the current attendance window refreshes', async () => {
+  authState.clientSession.permissions = new Set(['attendance:punch_self']);
+  let currentWindowRequests = 0;
+  graphClient.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument) {
+      currentWindowRequests += 1;
+      return Promise.resolve({
+        attendanceDayWindow: {
+          ...currentWindowResponse.attendanceDayWindow,
+          workDate: currentWindowRequests === 1 ? '2026-08-25' : '2026-08-26',
+          endsAt: '2026-08-26T23:30:00Z',
+        },
+      });
+    }
+    return Promise.resolve(boardResponse());
+  });
+  renderPage();
+  const month = await screen.findByLabelText<HTMLSelectElement>('Month');
+  fireEvent.change(month, { target: { value: '6' } });
+  await waitFor(() => expect(month.value).toBe('6'));
+
+  await act(async () => {
+    window.dispatchEvent(new Event('focus'));
+    await Promise.resolve();
+  });
+
+  await waitFor(() => expect(currentWindowRequests).toBe(2));
+  expect(month.value).toBe('6');
+});
diff --git a/src/modules/attendance/AttendancePage.ownership.test.tsx b/src/modules/attendance/AttendancePage.ownership.test.tsx
index 2ac64bc..38b191b 100644
--- a/src/modules/attendance/AttendancePage.ownership.test.tsx
+++ b/src/modules/attendance/AttendancePage.ownership.test.tsx
@@ -2,7 +2,10 @@
 import { act, fireEvent, screen, waitFor } from '@testing-library/react';
 import { expect, it, vi } from 'vitest';
 
-import { MyAttendanceBoardDocument } from '../../api/attendance/graphql';
+import {
+  AttendanceCurrentDayWindowDocument,
+  MyAttendanceBoardDocument,
+} from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 
 import {
@@ -10,6 +13,7 @@ import {
   graphClient,
   authState,
   policyResponse,
+  currentWindowResponse,
   deferred,
   boardResponse,
   renderPage,
@@ -22,6 +26,8 @@ it('does not let a deferred refresh overwrite a newer month request', async () =
   let boardCalls = 0;
   graphClient.request.mockImplementation((document: unknown, variables?: { fromDate?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     boardCalls += 1;
     if (boardCalls === 2) return refresh.promise;
     return Promise.resolve(
@@ -87,6 +93,8 @@ it('hides stale paging controls and rows during a deferred month transition', as
   let boardCalls = 0;
   graphClient.request.mockImplementation((document: unknown, variables?: { fromDate?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     boardCalls += 1;
     if (boardCalls === 2) return nextMonth.promise;
     return Promise.resolve(
@@ -160,6 +168,8 @@ it('hides stale board rows and paging during a deferred client/session transitio
   const replacementClient = { request: vi.fn() };
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(
       boardResponse({
         endCursor: 'client-a-next',
@@ -185,6 +195,8 @@ it('hides stale board rows and paging during a deferred client/session transitio
   });
   replacementClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return replacement.promise;
   });
 
@@ -243,6 +255,8 @@ it('resets a page-two cursor before requesting a deferred client/session transit
   const replacementClient = { request: vi.fn() };
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     if (variables?.after === 'client-a-page-two') {
       return Promise.resolve(
         boardResponse({
@@ -292,6 +306,8 @@ it('resets a page-two cursor before requesting a deferred client/session transit
   });
   replacementClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return replacement.promise;
   });
 
diff --git a/src/modules/attendance/AttendancePage.paging.test.tsx b/src/modules/attendance/AttendancePage.paging.test.tsx
index 642faff..1a5d613 100644
--- a/src/modules/attendance/AttendancePage.paging.test.tsx
+++ b/src/modules/attendance/AttendancePage.paging.test.tsx
@@ -2,11 +2,15 @@
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
@@ -77,6 +81,8 @@ it('keeps complete monthly totals unchanged when navigating attendance pages', a
   });
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(variables?.after === 'page-two' ? secondPage : firstPage);
   });
 
@@ -102,6 +108,8 @@ it('keeps complete monthly totals unchanged when navigating attendance pages', a
 it('shows no average for an open-only month while identifying incomplete punches', async () => {
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(
       boardResponse({
         summary: {
@@ -123,6 +131,8 @@ it('shows no average for an open-only month while identifying incomplete punches
 it('uses the local cursor stack when returning to a prior page', async () => {
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     if (variables?.after === 'cursor-one') {
       return Promise.resolve(boardResponse({ endCursor: 'cursor-two', hasNextPage: true }));
     }
diff --git a/src/modules/attendance/AttendancePage.refresh.test.tsx b/src/modules/attendance/AttendancePage.refresh.test.tsx
index 5b6790b..4ecd3e8 100644
--- a/src/modules/attendance/AttendancePage.refresh.test.tsx
+++ b/src/modules/attendance/AttendancePage.refresh.test.tsx
@@ -2,6 +2,7 @@
 import { act, fireEvent, screen, waitFor } from '@testing-library/react';
 import { expect, it } from 'vitest';
 
+import { AttendanceCurrentDayWindowDocument } from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 
 import {
@@ -10,6 +11,7 @@ import {
   policyResponse,
   deferred,
   boardResponse,
+  currentWindowResponse,
   renderPage,
   advanceToNextPage,
 } from './attendancePageTestSupport';
@@ -19,6 +21,8 @@ it('does not show refresh success after refresh A is superseded by B and return
   let boardCalls = 0;
   graphClient.request.mockImplementation((document: unknown, variables?: { fromDate?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     boardCalls += 1;
     if (boardCalls === 2) return pendingRefresh.promise;
     return Promise.resolve(
@@ -65,6 +69,8 @@ it('keeps adjustment controls unavailable until the policy is resolved without r
   authState.clientSession.permissions = new Set(['attendance:punch_self']);
   graphClient.request.mockImplementation((document: unknown, variables?: { after?: string }) => {
     if (document === AttendanceAdjustmentPolicyDocument) return policy.promise;
+    if (document === AttendanceCurrentDayWindowDocument)
+      return Promise.resolve(currentWindowResponse);
     return Promise.resolve(
       boardResponse({
         endCursor: variables?.after ? null : 'page-two',
@@ -78,7 +84,7 @@ it('keeps adjustment controls unavailable until the policy is resolved without r
   expect((addButton as HTMLButtonElement).disabled).toBe(true);
   expect(screen.queryByRole('button', { name: 'Adjust day' })).toBeNull();
   await advanceToNextPage();
-  await waitFor(() => expect(graphClient.request).toHaveBeenCalledTimes(3));
+  await waitFor(() => expect(graphClient.request).toHaveBeenCalledTimes(4));
 
   await act(async () => {
     await Promise.resolve();
diff --git a/src/modules/attendance/attendancePageTestSupport.tsx b/src/modules/attendance/attendancePageTestSupport.tsx
index 895dd02..fb951d8 100644
--- a/src/modules/attendance/attendancePageTestSupport.tsx
+++ b/src/modules/attendance/attendancePageTestSupport.tsx
@@ -4,6 +4,7 @@ import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/re
 import { MemoryRouter } from 'react-router-dom';
 import { afterEach, beforeEach, expect, vi } from 'vitest';
 
+import { AttendanceCurrentDayWindowDocument } from '../../api/attendance/graphql';
 import { AttendanceAdjustmentPolicyDocument } from '../../api/graphql/graphql';
 import type { ParsedClientSession } from '../../auth/clientSession';
 
@@ -35,6 +36,15 @@ vi.mock('../../contexts/AuthContext', () => ({
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
@@ -127,6 +137,9 @@ beforeEach(() => {
   graphClient.request.mockReset();
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument) {
+      return Promise.resolve(currentWindowResponse);
+    }
     return Promise.resolve(boardResponse({ endCursor: 'opaque-next', hasNextPage: true }));
   });
 });
diff --git a/src/modules/attendance/components/AttendancePageFeedback.tsx b/src/modules/attendance/components/AttendancePageFeedback.tsx
index 3af9b50..57161b5 100644
--- a/src/modules/attendance/components/AttendancePageFeedback.tsx
+++ b/src/modules/attendance/components/AttendancePageFeedback.tsx
@@ -1,13 +1,12 @@
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
@@ -17,7 +16,7 @@ export const AttendancePageToolbar = ({ model }: { model: AttendancePageModel })
           type="button"
           disabled={!policyReady}
           title={policyReady ? undefined : 'Loading adjustment policy'}
-          onClick={() => openAdjust(toIsoDate(new Date()))}
+          onClick={() => currentWorkDate && openAdjust(currentWorkDate)}
         >
           {policyReady ? 'Add Missed Punches' : 'Loading adjustment policy…'}
         </Button>
@@ -26,7 +25,15 @@ export const AttendancePageToolbar = ({ model }: { model: AttendancePageModel })
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
@@ -50,6 +57,24 @@ export const AttendancePageNotices = ({ model }: { model: AttendancePageModel })
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
@@ -86,6 +111,8 @@ export const AttendancePageEditor = ({ model }: { model: AttendancePageModel })
           editingSegmentId={adjustDefaultSegment?.id}
           defaultCheckIn={adjustDefaultSegment?.checkInTime}
           defaultCheckOut={adjustDefaultSegment?.checkOutTime}
+          defaultCheckInAt={adjustDefaultSegment?.checkInAt}
+          defaultCheckOutAt={adjustDefaultSegment?.checkOutAt}
           existingSegments={currentBoard?.attendance ?? []}
           existingSegmentsComplete={existingSegmentsComplete}
           existingSegmentsCoverage={{ fromDate: monthBounds.start, toDate: monthBounds.end }}
diff --git a/src/modules/attendance/components/ManualAttendanceModal.test.tsx b/src/modules/attendance/components/ManualAttendanceModal.test.tsx
index eded690..281d22f 100644
--- a/src/modules/attendance/components/ManualAttendanceModal.test.tsx
+++ b/src/modules/attendance/components/ManualAttendanceModal.test.tsx
@@ -3,16 +3,49 @@
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
@@ -43,6 +76,7 @@ describe('ManualAttendanceModal', () => {
     renderModal();
     const punchIn = screen.getByLabelText('Punch In');
     const punchOut = screen.getByLabelText('Punch Out');
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.change(punchIn, { target: { value: '18:00' } });
     fireEvent.change(punchOut, { target: { value: '09:00' } });
@@ -52,20 +86,26 @@ describe('ManualAttendanceModal', () => {
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
@@ -79,8 +119,8 @@ describe('ManualAttendanceModal', () => {
   });
 
   it('closes only after the attendance segment is saved', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal();
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
@@ -88,8 +128,63 @@ describe('ManualAttendanceModal', () => {
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
@@ -103,6 +198,7 @@ describe('ManualAttendanceModal', () => {
         },
       ],
     });
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
@@ -111,7 +207,6 @@ describe('ManualAttendanceModal', () => {
   });
 
   it('defers overlap checks when Add defaults outside a historical loaded range', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal({
       defaultWorkDate: '2026-08-24',
       defaultCheckIn: '10:00:00',
@@ -127,6 +222,7 @@ describe('ManualAttendanceModal', () => {
         },
       ],
     });
+    await screen.findByText(/Attendance window:/);
 
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
@@ -135,7 +231,6 @@ describe('ManualAttendanceModal', () => {
   });
 
   it('defers overlap checks after the user changes the date outside loaded coverage', async () => {
-    request.mockResolvedValueOnce({});
     const { onClose, onSaved } = renderModal({
       defaultWorkDate: '2025-01-15',
       defaultCheckIn: '10:00:00',
@@ -153,6 +248,7 @@ describe('ManualAttendanceModal', () => {
     });
 
     fireEvent.change(screen.getByLabelText('Work Date'), { target: { value: '2026-08-24' } });
+    await screen.findByText(/24 Aug 2026/);
     fireEvent.click(screen.getByRole('button', { name: 'Save Segment' }));
 
     await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
diff --git a/src/modules/attendance/components/ManualAttendanceModal.tsx b/src/modules/attendance/components/ManualAttendanceModal.tsx
index f23577a..fbb40da 100644
--- a/src/modules/attendance/components/ManualAttendanceModal.tsx
+++ b/src/modules/attendance/components/ManualAttendanceModal.tsx
@@ -1,14 +1,15 @@
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
@@ -18,6 +19,7 @@ import {
 } from '../../../utils/attendanceValidation';
 import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
 import { formatBackendTime } from '../../../utils/timeFormat';
+import { useAttendanceCorrectionWindows } from '../hooks/useAttendanceDayWindows';
 
 const DEFAULT_CHECK_IN = '09:00';
 const DEFAULT_CHECK_OUT = '18:00';
@@ -36,6 +38,8 @@ export interface ManualAttendanceModalProps {
   editingSegmentId?: string | null;
   defaultCheckIn?: string | null;
   defaultCheckOut?: string | null;
+  defaultCheckInAt?: string | null;
+  defaultCheckOutAt?: string | null;
   existingSegments: AttendanceSegmentInterval[];
   /** Defaults to true for callers that supply a complete list. */
   existingSegmentsComplete?: boolean;
@@ -53,6 +57,8 @@ const ManualAttendanceModal = ({
   editingSegmentId,
   defaultCheckIn,
   defaultCheckOut,
+  defaultCheckInAt,
+  defaultCheckOutAt,
   existingSegments,
   existingSegmentsComplete = true,
   existingSegmentsCoverage,
@@ -64,13 +70,19 @@ const ManualAttendanceModal = ({
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
@@ -79,15 +91,31 @@ const ManualAttendanceModal = ({
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
@@ -99,10 +127,22 @@ const ManualAttendanceModal = ({
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
@@ -124,16 +164,18 @@ const ManualAttendanceModal = ({
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
@@ -189,13 +231,59 @@ const ManualAttendanceModal = ({
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
@@ -209,6 +297,20 @@ const ManualAttendanceModal = ({
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
diff --git a/src/modules/attendance/hooks/useAttendanceEditor.ts b/src/modules/attendance/hooks/useAttendanceEditor.ts
index 4c588e5..c91ae21 100644
--- a/src/modules/attendance/hooks/useAttendanceEditor.ts
+++ b/src/modules/attendance/hooks/useAttendanceEditor.ts
@@ -1,17 +1,20 @@
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
@@ -35,13 +38,16 @@ export function useAttendanceEditor(adjustPolicyDays: number, client: object, id
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
diff --git a/src/modules/attendance/hooks/useAttendancePageModel.ts b/src/modules/attendance/hooks/useAttendancePageModel.ts
index ff2f525..703a880 100644
--- a/src/modules/attendance/hooks/useAttendancePageModel.ts
+++ b/src/modules/attendance/hooks/useAttendancePageModel.ts
@@ -1,4 +1,4 @@
-import { useMemo } from 'react';
+import { useEffect, useMemo, useRef } from 'react';
 
 import { authorizationStateKey, createPermissionService } from '../../../auth/permissionService';
 import { useAuth } from '../../../contexts/AuthContext';
@@ -9,6 +9,7 @@ import { monthBoundsIso } from '../../../utils/calendarRange';
 import { attendanceSegmentRows } from './attendanceSegmentRows';
 import { useAttendanceAdjustmentPolicy } from './useAttendanceAdjustmentPolicy';
 import { useAttendanceCursor } from './useAttendanceCursor';
+import { useCurrentAttendanceDayWindow } from './useAttendanceDayWindows';
 import { useAttendanceEditor } from './useAttendanceEditor';
 import { useAttendancePeriod } from './useAttendancePeriod';
 import { usePersonalAttendanceBoard } from './usePersonalAttendanceBoard';
@@ -20,10 +21,35 @@ export function useAttendancePageModel() {
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
@@ -50,13 +76,11 @@ export function useAttendancePageModel() {
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
@@ -92,6 +116,9 @@ export function useAttendancePageModel() {
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
@@ -20,7 +20,10 @@ const AttendanceSegments = ({ segments, startIndex = 0 }: AttendanceSegmentsProp
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
@@ -33,6 +36,11 @@ const AttendanceSegments = ({ segments, startIndex = 0 }: AttendanceSegmentsProp
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
diff --git a/src/modules/dashboard/components/PunchInOut.test.tsx b/src/modules/dashboard/components/PunchInOut.test.tsx
index 41cb213..6352ee4 100644
--- a/src/modules/dashboard/components/PunchInOut.test.tsx
+++ b/src/modules/dashboard/components/PunchInOut.test.tsx
@@ -1,16 +1,22 @@
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
@@ -19,6 +25,8 @@ vi.mock('../../../hooks/useGraphClient', () => ({
 
 vi.mock('../../../contexts/AuthContext', () => ({
   useAuth: () => ({
+    tenantId: graphState.tenantId,
+    user: { id: graphState.userId },
     clientSession: {
       employeeId: 'employee-1',
       permissions: graphState.permissions,
@@ -57,6 +65,10 @@ const segment = (index: number) => ({
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
@@ -75,10 +87,13 @@ function renderCard() {
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
@@ -105,7 +120,7 @@ describe('PunchInOut truthful states', () => {
 
     expect(await screen.findByText('Session 1')).toBeTruthy();
     expect(screen.queryByRole('button', { name: 'Punch In' })).toBeNull();
-    expect(graphState.client.request).toHaveBeenCalledWith(PunchDaySummaryDocument);
+    expect(graphState.client.request).toHaveBeenCalledWith(AttendancePunchDaySummaryDocument);
   });
 
   it('renders an actionable summary failure and disables punching until summary data is ready', async () => {
@@ -130,6 +145,159 @@ describe('PunchInOut truthful states', () => {
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
+
+  it('clears an owned busy mutation when only the GraphQL client is replaced', async () => {
+    const staleMutation = deferred<{ punchToday: ReturnType<typeof segment> }>();
+    const oldClient = graphState.client;
+    oldClient.request.mockImplementation((document) => {
+      if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary());
+      if (document === AttendancePunchTodayDocument) return staleMutation.promise;
+      throw new Error('Unexpected document');
+    });
+    const user = userEvent.setup();
+    const view = renderCard();
+    await screen.findByText('Session 1');
+    await user.click(screen.getByRole('checkbox', { name: /Record GPS location/i }));
+    await user.click(screen.getByRole('button', { name: 'Punch In' }));
+    expect(screen.getByRole<HTMLButtonElement>('button', { name: /Recording/i }).disabled).toBe(
+      true
+    );
+
+    const replacementPunch = { ...segment(4), source: 'replacement-client' };
+    const replacementClient = {
+      request: vi.fn((document) => {
+        if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary(0));
+        if (document === AttendancePunchTodayDocument) {
+          return Promise.resolve({ punchToday: replacementPunch });
+        }
+        throw new Error('Unexpected document');
+      }),
+    };
+    graphState.client = replacementClient;
+    view.rerender(<PunchInOut />);
+
+    const replacementButton = await screen.findByRole<HTMLButtonElement>('button', {
+      name: 'Punch In',
+    });
+    expect(replacementButton.disabled).toBe(false);
+    await user.click(replacementButton);
+    expect(await screen.findByText('Source: replacement-client')).toBeTruthy();
+
+    await act(async () => {
+      staleMutation.resolve({ punchToday: { ...segment(5), source: 'stale-client' } });
+      await staleMutation.promise;
+    });
+
+    expect(screen.queryByText('Source: stale-client')).toBeNull();
+    expect(screen.getByText('Source: replacement-client')).toBeTruthy();
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
@@ -173,13 +341,14 @@ describe('PunchInOut truthful states', () => {
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
@@ -204,8 +373,9 @@ describe('PunchInOut truthful states', () => {
 
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
@@ -225,8 +395,8 @@ describe('PunchInOut submission and display safeguards', () => {
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
diff --git a/src/modules/dashboard/components/PunchInOut.tsx b/src/modules/dashboard/components/PunchInOut.tsx
index 65c8424..1cb9448 100644
--- a/src/modules/dashboard/components/PunchInOut.tsx
+++ b/src/modules/dashboard/components/PunchInOut.tsx
@@ -1,6 +1,6 @@
-import { useCallback, useEffect, useRef, useState } from 'react';
+import { useEffect, useLayoutEffect, useRef, useState, type MutableRefObject } from 'react';
 
-import { PunchDaySummaryDocument, PunchTodayDocument } from '../../../api/graphql/graphql';
+import { AttendancePunchTodayDocument } from '../../../api/attendance/graphql';
 import { authorizationStateKey, createPermissionService } from '../../../auth/permissionService';
 import Badge from '../../../components/common/Badge';
 import Button from '../../../components/common/Button';
@@ -10,22 +10,19 @@ import PageNotice from '../../../components/common/PageNotice';
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
@@ -41,13 +38,17 @@ function getCurrentPosition(): Promise<GeolocationPosition> {
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
@@ -78,10 +79,27 @@ const useDashboardCardClock = () => {
 
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
@@ -90,34 +108,65 @@ const usePunchMutation = ({
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
+    submittingRef.current = false;
+    setSubmitting(false);
+    setMutationError(null);
+    setLastPunch(null);
+    return () => {
+      mountedRef.current = false;
+      generationRef.current += 1;
+      submittingRef.current = false;
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
 
@@ -265,43 +314,40 @@ const PunchActionArea = ({
 
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
@@ -309,10 +355,20 @@ const AuthorizedPunchInOut = ({ canPunch }: AuthorizedPunchInOutProps) => {
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
@@ -355,14 +411,15 @@ const AuthorizedPunchInOut = ({ canPunch }: AuthorizedPunchInOutProps) => {
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
diff --git a/src/modules/dashboard/components/attendanceSummaryTypes.ts b/src/modules/dashboard/components/attendanceSummaryTypes.ts
index 473627b..3940ab6 100644
--- a/src/modules/dashboard/components/attendanceSummaryTypes.ts
+++ b/src/modules/dashboard/components/attendanceSummaryTypes.ts
@@ -14,6 +14,10 @@ export type AttendanceRow = {
 
 export type Summary = {
   workDate: string;
+  startsAt: string;
+  endsAt: string;
+  timezone: string;
+  boundaryMinutes: number;
   totalWorkedMinutes: number;
   openSegment: AttendanceRow | null;
   segments: AttendanceRow[];
diff --git a/src/modules/hr/HrAttendanceManagementPage.context.test.tsx b/src/modules/hr/HrAttendanceManagementPage.context.test.tsx
index 38a44c8..d9490c4 100644
--- a/src/modules/hr/HrAttendanceManagementPage.context.test.tsx
+++ b/src/modules/hr/HrAttendanceManagementPage.context.test.tsx
@@ -6,10 +6,11 @@ import { Link, MemoryRouter, Route, Routes, useLocation, useNavigate } from 'rea
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
 
@@ -64,6 +65,8 @@ const ashaRow = {
   employeeName: 'Asha Rao',
   employeeCode: 'EMP-0042',
   workDate: '2026-08-24',
+  checkInAt: '2026-08-24T03:30:00Z',
+  checkOutAt: '2026-08-24T12:00:00Z',
   checkInTime: '09:00:00',
   checkOutTime: '17:30:00',
   status: 'PRESENT',
@@ -93,6 +96,23 @@ const settle = async () => {
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
@@ -100,7 +120,11 @@ beforeEach(() => {
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
@@ -113,6 +137,8 @@ describe('HR attendance context', () => {
     render(<HrAttendanceManagementPage />);
     await settle();
     fireEvent.click(screen.getAllByRole('button', { name: 'Add segment for Asha Rao' })[0]);
+    await settle();
+    expect(screen.getByText(/Attendance window:/)).toBeTruthy();
     expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-08-24');
     fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '18:00' } });
     fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '19:00' } });
@@ -121,10 +147,12 @@ describe('HR attendance context', () => {
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
@@ -132,7 +160,7 @@ describe('HR attendance context', () => {
     });
     expect(
       graphState.client.request.mock.calls.some(
-        ([document]) => document === UpdateManagedAttendanceSegmentDocument
+        ([document]) => document === AttendanceUpdateManagedSegmentDocument
       )
     ).toBe(false);
     expect(screen.queryByRole('dialog')).toBeNull();
diff --git a/src/modules/hr/HrAttendanceManagementPage.test.tsx b/src/modules/hr/HrAttendanceManagementPage.test.tsx
index 7bb424a..af1fe91 100644
--- a/src/modules/hr/HrAttendanceManagementPage.test.tsx
+++ b/src/modules/hr/HrAttendanceManagementPage.test.tsx
@@ -6,9 +6,10 @@ import { MemoryRouter } from 'react-router-dom';
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
 
@@ -34,6 +35,8 @@ const ashaRow = {
   employeeName: 'Asha Rao',
   employeeCode: 'EMP-0042',
   workDate: '2026-08-24',
+  checkInAt: '2026-08-24T03:30:00Z',
+  checkOutAt: '2026-08-24T12:00:00Z',
   checkInTime: '09:00:00',
   checkOutTime: '17:30:00',
   status: 'PRESENT',
@@ -73,6 +76,23 @@ const settle = async () => {
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
@@ -260,7 +280,10 @@ it('returns to the prior page and refreshes the current opaque page', async () =
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
@@ -283,6 +306,8 @@ it('resets to page one, refetches, and identifies the employee after a successfu
   fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
   await settle();
   fireEvent.click(screen.getAllByRole('button', { name: 'Adjust Bina Shah on 2026-08-24' })[0]);
+  await settle();
+  expect(screen.getByText(/Attendance window:/)).toBeTruthy();
   fireEvent.change(screen.getByLabelText('Reason'), {
     target: { value: 'Approved biometric correction' },
   });
@@ -290,7 +315,7 @@ it('resets to page one, refetches, and identifies the employee after a successfu
   await settle();
 
   expect(graphState.client.request).toHaveBeenCalledWith(
-    UpdateManagedAttendanceSegmentDocument,
+    AttendanceUpdateManagedSegmentDocument,
     expect.anything()
   );
   expect(graphState.client.request).toHaveBeenLastCalledWith(ManagedAttendancePageDocument, {
@@ -373,7 +398,7 @@ it('fails closed across a client replacement and ignores the old page request',
     await Promise.resolve();
   });
   expect(screen.getAllByText('Replacement Client Row')[0]).toBeTruthy();
-  expect(oldClient.request).toHaveBeenCalledTimes(4);
+  expect(oldClient.request).toHaveBeenCalledTimes(5);
 });
 
 it('does not publish a late query completion from a replaced client', async () => {
diff --git a/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx b/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
index cb5d6c0..0f35414 100644
--- a/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
+++ b/src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
@@ -4,9 +4,10 @@ import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-libra
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
@@ -29,6 +30,8 @@ const row: ManagedAttendanceRow = {
   workDate: '2026-08-24',
   checkInTime: '09:00:00',
   checkOutTime: '17:30:00',
+  checkInAt: '2026-08-24T03:30:00Z',
+  checkOutAt: '2026-08-24T12:00:00Z',
   status: 'PRESENT',
   source: 'BIOMETRIC',
   regularizationStatus: 'REGULARIZED',
@@ -40,6 +43,7 @@ const baseProps = {
   isOpen: true,
   onClose: vi.fn(),
   employee,
+  initialWorkDate: '2026-08-24',
   existingSegments: [row],
   existingSegmentsComplete: false,
   existingSegmentsCoverage: { fromDate: '2026-08-01', toDate: '2026-08-31' },
@@ -56,7 +60,8 @@ const deferred = <T,>() => {
   };
 };
 
-function fillValidForm(reason = 'Correct biometric outage') {
+async function fillValidForm(reason = 'Correct biometric outage') {
+  await screen.findByText(/Attendance window:/);
   fireEvent.change(screen.getByLabelText('Work Date'), { target: { value: '2026-08-24' } });
   fireEvent.change(screen.getByLabelText('Punch In'), { target: { value: '09:00' } });
   fireEvent.change(screen.getByLabelText('Punch Out'), { target: { value: '17:30' } });
@@ -65,7 +70,27 @@ function fillValidForm(reason = 'Correct biometric outage') {
 
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
@@ -77,14 +102,16 @@ it('adds for an immutable employee using the generated managed mutation and trim
 
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
@@ -97,25 +124,66 @@ it('adds for an immutable employee using the generated managed mutation and trim
 
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
 
@@ -124,13 +192,17 @@ it.each([
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
@@ -138,35 +210,49 @@ it.each([
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
@@ -174,13 +260,37 @@ it('blocks a known overlap when the loaded attendance page is complete', async (
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
@@ -200,11 +310,37 @@ it('keeps every entered value and the modal open after a save error', async () =
 
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
diff --git a/src/modules/hr/attendance/AttendanceRegularizationModal.tsx b/src/modules/hr/attendance/AttendanceRegularizationModal.tsx
index 1b893b2..603a238 100644
--- a/src/modules/hr/attendance/AttendanceRegularizationModal.tsx
+++ b/src/modules/hr/attendance/AttendanceRegularizationModal.tsx
@@ -3,6 +3,7 @@ import Input from '../../../components/common/Input';
 import Modal from '../../../components/common/Modal';
 import PageNotice from '../../../components/common/PageNotice';
 import Textarea from '../../../components/common/Textarea';
+import { formatAttendanceWindow } from '../../../utils/attendanceDay';
 
 import {
   useAttendanceRegularization,
@@ -11,19 +12,144 @@ import {
 
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
@@ -32,7 +158,7 @@ const AttendanceRegularizationModal = (props: AttendanceRegularizationModalProps
     formError,
     isEditing,
     submit,
-  } = useAttendanceRegularization(props);
+  } = state;
 
   const submitLabel = isEditing ? 'Update segment' : 'Save segment';
   return (
@@ -56,47 +182,7 @@ const AttendanceRegularizationModal = (props: AttendanceRegularizationModalProps
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
diff --git a/src/modules/hr/attendance/useAttendanceRegularization.ts b/src/modules/hr/attendance/useAttendanceRegularization.ts
index 77e6423..0f6f161 100644
--- a/src/modules/hr/attendance/useAttendanceRegularization.ts
+++ b/src/modules/hr/attendance/useAttendanceRegularization.ts
@@ -1,10 +1,18 @@
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
@@ -13,6 +21,7 @@ import {
 } from '../../../utils/attendanceValidation';
 import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
 import { formatBackendTime } from '../../../utils/timeFormat';
+import { useAttendanceCorrectionWindows } from '../../attendance/hooks/useAttendanceDayWindows';
 
 import type { ManagedAttendanceEmployee, ManagedAttendanceRow } from './managedAttendanceTypes';
 
@@ -35,14 +44,6 @@ export interface AttendanceRegularizationModalProps {
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
@@ -50,6 +51,10 @@ function reasonError(value: string): string | null {
   return null;
 }
 
+function optionalScalarString(value: unknown): string | null {
+  return typeof value === 'string' ? value : null;
+}
+
 const useAttendanceFields = ({
   isOpen,
   editingRow,
@@ -59,10 +64,15 @@ const useAttendanceFields = ({
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
@@ -70,6 +80,7 @@ const useAttendanceFields = ({
   const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
   const [formError, setFormError] = useState<string | null>(null);
   const isEditing = editingRow !== null && editingRow !== undefined;
+  const windows = useAttendanceCorrectionWindows(client, isOpen, workDate);
 
   useEffect(() => {
     mountedRef.current = true;
@@ -87,7 +98,11 @@ const useAttendanceFields = ({
 
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
@@ -96,16 +111,36 @@ const useAttendanceFields = ({
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
@@ -119,9 +154,58 @@ const useAttendanceFields = ({
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
@@ -139,20 +223,31 @@ export const useAttendanceRegularization = ({
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
 
@@ -161,10 +256,19 @@ export const useAttendanceRegularization = ({
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
@@ -189,29 +293,18 @@ export const useAttendanceRegularization = ({
 
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
diff --git a/src/utils/attendanceValidation.test.ts b/src/utils/attendanceValidation.test.ts
index 37fa22e..9be7323 100644
--- a/src/utils/attendanceValidation.test.ts
+++ b/src/utils/attendanceValidation.test.ts
@@ -4,8 +4,18 @@ import { validateManualAttendanceSegment } from './attendanceValidation';
 
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
 
@@ -40,7 +50,7 @@ describe('validateManualAttendanceSegment', () => {
       validateManualAttendanceSegment({ ...validInput, checkIn: '18:00', checkOut: '09:00' })
     ).toEqual({
       field: 'checkOut',
-      message: 'Punch In must be before Punch Out for the same calendar day.',
+      message: 'Punch In must be before Punch Out.',
     });
   });
 
@@ -119,6 +129,40 @@ describe('validateManualAttendanceSegment', () => {
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
@@ -173,7 +217,7 @@ describe('validateManualAttendanceSegment', () => {
       validateManualAttendanceSegment({ ...partialInput, checkIn: '18:00', checkOut: '09:00' })
     ).toEqual({
       field: 'checkOut',
-      message: 'Punch In must be before Punch Out for the same calendar day.',
+      message: 'Punch In must be before Punch Out.',
     });
   });
 
@@ -182,6 +226,16 @@ describe('validateManualAttendanceSegment', () => {
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
@@ -197,4 +251,58 @@ describe('validateManualAttendanceSegment', () => {
       })
     ).toBeNull();
   });
+
+  it('rejects an intrinsically 24-hour interval when segment coverage is incomplete', () => {
+    expect(
+      validateManualAttendanceSegment({
+        ...validInput,
+        checkInDate: '2025-01-15',
+        checkOutDate: '2025-01-16',
+        checkIn: '00:00',
+        checkOut: '00:00',
+        window: {
+          workDate: '2025-01-15',
+          startsAt: '2025-01-14T23:30:00Z',
+          endsAt: '2025-01-16T00:30:00Z',
+          timezone: 'UTC',
+          boundaryMinutes: 0,
+        },
+        existingSegmentsComplete: false,
+      })
+    ).toEqual({
+      field: 'form',
+      message: 'Total attendance for a day must be less than 24 hours.',
+    });
+  });
+
+  it('enforces the intrinsic cap outside loaded coverage while accepting an exact-end interval below it', () => {
+    const transitionInput = {
+      ...validInput,
+      checkInDate: '2025-01-15',
+      checkOutDate: '2025-01-16',
+      checkIn: '00:00',
+      checkOut: '00:00',
+      window: {
+        workDate: '2025-01-15',
+        startsAt: '2025-01-14T23:30:00Z',
+        endsAt: '2025-01-16T00:30:00Z',
+        timezone: 'UTC',
+        boundaryMinutes: 0,
+      },
+      existingSegmentsComplete: true,
+      existingSegmentsCoverage: { fromDate: '2025-02-01', toDate: '2025-02-28' },
+    };
+
+    expect(validateManualAttendanceSegment(transitionInput)).toEqual({
+      field: 'form',
+      message: 'Total attendance for a day must be less than 24 hours.',
+    });
+    expect(
+      validateManualAttendanceSegment({
+        ...transitionInput,
+        checkIn: '00:31',
+        checkOut: '00:30',
+      })
+    ).toBeNull();
+  });
 });
diff --git a/src/utils/attendanceValidation.ts b/src/utils/attendanceValidation.ts
index d06f77f..891fc74 100644
--- a/src/utils/attendanceValidation.ts
+++ b/src/utils/attendanceValidation.ts
@@ -1,5 +1,6 @@
+import type { AttendanceDayWindowMetadata } from './attendanceDay';
+import { tenantLocalDateTimeToInstant } from './attendanceDay';
 import { naiveTimeToMinutes } from './attendanceDuration';
-import { toIsoDate } from './calendarRange';
 
 export const MAX_ATTENDANCE_MINUTES_PER_DAY = 24 * 60;
 
@@ -8,6 +9,8 @@ export interface AttendanceSegmentInterval {
   workDate: string;
   checkInTime?: string | null;
   checkOutTime?: string | null;
+  checkInAt?: string | null;
+  checkOutAt?: string | null;
   source?: string | null;
 }
 
@@ -18,8 +21,12 @@ export interface ExistingSegmentsCoverage {
 
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
@@ -28,7 +35,13 @@ export interface ManualAttendanceValidationInput {
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
@@ -48,81 +61,206 @@ function intervalsOverlap(
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
+const durationCapError = (): ManualAttendanceValidationError => ({
+  field: 'form',
+  message: 'Total attendance for a day must be less than 24 hours.',
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
 
-  if (existingMinutes + newMinutes >= MAX_ATTENDANCE_MINUTES_PER_DAY) {
-    return { field: 'form', message: 'Total attendance for a day must be less than 24 hours.' };
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
   }
+  const comparableDates =
+    input.checkInDate === input.workDate && input.checkOutDate === input.workDate;
+  const overlaps =
+    valid &&
+    comparableDates &&
+    intervalsOverlap(requested.wallStart, requested.wallEnd, start, end);
+  return { error: overlaps ? overlapError() : null, minutes };
+}
 
-  return null;
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
+  }
+  const requestedMinutes = (requested.end - requested.start) / 60_000;
+  return existingMinutes + requestedMinutes < MAX_ATTENDANCE_MINUTES_PER_DAY
+    ? null
+    : durationCapError();
+}
+
+export function validateManualAttendanceSegment(
+  input: ManualAttendanceValidationInput
+): ManualAttendanceValidationError | null {
+  const requiredError = requiredInputError(input);
+  if (requiredError) return requiredError;
+  const { error, interval } = requestedInterval(input);
+  if (error || !interval) return error;
+  const requestedMinutes = (interval.end - interval.start) / 60_000;
+  if (requestedMinutes >= MAX_ATTENDANCE_MINUTES_PER_DAY) return durationCapError();
+  const isWithinLoadedCoverage =
+    input.existingSegmentsCoverage === undefined ||
+    (input.workDate >= input.existingSegmentsCoverage.fromDate &&
+      input.workDate <= input.existingSegmentsCoverage.toDate);
+  if (input.existingSegmentsComplete === false || !isWithinLoadedCoverage) return null;
+  return validateExistingSegments(input, interval);
 }

diff --git a/src/modules/admin/AdminAttendancePolicyPage.test.tsx b/src/modules/admin/AdminAttendancePolicyPage.test.tsx
new file mode 100644
index 0000000..0eff242
--- /dev/null
+++ b/src/modules/admin/AdminAttendancePolicyPage.test.tsx
@@ -0,0 +1,363 @@
+// @vitest-environment jsdom
+
+import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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
+  tenantId: 'tenant-1',
+  userId: 'admin-user-1',
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
+  useAuth: () => ({
+    clientSession: state.session,
+    tenantId: state.tenantId,
+    user: { id: state.userId },
+  }),
+}));
+
+const deferred = <T,>() => {
+  let resolve!: (value: T | PromiseLike<T>) => void;
+  let reject!: (reason?: unknown) => void;
+  const promise = new Promise<T>((res, rej) => {
+    resolve = res;
+    reject = rej;
+  });
+  return { promise, reject, resolve };
+};
+
+const policy = (revision = 7, ipAllowlist: string | null = null) => ({
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
+    ipAllowlist,
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
+  state.tenantId = 'tenant-1';
+  state.userId = 'admin-user-1';
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
+
+describe('attendance day proposal ownership', () => {
+  it('discards a delayed preview when the administrator edits the proposal', async () => {
+    const firstPreview = deferred<typeof preview>();
+    let previewCount = 0;
+    state.client.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy());
+      if (document === PreviewAttendanceDayPolicyDocument) {
+        previewCount += 1;
+        return previewCount === 1 ? firstPreview.promise : Promise.resolve(preview);
+      }
+      if (document === ScheduleAttendanceDayPolicyDocument) {
+        return Promise.resolve({ scheduleAttendanceDayPolicy: policy(8).attendanceDayPolicy });
+      }
+      throw new Error('Unexpected operation');
+    });
+    render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '07:00' },
+    });
+
+    await act(async () => {
+      firstPreview.resolve(preview);
+      await firstPreview.promise;
+    });
+
+    expect(screen.queryByRole('button', { name: 'Schedule change' })).toBeNull();
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    await screen.findByRole('button', { name: 'Schedule change' });
+    fireEvent.click(screen.getByRole('checkbox', { name: /confirm this exact transition/i }));
+    fireEvent.click(screen.getByRole('button', { name: 'Schedule change' }));
+    await waitFor(() =>
+      expect(state.client.request).toHaveBeenCalledWith(ScheduleAttendanceDayPolicyDocument, {
+        input: {
+          boundaryTime: '07:00',
+          effectiveWorkDate: '2026-09-20',
+          expectedRevision: 7,
+        },
+      })
+    );
+  });
+
+  it('discards policy and preview responses owned by a replaced tenant, user, and client', async () => {
+    const stalePreview = deferred<typeof preview>();
+    const oldClient = state.client;
+    oldClient.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy(7));
+      if (document === PreviewAttendanceDayPolicyDocument) return stalePreview.promise;
+      throw new Error('Unexpected operation');
+    });
+    const view = render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+
+    const replacementPolicy = policy(7, '10.0.0.1');
+    replacementPolicy.attendanceDayPolicy.currentPolicy.boundaryMinutes = 420;
+    replacementPolicy.attendancePunchPolicy.id = 'policy-tenant-2';
+    state.tenantId = 'tenant-2';
+    state.userId = 'admin-user-2';
+    state.client = { request: vi.fn().mockResolvedValue(replacementPolicy) };
+    view.rerender(<AdminAttendancePolicyPage />);
+
+    expect(await screen.findByText('Current start: 07:00')).toBeTruthy();
+    expect(document.querySelector<HTMLTextAreaElement>('textarea')?.value).toBe('10.0.0.1');
+    await act(async () => {
+      stalePreview.resolve(preview);
+      await stalePreview.promise;
+    });
+
+    expect(screen.queryByRole('button', { name: 'Schedule change' })).toBeNull();
+    expect(screen.getByText('Current start: 07:00')).toBeTruthy();
+    expect(state.client.request).not.toHaveBeenCalledWith(
+      ScheduleAttendanceDayPolicyDocument,
+      expect.anything()
+    );
+  });
+});
+
+describe('attendance policy context ownership', () => {
+  it('does not publish a delayed live-punch policy load after context replacement', async () => {
+    const staleLoad = deferred<ReturnType<typeof policy>>();
+    const oldClient = state.client;
+    oldClient.request.mockReturnValue(staleLoad.promise);
+    const view = render(<AdminAttendancePolicyPage />);
+    await waitFor(() =>
+      expect(oldClient.request).toHaveBeenCalledWith(AttendancePolicySettingsDocument)
+    );
+
+    const replacementPolicy = policy(7, '10.0.0.2');
+    replacementPolicy.attendanceDayPolicy.currentPolicy.boundaryMinutes = 420;
+    state.tenantId = 'tenant-2';
+    state.userId = 'admin-user-2';
+    state.client = { request: vi.fn().mockResolvedValue(replacementPolicy) };
+    view.rerender(<AdminAttendancePolicyPage />);
+    expect(await screen.findByText('Current start: 07:00')).toBeTruthy();
+
+    const stalePolicy = policy(7, '192.0.2.1');
+    await act(async () => {
+      staleLoad.resolve(stalePolicy);
+      await staleLoad.promise;
+    });
+
+    expect(screen.getByText('Current start: 07:00')).toBeTruthy();
+    expect(document.querySelector<HTMLTextAreaElement>('textarea')?.value).toBe('10.0.0.2');
+  });
+
+  it('does not reload or publish a delayed schedule conflict after context replacement', async () => {
+    const staleSchedule = deferred<never>();
+    const oldClient = state.client;
+    oldClient.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy(7));
+      if (document === PreviewAttendanceDayPolicyDocument) return Promise.resolve(preview);
+      if (document === ScheduleAttendanceDayPolicyDocument) return staleSchedule.promise;
+      throw new Error('Unexpected operation');
+    });
+    const view = render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    await screen.findByRole('button', { name: 'Schedule change' });
+    fireEvent.click(screen.getByRole('checkbox', { name: /confirm this exact transition/i }));
+    fireEvent.click(screen.getByRole('button', { name: 'Schedule change' }));
+
+    const replacementPolicy = policy(7);
+    replacementPolicy.attendanceDayPolicy.currentPolicy.boundaryMinutes = 420;
+    state.tenantId = 'tenant-2';
+    state.userId = 'admin-user-2';
+    state.client = { request: vi.fn().mockResolvedValue(replacementPolicy) };
+    view.rerender(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 07:00');
+
+    await act(async () => {
+      staleSchedule.reject({ code: 'CONFLICT' });
+      try {
+        await staleSchedule.promise;
+      } catch {
+        // The rejected request is intentionally stale.
+      }
+    });
+
+    expect(screen.queryByText(/changed while you were reviewing/i)).toBeNull();
+    expect(screen.getByText('Current start: 07:00')).toBeTruthy();
+    expect(
+      oldClient.request.mock.calls.filter(
+        ([document]) => document === AttendancePolicySettingsDocument
+      )
+    ).toHaveLength(1);
+  });
+});

diff --git a/src/modules/admin/AttendanceDayPolicySettings.tsx b/src/modules/admin/AttendanceDayPolicySettings.tsx
new file mode 100644
index 0000000..5c999fd
--- /dev/null
+++ b/src/modules/admin/AttendanceDayPolicySettings.tsx
@@ -0,0 +1,162 @@
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
+              disabled={busy === 'schedule'}
+              fullWidth
+              required
+            />
+            <Input
+              type="date"
+              label="Effective work date"
+              value={effectiveDate}
+              onChange={(event) => changeDraft(() => setEffectiveDate(event.target.value))}
+              disabled={busy === 'schedule'}
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
+                disabled={busy !== null}
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

diff --git a/src/modules/admin/useAttendanceDayPolicyDraft.ts b/src/modules/admin/useAttendanceDayPolicyDraft.ts
new file mode 100644
index 0000000..d341d4b
--- /dev/null
+++ b/src/modules/admin/useAttendanceDayPolicyDraft.ts
@@ -0,0 +1,208 @@
+import { ClientError } from 'graphql-request';
+import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';
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
+  ownerKey: string;
+  policy: AttendanceDayPolicy;
+  onPolicyChanged: (policy: AttendanceDayPolicy) => void;
+  reloadPolicy: () => Promise<void>;
+}
+
+interface PolicyProposalInput {
+  boundaryTime: string;
+  effectiveWorkDate: string;
+  expectedRevision: number;
+}
+
+interface PolicyProposal {
+  input: PolicyProposalInput;
+  preview: Preview;
+}
+
+function useRequestOwnership(client: object, ownerKey: string) {
+  const mounted = useRef(false);
+  const ownerGeneration = useRef(0);
+  const previewGeneration = useRef(0);
+  const scheduleGeneration = useRef(0);
+  useLayoutEffect(() => {
+    mounted.current = true;
+    ownerGeneration.current += 1;
+    previewGeneration.current += 1;
+    scheduleGeneration.current += 1;
+    return () => {
+      mounted.current = false;
+      ownerGeneration.current += 1;
+      previewGeneration.current += 1;
+      scheduleGeneration.current += 1;
+    };
+  }, [client, ownerKey]);
+  return {
+    ownerGeneration,
+    ownsRequest: (generation: number) => mounted.current && ownerGeneration.current === generation,
+    previewGeneration,
+    scheduleGeneration,
+  };
+}
+
+const conflictMessage = async (reloadPolicy: () => Promise<void>) => {
+  try {
+    await reloadPolicy();
+    return 'The attendance day policy changed while you were reviewing it. The latest policy was reloaded; preview your retained draft again.';
+  } catch {
+    return 'The attendance day policy changed while you were reviewing it. Your draft was retained, but the latest policy could not be reloaded. Reload the page before previewing again.';
+  }
+};
+
+function proposalIsConfirmed(
+  proposal: PolicyProposal | null,
+  confirmed: boolean,
+  busy: 'preview' | 'schedule' | null
+): proposal is PolicyProposal {
+  return proposal !== null && confirmed && busy === null;
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
+  ownerKey,
+  policy,
+  onPolicyChanged,
+  reloadPolicy,
+}: AttendanceDayPolicyDraftOptions) {
+  const client = useGraphClient('client');
+  const [boundary, setBoundary] = useState('');
+  const [effectiveDate, setEffectiveDate] = useState('');
+  const [proposal, setProposal] = useState<PolicyProposal | null>(null);
+  const [confirmed, setConfirmed] = useState(false);
+  const [busy, setBusy] = useState<'preview' | 'schedule' | null>(null);
+  const [error, setError] = useState<string | null>(null);
+  const [success, setSuccess] = useState<string | null>(null);
+  const policyRef = useRef(policy);
+  policyRef.current = policy;
+  const { ownerGeneration, ownsRequest, previewGeneration, scheduleGeneration } =
+    useRequestOwnership(client, ownerKey);
+
+  useLayoutEffect(() => {
+    const currentPolicy = policyRef.current;
+    const draft = currentPolicy.pendingPolicy ?? currentPolicy.currentPolicy;
+    setBoundary(boundaryTime(draft.boundaryMinutes));
+    setEffectiveDate(currentPolicy.pendingPolicy?.effectiveWorkDate ?? '');
+    setProposal(null);
+    setConfirmed(false);
+    setBusy(null);
+    setError(null);
+    setSuccess(null);
+  }, [client, ownerKey]);
+
+  const changeDraft = (change: () => void) => {
+    previewGeneration.current += 1;
+    change();
+    setProposal(null);
+    setConfirmed(false);
+    setError(null);
+    setSuccess(null);
+    setBusy((current) => (current === 'preview' ? null : current));
+  };
+  const requestPreview = async (event: FormEvent) => {
+    event.preventDefault();
+    const input: PolicyProposalInput = {
+      boundaryTime: boundary,
+      effectiveWorkDate: effectiveDate,
+      expectedRevision: policy.revision,
+    };
+    const request = ++previewGeneration.current;
+    const owner = ownerGeneration.current;
+    setBusy('preview');
+    setError(null);
+    setSuccess(null);
+    setConfirmed(false);
+    try {
+      const result = await client.request<PreviewAttendanceDayPolicyQuery>(
+        PreviewAttendanceDayPolicyDocument,
+        { input }
+      );
+      if (!ownsRequest(owner) || previewGeneration.current !== request) return;
+      setProposal({ input, preview: result.previewAttendanceDayPolicy });
+    } catch (reason) {
+      if (!ownsRequest(owner) || previewGeneration.current !== request) return;
+      setProposal(null);
+      setError(graphQlUserMessage(reason));
+    } finally {
+      if (ownsRequest(owner) && previewGeneration.current === request) setBusy(null);
+    }
+  };
+  const schedule = async () => {
+    if (!proposalIsConfirmed(proposal, confirmed, busy)) return;
+    const confirmedProposal = proposal;
+    const request = ++scheduleGeneration.current;
+    const owner = ownerGeneration.current;
+    const ownsSchedule = () => ownsRequest(owner) && scheduleGeneration.current === request;
+    setBusy('schedule');
+    setError(null);
+    setSuccess(null);
+    try {
+      const result = await client.request<{ scheduleAttendanceDayPolicy: AttendanceDayPolicy }>(
+        ScheduleAttendanceDayPolicyDocument,
+        { input: confirmedProposal.input }
+      );
+      if (!ownsSchedule()) return;
+      onPolicyChanged(result.scheduleAttendanceDayPolicy);
+      setProposal(null);
+      setConfirmed(false);
+      setSuccess('Attendance day change scheduled.');
+    } catch (reason) {
+      if (!ownsSchedule()) return;
+      setProposal(null);
+      setConfirmed(false);
+      if (!isConflict(reason)) {
+        setError(graphQlUserMessage(reason));
+      } else {
+        const message = await conflictMessage(reloadPolicy);
+        if (!ownsSchedule()) return;
+        setError(message);
+      }
+    } finally {
+      if (ownsSchedule()) setBusy(null);
+    }
+  };
+  return {
+    boundary,
+    busy,
+    changeDraft,
+    confirmed,
+    effectiveDate,
+    error,
+    preview: proposal?.preview ?? null,
+    requestPreview,
+    schedule,
+    setBoundary,
+    setConfirmed,
+    setEffectiveDate,
+    success,
+  };
+}

diff --git a/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx b/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx
new file mode 100644
index 0000000..06b8091
--- /dev/null
+++ b/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx
@@ -0,0 +1,124 @@
+// @vitest-environment jsdom
+
+import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
+import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
+
+import { AttendanceCurrentDayWindowDocument } from '../../../api/attendance/graphql';
+import type { useGraphClient } from '../../../hooks/useGraphClient';
+
+import { useCurrentAttendanceDayWindow } from './useAttendanceDayWindows';
+
+type GraphClient = ReturnType<typeof useGraphClient>;
+
+const deferred = <T,>() => {
+  let resolve!: (value: T | PromiseLike<T>) => void;
+  const promise = new Promise<T>((res) => {
+    resolve = res;
+  });
+  return { promise, resolve };
+};
+
+const windowResponse = (workDate: string, startsAt: string, endsAt: string) => ({
+  attendanceDayWindow: {
+    workDate,
+    startsAt,
+    endsAt,
+    timezone: 'UTC',
+    boundaryMinutes: 0,
+  },
+});
+
+beforeEach(() => {
+  vi.useFakeTimers({ shouldAdvanceTime: true });
+  vi.setSystemTime(new Date('2026-09-11T12:00:00Z'));
+});
+
+afterEach(() => {
+  cleanup();
+  vi.useRealTimers();
+});
+
+describe('useCurrentAttendanceDayWindow lifecycle', () => {
+  it('refreshes at the exact exclusive attendance-day end', async () => {
+    const request = vi
+      .fn()
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-11', '2026-09-10T12:01:00Z', '2026-09-11T12:01:00Z')
+      )
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-12', '2026-09-11T12:01:00Z', '2026-09-12T12:01:00Z')
+      );
+    const client = { request } as unknown as GraphClient;
+    const { result } = renderHook(() => useCurrentAttendanceDayWindow(client, 'tenant-1:user-1'));
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-11'));
+
+    await act(async () => {
+      vi.advanceTimersByTime(60_000);
+      await Promise.resolve();
+      await Promise.resolve();
+    });
+
+    expect(request).toHaveBeenCalledTimes(2);
+    expect(result.current.data?.workDate).toBe('2026-09-12');
+  });
+
+  it('refreshes when a suspended page regains focus without changing the selected period', async () => {
+    const request = vi
+      .fn()
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-11', '2026-09-10T12:00:00Z', '2026-09-12T12:00:00Z')
+      )
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-12', '2026-09-11T12:00:00Z', '2026-09-13T12:00:00Z')
+      );
+    const client = { request } as unknown as GraphClient;
+    const { result } = renderHook(() => useCurrentAttendanceDayWindow(client, 'tenant-1:user-1'));
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-11'));
+
+    window.dispatchEvent(new Event('focus'));
+
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-12'));
+    expect(request).toHaveBeenCalledTimes(2);
+  });
+
+  it('rejects an already-expired current-window response and fails closed', async () => {
+    const request = vi
+      .fn()
+      .mockResolvedValue(
+        windowResponse('2026-09-10', '2026-09-09T12:00:00Z', '2026-09-11T11:59:59Z')
+      );
+    const client = { request } as unknown as GraphClient;
+    const { result } = renderHook(() => useCurrentAttendanceDayWindow(client, 'tenant-1:user-1'));
+
+    await waitFor(() => expect(result.current.phase).toBe('initial-error'));
+    expect(result.current.data).toBeNull();
+  });
+
+  it('does not publish a delayed response after the client and identity change', async () => {
+    const stale = deferred<ReturnType<typeof windowResponse>>();
+    const oldRequest = vi.fn().mockReturnValue(stale.promise);
+    const newRequest = vi
+      .fn()
+      .mockResolvedValue(
+        windowResponse('2026-09-12', '2026-09-11T12:00:00Z', '2026-09-12T12:00:00Z')
+      );
+    let client = { request: oldRequest } as unknown as GraphClient;
+    let identity = 'tenant-1:user-1';
+    const { result, rerender } = renderHook(() => useCurrentAttendanceDayWindow(client, identity));
+    await waitFor(() =>
+      expect(oldRequest).toHaveBeenCalledWith(AttendanceCurrentDayWindowDocument)
+    );
+
+    client = { request: newRequest } as unknown as GraphClient;
+    identity = 'tenant-2:user-2';
+    rerender();
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-12'));
+
+    await act(async () => {
+      stale.resolve(windowResponse('2026-09-10', '2026-09-09T12:00:00Z', '2026-09-13T12:00:00Z'));
+      await stale.promise;
+    });
+
+    expect(result.current.data?.workDate).toBe('2026-09-12');
+  });
+});

diff --git a/src/modules/attendance/hooks/useAttendanceDayWindows.ts b/src/modules/attendance/hooks/useAttendanceDayWindows.ts
new file mode 100644
index 0000000..e27ed92
--- /dev/null
+++ b/src/modules/attendance/hooks/useAttendanceDayWindows.ts
@@ -0,0 +1,171 @@
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
+type CurrentWindow = AttendanceCurrentDayWindowQuery['attendanceDayWindow'];
+
+function validateCurrentWindow(window: CurrentWindow): void {
+  const startsAt = Date.parse(window.startsAt);
+  const endsAt = Date.parse(window.endsAt);
+  if (!Number.isFinite(startsAt) || !Number.isFinite(endsAt) || startsAt >= endsAt) {
+    throw new Error('Attendance day window response was invalid.');
+  }
+  if (Date.now() < startsAt || Date.now() >= endsAt) {
+    throw new Error('Attendance day window response was outside the current attendance day.');
+  }
+}
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
+    validateCurrentWindow(result.attendanceDayWindow);
+    return result.attendanceDayWindow;
+  }, [client, identity]);
+  const { data, error, phase, refresh } = useRetainedQuery(load);
+  const refreshedBoundary = useRef<string | null>(null);
+  const resumeInFlight = useRef<Promise<void> | null>(null);
+
+  useEffect(() => {
+    refreshedBoundary.current = null;
+    resumeInFlight.current = null;
+  }, [client, identity]);
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
+  const dataIsCurrent = Boolean(
+    phase === 'ready' &&
+    data &&
+    Date.now() >= Date.parse(data.startsAt) &&
+    Date.now() < Date.parse(data.endsAt)
+  );
+  return { data: dataIsCurrent ? data : null, error, phase, refresh };
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

