const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    const learner = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });
    const exe = b.addExecutable(.{ .name = "lab-06", .root_module = learner });
    b.installArtifact(exe);
    const tests = b.addTest(.{ .root_module = b.createModule(.{
        .root_source_file = b.path("test/contract.zig"),
        .target = target,
        .optimize = optimize,
        .imports = &.{.{ .name = "learner", .module = learner }},
    }) });
    b.step("test", "Run learner contract tests (SKIP until implemented)")
        .dependOn(&b.addRunArtifact(tests).step);
}
