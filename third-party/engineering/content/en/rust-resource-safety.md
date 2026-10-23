# Rust resource and failure safety

Status: engineering guidance, version 0.1.3. Reviewed against the primary
references below on 2026-10-21. Each implementation records its actual supported
Rust/dependency versions and test environment separately. Re-review when runtime,
allocator, subprocess handling, OS containment or input limits change.

## Memory and data boundaries

Validate sizes before allocation, then enforce per-item and aggregate byte,
entry and nesting budgets while reading. Prefer streaming hashing, parsing and
copying; a checked file size does not justify reading an archive into one buffer.
Reject changes observed during a read. Bound decompressed data independently.
For retained collections use checked arithmetic and fallible reservation where
appropriate. Do not promise recovery from every allocator failure: some aborts
and OS kills cannot be handled inside the process. `catch_unwind` is not OOM
containment. Review repeated cloning, retained `Arc` graphs and unbounded caches.

## Concurrency belongs to a shared budget

Acquire a capacity permit before spawning work. Bound channels, queues, workers,
processes and retries, and apply backpressure rather than accumulating tasks.
Separate products running on the same machine share an admission budget; a
per-process cap alone is insufficient. CPU quotas and job-count flags do not
necessarily constrain library thread pools. Verify effective CPU affinity and
pool settings as well as the aggregate process/thread limit.

Use fallible thread admission (`Builder::spawn_scoped`) where exhaustion is
possible. A scoped join still waits for already-created workers after a later
spawn fails; a fixed-count barrier can therefore deadlock during error handling.
Give waiting workers a cancellation path, release them before joining, and test
partial admission without exhausting the host. A refused required worker is a
failed test, not reduced concurrency reported as complete coverage.

## Ownership, interruption and errors

Use typed outcomes for unavailable resources, cancelled work, timeout, child
failure and incomplete evidence. Await each owned child and release permits on
all exit paths. A timeout around a future is not proof its blocking operation
stopped. Review cancellation requirements before using `spawn_blocking`; started
blocking tasks are not made stoppable by aborting their handles.

Prefer maintained OS/runtime libraries for process supervision. Terminate only
verified owned children or the dedicated job/container; never target PID/group
zero, the user's session, the VM or unrelated processes. Use bounded graceful
shutdown followed by bounded forced termination and reap completion. Drain or
bound output so a full pipe cannot deadlock shutdown. Library code returns
errors rather than terminating its host process.

## Host protection and failure evidence

Check effective resource delegation before launching a build or stress test.
Keep explicit headroom for the host and abort admission if it is unavailable.
Combine OS memory/process limits with a shared admission lock, serial defaults,
bounded runtime and pressure observation. A cgroup limit does not prove that a
VM, filesystem or ancestor group is immune to failure. Never claim platform
safety from a single successful containment probe.

Write an incomplete marker before expensive work; commit success only after
all required steps, artifact hashes and source/version checks complete. The
outside supervisor records abnormal unit exits. Missing or truncated records
remain failures. A killed process cannot reliably write its own final receipt.
After an abrupt stop, preserve local changes and verify repository integrity;
do not build or publish from a corrupt Git object database.

## Build storage and dependency budgets

Measure published archives separately from local build directories. Debug symbols,
incremental state, feature combinations, targets and repeated dependency builds can
dominate `target/` without increasing the delivered package. For constrained local
checks, use one Cargo job, `debug = 0` and `incremental = false` in the dev/test
profiles, while keeping assertions and overflow checks enabled. Full debugger
information is an explicit alternative; release settings remain owner-controlled.
These settings reduce build storage, not a guaranteed memory ceiling.

Review duplicate dependency versions by inverse dependency paths and enabled
features. Separate optional, test, build and target-specific dependencies from
the product runtime. Do not force incompatible versions together, lower security
requirements, or bump package versions merely to deduplicate a lockfile. Verify
actual consumer/API compatibility before changing a dependency boundary.

Use bounded file-list/archive inspection before rebuilding. Exclude local state,
credentials, caches and compiler output from source packages; retain required
licenses, notices and runtime dependencies. Clean reproducible output only after
checking active builders and tracked files. Keep source, unmerged work and receipts.
Use finite retention for per-candidate build directories rather than accumulating
copies indefinitely. On WSL, deleting guest files does not guarantee immediate
reclamation of the Windows VHD allocation; check host free space separately.

## Private temporary and test state

Create private test directories with explicit permissions and trusted ancestry;
do not assume a caller's umask or a build directory is private. Keep the cleanup
guard alive until its users finish, and set generated helper executable/configuration
permissions before admission. Construct unsafe permissions explicitly in rejection
tests. A harness may tighten its own creation mask for owned children; it must not
change a user's session or weaken production validation. Unix permission tests and
portable contract tests are not Windows ACL/DPAPI acceptance.

## Tests and review

Use small synthetic inputs and controlled child exits for ordinary regressions.
Test limits, cancellation before/after spawn, missing executables, failed exit,
partial output, unavailable isolation and rejected publication without exhausting
host memory. Actual OOM, large fan-out and VM-kill experiments require a separate
explicitly reviewed disposable environment. Record measured peak memory/tasks,
exit reason, skipped cases and scope; distinguish leaks from bounded high use,
thread exhaustion, abrupt host failure and an unknown cause.

A local build is not hosted CI, full product acceptance or provenance attestation.
Its exact source, version, executed steps and artifacts remain explicit. Never
change a failed hosted check to passed merely because a different local scope
completed. Keep implementation units focused, normally under 120 lines, and
avoid adding a second custom runtime, encryption layer or lifecycle authority.

## Primary references

- [Rust Vec and fallible reservation](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.try_reserve)
- [Tokio blocking-task cancellation](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html)
- [systemd resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html)
- [Cargo build profiles](https://doc.rust-lang.org/cargo/reference/profiles.html)
- [Cargo package file selection](https://doc.rust-lang.org/cargo/reference/manifest.html#the-include-and-exclude-fields)

- [tempfile Builder permissions](https://docs.rs/tempfile/3.27.0/tempfile/struct.Builder.html#method.permissions)
- [Rust fallible scoped thread creation](https://doc.rust-lang.org/std/thread/struct.Builder.html#method.spawn_scoped)
- [Rust scope joining guarantees](https://doc.rust-lang.org/std/thread/fn.scope.html)
