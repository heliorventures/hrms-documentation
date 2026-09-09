# HRMS video notifications implementation plan

> For agentic workers: use superpowers:subagent-driven-development. Backend/media is one independently testable task; root owns UI and integration. No commits.

**Goal:** Allow external video links and private video uploads with in-app playback and seeking.

**Architecture:** Keep image/document GraphQL uploads unchanged. Add a dedicated announcement video reference and operation-owned HTTP upload stage. Short-lived, purpose-bound media tickets carry tenant, user and stage/announcement identity; HTTP handlers recheck mutable account, scope and audience before accepting bytes or serving each range. Store private media using the existing local/S3 provider configuration.

**Tech stack:** Rust/Axum/SeaORM/PostgreSQL/Liquibase; React/TypeScript; existing HMAC, storage and GraphQL libraries.

**Spec:** ../specs/2026-09-08-hrms-enhancements.md, Phase 3 video requirements.

## Global constraints

- Initial uploaded video limit is 50 MiB (50 * 1024 * 1024 bytes). Reject oversize before/during reading, never Base64-encode video.
- Support MP4 and WebM containers; validate declared MIME against container signature. Browser codec support may vary; expose an actionable playback failure.
- External links use validated HTTP(S) URLs and open a new tab with noopener/noreferrer. Do not fetch arbitrary external URLs on the server.
- Respect tenant, author, employee-post moderation, publication window and audience restrictions for every playback request. Uploaded objects stay private.
- Preserve existing dirty notification automation, payroll, comp-off and Phase 1 work. No migrations, deployment, live writes, commits, Dart or Flutter commands.
- User has approved implementation and scoped tests/builds. Global codegen requires unavailable gateway 4009; export real service SDL offline and validate inline operations instead.

## Task 1: Media persistence, authorization and HTTP contract

**Files:** create `hrms-database/changelog/migrations/0079_announcement_video/announcement_video.xml`; extend announcement entity `hrms-svc/crates/kabipay-db-entities/src/tenant/d0027_communication_audit.rs`; create `d0079_announcement_video.rs`; notification `services/announcement_video.rs`, `services/announcement_audience.rs`, `http_media.rs`; modify notification main/lib/resolvers/storage/notification_service; extend cleanup worker integration only for expired video stages. Root registers migration/entity modules and changes deployment configuration.

**Interfaces produced:**

```graphql
mutation PrepareAnnouncementVideo($fileName: String!, $mimeType: String!, $fileSizeBytes: Int!) {
  prepareAnnouncementVideoUpload(fileName: $fileName, mimeType: $mimeType, fileSizeBytes: $fileSizeBytes) {
    stageId uploadUrl expiresAt
  }
}
query AnnouncementVideo($announcementId: UUID!) {
  announcementVideo(announcementId: $announcementId) { playbackUrl mimeType fileName expiresAt }
}
```

`POST /files/announcement-video/upload?token=...` consumes raw video bytes, returns JSON `{ stageId }` only when durable upload is complete. `GET /files/announcement-video/play?token=...` supports a single HTTP byte range, 206/416, Content-Range, Accept-Ranges and Content-Length. Tokens use a distinct purpose; do not reuse unrestricted employee-document tokens. Token URLs are generated from validated `KABIPAY_NOTIFICATION_PUBLIC_BASE`. Return `Cache-Control: private, no-store`, `Referrer-Policy: no-referrer` and `X-Content-Type-Options: nosniff`.

Announcement DTO adds `hasVideoAttachment: Boolean!` and `videoLink: String`. Create input adds optional `videoUploadStageId: UUID` and `videoLink: String`; update input adds these plus `removeVideo: Boolean`. Link and uploaded video are mutually exclusive per announcement. Stage claim is tenant+user bound and transactional with announcement creation/update. Preserve images/documents and moderation behavior. Expired, reused, wrong-owner and wrong-purpose stages fail closed; deletion/replacement and abandoned stages use durable cleanup without deleting referenced files.

- [x] Write failing unit/service tests for size bounds, MIME signature, ticket purpose/expiry, byte ranges, hidden parent authorization before storage, wrong-owner/reused stage and external URL validation.
- [x] Add migration constraints and entity fields, using tenant-qualified foreign keys and a dedicated stage parent relationship. Do not weaken existing company-document staging constraints.
- [x] Extract shared current announcement visibility checks and reuse them in existing attachments and media. Refresh mutable viewer account, employee/role audience state on playback.
- [x] Implement bounded upload to temporary storage with cleanup on failure, provider-backed persistence, atomic one-time claim and expiring abandoned-stage cleanup. Avoid buffering the full 50 MiB in memory and avoid user-controlled storage paths.
- [x] Implement partial local/S3 reads and HTTP response behavior. A useful range regression is `bytes=10-19` of size 100 -> status206, 10 bytes, Content-Range `bytes 10-19/100`; suffix and open ranges work; invalid/unsatisfiable ranges return416.
- [x] Extend DTOs and create/update/delete operations while preserving existing announcement authorization and cleanup.
- [x] Run notification tests and cargo check. Export actual SDL for root; write `../reviews/2026-09-08-phase3-video-backend.md` with paths, command results and runtime limitations.

## Task 2: Creation, playback and deployment integration (root)

**Files:** notification form/types/controller and input helper; `modules/notifications/videoDocuments.ts`, `announcementVideoUpload.ts`, `components/AnnouncementVideo.tsx`; announcement list; admin edit input/form; UI schema extension; notification public-base environment examples and `hrms-documentation/deploy/Caddyfile.example`.

- [x] Add compact link/upload choice to announcement creation and editing. Upload shows progress and can be cancelled; disallow duplicate submission and stale tenant/session completion.
- [x] Prepare stage via GraphQL, send raw bytes with XHR for progress, then create/update announcement with the returned stage ID. Preserve a completed stage across a retry of the same submission; discard it when the file/owner changes.
- [x] Fetch an authorized playback URL on explicit play; render native video controls with metadata preload, inline mobile playback, seeking and retry/renewal for expired playback tickets. Never load the full video as a browser Blob.
- [x] Render external link with clear label, new-tab behavior and no unsafe schemes. Keep inaccessible media errors actionable without exposing storage coordinates.
- [x] Add Caddy proxy for `/files/announcement-video/*` to notification port4028 in API, tenant-host and local sections; document the public-base config and 50 MiB proxy allowance. No deployment.
- [x] Verify UI cap/MIME/link validation, progress/cancellation, stale owner completion and playback behavior. Validate new queries and announcement shapes against actual exported SDL, run scoped lint/TypeScript/build.

## Task 3: Review and evidence

- [x] Independent source review of tenant/audience authorization, stage races, cleanup and range behavior; resolve material findings.
- [x] Record functional/static tests separately from signed-in browser, actual uploaded media/provider and deployment proof. Leave source uncommitted.

## Ledger

- Preflight: Tasks1/2 share only the explicitly named GraphQL/HTTP contract; backend implementer does not edit UI or deployment files. Root alone registers shared entity/migration lists. Existing company-document stage is not reused because its FK and purpose constrain it to company documents.
- Technical choice: MP4/WebM are the initial browser-playable containers; 50 MiB uses the existing application's binary-megabyte convention. Ticket lifetime is a short technical access window and does not change announcement publication expiry.

## Final source/static status

Implemented and source-reviewed; scoped tests, actual SDL validation, TypeScript, production UI build and scoped lint passed. See phase-specific review files. Checked items describe source/static work only. Browser, live tenant/provider, migration and deployment acceptance remain outstanding. No commits or live writes.
