const std = @import("std");
const chapters = [_][]const u8{
    "01-file-descriptor",
    "02-raw-file-io",
    "03-blocking-tcp",
    "04-nonblocking-tcp",
    "05-poll",
    "06-epoll",
    "07-epoll-echo-server",
    "08-epoll-chat-server",
    "09-io-uring-basics",
    "10-io-uring-file-io",
    "11-io-uring-network",
    "12-event-loop",
    "13-std-io",
    "14-std-io-async",
    "15-reactor-proactor",
    "16-benchmark",
    "capstone",
};

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    const selected = b.option([]const u8, "chapter", "Chapter 01..16 or capstone");
    const chapter_step = b.step("chapter", "Install selected chapter (default 01)");
    const test_step = b.step("test", "Run chapter contract tests");
    if (selected) |id| {
        var valid = false;
        for (chapters) |dir| {
            const short_id = if (std.mem.eql(u8, dir, "capstone")) dir else dir[0..2];
            if (std.mem.eql(u8, id, short_id) or std.mem.eql(u8, id, dir)) valid = true;
        }
        if (!valid) @panic("unknown chapter; use 01..16 or capstone");
    }
    for (chapters) |dir| {
        const id = if (std.mem.eql(u8, dir, "capstone")) dir else dir[0..2];
        if (selected) |choice| {
            if (!std.mem.eql(u8, choice, id) and !std.mem.eql(u8, choice, dir)) continue;
        }
        const learner = b.createModule(.{
            .root_source_file = b.path(b.fmt("{s}/src/main.zig", .{dir})),
            .target = target,
            .optimize = optimize,
        });
        const exe = b.addExecutable(.{ .name = b.fmt("lab-{s}", .{id}), .root_module = learner });
        const install = b.addInstallArtifact(exe, .{});
        b.getInstallStep().dependOn(&install.step);
        if (selected != null or std.mem.eql(u8, id, "01")) chapter_step.dependOn(&install.step);
        const tests = b.addTest(.{ .root_module = b.createModule(.{
            .root_source_file = b.path(b.fmt("{s}/test/contract.zig", .{dir})),
            .target = target,
            .optimize = optimize,
            .imports = &.{.{ .name = "learner", .module = learner }},
        }) });
        test_step.dependOn(&b.addRunArtifact(tests).step);
    }
}
